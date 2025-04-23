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