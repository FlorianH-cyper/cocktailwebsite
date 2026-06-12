"""One-off helper: rewrite all oz measures in the cocktail seed file to cl,
using the bartending convention 1 oz = 3 cl. Handles integers ("2 oz"),
decimals ("1.5 oz"), fractions ("1/2 oz"), mixed numbers ("1 1/2 oz") and
ranges ("2-3 oz"), keeping any descriptor text around the quantity."""

import json
import os
import re
from fractions import Fraction

SEED_FILE = os.path.join(os.path.dirname(__file__), "cocktails_seed.json")

CL_PER_OZ = 3

_QTY = r'(?:\d+\s+\d+/\d+|\d+/\d+|\d*\.\d+|\d+)'
_OZ_RE = re.compile(
    rf'(?P<low>{_QTY})(?:\s*-\s*(?P<high>{_QTY}))?\s*(?:fl\.?\s*)?oz\b',
    re.IGNORECASE,
)

# 70 ml is exactly 7 cl; the "2 fl oz" part is just the imperial approximation.
_SPECIAL_CASES = {'70ml/2fl oz': '7 cl'}


def _quantity_to_cl(text):
    quantity = sum(Fraction(part) for part in text.split()) * CL_PER_OZ
    if quantity.denominator == 1:
        return str(quantity.numerator)
    return f"{float(quantity):.2f}".rstrip('0').rstrip('.')


def _convert_match(match):
    low = _quantity_to_cl(match.group('low'))
    if match.group('high'):
        return f"{low}-{_quantity_to_cl(match.group('high'))} cl"
    return f"{low} cl"


def convert_measure(measure):
    if measure is None:
        return measure, False
    if measure.strip() in _SPECIAL_CASES:
        return _SPECIAL_CASES[measure.strip()] + " ", True
    converted = _OZ_RE.sub(_convert_match, measure)
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
