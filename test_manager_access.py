import json
from app import app, db
from models import User

with app.app_context():
    with app.test_client() as client:
        # Login as manager
        res = client.post('/api/login', json={'email': 'testmanager@chinhinforcast.com', 'password': 'password'})
        print(f"Login Manager: {res.status_code}")

        # Access location summary
        res = client.get('/api/warehouse/summary?location_id=1')
        print(f"Manager Location 1 Summary: {res.status_code}")

        res = client.get('/api/warehouse/summary?location_id=2')
        print(f"Manager Location 2 Summary: {res.status_code}")

        # Login as warehouse user (assigned to loc 1 and 2)
        res = client.post('/api/login', json={'email': 'testwarehouse@chinhinforcast.com', 'password': 'password'})
        print(f"Login Warehouse: {res.status_code}")

        res = client.get('/api/warehouse/summary?location_id=1')
        print(f"Warehouse Location 1 Summary: {res.status_code}")

        res = client.get('/api/warehouse/summary?location_id=3') # Not assigned
        print(f"Warehouse Location 3 Summary: {res.status_code}")
