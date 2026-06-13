"""Merge ingredient name variants (case/spelling) to a single canonical name."""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

JOBS_DIR = os.path.dirname(__file__)
SEED_FILE = os.path.join(JOBS_DIR, "cocktails_seed.json")
MAP_FILE = os.path.join(JOBS_DIR, "ingredient_unit_map.json")
RULES_FILE = os.path.join(JOBS_DIR, "ingredient_unit_rules.py")


def _build_alias_map(seed: list[dict], unit_map: dict) -> dict[str, str]:
    counts: Counter[str] = Counter()
    for cocktail in seed:
        for i in range(1, 16):
            ing = cocktail.get(f"ingredient_{i}")
            if ing:
                counts[ing] += 1

    by_lower: dict[str, set[str]] = defaultdict(set)
    for name in set(counts) | set(unit_map):
        by_lower[name.lower()].add(name)

    aliases: dict[str, str] = {}
    for variants in by_lower.values():
        if len(variants) <= 1:
            continue
        canonical = sorted(variants, key=lambda v: (-counts[v], v))[0]
        for variant in variants:
            if variant != canonical:
                aliases[variant] = canonical
    return aliases


def _rename_in_all_ingredients(text: str, aliases: dict[str, str]) -> str:
    if not text:
        return text
    parts = [p.strip() for p in text.split("  -  ")]
    return "  -  ".join(aliases.get(p, p) for p in parts)


def merge_seed(seed: list[dict], aliases: dict[str, str]) -> int:
    changes = 0
    for cocktail in seed:
        for i in range(1, 16):
            key = f"ingredient_{i}"
            ing = cocktail.get(key)
            if ing in aliases:
                cocktail[key] = aliases[ing]
                changes += 1
        old_all = cocktail.get("all_ingredients")
        if old_all:
            new_all = _rename_in_all_ingredients(old_all, aliases)
            if new_all != old_all:
                cocktail["all_ingredients"] = new_all
    return changes


def merge_unit_map(unit_map: dict, aliases: dict[str, str]) -> dict:
    merged: dict = {}
    for name, entry in unit_map.items():
        canonical = aliases.get(name, name)
        if canonical not in merged:
            merged[canonical] = entry
    return dict(sorted(merged.items(), key=lambda x: x[0].lower()))


def merge_rules_file(aliases: dict[str, str]) -> None:
    with open(RULES_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    canonicals = set(aliases.values())
    out: list[str] = []
    for line in lines:
        key_match = re.match(r'\s+"([^"]+)":\s*\(', line)
        if key_match:
            key = key_match.group(1)
            if key in aliases:
                canonical = aliases[key]
                if canonical in canonicals:
                    continue
                line = line.replace(f'"{key}"', f'"{canonical}"', 1)
        out.append(line)

    with open(RULES_FILE, "w", encoding="utf-8") as f:
        f.writelines(out)


def main() -> None:
    with open(SEED_FILE, encoding="utf-8") as f:
        seed = json.load(f)
    with open(MAP_FILE, encoding="utf-8") as f:
        unit_map = json.load(f)

    aliases = _build_alias_map(seed, unit_map)
    if not aliases:
        print("No duplicates found.")
        return

    seed_changes = merge_seed(seed, aliases)
    new_map = merge_unit_map(unit_map, aliases)

    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=1)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(new_map, f, ensure_ascii=False, indent=2)

    merge_rules_file(aliases)

    print(f"Merged {len(aliases)} alias(es) into {len(set(aliases.values()))} canonical name(s)")
    print(f"Seed ingredient field updates: {seed_changes}")
    print(f"Map entries: {len(unit_map)} -> {len(new_map)}")
    print()
    by_canonical: dict[str, list[str]] = defaultdict(list)
    for old, new in sorted(aliases.items(), key=lambda x: (x[1].lower(), x[0].lower())):
        by_canonical[new].append(old)
    for canonical, olds in sorted(by_canonical.items(), key=lambda x: x[0].lower()):
        print(f"  {canonical} <- {', '.join(olds)}")


if __name__ == "__main__":
    main()
