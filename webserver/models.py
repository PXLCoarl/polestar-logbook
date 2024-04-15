from . import db
from flask_login import UserMixin
from sqlalchemy import event


class TripData(db.Model):
    row: int = db.Column(db.Integer, primary_key=True)
    alt: int = db.Column(db.Integer)
    ambientTemperature: int = db.Column(db.Integer)
    apiVersion: str = db.Column(db.String(5))
    appVersion: str = db.Column(db.String(20))
    batteryLevel: int = db.Column(db.Integer)
    chargePortConnected: bool = db.Column(db.Boolean)
    drivingPoints: str = db.Column(db.String(5000))
    ignitionState: str = db.Column(db.String(20))
    lat: float = db.Column(db.Float)
    lon: float = db.Column(db.Float)
    power: float = db.Column(db.Float)
    selectedGear: str = db.Column(db.String(1))
    speed: float = db.Column(db.Float)
    stateOfCharge: float = db.Column(db.Float)
    timestamp: int = db.Column(db.Integer)
    trip_id: str = db.Column(db.String(36), db.ForeignKey('trips.trip_id'))
    trip = db.relationship('Trips', back_populates='trip_data')
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    user = db.relationship('User', backref='trip_data')
        
class Trips(db.Model):
    row: int = db.Column(db.Integer, primary_key = True)
    trip_id: str = db.Column(db.String(36))
    trip_name: str = db.Column(db.String(100))
    trip_data = db.relationship('TripData', back_populates='trip')
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    trash = db.Column(db.Boolean, default=False)
    #user = db.relationship('User', backref='user_trips')
    
    
class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    webhook = db.Column(db.String(5), unique=True)
    api_key = db.Column(db.String(25), unique=True)
    trips = db.relationship('Trips', backref='user', lazy=True)
    user_settings = db.relationship('UserSettings', backref='user', uselist=False, lazy=True)
    def get_id(self):
        return str(self.user_id)
    
class UserSettings(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, primary_key=True)
    license_plate = db.Column(db.String(10), default='Kennzeichen')
    trip_amount = db.Column(db.Integer, default=50)
    trip_delay = db.Column(db.Integer, default=30)
    tibber_email = db.Column(db.String(100), default='Tibber Login')
    tibber_password = db.Column(db.String(100), default='Tibber Password')
    timezone = db.Column(db.String(100), default='Europe/Berlin')
    
@event.listens_for(User, 'after_insert')
def create_user_settings(mapper, connection, target):
    user_id = target.user_id
    connection.execute(UserSettings.__table__.insert().values(user_id=user_id))