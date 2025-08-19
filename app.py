from flask import Flask, request, jsonify
import openai
import os
import json
import re # Import the regular expression library

app = Flask(__name__)

# Get the API key from environment variables for security
openai.api_key = os.getenv("OPENAI_API_KEY")

def convert_fstrings_to_format(python_code):
    """
    Automatically finds and converts f-strings to .format() syntax.
    This is a robust way to ensure IronPython compatibility.
    """
    # Regex to find f-strings and capture the content and variables
    # It handles both single and double quotes
    fstring_pattern = re.compile(r"f(['\"])(.*?)\{([^}]+)\}(.*?)(\1)")

    def replacer(match):
        # This function builds the .format() string
        quote = match.group(1)
        pre_variable = match.group(2)
        variable = match.group(3)
        post_variable = match.group(4)
        
        # Construct the new string and the argument for .format()
        new_string = quote + pre_variable + '{}' + post_variable + quote
        format_argument = variable
        
        return "{}.format({})".format(new_string, format_argument)

    # Keep replacing until no f-strings are left
    converted_code = python_code
    while fstring_pattern.search(converted_code):
        converted_code = fstring_pattern.sub(replacer, converted_code)
        
    return converted_code

def generate_compliance_script(revit_data_json):
    """
    Generates a pyRevit Python script by calling an LLM.
    """
    revit_data_str = json.dumps(revit_data_json, indent=2)

    # A simpler prompt, as we no longer need to give complex negative instructions
    prompt = f"""
    You are an expert Revit API developer. Generate a complete, standalone pyRevit script.
    The script should perform a compliance check based on the provided JSON data.
    Generate ONLY the Python code.

    Here is the data from the Revit model:
    {revit_data_str}
    """

    try
    # In a real application, you would call your LLM here.
    # For this example, we will use a static script that CONTAINS f-strings
    # to prove that our converter works.
    
        # --- START OF SIMULATED LLM RESPONSE (contains f-strings) ---
        llm_generated_script = """# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

# This script is written in MODERN Python by the LLM
doc = __revit__.ActiveUIDocument.Document
t = Transaction(doc, "Compliance Check")
t.Start()
try:
    # Example of a line that WILL BE CONVERTED
    print(f"Starting compliance check on {doc.Title}")
    
    # Your logic here to iterate through doors, etc.
    # For every door, the LLM might generate this:
    # door_id = "some_door_id"
    # print(f"✓ Door {door_id} analyzed successfully")

    t.Commit()
except Exception as e:
    t.RollBack()
    # Another example of a line that WILL BE CONVERTED
    print(f"✗ An error occurred: {str(e)}")

TaskDialog.Show("Complete", "Compliance check finished.")
"""
    # --- END OF SIMULATED LLM RESPONSE ---

        # THE CRITICAL STEP: Convert the AI's modern code to be IronPython compatible
        final_script = convert_fstrings_to_format(llm_generated_script)
        
        return final_script

    except Exception as e:
        error_message = "# An error occurred: {}".format(str(e))
        print(error_message)
        return error_message

@app.route('/api/llm', methods=['POST'])
def handle_request():
    if not request.json:
        return jsonify({"error": "Invalid request: no JSON payload"}), 400

    revit_data = request.json
    generated_script = generate_compliance_script(revit_data)
    
    return generated_script, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))