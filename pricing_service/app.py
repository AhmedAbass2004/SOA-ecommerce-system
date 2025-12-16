from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import requests

app = Flask(__name__)

# ===================== CONFIG =====================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ahmedmohamed123",
    "database": "ecommerce_system"
}

INVENTORY_SERVICE_URL = "http://localhost:5002"

# ===================== DB CONNECTION =====================
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("DB Error:", e)
        return None

# ===================== DISCOUNT LOGIC =====================
def get_discount(product_id, quantity):
    connection = get_db_connection()
    if not connection:
        return 0

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT discount_percentage
        FROM pricing_rules
        WHERE product_id = %s AND min_quantity <= %s
        ORDER BY min_quantity DESC
        LIMIT 1
    """
    cursor.execute(query, (product_id, quantity))
    rule = cursor.fetchone()

    cursor.close()
    connection.close()

    return float(rule["discount_percentage"]) if rule else 0

# ===================== TAX LOGIC =====================
def get_tax_rate(region="Default"):
    connection = get_db_connection()
    if not connection:
        # Safe fallback if DB is down
        return 10.00

    cursor = connection.cursor(dictionary=True)

    # Try region-specific tax
    cursor.execute(
        "SELECT tax_rate FROM tax_rates WHERE region = %s",
        (region,)
    )
    tax = cursor.fetchone()

    # Fallback to Default (10%)
    if not tax:
        cursor.execute(
            "SELECT tax_rate FROM tax_rates WHERE region = 'Default'"
        )
        tax = cursor.fetchone()

    cursor.close()
    connection.close()

    # Final safety fallback
    return float(tax["tax_rate"]) if tax else 10.00


# ===================== PRICING ENDPOINT =====================
@app.route("/api/pricing/calculate", methods=["POST"])
def calculate_pricing():
    """
    Calculate final pricing for a list of products including discounts and taxes.
    Input JSON example:
    {
        "products": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 1}
        ],
        "region": "Egypt"  # optional
    }
    """
    data = request.get_json()
    if not data or "products" not in data:
        return jsonify({"error": "products list is required"}), 400

    products = data["products"]
    region = data.get("region", "Default")

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)
    final_total = 0.0
    pricing_items = []

    # --- Get tax rate ---
    cursor.execute("SELECT tax_rate FROM tax_rates WHERE region = %s", (region,))
    tax_row = cursor.fetchone()
    if not tax_row:
        cursor.execute("SELECT tax_rate FROM tax_rates WHERE region = 'Default'")
        tax_row = cursor.fetchone()
    tax_rate = float(tax_row["tax_rate"]) if tax_row else 10.0

    # --- Calculate pricing per product ---
    for product in products:
        product_id = product["product_id"]
        quantity = product["quantity"]

        # Get base unit price
        cursor.execute("SELECT unit_price FROM inventory WHERE product_id = %s", (product_id,))
        inv_row = cursor.fetchone()
        if not inv_row:
            continue
        unit_price = float(inv_row["unit_price"])

        # Apply discount if any
        cursor.execute("""
            SELECT discount_percentage, min_quantity 
            FROM pricing_rules 
            WHERE product_id = %s AND min_quantity <= %s
            ORDER BY discount_percentage DESC LIMIT 1
        """, (product_id, quantity))
        discount_row = cursor.fetchone()
        discount_percentage = float(discount_row["discount_percentage"]) if discount_row else 0.0

        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount_percentage / 100)
        subtotal_after_discount = subtotal - discount_amount

        # Tax calculation
        tax_amount = subtotal_after_discount * (tax_rate / 100)
        total = subtotal_after_discount + tax_amount
        final_total += total

        pricing_items.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal_after_discount,
            "discount_percentage": discount_percentage,
            "tax_amount": tax_amount,
            "total": total
        })

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "pricing": {
            "final_total": round(final_total, 2),
            "items": pricing_items
        }
    }), 200


# ===================== HEALTH =====================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "Pricing Service",
        "status": "running",
        "port": 5003
    }), 200

# ===================== RUN =====================
if __name__ == "__main__":
    print("Starting Pricing Service on port 5003...")
    print("GET http://localhost:5003/health")
    print("POST http://localhost:5003/api/pricing/calculate")
    app.run(host="0.0.0.0", port=5003, debug=True)
