from flask import Blueprint, request, render_template, render_template_string, redirect, url_for, send_file
from flask_login import login_required, current_user
from geopy.distance import geodesic
from geopy import distance as dt
from statistics import mean
from .models import User, TripData, Trips, UserSettings
from . import db
from icecream import ic
from datetime import datetime, timedelta
from utilities import create_line, add_points
import json, uuid, folium, folium.plugins, csv

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@routes.route('/profile', methods=['GET', 'POST'])
@login_required
def profile() -> str:
    user: User = current_user
    url: str = f'http://192.168.188.43:31777/webhooks/{user.webhook}?api_key={user.api_key}'
    trips: list[Trips] = user.trips
    trash = [trip for trip in trips if trip.trash]
    return render_template('profile.html', user=user, trash=trash)

@routes.route('/trips', methods=['GET', 'POST'])
@login_required
def trips() -> str:
    user: User = current_user
    trips: list[Trips] = user.trips
    trips = [trip for trip in trips if not trip.trash]
    return render_template("trips.html", username=user.name, trips=trips)

@routes.route('/map/<trip_id>')
def debug_map(trip_id: str) -> folium.Map:
    trip: Trips = Trips.query.filter_by(trip_id=trip_id).first()
    trip_data: list[TripData] = trip.trip_data
    #trip_data.sort(key=lambda x: x.timestamp)
    coordinates: list[tuple[float]] = []
    for data in trip_data:
        lat = data.lat
        lon = data.lon
        coordinates.append((lat, lon))
    
    map = folium.Map(
        location=[coordinates[(len(coordinates) // 2)][0], coordinates[(len(coordinates) // 2)][1]],
        tiles='https://tile.openstreetmap.de/{z}/{x}/{y}.png',
        zoom_start=9,
        attr=r'<a href=https://www.openstreetmap.org/copyright>OpenStreetMap</a> contributors'
    )
        
    map = create_line(trip=trip, map=map)
    map = add_points(coordinates, map=map)
    
    map.get_root().width = "1000px"
    map.get_root().height = "700px"
    iframe = map.get_root()._repr_html_()
    
    timestamp = (trip_data[-1].timestamp - trip_data[0].timestamp) / 1000
    hours = int(timestamp // 3600)
    minutes = int(timestamp % 3600 // 60)
    
    import json

    drivingpoints: list[dict] = [point for data in trip_data if data.drivingPoints for points in [json.loads(data.drivingPoints)] for point in points]

    
    distance = 0
    for point in drivingpoints:
        delta: float = point.get('distance_delta', 0)
        distance += delta
    '''
    [{"alt": 484.1669, 
    "distance_delta": 0.0, 
    "driving_point_epoch_time": 1701678768158, 
    "energy_delta": 0.0, 
    "lat": 48.795467, 
    "lon": 13.260598, 
    "point_marker_type": 1,
    "state_of_charge": 0.93}]
    '''
           
    length_str = f'{hours} hrs {minutes} min'
    mean_speed = round(mean([data.speed for data in trip_data]) * 3.6, 2)
    usage = (trip_data[0].batteryLevel - trip_data[-1].batteryLevel)
    mean_usage = round(mean([data.power for data in trip_data]) / 1e+6, 2)
    mean_usage_kwh = round(((usage / (distance)) * 100), 2)
    
    trip_stats = {'length': length_str, 'distance': round((distance / 1000), 2), 'mean_speed': mean_speed, 'usage': usage, 'kW/100km': mean_usage, 'kWh/100km': mean_usage_kwh}
    
    
    return render_template('map.html',
        iframe=iframe,
        trip = trip,
        trip_stats=trip_stats        
    )
    


@routes.route('/webhooks/<endpoint>', methods=['POST'])
def webhooks(endpoint):
    user: User = User.query.filter_by(webhook=endpoint).first()
    if not user:
        return "Unauthorized", 401
    user_settings: UserSettings = user.user_settings
    user_id: int = user.user_id
    api_key: str = request.args.get('api_key')
    
    content_type = request.headers.get('Content-Type')
    if not content_type == 'application/json':
        return "Wrong content type", 401
    if not user or user.api_key != api_key:
        return "Unauthorized", 401
    last_entry: TripData = TripData.query.filter_by(user_id=user_id).order_by(TripData.row.desc()).first()
    if last_entry:
        last_timestamp: int = last_entry.timestamp
    else:
        last_timestamp: int = 0
    
    data: dict = request.get_json()
    
    time_difference = (datetime.fromtimestamp(data['timestamp'] / 1000) - datetime.fromtimestamp(last_timestamp / 1000))
    if time_difference < timedelta(seconds=0):
        trip_uuid: str = str(uuid.uuid4())
        trip = Trips(trip_id=trip_uuid, trip_name=f"{datetime.fromtimestamp(data['timestamp'] / 1000).strftime('%d-%m-%Y %H:%M:%S')}", user_id=user_id)
        db.session.add(trip)
    elif time_difference >= timedelta(minutes=user_settings.trip_delay):
        trip_uuid: str = str(uuid.uuid4())
        trip = Trips(trip_id=trip_uuid, trip_name=f"{datetime.fromtimestamp(data['timestamp'] / 1000).strftime('%d-%m-%Y %H:%M:%S')}", user_id=user_id)
        db.session.add(trip)
    else:
        trip_uuid: str = last_entry.trip_id
        trip = Trips.query.filter_by(trip_id=trip_uuid).first()
    
    if 'chargingSessions' in data:
        data.pop('chargingSessions')
    
    if 'drivingPoints' in data:
        driving_points = json.dumps(data.pop('drivingPoints'))
    else:
        driving_points = None
    trip_data = TripData(trip_id=trip_uuid, user_id=user_id, drivingPoints=driving_points, **data)
    db.session.add(trip_data)
    db.session.commit()
    
    return "Success", 200


@login_required
@routes.route('/api/changename/<trip_id>', methods=['GET'])
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
@routes.route('/api/deletetrip/<trip_id>', methods=['GET'])
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
@routes.route('/api/restoretrip/<trip_id>', methods=['GET'])
def restore_trip(trip_id):
    
    trip = db.session.query(Trips).filter(Trips.trip_id == trip_id).first()
    if not trip:
        return redirect(url_for('routes.trips'))
    
    trip.trash = False
    db.session.commit()
    
    return redirect(url_for('routes.trips'))
