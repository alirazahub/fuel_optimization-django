from fuel_opt.models import FuelStation
from .distance import haversine

def extract_fuel_stop_points(route, max_range=500):
    steps = route["routes"][0]["legs"][0]["steps"]
    fuel_points = []
    distance = 0

    for step in steps:
        miles = step["distance"]["value"] / 1609.34
        distance += miles
        if distance >= max_range:
            fuel_points.append(step["end_location"])
            distance = 0
    return fuel_points

def find_cheapest_station(lat, lng, radius=50):
    stations = FuelStation.objects.all()
    nearby = [s for s in stations if haversine(lat, lng, s.latitude, s.longitude) <= radius]
    return min(nearby, key=lambda x: x.price) if nearby else None

def calculate_cost(total_miles, stations):
    if not stations:
        return 0
    gallons = total_miles / 10
    avg_price = sum(s.price for s in stations) / len(stations)
    return gallons * avg_price
