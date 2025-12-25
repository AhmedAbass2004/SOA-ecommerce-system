from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ===================== SERVICE URLS =====================
CUSTOMER_SERVICE_URL = "http://localhost:5004"

# ===================== HELPER FUNCTION =====================
def get_customer_info(customer_id):
    """Call Customer Service to get customer contact info"""
    try:
        response = requests.get(
            f"{CUSTOMER_SERVICE_URL}/api/customers/{customer_id}",
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        return None, f"Customer Service unreachable: {e}"

    if response.status_code != 200:
        return None, f"Customer Service error: {response.text}"

    data = response.json()
    return data["customer"], None


# ===================== SEND NOTIFICATION =====================
@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    order_id = data.get("order_id")
    customer_id = data.get("customer_id")
    notification_message = data.get("message")

    if not order_id or not customer_id:
        return jsonify({
            "success": False,
            "error": "order_id and customer_id are required"
        }), 400

    # 1️⃣ Get customer contact info
    customer, error = get_customer_info(customer_id)
    if error:
        return jsonify({"success": False, "error": error}), 502

    # 2️⃣ Simulate sending notification
    print("\n=== SENDING NOTIFICATION ===")
    print(f"EMAIL SENT TO: {customer['email']}")
    print(f"Subject: Order #{order_id} Confirmed")
    print(f"Body: {notification_message}")

    return jsonify({
        "success": True,
        "message": "Notification sent successfully",
        "notification": {
            "order_id": order_id,
            "customer_id": customer_id,
            "email": customer["email"],
            "phone": customer["phone"],
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }), 200


# ===================== HEALTH CHECK =====================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "service": "Notification Service",
        "status": "running",
        "port": 5005,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200


# ===================== MAIN =====================
if __name__ == '__main__':
    print("=" * 70)
    print("NOTIFICATION SERVICE")
    print("=" * 70)
    print("Listening on port 5005")
    print("POST /api/notifications/send")
    print("=" * 70)

    app.run(host="0.0.0.0", port=5005, debug=True)
