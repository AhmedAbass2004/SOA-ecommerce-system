from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'mada12345',
    'database': 'ecommerce_system'
}

# Service URLs
INVENTORY_SERVICE_URL = "http://localhost:5002"
PRICING_SERVICE_URL = "http://localhost:5003"

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


@app.route('/api/orders/create', methods=['POST'])
def create_order():
    """
    Create a new order with full pricing calculation including discounts and taxes.
    Integrates with both Inventory and Pricing services.
    """
    connection = None
    cursor = None

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        customer_id = data.get("customer_id")
        products = data.get("products")
        region = data.get("region", "Default")  # Optional region for tax calculation

        # Validate input
        try:
            validate_customer_id(customer_id)
            validate_products(products)
        except ValueError as ve:
            return jsonify({"success": False, "error": f"Validation error: {str(ve)}"}), 400

        if not customer_exists(customer_id):
            return jsonify({"success": False, "error": f"Customer {customer_id} not found"}), 404

        # --- Step 1: Check stock availability ---
        print("\n=== Step 1: Checking Inventory ===")
        for product in products:
            product_id = product["product_id"]
            try:
                resp = requests.get(
                    f"{INVENTORY_SERVICE_URL}/api/inventory/check/{product_id}", 
                    timeout=5
                )
            except requests.exceptions.RequestException as req_err:
                return jsonify({
                    "success": False, 
                    "error": f"Inventory Service unreachable: {req_err}"
                }), 503

            if resp.status_code != 200:
                return jsonify({
                    "success": False,
                    "error": f"Inventory Service error for product {product_id}: {resp.text}"
                }), resp.status_code

            try:
                stock_data = resp.json()["product"]
            except (ValueError, KeyError):
                return jsonify({
                    "success": False,
                    "error": f"Invalid JSON from Inventory Service for product {product_id}"
                }), 502

            if stock_data["quantity_available"] < product["quantity"]:
                return jsonify({
                    "success": False,
                    "error": f"Insufficient stock for product {product_id}. Available: {stock_data['quantity_available']}, Requested: {product['quantity']}"
                }), 400
            
            print(f"✓ Product {product_id}: {stock_data['quantity_available']} available")

        # --- Step 2: Calculate pricing with discounts and taxes ---
        print("\n=== Step 2: Calculating Pricing (with discounts & taxes) ===")
        pricing_payload = {
            "products": [
                {"product_id": p["product_id"], "quantity": p["quantity"]} 
                for p in products
            ],
            "region": region
        }

        try:
            pricing_resp = requests.post(
                f"{PRICING_SERVICE_URL}/api/pricing/calculate",
                json=pricing_payload,
                timeout=5
            )
        except requests.exceptions.RequestException as req_err:
            return jsonify({
                "success": False,
                "error": f"Pricing Service unreachable: {req_err}"
            }), 503

        if pricing_resp.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Pricing Service error: {pricing_resp.text}"
            }), pricing_resp.status_code

        try:
            pricing_data = pricing_resp.json()
            final_total = pricing_data["pricing"]["final_total"]
            pricing_items = pricing_data["pricing"]["items"]
            print(f"✓ Final Total (with discounts & taxes): ${final_total}")
        except (ValueError, KeyError) as e:
            return jsonify({
                "success": False,
                "error": f"Invalid response from Pricing Service: {e}"
            }), 502

        # --- Step 3: Create order in database ---
        print("\n=== Step 3: Creating Order in Database ===")
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        cursor = connection.cursor()
        
        # Insert order
        cursor.execute(
            "INSERT INTO orders (customer_id, total_amount, status) VALUES (%s, %s, %s)",
            (customer_id, round(final_total, 2), 'confirmed')
        )
        order_id = cursor.lastrowid
        print(f"✓ Order created with ID: {order_id}")

        # Insert order items with pricing details
        for pricing_item in pricing_items:
            cursor.execute(
                """INSERT INTO order_items 
                   (order_id, product_id, quantity, unit_price, subtotal) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    order_id,
                    pricing_item["product_id"],
                    pricing_item["quantity"],
                    pricing_item["unit_price"],
                    pricing_item["total"]  # This includes discount and tax
                )
            )

        connection.commit()
        print(f"✓ Order items saved")

        # --- Step 4: Update inventory ---
        print("\n=== Step 4: Updating Inventory ===")
        inventory_payload = {
            "products": [
                {"product_id": p["product_id"], "quantity": p["quantity"]} 
                for p in products
            ]
        }
        
        try:
            update_resp = requests.put(
                f"{INVENTORY_SERVICE_URL}/api/inventory/update_after_order",
                json=inventory_payload,
                timeout=5
            )
        except requests.exceptions.RequestException as req_err:
            connection.rollback()
            return jsonify({
                "success": False,
                "error": f"Inventory update failed: {req_err}"
            }), 503

        if update_resp.status_code != 200:
            connection.rollback()
            return jsonify({
                "success": False,
                "error": f"Failed to update inventory: {update_resp.text}"
            }), update_resp.status_code
        
        print(f"✓ Inventory updated")

        # Get order timestamp
        cursor.execute("SELECT created_at FROM orders WHERE order_id = %s", (order_id,))
        created_at = cursor.fetchone()[0].strftime("%Y-%m-%d %H:%M:%S")

        # Prepare response with detailed pricing breakdown
        order_response = {
            "order_id": order_id,
            "customer_id": customer_id,
            "products": products,
            "pricing_breakdown": pricing_items,
            "total_amount": round(final_total, 2),
            "status": "confirmed",
            "created_at": created_at,
            "region": region
        }

        print("\n=== Order Created Successfully! ===\n")
        return jsonify({
            "success": True,
            "message": "Order created successfully with pricing calculations",
            "order": order_response
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"ERROR: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Retrieve order details by ID"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get order
        cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404
        
        # Get order items
        cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        
        # Format response
        order["total_amount"] = float(order["total_amount"])
        order["created_at"] = str(order["created_at"])
        
        for item in items:
            item["unit_price"] = float(item["unit_price"])
            item["subtotal"] = float(item["subtotal"])
        
        return jsonify({
            "success": True,
            "order": order,
            "items": items
        }), 200
        
    except Error as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
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
        "total_orders": order_count,
        "integrations": {
            "inventory_service": INVENTORY_SERVICE_URL,
            "pricing_service": PRICING_SERVICE_URL
        }
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("ORDER SERVICE - WITH PRICING INTEGRATION")
    print("=" * 70)
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
    
    print("\nService Integrations:")
    print(f"  Inventory Service: {INVENTORY_SERVICE_URL}")
    print(f"  Pricing Service:   {PRICING_SERVICE_URL}")
    
    print("\nStarting Order Service on port 5001...")
    print("\nAvailable endpoints:")
    print("  POST   http://localhost:5001/api/orders/create")
    print("         - Create order with automatic pricing calculation")
    print("  GET    http://localhost:5001/api/orders/<order_id>")
    print("         - Retrieve order details by ID")
    print("  GET    http://localhost:5001/health")
    print("         - Health check endpoint")
    print("\n" + "=" * 70)
    print("🚀 Service ready - Now calculates discounts & taxes automatically!")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)