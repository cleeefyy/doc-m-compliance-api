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
    """
    fstring_pattern = re.compile(r"f(['\"])(.*?)\{([^}]+)\}(.*?)(\1)")

    def replacer(match):
        quote = match.group(1)
        pre_variable = match.group(2)
        variable = match.group(3)
        post_variable = match.group(4)
        new_string = quote + pre_variable + '{}' + post_variable + quote
        format_argument = variable
        return "{}.format({})".format(new_string, format_argument)

    converted_code = python_code
    while fstring_pattern.search(converted_code):
        converted_code = fstring_pattern.sub(replacer, converted_code)
    return converted_code

def generate_compliance_script(revit_data_json):
    """
    Generates a pyRevit Python script by calling an LLM.
    """
    revit_data_str = json.dumps(revit_data_json, indent=2)
    
    prompt = f"""
    You are an expert Revit API developer. Generate a complete, standalone pyRevit script.
    The script should perform a compliance check based on the provided JSON data.
    Generate ONLY the Python code.

    Here is the data from the Revit model:
    {revit_data_str}
    """

    try:
        # This is where you would call your actual LLM
        # For this example, we'll use a static script to ensure it works
        llm_generated_script = """# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document
print(f"Starting compliance check on {doc.Title}")
TaskDialog.Show("Complete", "Compliance check finished.")
"""
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