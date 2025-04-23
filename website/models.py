# database models

from . import db # imports db from __init__.py
from flask_login import UserMixin # custom class which we can inherit
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

class Party(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    number_of_participants = db.Column(db.Integer)
    drinks_per_participant = db.Column(db.Integer)
    number_of_drinks_needed = db.Column(db.Integer)
    menu_items = db.relationship('Menuitem', cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # foreignkey has smallcap notation

    @hybrid_property
    def added_drinks(self):
        return sum(menu_item.amount for menu_item in self.menu_items)

    @added_drinks.expression
    def added_drinks(cls):
        return (
            db.session.query(func.coalesce(func.sum(Menuitem.amount), 0))
            .filter(Menuitem.party_id == cls.id)
            .correlate(cls)
            .as_scalar()
        )
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    parties = db.relationship('Party') # relationship references the name of the class

class Menuitem(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    cocktail_id = db.Column(db.Integer, db.ForeignKey('cocktail.id'), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('party.id'), nullable=False)
    amount = db.Column(db.Integer)
    shoppinglistitems = db.relationship('Shoppinglistitem', cascade="all, delete-orphan")

class Cocktail(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    alcoholic = db.Column(db.Boolean, nullable=False, default=True)
    glass = db.Column(db.String(100))
    image = db.Column(db.String(1000))
    all_ingredients = db.Column(db.String(1000))
    instructions = db.Column(db.String(1000))
    number_of_ingredients = db.Column(db.Integer)
    ingredient_1 = db.Column(db.String(100))
    ingredient_2 = db.Column(db.String(100))
    ingredient_3 = db.Column(db.String(100))
    ingredient_4 = db.Column(db.String(100))
    ingredient_5 = db.Column(db.String(100))
    ingredient_6 = db.Column(db.String(100))
    ingredient_7 = db.Column(db.String(100))
    ingredient_8 = db.Column(db.String(100))
    ingredient_9 = db.Column(db.String(100))
    ingredient_10 = db.Column(db.String(100))
    ingredient_11 = db.Column(db.String(100))
    ingredient_12 = db.Column(db.String(100))
    ingredient_13 = db.Column(db.String(100))
    ingredient_14 = db.Column(db.String(100))
    ingredient_15 = db.Column(db.String(100))
    measure_1 = db.Column(db.String(100))
    measure_2 = db.Column(db.String(100))
    measure_3 = db.Column(db.String(100))
    measure_4 = db.Column(db.String(100))
    measure_5 = db.Column(db.String(100))
    measure_6 = db.Column(db.String(100))
    measure_7 = db.Column(db.String(100))
    measure_8 = db.Column(db.String(100))
    measure_9 = db.Column(db.String(100))
    measure_10 = db.Column(db.String(100))
    measure_11 = db.Column(db.String(100))
    measure_12 = db.Column(db.String(100))
    measure_13 = db.Column(db.String(100))
    measure_14 = db.Column(db.String(100))
    measure_15 = db.Column(db.String(100))
    menu_items = db.relationship('Menuitem', backref='cocktail', lazy=True)



class Shoppinglistitem(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    menuitem_id = db.Column(db.Integer, db.ForeignKey('menuitem.id'), nullable=False)
    ingredient = db.Column(db.String(100))
    measure = db.Column(db.String(100))


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))


