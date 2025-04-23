import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getenv('PYTHONPATH'))

from website import create_app
from website.jobs.fetch_cocktails_data import fetch_all_cocktails
from website.jobs.write_cocktails_data import write_cocktails_to_db
from website.jobs.get_ingredients_data import get_all_ingredients_from_cocktails
from website.jobs.write_ingredients_data import write_ingredients_to_db

app = create_app()

with app.app_context():
    cocktails = fetch_all_cocktails()
    write_cocktails_to_db(cocktails)    
    print("Cocktails written to database")
    ingredients = get_all_ingredients_from_cocktails(cocktails)
    write_ingredients_to_db(ingredients)
    print("Ingredients written to database")
