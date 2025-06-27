import numpy as np
import socket
import pickle
import logging
from flask import Flask, request, jsonify, render_template, abort

# Initialize Flask App
flask_app = Flask(__name__, template_folder='templates', static_folder='static')

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load model safely
try:
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
        logging.info("Model loaded successfully.")
except FileNotFoundError:
    logging.error("Model file not found.")
    raise
except Exception as e:
    logging.error("Error loading model: %s", e)
    raise

# DNS Resolver (Server-Side)
def resolve_dns(domain):
    try:
        ip = socket.gethostbyname(domain)
        # Block private IPs
        if ip.startswith(("10.", "172.", "192.168.")):
            return {"error": "Private IP resolved - not accessible."}
        return {"domain": domain, "ip": ip}
    except socket.gaierror:
        return {"error": "DNS resolution failed."}

# Routes
@flask_app.route("/")
def home():
    return render_template("index.html")

@flask_app.route("/predict", methods=["POST"])
def predict():
    try:
        float_features = [float(x) for x in request.form.values()]
        features = [np.array(float_features)]
        prediction = model.predict(features)
        result = prediction[0]
        return render_template("index.html", prediction_text=f"The Predicted Crop is {result}")
    except ValueError as e:
        logging.error("Invalid input: %s", e)
        return render_template("index.html", prediction_text="Error: Invalid input values.")
    except Exception as e:
        logging.error("Prediction error: %s", e)
        return render_template("index.html", prediction_text="Prediction failed due to internal error.")

@flask_app.route("/resolve-dns", methods=["POST"])
def dns_lookup():
    domain = request.form.get("domain", "")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    result = resolve_dns(domain)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)

@flask_app.errorhandler(404)
def not_found(e):
    return render_template("404.html", error=str(e)), 404

if __name__ == "__main__":
    flask_app.run(debug=True, port=208)
