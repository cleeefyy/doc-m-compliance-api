from flask import Flask, request, jsonify
import openai
import os
import json

app = Flask(__name__)

# Get the API key from environment variables for security
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_compliance_script(revit_data_json):
    """
    Generates a pyRevit Python script by calling an LLM with specific instructions.
    """
    # Convert the incoming data into a string for the prompt
    revit_data_str = json.dumps(revit_data_json, indent=2)

    # This is the crucial prompt that instructs the AI.
    # It explicitly forbids f-strings and requires IronPython 2.7 compatibility.
    prompt = f"""
    You are an expert Revit API developer. Your task is to generate a complete, standalone pyRevit script.

    **CRITICAL INSTRUCTIONS:**
    1.  The script MUST be 100% compatible with IronPython 2.7, as used by pyRevit.
    2.  DO NOT use f-strings (e.g., f"Hello {name}").
    3.  You MUST use the .format() method for all string formatting (e.g., "Hello {}".format(name)).
    4.  The script should perform a compliance check based on the provided JSON data.
    5.  Generate ONLY the Python code. Do not include any explanations, comments, or markdown.

    Here is the data from the Revit model:
    {revit_data_str}

    Generate the script now.
    """

    try:
        # This is the actual call to the OpenAI API.
        # Ensure you are using a model that follows instructions well, like gpt-4.
        response = openai.ChatCompletion.create(
            model="gpt-4", # Or another suitable model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates IronPython scripts for pyRevit."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the generated Python code from the response
        generated_script = response.choices[0].message['content']
        
        return generated_script

    except Exception as e:
        error_message = "# An error occurred while calling the LLM: {}".format(str(e))
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