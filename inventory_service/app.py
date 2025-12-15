from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

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


@app.route('/api/inventory/check/<int:product_id>', methods=['GET'])
def check_inventory(product_id):
    """
    Check stock availability for a specific product
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Query product inventory
        query = "SELECT * FROM inventory WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({
            "success": True,
            "product": {
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "quantity_available": product["quantity_available"],
                "unit_price": float(product["unit_price"]),
                "in_stock": product["quantity_available"] > 0,
                "last_updated": str(product["last_updated"])
            }
        }), 200
        
    except Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/api/inventory/all', methods=['GET'])
def get_all_inventory():
    """
    Get all products in inventory
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM inventory ORDER BY product_id"
        cursor.execute(query)
        products = cursor.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for product in products:
            product["unit_price"] = float(product["unit_price"])
            product["last_updated"] = str(product["last_updated"])
        
        return jsonify({
            "success": True,
            "products": products,
            "count": len(products)
        }), 200
        
    except Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/api/inventory/update', methods=['PUT'])
def update_inventory():
    """
    Update inventory after order placement
    Expected JSON:
    {
        "products": [
            {"product_id": int, "quantity": int}
        ]
    }
    """
    connection = None
    cursor = None
    
    try:
        data = request.get_json()
        
        if not data or "products" not in data:
            return jsonify({"error": "products list is required"}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        updated_products = []
        
        for product in data["products"]:
            product_id = product.get("product_id")
            quantity = product.get("quantity")
            
            if not product_id or not quantity:
                continue
            
            # Check current stock
            cursor.execute(
                "SELECT quantity_available FROM inventory WHERE product_id = %s",
                (product_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "error": f"Product {product_id} not found"
                }), 404
            
            current_stock = result["quantity_available"]
            
            # Check if enough stock
            if current_stock < quantity:
                return jsonify({
                    "error": f"Insufficient stock for product {product_id}. Available: {current_stock}, Requested: {quantity}"
                }), 400
            
            # Update inventory
            new_quantity = current_stock - quantity
            update_query = """
                UPDATE inventory 
                SET quantity_available = %s, 
                    last_updated = CURRENT_TIMESTAMP 
                WHERE product_id = %s
            """
            cursor.execute(update_query, (new_quantity, product_id))
            
            updated_products.append({
                "product_id": product_id,
                "previous_quantity": current_stock,
                "new_quantity": new_quantity,
                "deducted": quantity
            })
        
        connection.commit()
        
        return jsonify({
            "success": True,
            "message": "Inventory updated successfully",
            "updated_products": updated_products
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


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    connection = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    
    if connection and connection.is_connected():
        connection.close()
    
    return jsonify({
        "service": "Inventory Service",
        "status": "running",
        "port": 5002,
        "database": db_status
    }), 200


if __name__ == '__main__':
    print("Starting Inventory Service on port 5002...")
    print("Available endpoints:")
    print("  GET    http://localhost:5002/api/inventory/check/<product_id>")
    print("  GET    http://localhost:5002/api/inventory/all")
    print("  PUT    http://localhost:5002/api/inventory/update")
    print("  GET    http://localhost:5002/health")
    app.run(host='0.0.0.0', port=5002, debug=True)