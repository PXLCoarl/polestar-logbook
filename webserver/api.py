from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import login_required, current_user
from .models import User, TripData, Trips, UserSettings
from . import db

api = Blueprint('api', __name__)

@login_required
@api.route('changename/<trip_id>', methods=['GET'])
def changename(trip_id):
    name: str = request.args.get('name')
    
    trip = db.session.query(Trips).filter(Trips.trip_id == trip_id).first()
    if trip:
        trip.trip_name = name
        db.session.commit()
        return redirect(url_for('routes.trips'))
    else:
        # Handle case where trip with given trip_id does not exist
        return "Trip not found", 404
    
@login_required   
@api.route('deletetrip/<trip_id>', methods=['GET'])
def delete_trip(trip_id):
    
    trip = db.session.query(Trips).filter(Trips.trip_id == trip_id).first()
    if not trip:
        return redirect(url_for('routes.trips'))
    
    if not trip.trash:
        trip.trash = True
    else:
        trip_data = trip.trip_data
        for data in trip_data:
            db.session.delete(data)
        db.session.delete(trip)
    db.session.commit()    
    
    return redirect(url_for('routes.trips'))

@login_required
@api.route('restoretrip/<trip_id>', methods=['GET'])
def restore_trip(trip_id):
    
    trip = db.session.query(Trips).filter(Trips.trip_id == trip_id).first()
    if not trip:
        return redirect(url_for('routes.trips'))
    
    trip.trash = False
    db.session.commit()
    
    return redirect(url_for('routes.trips'))

@login_required
@api.route('changepassword', methods=['POST'])
def change_password():
    from icecream import ic
    ic(request.form)
    return redirect('/success')