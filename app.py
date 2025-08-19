from flask import Flask, request, jsonify
import openai
import os
import json

app = Flask(__name__)

# It's better to get the API key from environment variables for security
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_DEFAULT_API_KEY_HERE")

def generate_compliance_script(room_data):
    """
    Generates a pyRevit Python script that checks for a wheelchair turning circle
    and draws a visual overlay in non-compliant rooms.
    """
    try:
        # Convert the incoming room data into a nicely formatted string for the prompt
        room_data_str = json.dumps(room_data, indent=2)

        # This is a placeholder for a real LLM call. In a real application, you would
        # send the prompt below to a powerful model like GPT-4 or a fine-tuned equivalent.
        # For this example, we will generate a static, corrected script that demonstrates the final output.

        prompt_template = f"""
You are an expert Revit API developer specializing in pyRevit scripts for building compliance.
Your task is to generate a complete, standalone IronPython 2.7 script for pyRevit.

The user has provided the following JSON data representing rooms in a Revit model:
{room_data_str}

The script must perform the following actions:
1.  Find all 'Room' elements in the current Revit document.
2.  For each room, check if its area is less than the area required for a 1500mm diameter turning circle (approximately 1.77 square meters or 19 square feet).
3.  If a room is non-compliant (too small), create a visual overlay inside that room.
4.  The overlay must be a red, semi-transparent cylinder representing the 1500mm turning circle. Use the 'DirectShape' API to create this geometry.
5.  All model modifications (creating DirectShapes) must be wrapped in a Revit Transaction.
6.  The script must be fully compatible with IronPython 2.7 (e.g., use .format() instead of f-strings).
7.  Print clear messages to the console for both compliant and non-compliant rooms.

Generate only the Python code. Do not include any explanations.
"""

        # --- STATIC SCRIPT GENERATION (Placeholder for a real LLM call) ---
        # A real LLM would generate the script below based on the prompt. This template
        # serves as the ideal output we want the LLM to produce.

        generated_script = """# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
import math

# --- Configuration ---
TURNING_CIRCLE_DIAMETER_MM = 1500.0
MIN_AREA_SQ_FEET = 19.0 # Approx. area for a 1500mm circle
OVERLAY_COLOR = Color(255, 0, 0) # Red
OVERLAY_TRANSPARENCY = 80 # 0-100

def create_turning_circle_overlay(doc, center_point):
    \"\"\"Creates a DirectShape cylinder to visualize the turning circle.\"\"\"
    app = doc.Application
    
    # Convert diameter from mm to internal feet
    radius_feet = (TURNING_CIRCLE_DIAMETER_MM / 2) / 304.8
    height_feet = 0.1 # A thin disc for visualization
    
    # Create a cylinder profile
    circle = Ellipse.Create(center_point, radius_feet, radius_feet, XYZ.BasisX, XYZ.BasisY, 0, 2 * math.pi)
    solid = GeometryCreationUtilities.CreateExtrusionGeometry([circle], XYZ.BasisZ, height_feet)
    
    # Create the DirectShape
    ds = DirectShape.CreateElement(doc, ElementId(BuiltInCategory.OST_GenericModel))
    ds.SetShape([solid])
    ds.Name = "Compliance Overlay - Turning Circle"
    
    # Set visual style (color and transparency)
    ogs = OverrideGraphicSettings()
    ogs.SetSurfaceForegroundPatternColor(OVERLAY_COLOR)
    ogs.SetSurfaceTransparency(OVERLAY_TRANSPARENCY)
    doc.ActiveView.SetElementOverrides(ds.Id, ogs)
    
    return ds

# --- Main Execution ---
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

print("--- Starting Turning Circle Compliance Check ---")

# Use a FilteredElementCollector to get all rooms
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
non_compliant_rooms = []

# Start a transaction to allow model changes (creating DirectShapes)
t = Transaction(doc, "Create Compliance Overlays")
t.Start()

try:
    for room in room_collector:
        # Ensure it's a valid, placed room with a location
        if room.Area > 0 and room.Location is not None:
            room_name = room.Name
            room_area_sq_feet = room.Area
            
            if room_area_sq_feet < MIN_AREA_SQ_FEET:
                non_compliant_rooms.append(room_name)
                print("WARNING: Room '{}' is NON-COMPLIant. Area: {:.2f} sq ft.".format(room_name, room_area_sq_feet))
                
                # Find room center to place the overlay
                location_point = room.Location.Point
                create_turning_circle_overlay(doc, location_point)
            else:
                print("OK: Room '{}' is compliant. Area: {:.2f} sq ft.".format(room_name, room_area_sq_feet))

    t.Commit()
    print("--- Transaction Committed Successfully ---")

except Exception as e:
    t.RollBack()
    print("An error occurred, transaction rolled back: {}".format(str(e)))

# --- Final Report ---
if non_compliant_rooms:
    message = "The following rooms are too small for a 1500mm turning circle:\\n\\n" + "\\n".join(non_compliant_rooms)
    TaskDialog.Show("Compliance Check Failed", message)
else:
    TaskDialog.Show("Compliance Check Passed", "All rooms are large enough for a 1500mm turning circle.")

print("--- Compliance Check Finished ---")
"""
        return generated_script

    except Exception as e:
        error_message = "Error generating script: {}".format(str(e))
        print(error_message)
        return "# An error occurred while generating the script: {}".format(str(e))


@app.route('/api/llm', methods=['POST'])
def handle_request():
    if not request.json:
        return jsonify({"error": "Invalid request: no JSON payload"}), 400
    room_data = request.json
    generated_script = generate_compliance_script(room_data)
    return generated_script, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))