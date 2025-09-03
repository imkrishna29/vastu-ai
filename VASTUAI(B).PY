# VASTU AI - Backend Server
# To run this:
# 1. Install Flask: pip install Flask Flask-Cors
# 2. Run from terminal: python app.py

from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Initialize Flask App ---
app = Flask(__name__)
# CORS is needed to allow the frontend (running on a different address) to communicate with the backend.
CORS(app)

# --- CORE VASTU DATA & RULES (now on the server) ---
ZONES = {
    'NW': { 'name': 'North-West', 'deity': 'Vayu' },
    'N':  { 'name': 'North', 'deity': 'Kubera' },
    'NE': { 'name': 'North-East', 'deity': 'Ishaan' },
    'W':  { 'name': 'West', 'deity': 'Varuna' },
    'C':  { 'name': 'Center', 'deity': 'Brahma' },
    'E':  { 'name': 'East', 'deity': 'Surya' },
    'SW': { 'name': 'South-West', 'deity': 'Nirut' },
    'S':  { 'name': 'South', 'deity': 'Yama' },
    'SE': { 'name': 'South-East', 'deity': 'Agni' }
}

VASTU_RULES = {
    "Pooja Room": "NE", "Kitchen": "SE", "Master Bedroom": "SW",
    "Children's Bedroom": "W", "Guest Bedroom": "NW", "Living Room": "E",
    "Toilet": "NW", "Study Room": "W", "Dining Area": "W",
    "Staircase": "S", "Cash Locker": "N", "Garage": "NW",
    "Main Entrance": "E" # Default, will be recalculated
}

ALTERNATIVE_RULES = {
    "Kitchen": ["NW"], "Living Room": ["N", "NE"], "Guest Bedroom": ["SE"],
    "Toilet": ["S", "W"], "Staircase": ["W", "SW"], "Garage": ["SE"]
}

# --- The Main Logic Function ---
def calculate_vastu_plan(required_rooms, facing_direction):
    """
    This function contains the core Vastu logic. It takes room requirements
    and plot direction, and returns a complete plan.
    """
    house_plan = {zone: 'Empty' for zone in ZONES}
    notes = []
    primary_placements = 0

    if "Main Entrance" not in required_rooms:
        required_rooms.append("Main Entrance")

    # --- Main Entrance Placement ---
    entrance_padas = {'N': [3, 4, 5], 'E': [3, 4, 5], 'S': [3, 4], 'W': [3, 4, 5]}
    ideal_entrance_zone = {'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W'}
    entrance_zone = ideal_entrance_zone.get(facing_direction, 'E')

    if house_plan[entrance_zone] == 'Empty':
        house_plan[entrance_zone] = 'Main Entrance'
        notes.append({
            'type': 'success',
            'text': f"<strong>Main Entrance:</strong> Placed in the <strong>{facing_direction}</strong> direction. Auspicious padas are {entrance_padas[facing_direction]}."
        })
        primary_placements += 1
    else:
        notes.append({
            'type': 'warning',
            'text': f"<strong>Main Entrance:</strong> Could not be ideally placed in the {facing_direction} direction."
        })

    # --- Step 1: Place rooms based on primary Vastu rules ---
    for room in required_rooms:
        if room == "Main Entrance": continue
        if room in VASTU_RULES:
            ideal_zone = VASTU_RULES[room]
            if house_plan[ideal_zone] == 'Empty':
                house_plan[ideal_zone] = room
                notes.append({'type': 'success', 'text': f"<strong>{room}:</strong> Placed in its ideal <strong>{ideal_zone} ({ZONES[ideal_zone]['name']})</strong> zone."})
                primary_placements += 1

    # --- Step 2: Place remaining rooms ---
    placed_rooms = list(house_plan.values())
    remaining_rooms = [r for r in required_rooms if r not in placed_rooms]

    # Try alternative placements
    for room in remaining_rooms[:]:
        if room in ALTERNATIVE_RULES:
            for alt_zone in ALTERNATIVE_RULES[room]:
                if house_plan[alt_zone] == 'Empty':
                    house_plan[alt_zone] = room
                    notes.append({'type': 'info', 'text': f"<strong>{room}:</strong> Placed in a secondary zone: <strong>{alt_zone}</strong>."})
                    remaining_rooms.remove(room)
                    break
    
    # Place leftovers
    empty_zones = [zone for zone, assigned_room in house_plan.items() if assigned_room == 'Empty' and zone != 'C']
    for room in remaining_rooms:
        if empty_zones:
            zone_to_place = empty_zones.pop(0)
            house_plan[zone_to_place] = room
            notes.append({'type': 'warning', 'text': f"<strong>{room}:</strong> No ideal spot found. Placed in available zone <strong>{zone_to_place}</strong>."})
        else:
            notes.append({'type': 'error', 'text': f"<strong>{room}:</strong> Could not be placed. Not enough zones."})

    # --- Step 3: Brahmasthan Check ---
    if house_plan['C'] != 'Empty':
        notes.append({
            'type': 'error',
            'text': f"<strong>Brahmasthan (Center):</strong> Occupied by <strong>{house_plan['C']}</strong>. This is a major Vastu defect."
        })
    else:
        notes.append({'type': 'success', 'text': "<strong>Brahmasthan (Center):</strong> Correctly kept open."})

    compliance_score = round((primary_placements / len(required_rooms)) * 100) if required_rooms else 0

    return {'housePlan': house_plan, 'notes': notes, 'complianceScore': compliance_score}

# --- API Endpoint ---
@app.route('/api/generate-plan', methods=['POST'])
def generate_plan_endpoint():
    """
    This is the API endpoint that the frontend will call.
    It receives plot data, calls the logic function, and returns the result.
    """
    data = request.get_json()
    
    if not data or 'rooms' not in data or 'facing' not in data:
        return jsonify({'error': 'Invalid input. Missing rooms or facing direction.'}), 400

    required_rooms = data['rooms']
    facing_direction = data['facing']
    
    # Call the core logic function to get the plan
    result = calculate_vastu_plan(required_rooms, facing_direction)
    
    # Return the result as JSON
    return jsonify(result)

# --- Run the Server ---
if __name__ == '__main__':
    # Runs the server on http://127.0.0.1:5000
    app.run(debug=True, port=5000)
