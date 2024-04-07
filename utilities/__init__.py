from .setup_logging import create_logger
import socket, folium, json


logger = create_logger()

def get_local_ip() -> str:
    try:
        host_name: str = socket.gethostname()
        local_ip: str = socket.gethostbyname(host_name)
        return local_ip
    except Exception as error:
        logger.error(f"An error occured while getting local IP: {error}")
        return None

def create_line(trip, map: folium.Map) -> folium.Map:
    from webserver.models import TripData, Trips
    trip: Trips = trip
    colors = ["#33ccff", "green", "#c600ff"]
    color_map = folium.LinearColormap(colors, vmin=0, vmax=60)
    trip_data: list[TripData] = trip.trip_data
    trip_data.sort(key=lambda x: x.timestamp)
    
    coordinates = [(data.lat, data.lon) for data in trip_data if data.lon and data.lat]

    speeds = [data.speed for data in trip_data] 
    power = [data.power for data in trip_data]
    soc = [data.stateOfCharge for data in trip_data]
    
     #This is slow, but gives really nice tooltips
    for i in range(len(coordinates) - 1):
        start = coordinates[i]
        end = coordinates[i+1]
        speed = speeds[i]
        speed_calc = round(speed * 3.6, 2)
        batterystate = round((soc[i] * 100))
        kilopower = round((power[i] / 1000000), 1)
        
        folium.PolyLine(locations=[start, end], color=color_map(speed),opacity=1, weight=3,tooltip=f'<p>Geschwindigkeit: {speed_calc} km/h <br />Batteriestand: {batterystate} % <br />Leistung: {kilopower} kW </p>', parse_html=True).add_to(map)
    
    '''folium.ColorLine(
        positions = coordinates,
        colors = speeds, 
        colormap =  color_map, 
        opacity = 1,
        weight = 3
        ).add_to(map)'''
    
    
    
    return map