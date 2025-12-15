from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

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
    Create a new order with automatic total_amount calculation.
    
    Expected JSON format:
    {
        "customer_id": integer,
        "products": [
            {"product_id": integer, "quantity": integer}
        ]
    }
    
    Returns:
    {
        "success": true,
        "message": "Order created successfully",
        "order": {
            "order_id": integer,
            "customer_id": integer,
            "products": [...],
            "total_amount": decimal,
            "status": "confirmed",
            "created_at": "timestamp"
        }
    }
    """
    connection = None
    cursor = None
    
    try:
        # Parse incoming JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided. Request body must contain JSON data"
            }), 400
        
        # Extract and validate parameters
        try:
            customer_id = data.get("customer_id")
            products = data.get("products")
            
            validate_customer_id(customer_id)
            validate_products(products)
            
        except ValueError as ve:
            return jsonify({
                "success": False,
                "error": f"Validation error: {str(ve)}"
            }), 400
        
        # Check if customer exists
        if not customer_exists(customer_id):
            return jsonify({
                "success": False,
                "error": f"Customer with ID {customer_id} does not exist"
            }), 404
        
        # Check if all products exist
        for product in products:
            if not product_exists(product["product_id"]):
                return jsonify({
                    "success": False,
                    "error": f"Product with ID {product['product_id']} does not exist"
                }), 404
        
        # Connect to database
        connection = get_db_connection()
        if not connection:
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = connection.cursor()
        
        # First insert order with total_amount=0 temporarily
        insert_order_query = """
            INSERT INTO orders (customer_id, total_amount, status)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_order_query, (customer_id, 0, 'confirmed'))
        order_id = cursor.lastrowid
        
        # Insert order items and calculate total_amount
        insert_item_query = """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """
        total_amount = 0
        
        for product in products:
            cursor.execute("SELECT unit_price FROM inventory WHERE product_id = %s", (product["product_id"],))
            unit_price = cursor.fetchone()[0]
            subtotal = unit_price * product["quantity"]
            total_amount += subtotal
            
            cursor.execute(insert_item_query, (
                order_id,
                product["product_id"],
                product["quantity"],
                unit_price,
                subtotal
            ))
        
        # Update the total_amount in orders table
        cursor.execute("UPDATE orders SET total_amount = %s WHERE order_id = %s", (round(total_amount, 2), order_id))
        
        # Commit transaction
        connection.commit()
        
        # Fetch created_at timestamp
        cursor.execute("SELECT created_at FROM orders WHERE order_id = %s", (order_id,))
        created_at = cursor.fetchone()[0].strftime("%Y-%m-%d %H:%M:%S")
        
        # Build order response
        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "products": products,
            "total_amount": round(total_amount, 2),
            "status": "confirmed",
            "created_at": created_at
        }
        
        cursor.close()
        connection.close()
        
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": order
        }), 201
    
    except Error as db_error:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": f"Database error: {str(db_error)}"
        }), 500
    
    except Exception as e:
        if connection:
            connection.rollback()
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
    """
    Retrieve order details by order ID
    
    Parameters:
        order_id: integer (from URL path)
    
    Returns:
    {
        "success": true,
        "order": {
            "order_id": integer,
            "customer_id": integer,
            "products": [...],
            "total_amount": decimal,
            "status": "confirmed",
            "created_at": "timestamp"
        }
    }
    """
    connection = None
    cursor = None
    
    try:
        # Validate order_id
        if order_id <= 0:
            return jsonify({
                "success": False,
                "error": "order_id must be a positive integer"
            }), 400
        
        # Connect to database
        connection = get_db_connection()
        if not connection:
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get order details
        order_query = """
            SELECT order_id, customer_id, total_amount, status, created_at
            FROM orders
            WHERE order_id = %s
        """
        cursor.execute(order_query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            connection.close()
            return jsonify({
                "success": False,
                "error": f"Order with ID {order_id} not found"
            }), 404
        
        # Get order items
        items_query = """
            SELECT oi.product_id, i.product_name, oi.quantity, oi.unit_price, oi.subtotal
            FROM order_items oi
            JOIN inventory i ON oi.product_id = i.product_id
            WHERE oi.order_id = %s
        """
        cursor.execute(items_query, (order_id,))
        items = cursor.fetchall()
        
        # Format products list
        products = [
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": float(item["unit_price"]),
                "subtotal": float(item["subtotal"])
            }
            for item in items
        ]
        
        # Build complete order object
        order_response = {
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "products": products,
            "total_amount": float(order["total_amount"]),
            "status": order["status"],
            "created_at": order["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        }
        
        cursor.close()
        connection.close()
        
        return jsonify({
            "success": True,
            "order": order_response
        }), 200
        
    except Error as db_error:
        print(f"Database error: {db_error}")
        return jsonify({
            "success": False,
            "error": f"Database error: {str(db_error)}"
        }), 500
        
    except Exception as e:
        print(f"Error retrieving order: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    """
    Get all orders (optional - for testing/debugging)
    
    Returns list of all orders
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get all orders
        query = """
            SELECT o.order_id, o.customer_id, c.name as customer_name, 
                   o.total_amount, o.status, o.created_at
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            ORDER BY o.created_at DESC
        """
        cursor.execute(query)
        orders = cursor.fetchall()
        
        # Format response
        orders_list = [
            {
                "order_id": order["order_id"],
                "customer_id": order["customer_id"],
                "customer_name": order["customer_name"],
                "total_amount": float(order["total_amount"]),
                "status": order["status"],
                "created_at": order["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            }
            for order in orders
        ]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            "success": True,
            "orders": orders_list,
            "count": len(orders_list)
        }), 200
        
    except Error as db_error:
        print(f"Database error: {db_error}")
        return jsonify({
            "success": False,
            "error": f"Database error: {str(db_error)}"
        }), 500
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500
        
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