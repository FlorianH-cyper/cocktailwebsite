from flask import Blueprint, render_template, request, flash, jsonify, redirect
from flask_login import login_required, current_user
from .models import Party, Cocktail, Menuitem, Shoppinglistitem, Rating, Inventoryitem
from website import db
import json
from website import db
from website.utils import (
    get_cocktail_ingredients_and_measures,
    aggregate_shopping_list,
    search_cocktails,
    cocktail_to_search_dict,
    cocktail_thumb_url,
    get_ratings_for_cocktails,
    get_cocktail_rating_summary,
    get_cocktail_ratings_detail,
    resolve_known_ingredient,
    get_known_ingredient_names,
)
views = Blueprint('views', __name__) # set up view blueprint for flask app


def _get_user_inventory():
    return (
        Inventoryitem.query.filter_by(user_id=current_user.id)
        .order_by(Inventoryitem.ingredient)
        .all()
    )



@views.route('/', methods=['GET', 'POST']) # will run whenever we access a url stating with /
@login_required
def parties():
    if request.method == 'POST':
        party_name = request.form.get('party_name')
        participants = int(request.form.get('participants'))
        drinks_per_participant = int(request.form.get('drinksPerParticipant'))
        number_of_drinks_needed = participants * drinks_per_participant
        if not party_name or not participants or not drinks_per_participant:
            flash('please enter all data to create party', category='error')
        else:
            new_party = Party(
                name=party_name, 
                number_of_participants= participants,
                drinks_per_participant = drinks_per_participant,
                number_of_drinks_needed = number_of_drinks_needed,
                user_id=current_user.id
                )
            db.session.add(new_party)
            db.session.commit()
            flash("party added", category='success')

    return render_template(
        "parties.html",
        user=current_user,
        inventory_items=_get_user_inventory(),
        inventory_return_to='/',
        known_ingredients=get_known_ingredient_names(),
    )




@views.route('/cocktailsearch', methods=['GET']) 
@login_required
def cocktailsearch():
    search_results, results_truncated = search_cocktails(
        name=request.args.get('cocktailName'),
        ingredient=request.args.get('ingredient'),
        alcoholic=request.args.get('alcoholic'),
    )
    ratings = get_ratings_for_cocktails(
        [cocktail.id for cocktail in search_results],
        user_id=current_user.id,
    )

    return render_template(
        "cocktailsearch.html",
        cocktails=search_results,
        ratings=ratings,
        results_truncated=results_truncated,
        cocktail_thumb_url=cocktail_thumb_url,
        user=current_user,
    )


@views.route('/api/cocktails', methods=['GET'])
@login_required
def api_cocktails():
    cocktails, truncated = search_cocktails(
        name=request.args.get('cocktailName'),
        ingredient=request.args.get('ingredient'),
        alcoholic=request.args.get('alcoholic'),
    )
    ratings = get_ratings_for_cocktails(
        [cocktail.id for cocktail in cocktails],
        user_id=current_user.id,
    )
    return jsonify({
        "cocktails": [
            cocktail_to_search_dict(c, ratings.get(c.id))
            for c in cocktails
        ],
        "truncated": truncated,
    })



@views.route('/delete-party', methods=['DELETE'])
def delete_party():
    data = json.loads(request.data)
    partyId = data['partyId'] # get party id from fe req
    party = Party.query.get(partyId) # find corresponding existing party in database
    if party:
        if party.user_id == current_user.id:
            db.session.delete(party)
            db.session.commit()
            flash('deleted succesfully', category='success')
    else:
        flash('did not work', category='error')

    return jsonify({}) # returns empty response

@views.route('/delete-menu-item', methods=['DELETE'])
def delte_menu_item():
    data = json.loads(request.data)
    menu_item_id = data['menuitemId'] 
    menu_item = Menuitem.query.get(menu_item_id)
    if menu_item:
        db.session.delete(menu_item)
        db.session.commit()
        flash('deleted succesfully', category='success')
    else:
        flash('did not work', category='error')
    return jsonify({}) # returns empty response


@views.route('/partydetails', methods=['GET'])
def partydetails():
    party_id = request.args.get('partyId')
    print(party_id)
    party = Party.query.get(party_id)
    menuitems = Menuitem.query.filter_by(party_id=party_id).all()
    listitems = Shoppinglistitem.query.filter(Shoppinglistitem.menuitem_id.in_([menuitem.id for menuitem in menuitems])).all()
    inventory = _get_user_inventory()
    aggregated_shopping_list = aggregate_shopping_list(listitems, menuitems, inventory)
    return render_template(
        "partydetails.html",
        party=party,
        shopping_list_view=aggregated_shopping_list,
        inventory_items=inventory,
        inventory_return_to=f'/partydetails?partyId={party_id}',
        user=current_user,
        known_ingredients=get_known_ingredient_names(),
    )


@views.route('/add-inventory-item', methods=['POST'])
@login_required
def add_inventory_item():
    ingredient = request.form.get('ingredient', '').strip()
    measure = request.form.get('measure', '').strip()
    return_to = request.form.get('return_to', '/')
    if not return_to.startswith('/') or return_to.startswith('//'):
        return_to = '/'

    if not ingredient or not measure:
        flash('Please enter both ingredient and amount.', category='error')
    else:
        canonical_ingredient = resolve_known_ingredient(ingredient)
        if not canonical_ingredient:
            flash(
                'That ingredient is not in the cocktail database. Choose one from the suggestions.',
                category='error',
            )
        else:
            db.session.add(Inventoryitem(
                user_id=current_user.id,
                ingredient=canonical_ingredient,
                measure=measure,
            ))
            db.session.commit()
            flash('Added to your inventory.', category='success')

    return redirect(return_to)


@views.route('/delete-inventory-item', methods=['DELETE'])
@login_required
def delete_inventory_item():
    data = request.get_json(silent=True) or {}
    item_id = data.get('inventoryItemId')
    item = Inventoryitem.query.get(item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Removed from inventory.', category='success')
    else:
        flash('Could not remove item.', category='error')
    return jsonify({})



@views.route('/add-cocktail-to-party', methods=['POST'])
def add_cocktail_to_party():
    data = json.loads(request.data)
    party_id = data['partyId']
    cocktail_id = data['cocktailId']
    amount = int(data['amount'])
    party = Party.query.get(party_id)
    cocktail = Cocktail.query.get(cocktail_id)   

    if not party or not cocktail:
        flash('did not work', category='error')
    else:
        existing_menu_item = Menuitem.query.filter_by(party_id=party_id, cocktail_id=cocktail_id).first()   
        
        if existing_menu_item:
            # Update the amount for the existing Menuitem
            existing_menu_item.amount += amount
            flash('Updated cocktail amount', category='success')
        
        else: 
            new_menu_item = Menuitem(
            party_id = party_id,
            cocktail_id = cocktail_id,
            amount = amount
            )
            db.session.add(new_menu_item)

            cocktail = Cocktail.query.filter_by(id=cocktail_id).first()
            data = get_cocktail_ingredients_and_measures(cocktail)
            for element in data:
                new_shopping_list_item = Shoppinglistitem(
                    menuitem_id = new_menu_item.id,
                    ingredient = element["ingredient"],
                    measure = element["measure"]
                )
                db.session.add(new_shopping_list_item)

            flash('added cocktails', category='success')
            

    db.session.commit()
            
    return jsonify({}) # returns empty response


@views.route('/api/cocktails/<int:cocktail_id>/ratings', methods=['GET'])
@login_required
def get_cocktail_ratings(cocktail_id):
    cocktail = Cocktail.query.get(cocktail_id)
    if not cocktail:
        return jsonify({"error": "cocktail not found"}), 404

    return jsonify(get_cocktail_ratings_detail(cocktail_id, current_user.id))


@views.route('/api/cocktails/<int:cocktail_id>/rate', methods=['POST'])
@login_required
def rate_cocktail(cocktail_id):
    data = json.loads(request.data)
    stars = data.get('stars')
    if stars is None:
        return jsonify({"error": "stars is required"}), 400

    try:
        stars = int(stars)
    except (TypeError, ValueError):
        return jsonify({"error": "stars must be an integer"}), 400

    if stars < 1 or stars > 5:
        return jsonify({"error": "stars must be between 1 and 5"}), 400

    cocktail = Cocktail.query.get(cocktail_id)
    if not cocktail:
        return jsonify({"error": "cocktail not found"}), 404

    rating = Rating.query.filter_by(
        user_id=current_user.id,
        cocktail_id=cocktail_id,
    ).first()
    if rating:
        rating.stars = stars
    else:
        rating = Rating(
            user_id=current_user.id,
            cocktail_id=cocktail_id,
            stars=stars,
        )
        db.session.add(rating)

    db.session.commit()
    return jsonify(get_cocktail_rating_summary(cocktail_id, current_user.id))
