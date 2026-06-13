"""One-pass sanity fixes for cocktails_seed.json — sense over strict unit uniformity."""

from __future__ import annotations

import json
import os
import re
from fractions import Fraction

from normalize_measures import (
    CL_PER_TSP,
    parse_measure,
    _normalize_unit_token,
)

JOBS_DIR = os.path.dirname(__file__)
SEED_FILE = os.path.join(JOBS_DIR, "cocktails_seed.json")

# Exact overrides: (cocktail name, ingredient) -> new measure
EXACT_FIXES: dict[tuple[str, str], str | None] = {
    ("Banana Cantaloupe Smoothie", "Cantaloupe"): "1/2",
    ("Irish Cream", "Coconut syrup"): "1.5 cl",
    ("Coffee Liqueur", "Sugar"): "60 cl",
    ("Creme de Menthe", "Sugar"): "192 cl",
    ("Homemade Kahlua", "Sugar"): "60 cl",
    ("Caribbean Orange Liqueur", "Sugar"): "48 cl",
    ("Adam Bomb", "Salt"): None,
    ("Cranberry Cordial", "Cranberries"): "1/2 kg",
    ("Coke and Drops", "Lemon juice"): "1.5 cl",
    ("Absolut limousine", "Absolut Citron"): "4.5 cl",
    ("Absolut limousine", "Lime juice"): "1.5 cl",
    ("Brain Fart", "Lemon juice"): "1 tsp",
    ("Ace", "Egg White"): "1 piece",
    ("Broadside", "Wormwood"): "1 tsp",
    ("Mango Mojito", "Mango"): "1 piece",
    ("Orange Whip", "Cream"): None,
    ("Strawberry Lemonade", "Strawberries"): "9 piece",
}

EIGHTH_CL = {0.125, 0.25, 0.375, 0.5, 0.625, 0.75}


def _is_eighth_cl(value: float) -> bool:
    return any(abs(value - v) < 0.002 for v in EIGHTH_CL)


def _round_cl(measure: str) -> str | None:
    parsed = parse_measure(measure)
    if not parsed:
        return None
    qty, _, unit = parsed
    if _normalize_unit_token(unit) != "cl":
        return None
    value = float(qty)
    if _is_eighth_cl(value):
        return None
    # Only touch obvious float artifacts (parts conversion noise).
    qty_text = str(measure).strip().split()[0]
    if not re.search(r"\.\d{3,}", qty_text):
        return None
    return f"{round(value, 1):g} cl"


def _batch_sugar_tsp(measure: str) -> str | None:
    parsed = parse_measure(measure)
    if not parsed:
        return None
    qty, _, unit = parsed
    if _normalize_unit_token(unit) != "tsp" or qty <= 48:
        return None
    cl = float(qty) * float(CL_PER_TSP)
    return f"{round(cl, 1):g} cl"


def _fix_tiny_liquid(measure: str, ingredient: str, category: str) -> str | None:
    parsed = parse_measure(measure)
    if not parsed:
        return None
    qty, _, unit = parsed
    if _normalize_unit_token(unit) != "cl":
        return None
    value = float(qty)
    if _is_eighth_cl(value):
        return None
    lower = ingredient.lower()
    if category == "juice" or " juice" in lower:
        if value < 0.15:
            return "0.5 cl"
    if category == "syrup_sugar" and "syrup" in lower:
        if value < 0.1:
            return "0.5 cl"
    return None


def _fix_shot_sip(measure: str, category: str) -> str | None:
    """Parts-conversion artifacts in shots (< 1 cl, ugly decimals)."""
    if category != "Shot":
        return None
    parsed = parse_measure(measure)
    if not parsed:
        return None
    qty, _, unit = parsed
    if _normalize_unit_token(unit) != "cl" or qty >= 1:
        return None
    qty_text = str(measure).strip().split()[0]
    if not re.search(r"\.\d{3,}", qty_text):
        return None
    return "1.5 cl"


def _fix_descriptor(measure: str) -> str | None:
    m = measure.strip()
    fixes = {
        "0.5 fresh": "1 piece",
        "1 fresh": "1 tsp",
        "1 Fresh": "1 piece",
        "1 package": None,
        "3 packages": "3 package",
        "0.625 dash": "1 dash",
    }
    if m in fixes:
        val = fixes[m]
        return val
    if re.match(r"^\d+\s+ripe$", m, re.I):
        n = re.match(r"^(\d+)", m).group(1)
        return f"{n} piece"
    if re.match(r"^\d+/\d+\s+kg\s+chopped$", m, re.I):
        return re.sub(r"\s+chopped$", "", m, flags=re.I)
    if m.lower().startswith("juice of"):
        return None
    return None


def apply_sanity_fixes(cocktails: list[dict]) -> list[str]:
    changes: list[str] = []

    for cocktail in cocktails:
        name = cocktail["name"]
        category = cocktail.get("category") or ""

        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            key = f"measure_{i}"
            old = cocktail.get(key)
            if not ing:
                continue

            new = None
            reason = ""

            if (name, ing) in EXACT_FIXES:
                new, reason = EXACT_FIXES[(name, ing)], "exact"
            elif old and str(old).strip():
                from ingredient_unit_rules import classify_ingredient

                cat, _ = classify_ingredient(ing)
                old_s = str(old).strip()

                for fn, r in (
                    (_fix_descriptor, "descriptor"),
                    (_batch_sugar_tsp, "batch_sugar"),
                    (lambda m: _fix_tiny_liquid(m, ing, cat), "tiny_liquid"),
                    (lambda m: _fix_shot_sip(m, category), "shot_pour"),
                    (_round_cl, "round_cl"),
                ):
                    candidate = fn(old_s)
                    if candidate is not None and candidate != old:
                        new, reason = candidate, r
                        break

            if reason:
                changes.append(f"{name} | {ing}: {old!r} -> {new!r} ({reason})")
                cocktail[key] = new

    return changes


def main() -> None:
    with open(SEED_FILE, encoding="utf-8") as f:
        cocktails = json.load(f)

    changes = apply_sanity_fixes(cocktails)

    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(cocktails, f, ensure_ascii=False, indent=1)

    print(f"Applied {len(changes)} sanity fixes")
    for line in changes:
        print(f"  {line}")


if __name__ == "__main__":
    main()
