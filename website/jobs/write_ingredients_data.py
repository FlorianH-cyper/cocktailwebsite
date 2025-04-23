from website import db
from website.models import Ingredient


def write_ingredients_to_db(ingredients):
    for ingredient in ingredients:
        if not Ingredient.query.filter_by(name=ingredient).first():
            new_ingredient = Ingredient(name=ingredient)
            db.session.add(new_ingredient)
            db.session.commit()