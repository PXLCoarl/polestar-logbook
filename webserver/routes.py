from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from .models import User, TripData, Trips, UserSettings
from . import db
from icecream import ic
from datetime import datetime, timedelta
import json, uuid

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@routes.route('/profile', methods=['GET', 'POST'])
@login_required
def profile() -> str:
    user: User = current_user
    url: str = f'http://192.168.188.43:31777/webhooks/{user.webhook}?api_key={user.api_key}'
    return render_template('profile.html', username=user.name, url=url)

@routes.route('/trips', methods=['GET', 'POST'])
@login_required
def trips() -> str:
    user: User = current_user
    trips: list = user.trips
    return render_template("trips.html", username=user.name, trips=trips)



@routes.route('/webhooks/<endpoint>', methods=['POST', 'GET'])
def webhooks(endpoint):
    user: User = User.query.filter_by(webhook=endpoint).first()
    user_settings: UserSettings = user.user_settings
    user_id: int = user.user_id
    api_key: str = request.args.get('api_key')
    if request.method == 'GET':
        if not user or user.api_key != api_key:
            return "Unauthorized", 401
        return f'{api_key = }'
    
    content_type = request.headers.get('Content-Type')
    if not content_type == 'application/json':
        return "Unauthorized", 401
    if not user or user.api_key != api_key:
        return "Unauthorized", 401
    last_entry: TripData = TripData.query.filter_by(user_id=user_id).order_by(TripData.row.desc()).first()
    if last_entry:
        last_timestamp: int = last_entry.timestamp
    else:
        last_timestamp: int = 0
    
    data: dict = request.get_json()
    
    time_difference = (datetime.fromtimestamp(data['timestamp'] / 1000) - datetime.fromtimestamp(last_timestamp / 1000))
    if time_difference >= timedelta(minutes=user_settings.trip_delay):
        trip_uuid: str = str(uuid.uuid4())
        trip = Trips(trip_id=trip_uuid, trip_name=f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", user_id=user_id)
        db.session.add(trip)
    else:
        trip_uuid: str = last_entry.trip_id
        trip = Trips.query.filter_by(trip_id=trip_uuid).first()
    
    driving_points = json.dumps(data.pop('drivingPoints'))
    
    trip_data = TripData(trip_id=trip_uuid, user_id=user_id, drivingPoints=driving_points, **data)
    db.session.add(trip_data)
    db.session.commit()
    
    return "Success", 200