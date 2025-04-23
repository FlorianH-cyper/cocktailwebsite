from website import db
from website.models import Cocktail

def write_cocktails_to_db(cocktails):
    for cocktail in cocktails:
        if not Cocktail.query.get(cocktail['idDrink']):  # Check if the ID exists
            new_cocktail = Cocktail(
                id = cocktail['idDrink'],
                name = cocktail['strDrink'],
                category = cocktail['strCategory'],
                alcoholic = True if cocktail['strAlcoholic'] == "Alcoholic" else False,
                glass = cocktail['strGlass'],
                instructions =cocktail['strInstructions'],
                image = cocktail['strDrinkThumb'],
                all_ingredients = cocktail['allIngredients'],
                number_of_ingredients = cocktail['numberOfIngredients'],
                ingredient_1 = cocktail['strIngredient1'],
                ingredient_2 = cocktail['strIngredient2'],
                ingredient_3 = cocktail['strIngredient3'],
                ingredient_4 = cocktail['strIngredient4'],
                ingredient_5 = cocktail['strIngredient5'],
                ingredient_6 = cocktail['strIngredient6'],
                ingredient_7 = cocktail['strIngredient7'],
                ingredient_8 = cocktail['strIngredient8'],
                ingredient_9 = cocktail['strIngredient9'],
                ingredient_10 = cocktail['strIngredient10'],
                ingredient_11 = cocktail['strIngredient11'],
                ingredient_12 = cocktail['strIngredient12'],
                ingredient_13 = cocktail['strIngredient13'],
                ingredient_14 = cocktail['strIngredient14'],
                ingredient_15 = cocktail['strIngredient15'],
                measure_1 = cocktail['strMeasure1'],
                measure_2 = cocktail['strMeasure2'],
                measure_3 = cocktail['strMeasure3'],
                measure_4 = cocktail['strMeasure4'],
                measure_5 = cocktail['strMeasure5'],
                measure_6 = cocktail['strMeasure6'],
                measure_7 = cocktail['strMeasure7'],
                measure_8 = cocktail['strMeasure8'],
                measure_9 = cocktail['strMeasure9'],
                measure_10 = cocktail['strMeasure10'],
                measure_11 = cocktail['strMeasure11'],
                measure_12 = cocktail['strMeasure12'],
                measure_13 = cocktail['strMeasure13'],
                measure_14 = cocktail['strMeasure14'],
                measure_15 = cocktail['strMeasure15']
                )
            
            db.session.add(new_cocktail)
            db.session.commit()










