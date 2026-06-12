import re
from fractions import Fraction

from ..models import Cocktail, Rating, User
from .. import db
from sqlalchemy import func


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


def aggregate_shopping_list(shopping_list, menuitems):
    amount_by_menuitem = {menuitem.id: menuitem.amount for menuitem in menuitems}

    items_by_ingredient = {}
    for item in shopping_list:
        items_by_ingredient.setdefault(item.ingredient, []).append(item)

    aggregated_shopping_list = {}
    for ingredient, items in items_by_ingredient.items():
        # One running total per unit (keyed case-insensitively, first spelling kept for display).
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
        terms = [
            f"{_format_quantity(total)} {unit}".strip()
            for total, unit in totals.values()
        ]
        aggregated_shopping_list[ingredient] = " + ".join(terms + unparseable)
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