
def get_all_ingredients_from_cocktails(cocktails):
    data = []
    for cocktail in cocktails:
        for i in range(1, 16):
            ingredient = cocktail[f'strIngredient{i}']
            if ingredient and ingredient not in data:
                data.append(ingredient)
    return data
