"""One-off helper: rewrite oz, shot, and ml measures in the cocktail seed file to cl.

Superseded by normalize_measures.py, which performs full measure normalization.
This script is kept for reference and partial conversions only.

Uses 1 oz = 3 cl, 1 shot = 4 cl (US standard), and 10 ml = 1 cl. Handles
integers, decimals, fractions, mixed numbers and ranges, keeping any descriptor
text after the unit."""

import json
import os
import re
from fractions import Fraction

SEED_FILE = os.path.join(os.path.dirname(__file__), "cocktails_seed.json")

CL_PER_OZ = 3
CL_PER_SHOT = 4
ML_TO_CL = Fraction(1, 10)

_QTY = r'(?:\d+\s+\d+/\d+|\d+/\d+|\d*\.\d+|\d+)'
_OZ_RE = re.compile(
    rf'(?P<low>{_QTY})(?:\s*-\s*(?P<high>{_QTY}))?\s*(?:fl\.?\s*)?oz\b',
    re.IGNORECASE,
)
_SHOT_RE = re.compile(
    rf'(?P<low>{_QTY})(?:\s*-\s*(?P<high>{_QTY}))?\s*shots?\b',
    re.IGNORECASE,
)
_ML_RE = re.compile(
    rf'(?P<low>{_QTY})(?:\s*-\s*(?P<high>{_QTY}))?\s*ml\b',
    re.IGNORECASE,
)

# 70 ml is exactly 7 cl; the "2 fl oz" part is just the imperial approximation.
_SPECIAL_CASES = {'70ml/2fl oz': '7 cl'}

def _quantity_to_cl(quantity_text, cl_per_unit):
    quantity = sum(Fraction(part) for part in quantity_text.split()) * cl_per_unit
    if quantity.denominator == 1:
        return str(quantity.numerator)
    return f"{float(quantity):.2f}".rstrip('0').rstrip('.')


def _convert_unit_match(match, cl_per_unit):
    low = _quantity_to_cl(match.group('low'), cl_per_unit)
    if match.group('high'):
        return f"{low}-{_quantity_to_cl(match.group('high'), cl_per_unit)} cl"
    return f"{low} cl"


def _convert_oz_match(match):
    return _convert_unit_match(match, CL_PER_OZ)


def _convert_shot_match(match):
    return _convert_unit_match(match, CL_PER_SHOT)


def _convert_ml_match(match):
    return _convert_unit_match(match, ML_TO_CL)


def convert_measure(measure):
    if measure is None:
        return measure, False
    if measure.strip() in _SPECIAL_CASES:
        return _SPECIAL_CASES[measure.strip()] + " ", True
    converted = _SHOT_RE.sub(_convert_shot_match, measure)
    converted = _OZ_RE.sub(_convert_oz_match, converted)
    converted = _ML_RE.sub(_convert_ml_match, converted)
    return converted, converted != measure


def convert_seed_file():
    with open(SEED_FILE, encoding="utf-8") as f:
        cocktails = json.load(f)

    converted_count = 0
    for cocktail in cocktails:
        for i in range(1, 16):
            key = f"measure_{i}"
            new_measure, changed = convert_measure(cocktail[key])
            if changed:
                cocktail[key] = new_measure
                converted_count += 1

    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(cocktails, f, ensure_ascii=False, indent=1)

    print(f"Converted {converted_count} measures in {os.path.abspath(SEED_FILE)}")


if __name__ == "__main__":
    convert_seed_file()
