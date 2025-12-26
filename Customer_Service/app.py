from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ===================== DATABASE CONFIG =====================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ahmedmohamed123',
    'database': 'ecommerce_system'
}

# ===================== SERVICE URLS =====================
ORDER_SERVICE_URL = "http://localhost:5001"

# ===================== DATABASE CONNECTION =====================
def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# ===================== ENDPOINT 1: GET CUSTOMER PROFILE =====================
@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """
    Get customer profile information
    Returns customer details including loyalty points
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Query customer data
        query = "SELECT * FROM customers WHERE customer_id = %s"
        cursor.execute(query, (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({"error": f"Customer {customer_id} not found"}), 404
        
        # Format response (matching your service style)
        customer["created_at"] = str(customer["created_at"])
        
        return jsonify({
            "success": True,
            "customer": customer
        }), 200
    
    except Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ===================== ENDPOINT 2: GET ORDER HISTORY =====================
@app.route('/api/customers/<int:customer_id>/orders', methods=['GET'])
def get_customer_orders(customer_id):
    """
    Get customer order history by calling Order Service
    """

    try:
        # Call Order Service
        response = requests.get(
            f"{ORDER_SERVICE_URL}/api/customers/{customer_id}/orders",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Failed to retrieve orders from Order Service"
            }), response.status_code

        order_data = response.json()

        return jsonify({
            "success": True,
            "order_summary": order_data.get("order_summary"),
            "orders": order_data.get("orders")
        }), 200

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Order Service unavailable"}), 503

    except requests.exceptions.Timeout:
        return jsonify({"error": "Order Service timeout"}), 504

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================== ENDPOINT 3: UPDATE LOYALTY POINTS =====================
@app.route('/api/customers/<int:customer_id>/loyalty', methods=['PUT'])
def update_loyalty_points(customer_id):
    """
    Update customer loyalty points
    Can add or set loyalty points
    
    Request body:
    {
        "points": 50,
        "action": "add"  // or "set"
    }
    """
    connection = None
    cursor = None
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get points from request
        points = data.get("points")
        action = data.get("action", "add")  # "add" or "set"
        
        if points is None:
            return jsonify({"error": "points field is required"}), 400
        
        if not isinstance(points, int):
            return jsonify({"error": "points must be an integer"}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if customer exists
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({"error": f"Customer {customer_id} not found"}), 404
        
        print(f"\n=== Updating Loyalty Points for {customer['name']} ===")
        print(f"Current points: {customer['loyalty_points']}")
        
        # Update loyalty points
        if action == "add":
            new_points = customer['loyalty_points'] + points
            cursor.execute(
                "UPDATE customers SET loyalty_points = loyalty_points + %s WHERE customer_id = %s",
                (points, customer_id)
            )
            print(f"Action: Add {points} points")
        elif action == "set":
            new_points = points
            cursor.execute(
                "UPDATE customers SET loyalty_points = %s WHERE customer_id = %s",
                (points, customer_id)
            )
            print(f"Action: Set to {points} points")
        else:
            return jsonify({"error": "action must be 'add' or 'set'"}), 400
        
        connection.commit()
        print(f"New points: {new_points}")
        print(f"✓ Loyalty points updated successfully\n")
        
        return jsonify({
            "success": True,
            "message": "Loyalty points updated successfully",
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "previous_points": customer['loyalty_points'],
            "points_changed": points,
            "new_points": new_points,
            "action": action
        }), 200
    
    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ===================== BONUS: GET ALL CUSTOMERS =====================
@app.route('/api/customers', methods=['GET'])
def get_all_customers():
    """Get all customers (for admin/testing purposes)"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers ORDER BY customer_id")
        customers = cursor.fetchall()
        
        # Format dates
        for customer in customers:
            customer["created_at"] = str(customer["created_at"])
        
        return jsonify({
            "success": True,
            "customers": customers,
            "count": len(customers)
        }), 200
    
    except Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ===================== HEALTH CHECK =====================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    connection = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
        except:
            customer_count = 0
    else:
        customer_count = 0
    
    return jsonify({
        "service": "Customer Service",
        "status": "running",
        "database": db_status,
        "port": 5004,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_customers": customer_count
    }), 200


# ===================== ERROR HANDLERS =====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ===================== MAIN =====================
if __name__ == '__main__':
    print("=" * 70)
    print("CUSTOMER SERVICE - SERVICE 4")
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
    print(f"  Order Service: {ORDER_SERVICE_URL}")
    
    print("\nStarting Customer Service on port 5004...")
    print("\nAvailable endpoints:")
    print("  GET    http://localhost:5004/api/customers/<customer_id>")
    print("         - Get customer profile")
    print("  GET    http://localhost:5004/api/customers/<customer_id>/orders")
    print("         - Get customer order history")
    print("  PUT    http://localhost:5004/api/customers/<customer_id>/loyalty")
    print("         - Update customer loyalty points")
    print("  GET    http://localhost:5004/api/customers")
    print("         - Get all customers (admin)")
    print("  GET    http://localhost:5004/health")
    print("         - Health check endpoint")
    print("\n" + "=" * 70)
    print("🚀 Customer Service Ready - Service 4 of 5 Complete!")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5004, debug=True)