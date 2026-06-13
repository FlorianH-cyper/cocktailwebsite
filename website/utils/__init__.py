import re
import json
from pathlib import Path
from fractions import Fraction

from ..models import Cocktail, Ingredient, Rating, User
from .. import db
from sqlalchemy import func

_INGREDIENT_LOOKUP_CACHE = None


def _build_ingredient_lookup():
    lookup = {}
    for (name,) in Ingredient.query.with_entities(Ingredient.name).all():
        if name:
            lookup[name.lower()] = name
    if not lookup:
        for cocktail in Cocktail.query.all():
            for i in range(1, 16):
                name = getattr(cocktail, f'ingredient_{i}')
                if name:
                    lookup.setdefault(name.lower(), name)
    return lookup


def get_ingredient_lookup():
    global _INGREDIENT_LOOKUP_CACHE
    if _INGREDIENT_LOOKUP_CACHE is None:
        _INGREDIENT_LOOKUP_CACHE = _build_ingredient_lookup()
    return _INGREDIENT_LOOKUP_CACHE


def resolve_known_ingredient(name):
    if not name:
        return None
    return get_ingredient_lookup().get(name.strip().lower())


def get_known_ingredient_names():
    return sorted(get_ingredient_lookup().values(), key=str.lower)


def get_cocktail_ingredients_and_measures(cocktail):
    data = []
    for i in range(1, 16):
        ingredient = getattr(cocktail, f'ingredient_{i}')
        measure = getattr(cocktail, f'measure_{i}')
        if ingredient:
            data.append({'ingredient': ingredient, 'measure': measure})
    return data


# Matches a leading quantity ("1", "0.5", "1/2", "1 1/2") followed by a unit ("oz", "cl", ...).
_MEASURE_RE = re.compile(r'^\s*(\d+\s+\d+/\d+|\d+/\d+|\d*\.\d+|\d+)\s*(.*?)\s*$')


def _parse_measure(measure):
    """Split a measure like '1 1/2 oz' into (Fraction(3, 2), 'oz'), or None if unparseable."""
    if not measure:
        return None
    match = _MEASURE_RE.match(str(measure))
    if not match:
        return None
    number, unit = match.groups()
    parts = number.split()
    quantity = sum(Fraction(part) for part in parts)
    return quantity, unit


def _format_quantity(quantity):
    whole, remainder = divmod(quantity.numerator, quantity.denominator)
    if remainder == 0:
        return str(whole)
    if whole == 0:
        return f"{remainder}/{quantity.denominator}"
    return f"{whole} {remainder}/{quantity.denominator}"


def _format_ingredient_measure(totals, unparseable):
    terms = [
        f"{_format_quantity(total)} {unit}".strip()
        for total, unit in totals.values()
    ]
    if not terms and not unparseable:
        return None
    return " + ".join(terms + unparseable)


def _parse_combined_measure(measure):
    totals = {}
    unparseable = []
    if not measure:
        return totals, unparseable
    for part in str(measure).split(' + '):
        part = part.strip()
        if not part:
            continue
        parsed = _parse_measure(part)
        if parsed is None:
            unparseable.append(part)
            continue
        quantity, unit = parsed
        unit_key = unit.lower()
        if unit_key in totals:
            totals[unit_key][0] += quantity
        else:
            totals[unit_key] = [quantity, unit]
    return totals, unparseable


def merge_inventory_measures(existing_measure, new_measure):
    totals, unparseable = _parse_combined_measure(existing_measure)
    new_totals, new_unparseable = _parse_combined_measure(new_measure)
    for unit_key, (quantity, unit) in new_totals.items():
        if unit_key in totals:
            totals[unit_key][0] += quantity
        else:
            totals[unit_key] = [quantity, unit]
    unparseable.extend(new_unparseable)
    return _format_ingredient_measure(totals, unparseable) or new_measure or existing_measure


def _inventory_totals_by_ingredient(inventory):
    totals_by_ingredient = {}
    for item in inventory or []:
        parsed_totals, _unparseable = _parse_combined_measure(item.measure)
        if not parsed_totals:
            continue
        ingredient_key = item.ingredient.lower()
        ingredient_totals = totals_by_ingredient.setdefault(ingredient_key, {})
        for unit_key, (quantity, unit) in parsed_totals.items():
            if unit_key in ingredient_totals:
                ingredient_totals[unit_key][0] += quantity
            else:
                ingredient_totals[unit_key] = [quantity, unit]
    return totals_by_ingredient


def _subtract_inventory(totals, unparseable, inventory_for_ingredient):
    if not inventory_for_ingredient:
        return totals, unparseable

    for unit_key, (on_hand, _unit) in inventory_for_ingredient.items():
        if unit_key not in totals:
            continue
        total, display_unit = totals[unit_key]
        remaining = total - on_hand
        if remaining <= 0:
            del totals[unit_key]
        else:
            totals[unit_key] = [remaining, display_unit]
    return totals, unparseable


def aggregate_shopping_list(shopping_list, menuitems, inventory=None):
    amount_by_menuitem = {menuitem.id: menuitem.amount for menuitem in menuitems}
    inventory_by_ingredient = _inventory_totals_by_ingredient(inventory)

    items_by_ingredient = {}
    for item in shopping_list:
        items_by_ingredient.setdefault(item.ingredient, []).append(item)

    aggregated_shopping_list = {}
    for ingredient, items in items_by_ingredient.items():
        totals = {}
        unparseable = []
        for item in items:
            amount = amount_by_menuitem[item.menuitem_id]
            parsed = _parse_measure(item.measure)
            if parsed is None:
                unparseable.append(f"{amount} * {item.measure}")
                continue
            quantity, unit = parsed
            key = unit.lower()
            if key in totals:
                totals[key][0] += quantity * amount
            else:
                totals[key] = [quantity * amount, unit]

        totals, unparseable = _subtract_inventory(
            totals,
            unparseable,
            inventory_by_ingredient.get(ingredient.lower()),
        )
        formatted = _format_ingredient_measure(totals, unparseable)
        if formatted:
            aggregated_shopping_list[ingredient] = formatted
    return aggregated_shopping_list


COCKTAIL_SEARCH_LIMIT = 50


def cocktail_thumb_url(cocktail_id):
    return f"/static/images/cocktails/thumbs/{cocktail_id}.jpg"


def search_cocktails(name=None, ingredient=None, alcoholic=None):
    query = Cocktail.query

    if name:
        query = query.filter(Cocktail.name.contains(name))
    if ingredient:
        query = query.filter(Cocktail.all_ingredients.contains(ingredient))
    if alcoholic == "alcoholic":
        query = query.filter(Cocktail.alcoholic == True)
    elif alcoholic == "non-alcoholic":
        query = query.filter(Cocktail.alcoholic == False)

    results = query.order_by(Cocktail.name).limit(COCKTAIL_SEARCH_LIMIT + 1).all()
    truncated = len(results) > COCKTAIL_SEARCH_LIMIT
    if truncated:
        results = results[:COCKTAIL_SEARCH_LIMIT]
    return results, truncated


def cocktail_to_search_dict(cocktail, rating=None):
    data = {
        "id": cocktail.id,
        "name": cocktail.name,
        "thumb": cocktail_thumb_url(cocktail.id),
        "image": cocktail.image,
        "instructions": cocktail.instructions or "",
        "number_of_ingredients": cocktail.number_of_ingredients,
        "all_ingredients": cocktail.all_ingredients or "",
    }
    if rating is not None:
        data["avg_rating"] = rating["avg"]
        data["rating_count"] = rating["count"]
        data["user_stars"] = rating["user_stars"]
    return data


def get_ratings_for_cocktails(cocktail_ids, user_id=None):
    if not cocktail_ids:
        return {}

    result = {
        cocktail_id: {"avg": None, "count": 0, "user_stars": None}
        for cocktail_id in cocktail_ids
    }

    stats = (
        db.session.query(
            Rating.cocktail_id,
            func.avg(Rating.stars).label("avg"),
            func.count(Rating.id).label("count"),
        )
        .filter(Rating.cocktail_id.in_(cocktail_ids))
        .group_by(Rating.cocktail_id)
        .all()
    )
    for row in stats:
        result[row.cocktail_id] = {
            "avg": round(float(row.avg), 1),
            "count": row.count,
            "user_stars": None,
        }

    if user_id:
        user_ratings = Rating.query.filter(
            Rating.user_id == user_id,
            Rating.cocktail_id.in_(cocktail_ids),
        ).all()
        for rating in user_ratings:
            result[rating.cocktail_id]["user_stars"] = rating.stars

    return result


def get_cocktail_rating_summary(cocktail_id, user_id=None):
    ratings = get_ratings_for_cocktails([cocktail_id], user_id=user_id)
    return ratings.get(cocktail_id, {"avg": None, "count": 0, "user_stars": None})


def _rating_user_display_name(user):
    if user.first_name:
        return user.first_name
    if user.email:
        return user.email.split("@", 1)[0]
    return "User"


def get_cocktail_ratings_detail(cocktail_id, user_id=None):
    summary = get_cocktail_rating_summary(cocktail_id, user_id=user_id)
    rows = (
        db.session.query(Rating, User)
        .join(User, Rating.user_id == User.id)
        .filter(Rating.cocktail_id == cocktail_id)
        .order_by(Rating.stars.desc(), User.first_name, User.email)
        .all()
    )
    ratings = [
        {
            "user_name": _rating_user_display_name(user),
            "stars": rating.stars,
            "is_you": user_id is not None and rating.user_id == user_id,
        }
        for rating, user in rows
    ]
    return {"summary": summary, "ratings": ratings}


_INGREDIENT_UNIT_MAP = None


def _ingredient_unit_map():
    global _INGREDIENT_UNIT_MAP
    if _INGREDIENT_UNIT_MAP is None:
        path = Path(__file__).resolve().parent.parent / "jobs" / "ingredient_unit_map.json"
        with path.open(encoding="utf-8") as f:
            _INGREDIENT_UNIT_MAP = json.load(f)
    return _INGREDIENT_UNIT_MAP


def get_inventory_unit(ingredient):
    """Standard unit for inventory entry (from ingredient_unit_map.json)."""
    for name, entry in _ingredient_unit_map().items():
        if name.lower() == ingredient.lower():
            unit = entry.get("unit")
            if unit in (None, "produce", "fruit"):
                return "piece"
            return unit
    return "cl"


def get_ingredient_inventory_units():
    return {name: get_inventory_unit(name) for name in _ingredient_unit_map()}