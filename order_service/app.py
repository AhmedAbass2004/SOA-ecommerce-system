from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for JSP application communication

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change if you used different username
    'password': 'ahmed',  # Change to your actual password
    'database': 'ecommerce_system'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def validate_customer_id(customer_id):
    """Validate customer ID parameter"""
    if customer_id is None:
        raise ValueError("customer_id is required")
    if not isinstance(customer_id, int) or customer_id <= 0:
        raise ValueError("customer_id must be a positive integer")
    return True

def validate_products(products):
    """Validate products list and structure"""
    if not products:
        raise ValueError("products list cannot be empty")
    
    if not isinstance(products, list):
        raise ValueError("products must be a list")
    
    for idx, product in enumerate(products):
        if not isinstance(product, dict):
            raise ValueError(f"Product at index {idx} must be an object")
        
        if "product_id" not in product:
            raise ValueError(f"Product at index {idx} missing product_id")
        
        if "quantity" not in product:
            raise ValueError(f"Product at index {idx} missing quantity")
        
        if not isinstance(product["product_id"], int) or product["product_id"] <= 0:
            raise ValueError(f"Product at index {idx} has invalid product_id")
        
        if not isinstance(product["quantity"], int) or product["quantity"] <= 0:
            raise ValueError(f"Product at index {idx} has invalid quantity (must be positive integer)")
    
    return True

def validate_total_amount(total_amount):
    """Validate total amount parameter"""
    if total_amount is None:
        raise ValueError("total_amount is required")
    
    if not isinstance(total_amount, (int, float)) or total_amount <= 0:
        raise ValueError("total_amount must be a positive number")
    
    return True

def customer_exists(customer_id):
    """Check if customer exists in database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        query = "SELECT customer_id FROM customers WHERE customer_id = %s"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None
    except Error as e:
        print(f"Database error: {e}")
        return False

def product_exists(product_id):
    """Check if product exists in inventory"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        query = "SELECT product_id FROM inventory WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None
    except Error as e:
        print(f"Database error: {e}")
        return False 


@app.route('/api/orders/create', methods=['POST'])
def create_order():
    """
    Create a new order with inventory integration and automatic total calculation.
    Handles connection errors and invalid responses from Inventory Service.
    """
    connection = None
    cursor = None
    INVENTORY_SERVICE_URL = "http://localhost:5002"

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        customer_id = data.get("customer_id")
        products = data.get("products")

        try:
            validate_customer_id(customer_id)
            validate_products(products)
        except ValueError as ve:
            return jsonify({"success": False, "error": f"Validation error: {str(ve)}"}), 400

        if not customer_exists(customer_id):
            return jsonify({"success": False, "error": f"Customer {customer_id} not found"}), 404

        total_amount = 0.0
        product_prices = []

        # --- Step 1: Check stock availability and get unit prices ---
        for product in products:
            product_id = product["product_id"]
            try:
                resp = requests.get(f"{INVENTORY_SERVICE_URL}/api/inventory/check/{product_id}", timeout=5)
            except requests.exceptions.RequestException as req_err:
                return jsonify({"success": False, "error": f"Inventory Service unreachable: {req_err}"}), 503

            # Check HTTP response
            if resp.status_code != 200:
                return jsonify({
                    "success": False,
                    "error": f"Inventory Service error for product {product_id}: {resp.text}"
                }), resp.status_code

            # Parse JSON safely
            try:
                stock_data = resp.json()["product"]
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": f"Invalid JSON from Inventory Service for product {product_id}"
                }), 502

            if stock_data["quantity_available"] < product["quantity"]:
                return jsonify({
                    "success": False,
                    "error": f"Insufficient stock for product {product_id}. Available: {stock_data['quantity_available']}, Requested: {product['quantity']}"
                }), 400

            unit_price = stock_data["unit_price"]
            subtotal = unit_price * product["quantity"]
            total_amount += subtotal
            product_prices.append({"product_id": product_id, "unit_price": unit_price, "subtotal": subtotal})

        # --- Step 2: Create order in database ---
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO orders (customer_id, total_amount, status) VALUES (%s, %s, %s)",
            (customer_id, round(total_amount, 2), 'confirmed')
        )
        order_id = cursor.lastrowid

        for i, product in enumerate(products):
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                (order_id, product["product_id"], product["quantity"], product_prices[i]["unit_price"], product_prices[i]["subtotal"])
            )

        connection.commit()

        # --- Step 3: Update inventory ---
        inventory_payload = {
            "products": [{"product_id": p["product_id"], "quantity": p["quantity"]} for p in products]
        }
        try:
            update_resp = requests.put(f"{INVENTORY_SERVICE_URL}/api/inventory/update_after_order", json=inventory_payload, timeout=5)
        except requests.exceptions.RequestException as req_err:
            connection.rollback()
            return jsonify({"success": False, "error": f"Inventory Service unreachable: {req_err}"}), 503

        if update_resp.status_code != 200:
            connection.rollback()
            return jsonify({"success": False, "error": f"Failed to update inventory: {update_resp.text}"}), update_resp.status_code

        cursor.execute("SELECT created_at FROM orders WHERE order_id = %s", (order_id,))
        created_at = cursor.fetchone()[0].strftime("%Y-%m-%d %H:%M:%S")

        order_response = {
            "order_id": order_id,
            "customer_id": customer_id,
            "products": products,
            "total_amount": round(total_amount, 2),
            "status": "confirmed",
            "created_at": created_at
        }

        return jsonify({"success": True, "message": "Order created successfully", "order": order_response}), 201

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Verifies that the Order Service is running and database is connected
    """
    connection = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
        except:
            order_count = 0
    else:
        order_count = 0
    
    return jsonify({
        "service": "Order Service",
        "status": "running",
        "database": db_status,
        "port": 5001,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_orders": order_count
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("ORDER SERVICE - PHASE 2 (MySQL Database Integration)")
    print("=" * 60)
    print("\nDatabase Configuration:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Database: {DB_CONFIG['database']}")
   
    
    # Test database connection
    test_conn = get_db_connection()
    if test_conn:
        print("  Status: ✓ Connected")
        test_conn.close()
    else:
        print("  Status: ✗ Connection Failed")
        print("\n⚠ WARNING: Database connection failed!")
        print("Please check your MySQL credentials in DB_CONFIG\n")
    
    print("\nStarting Order Service on port 5001...")
    print("\nAvailable endpoints:")
    print("  POST   http://localhost:5001/api/orders/create")
    print("         - Create new order from JSP application")
    print("  GET    http://localhost:5001/api/orders/<order_id>")
    print("         - Retrieve order details by ID")
    print("  GET    http://localhost:5001/api/orders")
    print("         - Get all orders (for testing)")
    print("  GET    http://localhost:5001/health")
    print("         - Health check endpoint")
    print("\n" + "=" * 60)
    print("Service ready to receive requests from JSP application")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)