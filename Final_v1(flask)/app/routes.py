from flask import Blueprint, request, jsonify, send_file
from app.services.dorking import (
    generate_name_variants,
    create_suspect_folder,
    load_cache,
    save_cache,
    perform_searches,
    process_results,
    save_to_json,
    perform_dorking
)
import os
import re
import json

api = Blueprint('api', __name__)

@api.route('/add-suspect', methods=['POST'])
def add_suspect():
    """
    API endpoint to add a suspect.
    Expects JSON payload with 'suspect_name' and optional 'email', 'nic', 'social_media'.
    """
    try:
        data = request.json
        suspect_name = data.get('suspect_name')
        email = data.get('email', '')
        nic = data.get('nic', '')
        social_media = data.get('social_media', '')

        if not suspect_name:
            return jsonify({"status": "error", "error": "Suspect name is required."}), 400

        # Check if suspect already exists
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', suspect_name)
        suspect_folder = os.path.join('suspects', sanitized_name)

        if os.path.exists(suspect_folder):
            # Suspect already exists
            return jsonify({"status": "exists", "message": "Suspect already exists.", "suspect_name": suspect_name}), 200

        # Create suspect folder and subfolders
        create_suspect_folder(suspect_name)

        # Save suspect details to a JSON file
        suspect_details = {
            "name": suspect_name,
            "email": email,
            "nic": nic,
            "social_media": social_media
        }
        details_file = os.path.join(suspect_folder, 'details.json')
        with open(details_file, 'w', encoding='utf-8') as f:
            json.dump(suspect_details, f, ensure_ascii=False, indent=4)

        # Optionally, add to cache
        cache = load_cache(suspect_folder)
        save_cache(suspect_folder, cache)

        # Generate a unique suspect ID (e.g., timestamp or UUID)
        import uuid
        suspect_id = str(uuid.uuid4())

        # Return success response with suspect_id
        return jsonify({"status": "success", "message": f"Suspect '{suspect_name}' added successfully.", "suspect_id": suspect_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@api.route('/delete-suspect', methods=['DELETE'])
def delete_suspect():
    """
    API endpoint to delete a suspect.
    Expects JSON payload with 'suspect_name'.
    """
    try:
        data = request.json
        suspect_name = data.get('suspect_name')

        if not suspect_name:
            return jsonify({"status": "error", "error": "Suspect name is required."}), 400

        # Sanitize suspect name
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', suspect_name)
        suspect_folder = os.path.join('suspects', sanitized_name)

        if not os.path.exists(suspect_folder):
            return jsonify({"status": "error", "error": "Suspect not found."}), 404

        # Remove the suspect folder and all its contents
        import shutil
        shutil.rmtree(suspect_folder)

        return jsonify({"status": "success", "message": f"Suspect '{suspect_name}' deleted successfully."}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@api.route('/add-connection', methods=['POST'])
def add_connection():
    """
    API endpoint to add a connection between two suspects.
    Expects JSON payload with 'source' and 'target'.
    """
    try:
        data = request.json
        source = data.get('source')
        target = data.get('target')

        if not source or not target:
            return jsonify({"status": "error", "error": "Source and target are required."}), 400

        # Here you can implement logic to store connections in a database or file
        # For simplicity, we'll assume connections are managed on the frontend

        return jsonify({"status": "success", "message": f"Connection added between '{source}' and '{target}'."}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@api.route('/dork-suspect', methods=['POST'])
def dork_suspect():
    """
    API endpoint to perform dorking (scraping) for a suspect.
    Expects JSON payload with 'suspect_name', 'search_all', 'search_engines'.
    """
    try:
        data = request.json
        suspect_name = data.get('suspect_name')
        search_all = data.get('search_all', False)
        search_engines = data.get('search_engines', [])

        if not suspect_name:
            return jsonify({"status": "error", "error": "Suspect name is required."}), 400

        # Check if suspect exists
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', suspect_name)
        suspect_folder = os.path.join('suspects', sanitized_name)

        if not os.path.exists(suspect_folder):
            return jsonify({"status": "error", "error": "Suspect not found. Please add the suspect first."}), 404

        # Check if results already exist
        results_file = os.path.join(suspect_folder, 'results.json')
        if os.path.exists(results_file):
            # Suspect has already been scraped
            return jsonify({"status": "exists", "message": "Suspect has already been scraped.", "suspect_name": suspect_name}), 200

        # Perform scraping based on options
        perform_dorking(suspect_name, search_all, search_engines)

        return jsonify({"status": "success", "message": f"Dorking initiated for {suspect_name}."}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@api.route('/get-results', methods=['GET'])
def get_results():
    """
    API endpoint to retrieve the JSON results file for a suspect.
    Expects query parameter 'suspect_name'.
    """
    try:
        suspect_name = request.args.get('suspect_name')
        if not suspect_name:
            return jsonify({"status": "error", "error": "Suspect name is required."}), 400

        # Sanitize and locate the suspect folder
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', suspect_name)
        suspect_folder = os.path.join('suspects', sanitized_name)
        results_file = os.path.join(suspect_folder, 'results.json')

        if not os.path.exists(results_file):
            return jsonify({"status": "error", "error": "Results not found for the given suspect."}), 404

        # Read and return the JSON data
        with open(results_file, 'r', encoding='utf-8') as f:
            results_data = json.load(f)

        return jsonify(results_data), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500