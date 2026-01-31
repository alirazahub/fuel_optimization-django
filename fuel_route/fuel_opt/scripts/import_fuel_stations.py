# scripts/import_fuel_stations.py
import pandas as pd
import requests
import time
import sys
import os
import django

# Get the path to the project root (two levels up from scripts)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Point to your settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuel_route.settings")
django.setup()

from fuel_opt.models import FuelStation
from django.conf import settings

# Read CSV instead of Excel
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "data.csv")
df = pd.read_csv(csv_path)

# Optional: keep track of already imported truckstops to avoid duplicates
imported_truckstops = set()

for _, row in df.iterrows():
    # Skip duplicate truckstops by name and address
    truckstop_key = (row["Truckstop Name"], row["Address"])
    if truckstop_key in imported_truckstops:
        continue

    imported_truckstops.add(truckstop_key)

    # Full address for geocoding
    address = f"{row['Address']}, {row['City']}, {row['State']}, USA"

    try:
        res = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": address,
                "key": settings.GOOGLE_MAPS_API_KEY
            },
            timeout=5  # avoid hanging
        ).json()
    except requests.RequestException as e:
        print(f"Request failed for {address}: {e}")
        continue

    if not res.get("results"):
        print(f"No geocoding results for {address}")
        continue

    loc = res["results"][0]["geometry"]["location"]

    # Create FuelStation record
    FuelStation.objects.create(
        name=row["Truckstop Name"],
        address=row["Address"],
        city=row["City"],
        state=row["State"],
        price=row["Retail Price"],
        latitude=loc["lat"],
        longitude=loc["lng"]
    )

    print(f"Imported {row['Truckstop Name']} at {loc['lat']}, {loc['lng']}")

    time.sleep(0.1)  # avoid rate limits
