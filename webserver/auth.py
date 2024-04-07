from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User
from . import db
import random, string

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

@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))
    


@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('register.html')
    
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email address already in use')
        return redirect(url_for('auth.signup'))
    
    webhook = None
    api_key = None
    while api_key is None or User.query.filter_by(api_key=api_key).first():
        api_key = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(25))
    while webhook is None or User.query.filter_by(webhook=webhook).first():
        webhook = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(5))
    new_user = User(email=email, name=name, webhook=webhook, api_key=api_key, password=generate_password_hash(password=password, method='pbkdf2:sha256'))
    db.session.add(new_user)
    db.session.commit()    
    return redirect(url_for('auth.login'))