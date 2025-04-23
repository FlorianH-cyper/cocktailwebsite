import string
import requests
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("KEY")


headers = {
      "x-rapidapi-key": key,
      "x-rapidapi-host": "the-cocktail-db.p.rapidapi.com"}
    
url = "https://the-cocktail-db.p.rapidapi.com/search.php"

def fetch_all_cocktails():

    all_cocktails_not_unique = []

    for letter in list(string.ascii_lowercase):
        cocktails_for_letter = fetch_cocktails_by_letter(letter)
        all_cocktails_not_unique += cocktails_for_letter

    all_cocktails_unique = [dict(t) for t in {frozenset(d.items()) for d in all_cocktails_not_unique}]
    result = get_ingredient_aggregations_from_data(all_cocktails_unique)

    return result


def fetch_cocktails_by_letter(letter):
    querystring = {"s":letter}
    response = requests.get(url, headers=headers, params = querystring)
    cocktails = response.json()["drinks"]

    if not isinstance(cocktails, list):
       cocktails = []

    return cocktails


def get_ingredient_aggregations_from_data(data):
   for entry in data:
      entry = map_ingredient_aggregations(entry)
   return data


def map_ingredient_aggregations(entry):
    entry["allIngredients"] = ''
    entry["numberOfIngredients"] = 0
    for i in range(15):
      ingredient = entry["strIngredient" + str(i + 1)]
      if ingredient:
          entry["numberOfIngredients"] += 1
          if i > 0:
              entry["allIngredients"] += "  -  "
          entry["allIngredients"] += ingredient
    return entry

