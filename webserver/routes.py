from flask import Blueprint, request, render_template, render_template_string
from flask_login import login_required, current_user
from geopy.distance import geodesic
from statistics import mean
from .models import User, TripData, Trips, UserSettings
from . import db
from icecream import ic
from datetime import datetime, timedelta
from utilities import create_line
import json, uuid, folium, folium.plugins

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

@routes.route('/map/<trip_id>')
def debug_map(trip_id: str) -> folium.Map:
    trip: Trips = Trips.query.filter_by(trip_id=trip_id).first()
    trip_data: list[TripData] = trip.trip_data
    trip_data.sort(key=lambda x: x.timestamp)
    coordinates: list[list[float]] = []
    for data in trip_data:
        lat = data.lat
        lon = data.lon
        coordinates.append([lat, lon])
    
    map = folium.Map(
        location=[coordinates[(len(coordinates) // 2)][0], coordinates[(len(coordinates) // 2)][1]],
        tiles='https://tile.openstreetmap.de/{z}/{x}/{y}.png',
        zoom_start=9,
        attr=r'<a href=https://www.openstreetmap.org/copyright>OpenStreetMap</a> contributors'
    )
        
    map = create_line(trip=trip, map=map)
    
    map.get_root().width = "1000px"
    map.get_root().height = "700px"
    iframe = map.get_root()._repr_html_()

    distance = 0
    for i in range(len(coordinates) - 1):
        distance += geodesic(coordinates[i], coordinates[i+1]).meters
    
    
    
    timestamp = (trip_data[-1].timestamp - trip_data[0].timestamp) / 1000
    hours = int(timestamp // 3600)
    minutes = int(timestamp % 3600 // 60)

    amount_dp = 0
    for i in range(len(trip_data)):
        drivingPoints = trip_data[i].drivingPoints
        drivingPoints = json.loads(drivingPoints)
        for obj in drivingPoints:
            # ic(obj)
            amount_dp += 1
    amount_trip_data = 0
    for i in range(len(trip_data)):
        amount_trip_data += 1
        
    length_str = f'{hours} hrs {minutes} min'
    mean_speed = round(mean([data.speed for data in trip_data]) * 3.6, 2)
    usage = (trip_data[0].batteryLevel - trip_data[-1].batteryLevel)
    mean_usage = round(mean([data.power for data in trip_data]) / 1e+6, 2)
    mean_usage_kwh = round(((usage / (distance)) * 100), 2)
    
    trip_stats = {'length': length_str, 'distance': round((distance / 1000), 2), 'mean_speed': mean_speed, 'usage': usage, 'kW/100km': mean_usage, 'kWh/100km': mean_usage_kwh}
    
    
    return render_template_string(
        """
        {% extends "base.html" %}

        {% block content %}
        <div class="columns">
            <div class="column is-4 is-offset-4">
                <p class="is-unselectable">Trip {{ trip.trip_name }}</p>
            </div>
        </div>
        <div class="columns">
            <div class="column">
                {{ iframe|safe }}
            </div>
            <div class="column">
                <!--<p class="subtitle"> Trip Data: </p>
                <div class="columns">
				            <!--<p>Dauer des Trips: <br> {trip_duration}</p>
                            <p>Strecke: <br> {trip_total_distance} km</p>
                            <p>Durchschnittsgeschwindigkeit:<br> {trip_mean_speed} km/h</p>
				            <p>Stromverbrauch: <br> {trip_energy} kWh</p>
                            <p>Durchschnittlicher Stromverbrauch:<br>{trip_energy_usage} kWh/100km</p>-->
                <p class="subtitle">Statistiken</p>
                <div class="fixed-grid has-2-cols">
                    <div class="grid">
                        <div class="cell has-text-right">Dauer:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('length') }}</div>
                        
                        <div class="cell has-text-right">Strecke:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('distance') }} km</div>
                        
                        <div class="cell has-text-right">⌀ Tempo:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('mean_speed') }} km/h</div>
                        
                        <div class="cell has-text-right">Verbrauch:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('usage')/1000 }} kWh</div>
                        
                        <div class="cell has-text-right">⌀ Verbrauch:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('kW/100km') }} kW/100km</div>
                        
                        <div class="cell has-text-right">⌀ Verbrauch:</div>
                        <div class="cell has-text-left">{{ trip_stats.get('kWh/100km') }} kWh/100km</div>
                        
                        <div class="cell has-text-right"># Driving Points:</div>
                        <div class="cell has-text-left">{{ amount_dp }}</div>
                        <div class="cell has-text-right"># Trip Data:</div>
                        <div class="cell has-text-left">{{ amount_trip_data }}</div>
                    </div>
                </div>
                
            </div>
        </div>
        {% endblock %}
        """,
        iframe=iframe,
        trip = trip,
        trip_stats=trip_stats,
        amount_dp = amount_dp,
        amount_trip_data = amount_trip_data
        
    )
    return map
    


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