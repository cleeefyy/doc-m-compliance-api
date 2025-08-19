from flask import Flask, request, jsonify
import openai
import os
import json # Import the json library

app = Flask(__name__)

# It's better to get the API key from environment variables for security
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_DEFAULT_API_KEY_HERE")

def generate_compliance_script(room_data):
    """
    Generates a pyRevit Python script based on room data.
    This version is compatible with IronPython and correctly injects the room data.
    """
    try:
        # For this example, we will generate a static, corrected script.
        # In a real-world scenario, you would use an LLM to generate this dynamically,
        # ensuring the output does not use f-strings.

        # Convert the incoming room_data (a Python list of dicts) into a JSON string representation
        # that can be embedded directly into the script.
        room_data_as_json_string = json.dumps(room_data)

        script_template = """# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
import json

def check_room_areas(room_data_list):
    print("--- Starting Room Area Compliance Check ---")
    non_compliant_rooms = []

    for room_info in room_data_list:
        room_name = room_info.get('Name', 'Unnamed')
        room_area = room_info.get('Area', 0.0)
        
        # Compliance rule: Area must be > 100 sq ft
        if room_area <= 100.0:
            non_compliant_rooms.append(room_name)
            # This print statement uses .format() for IronPython compatibility
            print("WARNING: Room '{}' has an area of {} sq ft, which is not compliant.".format(room_name, room_area))

    if non_compliant_rooms:
        message = "The following rooms are not compliant (Area <= 100 sq ft):\\n\\n" + "\\n".join(non_compliant_rooms)
        TaskDialog.Show("Compliance Check Failed", message)
    else:
        TaskDialog.Show("Compliance Check Passed", "All rooms meet the minimum area requirement.")
    
    print("--- Compliance Check Finished ---")

# The JSON data from the C# add-in is now correctly embedded into the script.
room_data_from_addin = {data_placeholder}
check_room_areas(room_data_from_addin)
""".format(data_placeholder=room_data_as_json_string) # Use .format() to inject the data

        return script_template

    except Exception as e:
        # This is the corrected f-string for the error message itself
        error_message = "Error generating script: {}".format(str(e))
        print(error_message)
        return "# An error occurred while generating the script: {}".format(str(e))


@app.route('/api/llm', methods=['POST'])
def handle_request():
    """
    API endpoint to receive data from the Revit add-in.
    """
    if not request.json:
        return jsonify({"error": "Invalid request: no JSON payload"}), 400

    room_data = request.json
    
    # Generate the compliance script
    generated_script = generate_compliance_script(room_data)
    
    # Return the generated script as plain text
    return generated_script, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))