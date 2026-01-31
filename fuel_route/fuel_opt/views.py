from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.google_maps import get_route
from .services.fuel_optimizer import extract_fuel_stop_points, find_cheapest_station, calculate_cost

class RouteAPIView(APIView):
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

        return Response({
            "distance_miles": round(miles, 2),
            "fuel_stops": [
                {
                    "name": s.name,
                    "price": s.price,
                    "lat": s.latitude,
                    "lng": s.longitude
                } for s in fuel_stops
            ],
            "total_fuel_cost": round(total_cost, 2)
        })
