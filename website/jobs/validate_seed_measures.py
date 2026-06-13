"""Quick validation helper for normalized cocktail seed measures."""

import importlib.util
import json
import re
from pathlib import Path

JOBS_DIR = Path(__file__).parent
spec = importlib.util.spec_from_file_location("nm", JOBS_DIR / "normalize_measures.py")
nm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nm)

cocktails = json.loads((JOBS_DIR / "cocktails_seed.json").read_text(encoding="utf-8"))
unit_map = json.loads((JOBS_DIR / "ingredient_unit_map.json").read_text(encoding="utf-8"))

after = nm.validate(cocktails, unit_map)
non_null = after["total_pairs"] - after["null_count"]

print("=== Final metrics ===")
print(f"Total pairs: {after['total_pairs']}")
print(f"Parseable (all): {after['parseable']} ({after['parseable_pct']}%)")
print(f"Parseable (non-null): {after['parseable']}/{non_null} ({round(100 * after['parseable'] / non_null, 1)}%)")
print(f"Null measures: {after['null_count']}")
print(f"Multi-unit ingredients: {after['multi_unit_ingredients']}")
print(f"Target-unit conform: {after['target_conform_pct']}%")
print(f"Remaining unparseable: {after['unparseable']}")

spirits = [
    "Vodka", "Gin", "Light rum", "Tequila", "Bourbon",
    "Campari", "Sweet Vermouth", "Dry Vermouth",
]
for spirit in spirits:
    non_cl = []
    total = 0
    for cocktail in cocktails:
        for i in range(1, 16):
            if cocktail.get(f"ingredient_{i}") != spirit:
                continue
            measure = cocktail.get(f"measure_{i}")
            if not measure:
                continue
            total += 1
            parsed = nm.parse_measure(measure)
            if parsed and not re.search(r"\bcl\b", str(measure), re.I):
                non_cl.append(measure)
    print(f"{spirit}: {total} measures, non-cl parseable: {len(non_cl)}")
