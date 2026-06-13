"""Authoritative ingredient → (category, unit) rules for ingredient_unit_map.json.

Used by normalize_measures.py --generate-map. Rules only — no seed-data fallback.
"""

from __future__ import annotations

import re

# Sentinel units (match normalize_measures.py)
FRUIT_UNIT = "fruit"
PRODUCE_UNIT = "produce"

# ---------------------------------------------------------------------------
# Exact overrides (highest priority)
# ---------------------------------------------------------------------------
MANUAL_OVERRIDES: dict[str, tuple[str, str | None]] = {
    # --- citrus (whole fruit, counted) ---
    "Lemon": ("citrus", FRUIT_UNIT),
    "Lime": ("citrus", FRUIT_UNIT),
    "lime": ("citrus", FRUIT_UNIT),
    "Orange": ("citrus", FRUIT_UNIT),
    "orange": ("citrus", FRUIT_UNIT),
    "Blood Orange": ("citrus", FRUIT_UNIT),
    # --- produce (cup / piece / lb — never cl) ---
    "Apple": ("produce", PRODUCE_UNIT),
    "Apricot": ("produce", PRODUCE_UNIT),
    "Banana": ("produce", PRODUCE_UNIT),
    "Berries": ("produce", PRODUCE_UNIT),
    "Blackberries": ("produce", PRODUCE_UNIT),
    "Blueberries": ("produce", PRODUCE_UNIT),
    "Cantaloupe": ("produce", PRODUCE_UNIT),
    "Carrot": ("produce", PRODUCE_UNIT),
    "Cherries": ("produce", PRODUCE_UNIT),
    "Cranberries": ("produce", PRODUCE_UNIT),
    "Cucumber": ("produce", PRODUCE_UNIT),
    "Figs": ("produce", PRODUCE_UNIT),
    "Fruit": ("produce", PRODUCE_UNIT),
    "Ginger": ("produce", PRODUCE_UNIT),
    "Grapes": ("produce", PRODUCE_UNIT),
    "Kiwi": ("produce", PRODUCE_UNIT),
    "Mango": ("produce", PRODUCE_UNIT),
    "Papaya": ("produce", PRODUCE_UNIT),
    "Peach": ("produce", PRODUCE_UNIT),
    "Pineapple": ("produce", PRODUCE_UNIT),
    "Strawberries": ("produce", PRODUCE_UNIT),
    "Watermelon": ("produce", PRODUCE_UNIT),
    # --- garnish ---
    "Basil": ("herb", "sprig"),
    "Cherry": ("garnish", "piece"),
    "Ice": ("garnish", None),
    "Lavender": ("herb", "sprig"),
    "Lemon peel": ("garnish", None),
    "Lime peel": ("garnish", None),
    "Maraschino cherry": ("garnish", "piece"),
    "Mint": ("herb", "sprig"),
    "Olive": ("garnish", "piece"),
    "Orange Peel": ("garnish", None),
    "Orange spiral": ("garnish", None),
    "Rosemary": ("herb", "sprig"),
    # --- spices & dry botanicals (never cl) ---
    "Allspice": ("spice", "tsp"),
    "Almond": ("spice", "tsp"),
    "Almond flavoring": ("extract", "tsp"),
    "Anis": ("spice", "tsp"),
    "Anise": ("spice", "tsp"),
    "Angelica root": ("spice", "tsp"),
    "Asafoetida": ("spice", "pinch"),
    "Black pepper": ("spice", "pinch"),
    "Cardamom": ("spice", "tsp"),
    "Cayenne pepper": ("spice", "pinch"),
    "Celery salt": ("spice", "pinch"),
    "Cinnamon": ("spice", "stick"),
    "Cloves": ("spice", "tsp"),
    "Coriander": ("spice", "tsp"),
    "Cocoa powder": ("spice", "tsp"),
    "Cumin seed": ("spice", "tsp"),
    "Fennel seeds": ("spice", "tsp"),
    "Licorice root": ("spice", "tsp"),
    "Marjoram leaves": ("herb", "tsp"),
    "Nutmeg": ("spice", "pinch"),
    "Pepper": ("spice", "pinch"),
    "Red Chili Flakes": ("spice", "pinch"),
    "Salt": ("spice", "pinch"),
    "Thyme": ("herb", "tsp"),
    "Vanilla": ("spice", "piece"),
    "Wormwood": ("spice", "tsp"),
    # --- extracts & sauces ---
    "Hot Sauce": ("sauce", "dash"),
    "Peppermint extract": ("extract", "tsp"),
    "Soy Sauce": ("sauce", "dash"),
    "Tabasco sauce": ("sauce", "dash"),
    "Vanilla extract": ("extract", "tsp"),
    "Worcestershire Sauce": ("sauce", "dash"),
    # --- sugar (dry vs liquid) ---
    "Brown sugar": ("syrup_sugar", "tsp"),
    "demerara Sugar": ("syrup_sugar", "tsp"),
    "Honey": ("syrup_sugar", "tsp"),
    "Powdered sugar": ("syrup_sugar", "tsp"),
    "Sugar": ("syrup_sugar", "tsp"),
    "Raspberry syrup": ("syrup_sugar", "tsp"),
    # --- bitters ---
    "Angostura Bitters": ("bitters", "dash"),
    "Bitters": ("bitters", "dash"),
    "Orange bitters": ("bitters", "dash"),
    "Peach Bitters": ("bitters", "dash"),
    "Peychaud bitters": ("bitters", "dash"),
    # --- eggs ---
    "Egg": ("solid", "piece"),
    "Egg white": ("solid", "piece"),
    "Egg yolk": ("solid", "piece"),
    # --- solids / food (not liquids) ---
    "Butter": ("solid", "tblsp"),
    "Candy": ("solid", "piece"),
    "Chocolate": ("solid", "piece"),
    "Chocolate ice-cream": ("solid", "cup"),
    "Chocolate milk": ("dairy", "cl"),
    "Cornstarch": ("solid", "tsp"),
    "Food coloring": ("solid", "drop"),
    "Jello": ("solid", "package"),
    "Marshmallows": ("solid", "piece"),
    "Mini-snickers bars": ("solid", "piece"),
    "Oreo cookie": ("solid", "piece"),
    "Raisins": ("solid", "cup"),
    "Salted Chocolate": ("solid", "piece"),
    "Sherbet": ("solid", "cup"),
    "Vanilla ice-cream": ("solid", "cup"),
    # --- dairy & coffee ---
    "Coffee": ("dairy", "cl"),
    "Condensed milk": ("dairy", "cl"),
    "Cream": ("dairy", "cl"),
    "Cream of coconut": ("syrup_sugar", "cl"),
    "Espresso": ("dairy", "cl"),
    "Half-and-half": ("dairy", "cl"),
    "Heavy cream": ("dairy", "cl"),
    "Hot Chocolate": ("dairy", "cl"),
    "Irish cream": ("liqueur", "cl"),
    "Light cream": ("dairy", "cl"),
    "Milk": ("dairy", "cl"),
    "Whipped cream": ("dairy", "cl"),
    "Whipping cream": ("dairy", "cl"),
    "Yoghurt": ("dairy", "cl"),
    # --- mixers ---
    "7-Up": ("mixer", "cl"),
    "Ale": ("mixer", "cl"),
    "Beer": ("mixer", "cl"),
    "Bitter lemon": ("mixer", "cl"),
    "Carbonated soft drink": ("mixer", "cl"),
    "Carbonated water": ("mixer", "cl"),
    "Club soda": ("mixer", "cl"),
    "Coca-Cola": ("mixer", "cl"),
    "Cider": ("mixer", "cl"),
    "Corona": ("mixer", "cl"),
    "Dr. Pepper": ("mixer", "cl"),
    "Fresca": ("mixer", "cl"),
    "Ginger ale": ("mixer", "cl"),
    "Ginger Beer": ("mixer", "cl"),
    "Goldschlager": ("liqueur", "cl"),
    "Grape Soda": ("mixer", "cl"),
    "Guinness stout": ("mixer", "cl"),
    "Iced tea": ("mixer", "cl"),
    "Kool-Aid": ("mixer", "cl"),
    "Lager": ("mixer", "cl"),
    "Lemon-lime soda": ("mixer", "cl"),
    "Lemonade": ("mixer", "cl"),
    "Limeade": ("mixer", "cl"),
    "Mountain Dew": ("mixer", "cl"),
    "Pepsi Cola": ("mixer", "cl"),
    "Pink lemonade": ("mixer", "cl"),
    "Root beer": ("mixer", "cl"),
    "Sarsaparilla": ("mixer", "cl"),
    "Schweppes Russchian": ("mixer", "cl"),
    "Soda Water": ("mixer", "cl"),
    "Sprite": ("mixer", "cl"),
    "Surge": ("mixer", "cl"),
    "Tea": ("mixer", "cl"),
    "Tonic Water": ("mixer", "cl"),
    "Tropicana": ("mixer", "cl"),
    "Water": ("mixer", "cl"),
    "Zima": ("mixer", "cl"),
    # --- premix / sauces (liquid) ---
    "caramel sauce": ("syrup_sugar", "cl"),
    "Caramel coloring": ("premix", "drop"),
    "Chocolate Sauce": ("syrup_sugar", "cl"),
    "Chocolate syrup": ("syrup_sugar", "cl"),
    "Daiquiri mix": ("premix", "cl"),
    "Fruit punch": ("premix", "cl"),
    "Pina colada mix": ("premix", "cl"),
    "Sour mix": ("premix", "cl"),
    "Sweet and sour": ("premix", "cl"),
    # --- wine & vermouth ---
    "Champagne": ("wine_vermouth", "cl"),
    "Port": ("wine_vermouth", "cl"),
    "Prosecco": ("wine_vermouth", "cl"),
    "Red wine": ("wine_vermouth", "cl"),
    "Rose": ("wine_vermouth", "cl"),
    "Ruby Port": ("wine_vermouth", "cl"),
    "Rosso Vermouth": ("wine_vermouth", "cl"),
    "Sherry": ("wine_vermouth", "cl"),
    "White Wine": ("wine_vermouth", "cl"),
    "Wine": ("wine_vermouth", "cl"),
    "Dry Vermouth": ("wine_vermouth", "cl"),
    "Sweet Vermouth": ("wine_vermouth", "cl"),
    "Vermouth": ("wine_vermouth", "cl"),
    # --- liqueurs (explicit; checked before generic spirit) ---
    "Advocaat": ("liqueur", "cl"),
    "Amaretto": ("liqueur", "cl"),
    "Amaro Montenegro": ("liqueur", "cl"),
    "Anisette": ("liqueur", "cl"),
    "Apfelkorn": ("liqueur", "cl"),
    "Baileys irish cream": ("liqueur", "cl"),
    "Benedictine": ("liqueur", "cl"),
    "Blackcurrant cordial": ("liqueur", "cl"),
    "Blue Curacao": ("liqueur", "cl"),
    "Butterscotch schnapps": ("liqueur", "cl"),
    "Campari": ("liqueur", "cl"),
    "Chambord raspberry liqueur": ("liqueur", "cl"),
    "Cherry Heering": ("liqueur", "cl"),
    "Cherry liqueur": ("liqueur", "cl"),
    "Chocolate liqueur": ("liqueur", "cl"),
    "Coconut Liqueur": ("liqueur", "cl"),
    "Coffee liqueur": ("liqueur", "cl"),
    "Cointreau": ("liqueur", "cl"),
    "Creme de Banane": ("liqueur", "cl"),
    "Creme de Cacao": ("liqueur", "cl"),
    "Creme de Cassis": ("liqueur", "cl"),
    "Creme de Mure": ("liqueur", "cl"),
    "Curacao": ("liqueur", "cl"),
    "Dark Creme de Cacao": ("liqueur", "cl"),
    "Drambuie": ("liqueur", "cl"),
    "Dubonnet Rouge": ("liqueur", "cl"),
    "Elderflower cordial": ("liqueur", "cl"),
    "Erin Cream": ("liqueur", "cl"),
    "Frangelico": ("liqueur", "cl"),
    "Galliano": ("liqueur", "cl"),
    "Ginger Syrup": ("syrup_sugar", "cl"),
    "Glycerine": ("liqueur", "cl"),
    "Godiva liqueur": ("liqueur", "cl"),
    "Grand Marnier": ("liqueur", "cl"),
    "Green Chartreuse": ("liqueur", "cl"),
    "Green Creme de Menthe": ("liqueur", "cl"),
    "White Creme de Menthe": ("liqueur", "cl"),
    "Irish cream": ("liqueur", "cl"),
    "Jagermeister": ("liqueur", "cl"),
    "Jägermeister": ("liqueur", "cl"),
    "Kahlua": ("liqueur", "cl"),
    "Kirschwasser": ("liqueur", "cl"),
    "Kummel": ("liqueur", "cl"),
    "Lillet": ("liqueur", "cl"),
    "Lillet Blanc": ("liqueur", "cl"),
    "Malibu rum": ("liqueur", "cl"),
    "Maraschino liqueur": ("liqueur", "cl"),
    "Melon Liqueur": ("liqueur", "cl"),
    "Midori melon liqueur": ("liqueur", "cl"),
    "Mint syrup": ("syrup_sugar", "cl"),
    "Orange Curacao": ("liqueur", "cl"),
    "Passoa": ("liqueur", "cl"),
    "Pisang Ambon": ("liqueur", "cl"),
    "Raspberry Liqueur": ("liqueur", "cl"),
    "Rosemary Syrup": ("syrup_sugar", "cl"),
    "Rumple Minze": ("liqueur", "cl"),
    "St. Germain": ("liqueur", "cl"),
    "Strawberry liqueur": ("liqueur", "cl"),
    "Tia maria": ("liqueur", "cl"),
    "Triple sec": ("liqueur", "cl"),
    "Hpnotiq": ("liqueur", "cl"),
    "Yellow Chartreuse": ("liqueur", "cl"),
    # --- anise-flavoured spirits (liquid — not the same as Anis/Anise spice) ---
    "Absinthe": ("spirit", "cl"),
    "Ouzo": ("spirit", "cl"),
    "Pernod": ("spirit", "cl"),
    "Ricard": ("spirit", "cl"),
    "Sambuca": ("spirit", "cl"),
    "Black Sambuca": ("spirit", "cl"),
    # --- syrups (liquid) ---
    "Agave Syrup": ("syrup_sugar", "cl"),
    "Blackcurrant squash": ("syrup_sugar", "cl"),
    "Cherry Grenadine": ("syrup_sugar", "cl"),
    "Coconut syrup": ("syrup_sugar", "cl"),
    "Corn syrup": ("syrup_sugar", "cl"),
    "Grenadine": ("syrup_sugar", "cl"),
    "Honey syrup": ("syrup_sugar", "cl"),
    "Lime juice cordial": ("syrup_sugar", "cl"),
    "Maple syrup": ("syrup_sugar", "cl"),
    "Orgeat Syrup": ("syrup_sugar", "cl"),
    "Passion fruit syrup": ("syrup_sugar", "cl"),
    "Pineapple Syrup": ("syrup_sugar", "cl"),
    "Roses sweetened lime juice": ("syrup_sugar", "cl"),
    "Sirup of roses": ("syrup_sugar", "cl"),
    "Sugar Syrup": ("syrup_sugar", "cl"),
    "Vanilla syrup": ("syrup_sugar", "cl"),
    # --- misc ---
    "Aperol": ("liqueur", "cl"),
    "Apple cider": ("mixer", "cl"),
    "Aquavit": ("spirit", "cl"),
    "Apricot Nectar": ("juice", "cl"),
    "Bacardi Limon": ("spirit", "cl"),
    "Cherry brandy": ("liqueur", "cl"),
    "Cherry Juice": ("juice", "cl"),
    "Grain alcohol": ("spirit", "cl"),
    "Hot Damn": ("liqueur", "cl"),
    "Maui": ("liqueur", "cl"),
    "Olive Brine": ("mixer", "cl"),
    "Peach nectar": ("juice", "cl"),
    "Yukon Jack": ("liqueur", "cl"),
    "Falernum": ("syrup_sugar", "cl"),
    "Coconut milk": ("dairy", "cl"),
}

# Whole-word spirit tokens (avoid "ginger" matching "gin")
SPIRIT_WORDS = frozenset({
    "vodka", "gin", "rum", "tequila", "whiskey", "whisky", "bourbon", "brandy",
    "scotch", "cognac", "mezcal", "pisco", "cachaca", "absinthe", "ouzo",
    "pernod", "ricard", "sambuca", "everclear", "slivovitz",
})

SPIRIT_PHRASES = (
    "151 proof rum", "blackstrap rum", "blended scotch", "blended whiskey",
    "gold rum", "gold tequila", "dark rum", "light rum", "white rum", "spiced rum",
    "coconut rum", "cranberry vodka", "lemon vodka", "lime vodka", "peach vodka",
    "raspberry vodka", "apple brandy", "apricot brandy", "blackberry brandy",
    "peach brandy", "coffee brandy", "apple schnapps", "applejack",
    "islay single malt scotch", "tennessee whiskey", "rye whiskey",
    "irish whiskey", "southern comfort", "wild turkey", "jack daniels",
    "jim beam", "johnnie walker", "crown royal", "firewater", "sloe gin",
    "absolut citron", "absolut kurant", "absolut peppar", "absolut vodka",
    "añejo rum", "blue curacao", "sweet vermouth", "dry vermouth",
)

LIQUEUR_HINTS = (
    "liqueur", "creme de", "crème de", "schnapps", "cordial", "amaretto",
    "baileys", "kahlua", "cointreau", "triple sec", "grand marnier",
    "chambord", "frangelico", "drambuie", "benedictine", "galliano",
    "chartreuse", "anisette", "midori", "malibu", "curacao",
)

JUICE_HINTS = (" juice", "juice ", "nectar")


def _words(lower: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", lower))


def classify_ingredient(name: str) -> tuple[str, str | None]:
    """Return (category, unit) for an ingredient name. Rules only."""
    if name in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[name]

    lower = name.lower()

    if "bitters" in lower:
        return "bitters", "dash"
    if any(h in lower for h in JUICE_HINTS) or lower.endswith(" juice"):
        return "juice", "cl"
    if lower.endswith(" peel"):
        return "garnish", None
    if any(h in lower for h in LIQUEUR_HINTS):
        return "liqueur", "cl"
    if "syrup" in lower or lower in ("grenadine", "falernum"):
        return "syrup_sugar", "cl"
    if lower.endswith(" extract") or lower.endswith(" flavoring"):
        return "extract", "tsp"
    if lower.endswith(" sauce") and "worcestershire" not in lower and "soy" not in lower:
        return "syrup_sugar", "cl"
    if lower in ("milk", "cream", "yoghurt", "yogurt") or " cream" in lower:
        return "dairy", "cl"
    if lower.endswith(" ale") or lower.endswith(" beer") or lower.endswith(" stout"):
        return "mixer", "cl"
    if lower.endswith(" cola") or " soda" in lower or lower.endswith(" water"):
        return "mixer", "cl"

    # Spirits: whole-word or known phrase only (never substring "gin" in "ginger")
    if lower in SPIRIT_WORDS or _words(lower) & SPIRIT_WORDS:
        return "spirit", "cl"
    if any(lower == p or lower.startswith(p + " ") for p in SPIRIT_PHRASES):
        return "spirit", "cl"
    if any(p in lower for p in SPIRIT_PHRASES):
        return "spirit", "cl"

    # Brand spirits
    brand_spirits = (
        "jack daniels", "jim beam", "wild turkey", "johnnie walker", "crown royal",
        "captain", "bacardi", "smirnoff", "stoli", "beefeater", "tanqueray",
    )
    if any(b in lower for b in brand_spirits):
        return "spirit", "cl"

    if lower.endswith("berries") or lower in (
        "apple", "banana", "pineapple", "grapes", "mango", "papaya", "watermelon",
        "cantaloupe", "apricot", "peach", "kiwi", "figs", "carrot", "cucumber",
        "ginger", "fruit",
    ):
        return "produce", PRODUCE_UNIT

    if lower in ("lemon", "lime", "orange"):
        return "citrus", FRUIT_UNIT

    # Unknown: prefer countable units over cl
    if lower.endswith(("root", "seed", "seeds", "leaves", "leaf")):
        return "spice", "tsp"
    if lower.endswith(" powder"):
        return "spice", "tsp"

    return "solid", "piece"
