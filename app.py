# app.py
import os, math
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

# configure via environment variables (easy for Cloud Run)
GEOFENCE_CENTER = {
    'lat': float(os.getenv('GEOFENCE_CENTER_LAT', '28.453489')),
    'lng': float(os.getenv('GEOFENCE_CENTER_LNG', '77.495797'))
}
GEOFENCE_RADIUS_M = float(os.getenv('GEOFENCE_RADIUS_M', '150'))  # meters
SECRET_TOKEN = os.getenv('SECRET_TOKEN', '')  # optional simple auth

def haversine_m(lat1, lon1, lat2, lon2):
    # returns distance in meters between two lat/lng points
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/log', methods=['POST'])
def log_event():
    # Simple token check (good for testing). For prod use OAuth / signed tokens.
    if SECRET_TOKEN:
        token = request.headers.get('X-API-Token', '')
        if token != SECRET_TOKEN:
            return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'bad request - no json'}), 400

    try:
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
    except Exception:
        return jsonify({'error': 'invalid lat/lng'}), 400

    event = data.get('event', 'unknown')
    ts = data.get('ts', None)

    distance_m = haversine_m(lat, lng, GEOFENCE_CENTER['lat'], GEOFENCE_CENTER['lng'])
    inside = distance_m <= GEOFENCE_RADIUS_M

    # Log to stdout — Cloud Run / Cloud Functions will capture this to Cloud Logging
    app.logger.info({
        'event': event,
        'lat': lat,
        'lng': lng,
        'distance_m': round(distance_m,1),
        'inside': inside,
        'ts': ts
    })

    return jsonify({'ok': True, 'inside': inside, 'distance_m': distance_m})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))
