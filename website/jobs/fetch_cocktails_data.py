"""Legacy one-off: pull cocktail records from a configured HTTP API.

Requires COCKTAIL_API_URL plus any auth headers in .env (not committed).
Day-to-day work should use cocktails_seed.json instead.
"""

import os
import string

import requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("COCKTAIL_API_URL", "")
headers = {
    name: value
    for name, value in (
        (os.getenv("COCKTAIL_API_AUTH_HEADER"), os.getenv("COCKTAIL_API_KEY")),
        (os.getenv("COCKTAIL_API_HOST_HEADER"), os.getenv("COCKTAIL_API_HOST")),
    )
    if name and value
}

def fetch_all_cocktails():
    if not url:
        raise RuntimeError(
            "COCKTAIL_API_URL is not set. This legacy import script is optional; "
            "use cocktails_seed.json for the bundled catalog."
        )

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

