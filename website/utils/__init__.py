from ..models import Cocktail, Rating
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


def aggregate_shopping_list(shopping_list, menuitems):
    for item in shopping_list:
        respective_menu_item = next(menuitem for menuitem in menuitems if menuitem.id == item.menuitem_id)
        item.measure = str(respective_menu_item.amount) + " * " +  str(item.measure) 
    aggregated_shopping_list = {}
    for item in shopping_list:
        if item.ingredient in aggregated_shopping_list:
            aggregated_shopping_list[item.ingredient] = str(aggregated_shopping_list[item.ingredient]) + " + " + str(item.measure) 
        else:
            aggregated_shopping_list[item.ingredient] = str(item.measure)
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