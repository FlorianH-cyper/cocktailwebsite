from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from website import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__) # set up auth blueprint for flask app

@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.password == password:
                flash('logged in succesfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.parties'))
            else:
                flash('incorrect password', category='error')
        else:
            flash('user does not exist', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('user already exists', category='error')
        elif len(email) < 5:
            flash('Email must be greater than 4 characters', category='error')
        elif len(first_name) < 3:
            flash('First name must be greater than 2 characters', category='error')
        elif password1 != password2:
            flash('Passwords must be the same', category='error')
        elif len(password1) < 4:
            flash('Password to short', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=password1)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.parties'))


    return render_template("sign_up.html", user=current_user)
