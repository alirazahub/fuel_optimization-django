import requests
from django.conf import settings

def get_route(start, end):
    res = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": start,
            "destination": end,
            "key": settings.GOOGLE_MAPS_API_KEY
        }
    )
    return res.json()
