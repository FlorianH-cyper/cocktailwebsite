from flask import Blueprint, render_template, request, flash,jsonify
from flask_login import login_required, current_user
from .models import Party, Cocktail, Menuitem, Shoppinglistitem
from website import db
import json
from website import db
from website.utils import get_cocktail_ingredients_and_measures, aggregate_shopping_list
views = Blueprint('views', __name__) # set up view blueprint for flask app



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

    return render_template("parties.html", user=current_user)


@views.route('/cocktailsearch', methods=['GET']) 
@login_required
def cocktailsearch():
    query = Cocktail.query
    
    by_name_search_string = request.args.get('cocktailName')
    by_ingredient_search_string = request.args.get('ingredient')
    alcoholic_filter = request.args.get('alcoholic')

    if(by_name_search_string):
        query = query.filter(Cocktail.name.contains(by_name_search_string))
    if by_ingredient_search_string:
        query = query.filter(Cocktail.all_ingredients.contains(by_ingredient_search_string))
    if alcoholic_filter:
        if(alcoholic_filter == "alcoholic"):
            query = query.filter(Cocktail.alcoholic == True)
        elif(alcoholic_filter == "non-alcoholic"):
            query = query.filter(Cocktail.alcoholic == False)
    
    search_results = query.all()

    return render_template("cocktailsearch.html", cocktails=search_results, user=current_user)



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
    aggregated_shopping_list = aggregate_shopping_list(listitems, menuitems)
    return render_template("partydetails.html", party=party, shopping_list_view=aggregated_shopping_list, user=current_user)



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
