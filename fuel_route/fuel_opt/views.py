from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from .services.google_maps import get_route
from .services.fuel_optimizer import extract_fuel_stop_points, find_cheapest_station, calculate_cost

def index(request):
    """Render the main UI page"""
    return render(request, 'fuel_opt/index.html', {
        'google_maps_key': settings.GOOGLE_MAPS_API_KEY
    })

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check

class RouteAPIView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        start = request.data.get("start")
        end = request.data.get("end")

        if not start or not end:
            return Response({"error": "Start and end locations are required"}, status=400)

        route = get_route(start, end)
        if route.get("status") != "OK":
            return Response({"error": "Google Maps API failed"}, status=500)

        miles = route["routes"][0]["legs"][0]["distance"]["value"] / 1609.34

        fuel_points = extract_fuel_stop_points(route)

        fuel_stops = []
        for p in fuel_points:
            station = find_cheapest_station(p["lat"], p["lng"])
            if station:
                fuel_stops.append(station)

        total_cost = calculate_cost(miles, fuel_stops)

        # Extract route polyline for map visualization
        polyline = route["routes"][0]["overview_polyline"]["points"]
        
        return Response({
            "distance_miles": round(miles, 2),
            "route": {
                "polyline": polyline,
                "start_address": route["routes"][0]["legs"][0]["start_address"],
                "end_address": route["routes"][0]["legs"][0]["end_address"]
            },
            "fuel_stops": [
                {
                    "name": s.name,
                    "address": s.address,
                    "city": s.city,
                    "state": s.state,
                    "price": s.price,
                    "lat": s.latitude,
                    "lng": s.longitude
                } for s in fuel_stops
            ],
            "total_fuel_cost": round(total_cost, 2),
            "fuel_consumption_gallons": round(miles / 10, 2)
        })
