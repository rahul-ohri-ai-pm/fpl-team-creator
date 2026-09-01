"""Web API server for FPL Team Analyzer frontend.

This Flask app serves as the bridge between the React frontend and the Python engine.
Run with: python web_api.py
Then access the frontend at http://localhost:5173 (dev) or http://localhost:8000 (prod)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from engine.fetch import fetch_live_fpl_squad, fetch_player_details
from engine.score import score_squad
from engine.optimize import get_transfer_recommendations
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/analyze', methods=['POST'])
def analyze_squad():
    """Analyze a squad and return recommendation."""
    try:
        data = request.json

        # Validate squad input
        squad = data.get('squad', {})
        bank = data.get('bank', 0.0)
        free_transfers = data.get('free_transfers', 1)

        if not squad:
            return jsonify({'error': 'No squad provided'}), 400

        # Score the current squad
        team_rating, position_breakdown, biggest_problem = score_squad(squad)

        # Get transfer recommendations
        recommendation, alternatives = get_transfer_recommendations(
            squad=squad,
            bank=bank,
            free_transfers=free_transfers
        )

        # Generate response
        return jsonify({
            'team_id': 'generated_' + str(int(time.time())),
            'team_rating': team_rating,
            'position_breakdown': position_breakdown,
            'biggest_problem': biggest_problem,
            'recommendation': recommendation,
            'alternatives': alternatives,
            'keep_reasoning': 'Your squad is well-balanced. Hold if you prefer to preserve transfers.',
            'starting_xi': squad,
            'timestamp': str(int(time.time()))
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-team', methods=['POST'])
def fetch_team():
    """Fetch live FPL squad by manager ID."""
    try:
        data = request.json
        manager_id = data.get('manager_id')

        if not manager_id:
            return jsonify({'error': 'No manager ID provided'}), 400

        # Fetch squad from FPL API
        squad, bank, free_transfers = fetch_live_fpl_squad(manager_id)

        if not squad:
            return jsonify({'error': 'Manager not found'}), 404

        return jsonify({
            'squad': squad,
            'bank': bank,
            'free_transfers': free_transfers,
            'manager_id': manager_id
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get list of all players for manual team builder."""
    try:
        # This should return all players from the FPL API
        # Format: [{'id': 1, 'name': 'Player Name', 'team': 'ARS', 'position': 'GK', 'price': 45}, ...]
        players = fetch_player_details()
        return jsonify(players)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr-screenshot', methods=['POST'])
def parse_screenshot():
    """Parse screenshot of FPL squad using OCR."""
    try:
        file = request.files.get('screenshot')
        if not file:
            return jsonify({'error': 'No screenshot provided'}), 400

        # TODO: Implement OCR parsing
        # For now, return a placeholder
        return jsonify({
            'error': 'OCR not yet implemented. Please use FPL ID or manual builder.'
        }), 501
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import time
    app.run(debug=True, host='0.0.0.0', port=8000)
