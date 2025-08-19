from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# It's better to get the API key from environment variables for security
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_DEFAULT_API_KEY_HERE")

def generate_compliance_script(room_data_json):
    """
    Generates a pyRevit Python script based on room data using an LLM.
    """
    try:
        # A more detailed prompt explaining the context and desired output
        prompt = f"""
        You are an expert in building compliance and Revit automation.
        Based on the following JSON data describing rooms in a Revit model, generate a complete, standalone pyRevit Python script.
        The script should check for a basic compliance rule: ensure every room has an area greater than 100 square feet.
        For each room that fails this check, the script should print a warning message to the console.
        The script must be compatible with IronPython 2.7.

        Room data:
        {room_data_json}

        Generate only the Python code. Do not include any explanations or markdown formatting.
        The script should start with the necessary imports (e.g., from Autodesk.Revit.DB import *).
        """

        # This is a placeholder for a real LLM call.
        # In a real application, you would use a library like 'openai' to call the model.
        # For this example, we will generate a static, corrected script.

        # --- STATIC SCRIPT GENERATION (Placeholder for LLM) ---
        
        # This generated script is now written to be compatible with IronPython.
        # It iterates through the provided room data.
        
        script_template = """
# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

def check_room_areas(room_data):
    doc = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument

    print("--- Starting Room Area Compliance Check ---")
    non_compliant_rooms = []

    for room_info in room_data:
        room_name = room_info.get('Name', 'Unnamed')
        room_area = room_info.get('Area', 0.0)
        
        # Compliance rule: Area must be > 100 sq ft
        if room_area <= 100.0:
            non_compliant_rooms.append(room_name)
            print("WARNING: Room '{}' has an area of {} sq ft, which is not compliant.".format(room_name, room_area))

    if non_compliant_rooms:
        message = "The following rooms are not compliant (Area <= 100 sq ft):\\n\\n" + "\\n".join(non_compliant_rooms)
        TaskDialog.Show("Compliance Check Failed", message)
    else:
        TaskDialog.Show("Compliance Check Passed", "All rooms meet the minimum area requirement.")
    
    print("--- Compliance Check Finished ---")

# The JSON data from the C# add-in would be passed here in a real scenario.
# For this example, we'll use the data sent in the request.
room_data_from_request = {room_data_json}
check_room_areas(room_data_from_request)
"""
        # For the purpose of this example, we return a fixed script.
        # The f-strings that caused the original error have been replaced with .format().
        # This is a simplified example. A real LLM would generate this dynamically.
        
        # Example of the corrected print statements that would be in a dynamically generated script:
        # print("✓ Door {} analyzed successfully".format(door.Id))
        # print("✗ Error processing door: {}".format(str(e)))
        
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