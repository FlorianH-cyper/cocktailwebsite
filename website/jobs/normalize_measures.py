"""Normalize cocktail seed measures to parseable, consistent units per ingredient.

Usage:
    python normalize_measures.py --generate-map   # create ingredient_unit_map.json
    python normalize_measures.py                  # dry-run + report
    python normalize_measures.py --write          # apply changes to cocktails_seed.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from fractions import Fraction

JOBS_DIR = os.path.dirname(__file__)
SEED_FILE = os.path.join(JOBS_DIR, "cocktails_seed.json")
MAP_FILE = os.path.join(JOBS_DIR, "ingredient_unit_map.json")
REPORT_FILE = os.path.join(JOBS_DIR, "normalize_report.txt")

CL_PER_OZ = Fraction(3)
CL_PER_SHOT = Fraction(4)
ML_TO_CL = Fraction(1, 10)
CL_PER_CUP = Fraction(24)
CL_PER_TBLSP = Fraction(3, 2)  # 1.5 cl
CL_PER_TSP = Fraction(1, 2)  # 0.5 cl
CL_PER_PINT = Fraction(48)
CL_PER_QT = Fraction(96)
CL_PER_GAL = Fraction(384)
CL_PER_L = Fraction(100)
CL_PER_JIGGER = Fraction(4, 5) * CL_PER_OZ  # 1.5 oz
CL_PER_FIFTH = Fraction(75)
CL_PER_BOTTLE = Fraction(75)
CL_PER_SPLASH = Fraction(3, 2)
CL_PER_DL = Fraction(10)
CL_PER_DROP = Fraction(1, 64) * CL_PER_TSP
CL_PER_LB = Fraction(48)  # rough liquid equivalent, rarely used
CL_PER_CAN = Fraction(33)  # ~330 ml
CL_PER_GLASS = Fraction(12)
CL_PER_BEER_GLASS = Fraction(50)
DROPS_PER_DASH = 4
CUP_PER_SCOOP = Fraction(1, 2)

# Longest-first so "tablespoons" matches before "tablespoon".
BASE_UNITS = (
    "tablespoons", "tablespoon", "teaspoons", "teaspoon", "jiggers", "jigger",
    "dashes", "dash", "shots", "shot", "splashes", "splash", "tablespoons",
    "cups", "cup", "pints", "pint", "quarts", "quart", "qt", "gallons", "gal",
    "bottles", "bottle", "fifths", "fifth", "parts", "part", "tblsp", "tbsp", "tsp",
    "spoons", "spoon",
    "measures", "measure",
    "sprigs", "sprig", "slices", "slice", "wedges", "wedge", "pieces", "piece",
    "sticks", "stick", "pinches", "pinch", "drops", "drop", "scoops", "scoop",
    "cans", "can", "handful", "inch", "inches", "whole", "cl", "ml", "oz", "l",
    "dl", "lb", "gr", "gram", "grams",
)

_QTY = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d*\.\d+|\d+)"
_MEASURE_RE = re.compile(rf"^\s*({_QTY})(?:\s*-\s*({_QTY}))?\s*(.*?)\s*$", re.IGNORECASE)

# Instruction-only measures → null (no shopping-list quantity).
_INSTRUCTION_ONLY = re.compile(
    r"^(top(?:\s+up\s+with|it\s+up\s+with)?|fill\s+with|garnish\s+with|to\s+taste|"
    r"to\s+fill|chilled|if\s+needed|optional|for\s+color|for\s+garnish|float|layer|"
    r"garnish|frozen|crushed|full\s+glass|squeeze|unsweetened|strong\s+cold|"
    r"\(if\s+needed\)|\(seltzer\s+water\)|\(claret\)|fill\s+to\s+top|"
    r"top\s+it\s+up\s+with|a\s+little\s+bit\s+of|very\s+sweet|float\s+\w+|"
    r"pods|grated|rimmed|for\s+topping|turkish\s+apple|mikey\s+bottle|"
    r"large\s+bottle|fill\s+to\s+top\s+with|or\s+lime)\.?$",
    re.IGNORECASE,
)

_LITERAL_FIXES = {
    "dash": "1 dash",
    "top": None,
    "fill with": None,
    "garnish with": None,
    "garnish": None,
    "to taste": None,
    "twist of": None,
    "whole": "1 piece",
    "pinch": "1 pinch",
    "fresh": None,
    "coarse": None,
    "black": None,
    "mini": None,
    "bacardi": None,
    "top up": None,
    "for topping": None,
    "by taste": None,
    "grated": None,
    "rimmed": None,
    "splash": "1 splash",
}

from ingredient_unit_rules import (
    FRUIT_UNIT,
    PRODUCE_UNIT,
    classify_ingredient,
)

COUNTABLE_GARNISH = {
    "Mint", "Cherry", "Maraschino cherry", "Maraschino Cherry", "Olive",
    "Basil", "Rosemary",
}
WHOLE_PRODUCE_NAMES = frozenset({
    "strawberries", "blueberries", "berries", "cranberries",
    "apple", "banana", "pineapple", "grapes", "mango", "papaya",
    "watermelon", "cantaloupe", "apricot", "peach", "kiwi", "figs",
    "carrot", "cucumber", "ginger", "fruit",
})
PRODUCE_COUNT_UNITS = frozenset({"piece", "pieces", "whole", "large", "medium", "small", "ripe"})
WHOLE_FRUIT_NAMES = frozenset({"lemon", "lime", "orange"})
LIQUID_CL_CATEGORIES = {"spirit", "liqueur", "wine_vermouth", "juice", "mixer", "dairy", "premix"}
CL_PER_FRUIT = Fraction(3)
MAX_FRUIT_COUNT = Fraction(6)


def _parse_quantity(text: str) -> Fraction:
    return sum(Fraction(part) for part in text.split())


def _is_whole_fruit(ingredient: str) -> bool:
    return ingredient.strip().lower() in WHOLE_FRUIT_NAMES


def _is_whole_produce(ingredient: str) -> bool:
    lower = ingredient.strip().lower()
    return lower in WHOLE_PRODUCE_NAMES or lower.endswith("berries")


def _cl_to_produce(qty_cl: Fraction) -> tuple[Fraction, str] | None:
    if qty_cl <= 0:
        return None
    if qty_cl == CL_PER_LB:
        return Fraction(1), "lb"
    if qty_cl % CL_PER_CUP == 0 and qty_cl / CL_PER_CUP <= 10:
        return qty_cl / CL_PER_CUP, "cup"
    # Small whole cl values on produce are usually miscounted pieces (e.g. "3" -> "3 cl").
    if qty_cl <= 12 and qty_cl.denominator == 1:
        return qty_cl, "piece"
    if qty_cl <= 12 and qty_cl % CL_PER_FRUIT == 0:
        return qty_cl / CL_PER_FRUIT, "piece"
    return None


def _format_produce_measure(quantity: Fraction, unit: str) -> str:
    unit = _singular_unit(unit.strip().lower())
    if unit in PRODUCE_COUNT_UNITS or unit == "piece":
        return f"{_format_quantity(quantity)} {unit if unit != 'whole' else 'piece'}"
    if not unit:
        return f"{_format_quantity(quantity)} piece"
    qty_text = _format_quantity(quantity)
    if unit == "cup" and quantity.denominator in (1, 2, 4):
        qty_text = _format_fruit_quantity(quantity)
    return f"{qty_text} {unit}".strip()


def _format_fruit_quantity(quantity: Fraction) -> str:
    whole, remainder = divmod(quantity.numerator, quantity.denominator)
    if remainder == 0:
        return str(whole)
    if whole == 0:
        return f"{remainder}/{quantity.denominator}"
    return f"{whole} {remainder}/{quantity.denominator}"


def _format_quantity(quantity: Fraction) -> str:
    if quantity.denominator == 1:
        return str(quantity.numerator)
    value = float(quantity)
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _format_measure(quantity: Fraction, unit: str) -> str:
    if unit == FRUIT_UNIT:
        return _format_fruit_quantity(quantity)
    qty = _format_quantity(quantity)
    unit = unit.strip()
    if not unit:
        return qty
    return f"{qty} {unit}"


def parse_measure(measure: str | None) -> tuple[Fraction, Fraction | None, str] | None:
    """Return (low, high_or_none, unit) or None if unparseable."""
    if not measure or not str(measure).strip():
        return None
    match = _MEASURE_RE.match(str(measure).strip())
    if not match:
        return None
    low_text, high_text, unit = match.groups()
    low = _parse_quantity(low_text)
    high = _parse_quantity(high_text) if high_text else None
    return low, high, unit.strip()


def _average_quantity(low: Fraction, high: Fraction | None) -> Fraction:
    if high is None:
        return low
    return (low + high) / 2


def extract_base_unit(unit: str) -> str:
    """Return canonical base unit, stripping brand/descriptor suffixes."""
    if not unit:
        return ""
    text = unit.strip().lower()
    if re.match(r"^c[lL]$", text):
        return "cl"
    if text.startswith("cl ") or text.startswith("cl."):
        return "cl"
    for base in BASE_UNITS:
        if text == base or text.startswith(base + " ") or text.startswith(base + ","):
            return _singular_unit(base)
    token = text.split()[0] if text.split() else text
    return _singular_unit(token)


def _singular_unit(unit: str) -> str:
    mapping = {
        "tablespoons": "tblsp",
        "tablespoon": "tblsp",
        "teaspoons": "tsp",
        "teaspoon": "tsp",
        "dashes": "dash",
        "splashes": "splash",
        "shots": "shot",
        "jiggers": "jigger",
        "cups": "cup",
        "pints": "pint",
        "pint": "pint",
        "quarts": "qt",
        "quart": "qt",
        "gallons": "gal",
        "gallon": "gal",
        "bottles": "bottle",
        "fifths": "fifth",
        "parts": "part",
        "tbsp": "tblsp",
        "measures": "measure",
        "sprigs": "sprig",
        "slices": "slice",
        "wedges": "wedge",
        "pieces": "piece",
        "sticks": "stick",
        "pinches": "pinch",
        "drops": "drop",
        "scoops": "scoop",
        "cans": "can",
        "inches": "inch",
        "grams": "gr",
        "gram": "gr",
        "spoons": "tblsp",
        "spoon": "tblsp",
    }
    return mapping.get(unit, unit)


def _normalize_unit_token(unit: str) -> str:
    return extract_base_unit(unit)


def _unit_to_cl_factor(unit: str) -> Fraction | None:
    u = _normalize_unit_token(unit)
    mapping = {
        "cl": Fraction(1),
        "ml": ML_TO_CL,
        "oz": CL_PER_OZ,
        "shot": CL_PER_SHOT,
        "jigger": CL_PER_JIGGER,
        "cup": CL_PER_CUP,
        "tblsp": CL_PER_TBLSP,
        "tsp": CL_PER_TSP,
        "pint": CL_PER_PINT,
        "qt": CL_PER_QT,
        "gal": CL_PER_GAL,
        "l": CL_PER_L,
        "dl": CL_PER_DL,
        "fifth": CL_PER_FIFTH,
        "bottle": CL_PER_BOTTLE,
        "splash": CL_PER_SPLASH,
        "drop": CL_PER_DROP,
        "lb": CL_PER_LB,
        "measure": CL_PER_OZ,  # 1 measure ~= 1 oz
        "can": CL_PER_CAN,
        "glass": CL_PER_GLASS,
    }
    return mapping.get(u)


def _dash_to_target(quantity: Fraction, target: str) -> tuple[Fraction, str]:
    if target == "dash":
        return quantity, "dash"
    if target == "cl":
        return quantity * CL_PER_TSP / 4, "cl"  # ~1 dash = 1/8 tsp
    if target == "tsp":
        return quantity / 4, "tsp"
    return quantity, target


def _tsp_to_target(quantity: Fraction, target: str) -> tuple[Fraction, str]:
    if target == "tsp":
        return quantity, "tsp"
    if target == "cl":
        return quantity * CL_PER_TSP, "cl"
    return quantity, target


BATCH_VOLUME_UNITS = frozenset({"pint", "qt", "gal", "l", "dl"})


def _batch_volume_to_cl(quantity: Fraction, base_unit: str) -> Fraction | None:
    """Batch sizes (L, pint, quart, …) always become cl — never pinch/tsp/dash."""
    factor = _unit_to_cl_factor(base_unit)
    if factor is None:
        return None
    return quantity * factor


def generate_unit_map(cocktails: list[dict]) -> dict[str, dict]:
    """Build ingredient -> {category, unit} from rules only."""
    unit_map: dict[str, dict] = {}
    for cocktail in cocktails:
        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            if ing and ing not in unit_map:
                category, unit = classify_ingredient(ing)
                unit_map[ing] = {"category": category, "unit": unit}

    return dict(sorted(unit_map.items(), key=lambda x: x[0].lower()))


def _fix_literal_measure(measure: str) -> str | None:
    """Map known literal strings before numeric parsing."""
    m = measure.strip()
    if not m:
        return None
    lower = m.lower()
    if lower in _LITERAL_FIXES:
        fixed = _LITERAL_FIXES[lower]
        return fixed if fixed is not None else None
    if _INSTRUCTION_ONLY.match(m):
        return None
    if lower.startswith("twist of") or lower.endswith("twist of"):
        return None
    if lower.startswith("add splash"):
        return "1 splash"
    add_cl = re.match(r"^add\s+(\d+(?:\.\d+)?)\s*cl\b", m, re.I)
    if add_cl:
        return f"{add_cl.group(1)} cl"
    add_splash = re.match(r"^add\s+splash$", m, re.I)
    if add_splash:
        return "1 splash"
    rim_pinch = re.search(r"(\d+)\s+pinch", m, re.I)
    if rim_pinch:
        return f"{rim_pinch.group(1)} pinch"
    if m in ("½", "1/2"):
        return "1/2"
    if m.startswith(", "):
        return None
    if re.match(r"^dash\.?$", m, re.I):
        return "1 dash"
    about_drops = re.match(r"^about\s+(\d+)\s+drops?$", m, re.I)
    if about_drops:
        return f"{about_drops.group(1)} drop"
    about_bottle = re.match(r"^about\s+1\s+bottle$", m, re.I)
    if about_bottle:
        return "1 bottle"
    or_pattern = re.match(r"^(\d+)\s+or\s+(\d+)$", m, re.I)
    if or_pattern:
        low = int(or_pattern.group(1))
        high = int(or_pattern.group(2))
        avg = Fraction(low + high, 2)
        return _format_quantity(avg)
    return m


def _convert_juice_of(measure: str, ingredient: str, target_unit: str) -> str | None:
    m = measure.strip().lower()
    if target_unit == FRUIT_UNIT:
        juice_fruit_map = {
            "juice of 1/4": Fraction(1, 4),
            "juice of 1/2": Fraction(1, 2),
            "juice of 1": Fraction(1),
            "juice of 2": Fraction(2),
        }
        for pattern, fruit_qty in juice_fruit_map.items():
            if m.startswith(pattern):
                return _format_measure(fruit_qty, FRUIT_UNIT)
        return None
    juice_cl_map = {
        "juice of 1/4": Fraction(3, 4),
        "juice of 1/2": Fraction(3, 2),
        "juice of 1": Fraction(3),
        "juice of 2": Fraction(6),
    }
    for pattern, cl_qty in juice_cl_map.items():
        if m.startswith(pattern):
            if target_unit == "cl":
                return _format_measure(cl_qty, "cl")
            return measure
    return None


def _cl_to_fruit_quantity(qty_cl: Fraction) -> Fraction | None:
    fruit_qty = qty_cl / CL_PER_FRUIT
    if fruit_qty <= 0 or fruit_qty > MAX_FRUIT_COUNT:
        return None
    return fruit_qty


def _normalize_fruit_measure(measure: str, target_unit: str) -> str | None:
    if target_unit != FRUIT_UNIT:
        return None
    parsed = parse_measure(measure)
    if parsed:
        low, high, unit = parsed
        qty = _average_quantity(low, high)
        base = _normalize_unit_token(unit)
        if base == "cl":
            if qty == CL_PER_LB:
                return _format_measure(Fraction(1), "lb")
            fruit_qty = _cl_to_fruit_quantity(qty)
            if fruit_qty is not None:
                return _format_measure(fruit_qty, FRUIT_UNIT)
            return measure
        if base in ("slice", "wedge"):
            return f"{_format_fruit_quantity(qty)} {base}"
        if base in ("lb",):
            return _format_measure(qty, "lb")
        if not base or base in ("whole", "large", "medium", "small"):
            return _format_measure(qty, FRUIT_UNIT)
    if re.match(r"^\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$", measure.strip()):
        parts = re.split(r"\s*-\s*", measure.strip())
        low = _parse_quantity(parts[0])
        high = _parse_quantity(parts[1]) if len(parts) > 1 else None
        return _format_measure(_average_quantity(low, high), FRUIT_UNIT)
    return None


def _normalize_produce_measure(measure: str, target_unit: str) -> str | None:
    if target_unit != PRODUCE_UNIT:
        return None
    parsed = parse_measure(measure)
    if parsed:
        low, high, unit = parsed
        qty = _average_quantity(low, high)
        base = _normalize_unit_token(unit)
        if base == "cl":
            converted = _cl_to_produce(qty)
            if converted is not None:
                q, u = converted
                return _format_produce_measure(q, u)
            return measure
        if base in ("cup", "lb", "piece") or base in PRODUCE_COUNT_UNITS:
            return _format_produce_measure(qty, base)
        if not base:
            return _format_produce_measure(qty, "piece")
    if re.match(r"^\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$", measure.strip()):
        parts = re.split(r"\s*-\s*", measure.strip())
        low = _parse_quantity(parts[0])
        high = _parse_quantity(parts[1]) if len(parts) > 1 else None
        return _format_produce_measure(_average_quantity(low, high), "piece")
    return None


def _normalize_dashes(measure: str) -> str | None:
    m = measure.strip()
    if re.match(r"^dash(es)?\.?$", m, re.I):
        return "1 dash"
    if re.match(r"^(\d+)\s*dash(es)?\.?$", m, re.I):
        n = re.match(r"^(\d+)", m).group(1)
        return f"{n} dash"
    return None


def _normalize_piece_measures(measure: str, target_unit: str, ingredient: str = "") -> str | None:
    m = measure.strip().lower()
    ing_lower = ingredient.lower()
    if m in ("1 cube", "cube") and target_unit == "tsp":
        return "1 tsp"
    if m == "cubes" and target_unit == "tsp":
        return "1 tsp"
    piece_patterns = {
        "1 cube": ("1", "piece"),
        "cube": ("1", "piece"),
        "sprig": ("1", "sprig"),
        "sprigs": ("1", "sprig"),
        "twist of": None,
        "wedge": ("1", "wedge"),
        "wedges": ("1", "wedge"),
        "slice": ("1", "slice"),
        "cubes": None,
        "crushed": None,
        "ground": ("1", "tsp"),
        "chopped": ("1", "tsp"),
    }
    for pattern, result in piece_patterns.items():
        if m == pattern or m.startswith(pattern + " "):
            if result is None:
                return None
            qty, unit = result
            if target_unit in ("piece", "sprig", "slice", "stick", "pinch", "tsp", "wedge"):
                use = target_unit if target_unit != "wedge" or unit == "wedge" else unit
                if target_unit == "tsp" and unit == "piece":
                    return "1 tsp"
                return f"{qty} {use}"
            return f"{qty} {unit}"
    parsed = parse_measure(measure)
    if parsed:
        low, high, unit = parsed
        base = _normalize_unit_token(unit)
        qty = _average_quantity(low, high)
        if base in ("cube", "cubes") and target_unit == "tsp":
            return _format_measure(qty, "tsp")
        if base in ("cube", "cubes") and target_unit == "piece":
            return _format_measure(qty, "piece")
        if base in ("sprig", "sprigs") and target_unit == "sprig":
            return _format_measure(qty, "sprig")
        if base in ("slice", "wedge", "piece", "whole") and target_unit in ("piece", "slice", "wedge", FRUIT_UNIT):
            out_unit = base if target_unit == FRUIT_UNIT and base in ("slice", "wedge") else target_unit
            if target_unit == FRUIT_UNIT and base in ("slice", "wedge"):
                return f"{_format_fruit_quantity(qty)} {base}"
            return _format_measure(qty, out_unit)
        if base in ("stick", "sticks") and target_unit == "stick":
            return _format_measure(qty, "stick")
        if base in ("pinch", "pinches") and target_unit == "tsp":
            return _format_measure(qty / 16, "tsp")
        if base in ("pinch", "pinches") and target_unit == "pinch":
            return _format_measure(qty, "pinch")
        if base in ("dash", "dashes") and target_unit == "dash":
            return _format_measure(qty, "dash")
        if not base and target_unit == "sprig" and ing_lower == "mint":
            return _format_measure(qty, "sprig")
        if not base and target_unit in ("piece", "sprig") and qty <= 10:
            return _format_measure(qty, target_unit)
    if re.match(r"^\d+(?:\s*-\s*\d+)?$", m) and target_unit == "sprig" and ing_lower == "mint":
        parts = re.split(r"\s*-\s*", m)
        low = _parse_quantity(parts[0])
        high = _parse_quantity(parts[1]) if len(parts) > 1 else None
        return _format_measure(_average_quantity(low, high), "sprig")
    return None


def _parts_target_total(cocktail: dict, total_parts: Fraction) -> Fraction:
    cat = (cocktail.get("category") or "").lower()
    glass = (cocktail.get("glass") or "").lower()
    if "shot" in cat or "shot glass" in glass or "cordial glass" in glass:
        return Fraction(45, 10)  # 4.5 cl
    if cat == "beer" or "pint" in glass:
        return Fraction(50)
    if "punch" in cat or "party" in cat:
        return max(Fraction(24), total_parts * Fraction(3, 2))
    if any(g in glass for g in ("collins", "highball", "hurricane", "mason", "beer")):
        return Fraction(18)
    return Fraction(12)


def _resolve_cl_per_part(
    cocktail: dict,
    part_rows: list[tuple[int, str, Fraction]],
    cl_rows: list[tuple[int, str, Fraction]],
) -> Fraction:
    total_parts = sum(qty for _, _, qty in part_rows)
    if not total_parts:
        return Fraction(3)
    if cl_rows:
        if len(cl_rows) == 1:
            return cl_rows[0][2]
        return sum(qty for _, _, qty in cl_rows) / total_parts
    return _parts_target_total(cocktail, total_parts) / total_parts


def _cl_qty_to_target(
    cl_qty: Fraction,
    target: str | None,
    category: str,
    ingredient: str,
) -> str:
    if target == "cl" or category in LIQUID_CL_CATEGORIES | {"syrup_sugar", "mixer", "premix"}:
        return _format_measure(cl_qty, "cl")
    if target == "tsp":
        return _format_measure(cl_qty / CL_PER_TSP, "tsp")
    if target == "dash":
        return _format_measure(cl_qty / (CL_PER_TSP / 4), "dash")
    if target == "tblsp":
        return _format_measure(cl_qty / CL_PER_TBLSP, "tblsp")
    if target == "pinch":
        return _format_measure(cl_qty / (CL_PER_TSP / 16), "pinch")
    if target == "cup":
        return _format_measure(cl_qty / CL_PER_CUP, "cup")
    if target == PRODUCE_UNIT or _is_whole_produce(ingredient):
        converted = _cl_to_produce(cl_qty)
        if converted:
            q, u = converted
            return _format_produce_measure(q, u)
        return _format_produce_measure(cl_qty / CL_PER_FRUIT, "piece")
    if target == FRUIT_UNIT or _is_whole_fruit(ingredient):
        fruit_qty = _cl_to_fruit_quantity(cl_qty)
        if fruit_qty is not None:
            return _format_measure(fruit_qty, FRUIT_UNIT)
        return _format_measure(cl_qty / CL_PER_FRUIT, FRUIT_UNIT)
    return _format_measure(cl_qty, "cl")


def _apply_parts_conversion(
    cocktail: dict,
    unit_map: dict[str, dict],
) -> list[tuple[str, str, str | None, str]]:
    part_rows: list[tuple[int, str, Fraction]] = []
    cl_rows: list[tuple[int, str, Fraction]] = []
    for i in range(1, 16):
        ing = cocktail.get(f"ingredient_{i}")
        meas = cocktail.get(f"measure_{i}")
        if not ing or not meas:
            continue
        parsed = parse_measure(str(meas).strip())
        if not parsed:
            continue
        low, high, unit = parsed
        qty = _average_quantity(low, high)
        base = _normalize_unit_token(unit)
        if base == "part":
            part_rows.append((i, ing, qty))
        elif base == "cl":
            cl_rows.append((i, ing, qty))

    if not part_rows:
        return []

    cl_per_part = _resolve_cl_per_part(cocktail, part_rows, cl_rows)
    changes: list[tuple[str, str, str | None, str]] = []
    for i, ing, qty in part_rows:
        old = cocktail.get(f"measure_{i}")
        entry = unit_map.get(ing, {"category": "other", "unit": "cl"})
        new = _cl_qty_to_target(
            qty * cl_per_part,
            entry.get("unit"),
            entry.get("category", "other"),
            ing,
        )
        if new != old:
            cocktail[f"measure_{i}"] = new
            changes.append((cocktail["name"], ing, old, new))
    return changes


def normalize_measure(
    measure: str | None,
    ingredient: str,
    unit_map: dict[str, dict],
) -> tuple[str | None, str]:
    """Return (new_measure, change_reason)."""
    if measure is None or not str(measure).strip():
        return measure, "unchanged"

    original = str(measure).strip()
    measure = _fix_literal_measure(original)
    if measure is None:
        return None, "instruction_null"
    if measure != original and not parse_measure(measure):
        if measure in ("1 dash", "1 bottle", "1 piece", "1 pinch") or " drop" in measure:
            pass
        elif not re.match(r"^[\d./\s]+$", measure):
            return measure, "literal_fix"

    ing_entry = unit_map.get(ingredient, {"category": "other", "unit": "cl"})
    target_unit = ing_entry.get("unit")
    category = ing_entry.get("category", "other")

    if target_unit is None:
        if category == "garnish" and ingredient in COUNTABLE_GARNISH:
            piece = _normalize_piece_measures(measure, "piece", ingredient)
            if piece:
                return piece, "garnish_piece"
        return None, "null_category"

    juice = _convert_juice_of(measure, ingredient, target_unit)
    if juice:
        return juice, "juice_of"

    dash = _normalize_dashes(measure)
    if dash and target_unit == "dash":
        return dash, "dash_fix"
    if dash and target_unit in ("cl", "tsp"):
        parsed_dash = parse_measure(dash)
        if parsed_dash:
            qty, _, _ = parsed_dash
            converted, out = _dash_to_target(qty, target_unit)
            return _format_measure(converted, out), "dash_fix"

    if _is_whole_produce(ingredient):
        produce = _normalize_produce_measure(measure, PRODUCE_UNIT)
        if produce:
            return produce, "produce_count"

    if _is_whole_fruit(ingredient):
        fruit = _normalize_fruit_measure(measure, target_unit)
        if fruit:
            return fruit, "fruit_count"

    piece = _normalize_piece_measures(measure, target_unit, ingredient)
    if piece is not None:
        if piece != measure:
            return piece, "piece_normalize"
        return piece, "unchanged"

    parsed = parse_measure(measure)
    if parsed is None:
        return measure, "unparseable"

    low, high, unit = parsed
    qty = _average_quantity(low, high)
    base_unit = _normalize_unit_token(unit)

    if base_unit in BATCH_VOLUME_UNITS:
        cl_qty = _batch_volume_to_cl(qty, base_unit)
        if cl_qty is not None:
            return _format_measure(cl_qty, "cl"), "batch_volume"

    if base_unit in ("part", "parts"):
        return _format_measure(qty * Fraction(3), "cl"), "parts_to_cl"

    if base_unit in ("drop", "drops") and target_unit == "dash":
        return _format_measure(qty / DROPS_PER_DASH, "dash"), "to_dash"

    if base_unit == "can" and target_unit == "cl":
        return _format_measure(qty * CL_PER_CAN, "cl"), "to_cl"

    if base_unit == "glass" and target_unit == "cl":
        glass_factor = CL_PER_BEER_GLASS if "beer" in ingredient.lower() else CL_PER_GLASS
        return _format_measure(qty * glass_factor, "cl"), "to_cl"

    if base_unit == "scoop" and target_unit == "cup":
        return _format_measure(qty * CUP_PER_SCOOP, "cup"), "to_cup"

    if base_unit == "cup":
        if target_unit == "tsp":
            return _format_measure(qty * CL_PER_CUP / CL_PER_TSP, "tsp"), "to_tsp"
        if target_unit == "cl":
            return _format_measure(qty * CL_PER_CUP, "cl"), "to_cl"

    if base_unit == "cl":
        if target_unit == "tsp":
            return _format_measure(qty / CL_PER_TSP, "tsp"), "to_tsp"
        if target_unit == "dash":
            return _format_measure(qty / (CL_PER_TSP / 4), "dash"), "to_dash"
        if target_unit == "pinch":
            return _format_measure(qty / (CL_PER_TSP / 16), "pinch"), "to_pinch"

    if base_unit == "tsp" and target_unit == "pinch":
        return _format_measure(qty * 16, "pinch"), "to_pinch"

    if base_unit == "tblsp" and target_unit == "tsp":
        return _format_measure(qty * 3, "tsp"), "to_tsp"

    if base_unit == "gr" and target_unit in ("tsp", "piece"):
        converted = qty / 5 if target_unit == "tsp" else qty / 20
        return _format_measure(converted, target_unit), "to_target"

    if base_unit in ("handful", "fresh") and target_unit == "sprig":
        sprigs = qty * 3 if base_unit == "handful" else qty
        return _format_measure(sprigs, "sprig"), "to_sprig"

    descriptor_units = frozenset({
        "cracked", "whole", "crushed", "one-inch", "3-inch", "beaten", "large",
        "frozen", "ripe", "long", "chunks", "chunk", "inch",
    })
    if base_unit in descriptor_units:
        if target_unit == "tsp":
            return _format_measure(qty, "tsp"), "descriptor_normalize"
        if target_unit == "stick":
            return _format_measure(qty, "stick"), "descriptor_normalize"
        if target_unit in ("piece", "sprig"):
            return _format_measure(qty, target_unit), "descriptor_normalize"
        if target_unit == PRODUCE_UNIT:
            return _format_produce_measure(qty, "piece"), "descriptor_normalize"
        if target_unit == FRUIT_UNIT:
            return _format_measure(qty, FRUIT_UNIT), "descriptor_normalize"

    if base_unit in ("dash", "dashes"):
        converted, out_unit = _dash_to_target(qty, target_unit)
        return _format_measure(converted, out_unit), "to_target"

    if base_unit in ("tsp", "tblsp"):
        if target_unit == "tsp":
            tsp_qty = qty if base_unit == "tsp" else qty * 3
            return _format_measure(tsp_qty, "tsp"), "to_tsp"
        if target_unit == "cl":
            cl_qty = qty * (CL_PER_TSP if base_unit == "tsp" else CL_PER_TBLSP)
            return _format_measure(cl_qty, "cl"), "to_cl"

    if base_unit in ("pinch", "pinches") and target_unit == "tsp":
        return _format_measure(qty / 16, "tsp"), "to_tsp"

    if base_unit in ("drop", "drops") and target_unit == "cl":
        return _format_measure(qty * CL_PER_DROP, "cl"), "to_cl"

    if base_unit == "splash" and target_unit == "cl":
        return _format_measure(qty * CL_PER_SPLASH, "cl"), "to_cl"

    if target_unit == PRODUCE_UNIT:
        if base_unit == "cl":
            converted = _cl_to_produce(qty)
            if converted is not None:
                q, u = converted
                return _format_produce_measure(q, u), "to_produce"
            return measure, "unchanged"
        if base_unit in ("cup", "lb", "piece") or base_unit in PRODUCE_COUNT_UNITS:
            return _format_produce_measure(qty, base_unit), "to_produce"
        if not base_unit:
            return _format_produce_measure(qty, "piece"), "to_produce"
        return measure, "unchanged"

    if target_unit == FRUIT_UNIT:
        if base_unit == "cl":
            fruit_qty = _cl_to_fruit_quantity(qty)
            if fruit_qty is not None:
                return _format_measure(fruit_qty, FRUIT_UNIT), "to_fruit"
        if base_unit in ("slice", "wedge", "lb"):
            if base_unit in ("slice", "wedge"):
                return f"{_format_fruit_quantity(qty)} {base_unit}", "to_target"
            return _format_measure(qty, base_unit), "to_target"
        if base_unit == "cl" and qty == CL_PER_LB:
            return _format_measure(Fraction(1), "lb"), "to_fruit"
        if not base_unit:
            return _format_measure(qty, FRUIT_UNIT), "to_fruit"
        return measure, "unchanged"

    if target_unit == "cl" and category in LIQUID_CL_CATEGORIES | {"syrup_sugar", "mixer"}:
        factor = _unit_to_cl_factor(base_unit)
        if factor is not None:
            return _format_measure(qty * factor, "cl"), "to_cl"

    if target_unit in ("piece", "sprig", "slice", "stick", "pinch", "wedge", PRODUCE_UNIT):
        if base_unit == "cl":
            converted = _cl_to_produce(qty)
            if converted is not None:
                q, u = converted
                return _format_produce_measure(q, u), "to_produce"
        if not base_unit or base_unit in ("whole", "large", "medium", "small"):
            unit = target_unit if target_unit != PRODUCE_UNIT else "piece"
            return _format_measure(qty, unit), "to_target"
        if base_unit == target_unit or (target_unit == PRODUCE_UNIT and base_unit == "piece"):
            return _format_measure(qty, base_unit), "to_target"

    if base_unit == target_unit:
        return _format_measure(qty, target_unit), "format_only"

    factor = _unit_to_cl_factor(base_unit)
    if factor and target_unit == "cl" and category not in {"produce", "citrus", "garnish"}:
        return _format_measure(qty * factor, "cl"), "to_cl"

    return _format_measure(qty, base_unit or target_unit), "unchanged"


def clean_measure_format(measure: str | None) -> str | None:
    if measure is None:
        return None
    s = str(measure).strip()
    if not s:
        return None
    s = re.sub(r"\bc[lL]\b", "cl", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_cocktails(
    cocktails: list[dict],
    unit_map: dict[str, dict],
) -> tuple[list[dict], dict]:
    stats = Counter()
    changes: list[str] = []

    for cocktail in cocktails:
        for name, ing, old, new in _apply_parts_conversion(cocktail, unit_map):
            changes.append(f"{name} | {ing}: {old!r} → {new!r} (parts_to_cl)")
            stats["parts_to_cl"] += 1

    for cocktail in cocktails:
        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            key = f"measure_{i}"
            old = cocktail.get(key)
            if not ing:
                continue

            new, reason = normalize_measure(old, ing, unit_map)
            new = clean_measure_format(new)
            if new != old:
                if old is not None and str(old).strip():
                    changes.append(f"{cocktail['name']} | {ing}: {old!r} → {new!r} ({reason})")
                cocktail[key] = new
                stats[reason] += 1
            elif new and new != old:
                cocktail[key] = new
                stats["format_only"] += 1

    return cocktails, {"stats": stats, "changes": changes}


def validate(cocktails: list[dict], unit_map: dict[str, dict]) -> dict:
    total = 0
    parseable = 0
    null_count = 0
    ing_units: dict[str, set[str]] = defaultdict(set)
    unparseable: Counter = Counter()

    for cocktail in cocktails:
        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            meas = cocktail.get(f"measure_{i}")
            if not ing:
                continue
            total += 1
            if meas is None or not str(meas).strip():
                null_count += 1
                continue
            parsed = parse_measure(meas)
            if parsed:
                parseable += 1
                _, _, unit = parsed
                canonical = _normalize_unit_token(unit)
                if canonical:
                    ing_units[ing].add(canonical)
            else:
                unparseable[str(meas).strip()] += 1

    multi_unit = {k: v for k, v in ing_units.items() if len(v) > 1}
    target_conform = 0
    target_total = 0
    for cocktail in cocktails:
        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            meas = cocktail.get(f"measure_{i}")
            if not ing or not meas:
                continue
            target = unit_map.get(ing, {}).get("unit")
            if not target:
                continue
            target_total += 1
            parsed = parse_measure(meas)
            if parsed:
                _, _, unit = parsed
                if _normalize_unit_token(unit) == target or (
                    target == "cl" and _normalize_unit_token(unit).startswith("cl")
                ):
                    target_conform += 1

    return {
        "total_pairs": total,
        "parseable": parseable,
        "parseable_pct": round(100 * parseable / total, 1) if total else 0,
        "null_count": null_count,
        "multi_unit_ingredients": len(multi_unit),
        "multi_unit_top": sorted(multi_unit.items(), key=lambda x: len(x[1]), reverse=True)[:20],
        "unparseable": unparseable.most_common(30),
        "target_conform_pct": round(100 * target_conform / target_total, 1) if target_total else 0,
    }


def write_report(
    path: str,
    before: dict,
    after: dict,
    stats: Counter,
    changes: list[str],
    dry_run: bool,
) -> None:
    lines = [
        f"Measure normalization report ({'DRY RUN' if dry_run else 'APPLIED'})",
        "=" * 60,
        "",
        "Before:",
        f"  Parseable: {before['parseable']}/{before['total_pairs']} ({before['parseable_pct']}%)",
        f"  Null measures: {before['null_count']}",
        f"  Multi-unit ingredients: {before['multi_unit_ingredients']}",
        "",
        "After:",
        f"  Parseable: {after['parseable']}/{after['total_pairs']} ({after['parseable_pct']}%)",
        f"  Null measures: {after['null_count']}",
        f"  Multi-unit ingredients: {after['multi_unit_ingredients']}",
        f"  Target-unit conform: {after['target_conform_pct']}%",
        "",
        "Change reasons:",
    ]
    for reason, count in stats.most_common():
        lines.append(f"  {reason}: {count}")

    lines.extend(["", "Top multi-unit ingredients (after):"])
    for ing, units in after["multi_unit_top"]:
        lines.append(f"  {ing}: {sorted(units)}")

    lines.extend(["", "Remaining unparseable (after):"])
    for meas, count in after["unparseable"]:
        lines.append(f"  {count:4d}  {meas!r}")

    lines.extend(["", f"Sample changes ({min(50, len(changes))} of {len(changes)}):"])
    for change in changes[:50]:
        lines.append(f"  {change}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize cocktail seed measures.")
    parser.add_argument("--generate-map", action="store_true", help="Generate ingredient_unit_map.json")
    parser.add_argument("--write", action="store_true", help="Write changes to cocktails_seed.json")
    args = parser.parse_args()

    with open(SEED_FILE, encoding="utf-8") as f:
        cocktails = json.load(f)

    if args.generate_map:
        unit_map = generate_unit_map(cocktails)
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(unit_map, f, ensure_ascii=False, indent=2)
        print(f"Generated {len(unit_map)} entries -> {MAP_FILE}")
        return

    if os.path.exists(MAP_FILE):
        with open(MAP_FILE, encoding="utf-8") as f:
            unit_map = json.load(f)
    else:
        unit_map = generate_unit_map(cocktails)
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(unit_map, f, ensure_ascii=False, indent=2)
        print(f"Auto-generated map -> {MAP_FILE}")

    before = validate(cocktails, unit_map)
    working = json.loads(json.dumps(cocktails))
    normalized, result = normalize_cocktails(working, unit_map)
    after = validate(normalized, unit_map)

    write_report(
        REPORT_FILE,
        before,
        after,
        result["stats"],
        result["changes"],
        dry_run=not args.write,
    )
    print(f"Report written to {REPORT_FILE}")
    print(f"Parseable: {before['parseable_pct']}% -> {after['parseable_pct']}%")
    print(f"Multi-unit ingredients: {before['multi_unit_ingredients']} -> {after['multi_unit_ingredients']}")

    if args.write:
        with open(SEED_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=1)
        print(f"Wrote {len(normalized)} cocktails to {SEED_FILE}")
    else:
        print("Dry run — pass --write to apply changes.")


if __name__ == "__main__":
    main()
