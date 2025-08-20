# app.py
from flask import Flask, request, jsonify, Response
from sanitizers import sanitize_for_ironpython
import json

app = Flask(__name__)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/api/llm", methods=["POST"])
def llm():
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": "invalid_json", "detail": str(e)}), 400

    # For now, we get the generated code from the test payload
    generated_code = payload.get("generated_code", "")

    if not isinstance(generated_code, str) or not generated_code.strip():
        return jsonify({"error": "empty_code_from_llm"}), 422

    # Sanitize the code for IronPython
    safe_code = sanitize_for_ironpython(generated_code)

    # Return the cleaned script as plain text
    return Response(safe_code, mimetype="text/plain; charset=utf-8")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)