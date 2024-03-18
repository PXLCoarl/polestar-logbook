from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user
from werkzeug.security import check_password_hash
from .models import User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user: User = User.query.filter_by(email=email).first()
    if not user or not check_password_hash( user.password, password):
        flash('User does not exist or login details are wrong')
        return redirect(url_for('auth.login')) 
    login_user(user, remember=remember)
    return redirect(url_for('routes.index'))