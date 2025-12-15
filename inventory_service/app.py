from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
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

# -------------------------------
# Inventory Endpoints
# -------------------------------

@app.route('/api/inventory/check/<int:product_id>', methods=['GET'])
def check_inventory(product_id):
    """Check stock availability for a specific product"""
    connection, cursor = None, None
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
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
    """Get all products in inventory"""
    connection, cursor = None, None
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inventory ORDER BY product_id")
        products = cursor.fetchall()
        
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

@app.route('/api/inventory/update_after_order', methods=['PUT'])
def update_inventory():
    """Update inventory after order placement"""
    connection, cursor = None, None
    try:
        data = request.get_json()
        if not data or "products" not in data or not isinstance(data["products"], list):
            return jsonify({"error": "products list is required and must be a list"}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        updated_products = []
        
        # Start transaction
        connection.start_transaction()
        
        for product in data["products"]:
            product_id = product.get("product_id")
            quantity = product.get("quantity")
            
            # Validate inputs
            if not isinstance(product_id, int) or product_id <= 0:
                return jsonify({"error": f"Invalid product_id: {product_id}"}), 400
            if not isinstance(quantity, int) or quantity <= 0:
                return jsonify({"error": f"Invalid quantity for product {product_id}"}), 400
            
            # Lock the row for update to prevent race conditions
            cursor.execute("SELECT quantity_available FROM inventory WHERE product_id = %s FOR UPDATE", (product_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"error": f"Product {product_id} not found"}), 404
            
            current_stock = result["quantity_available"]
            if current_stock < quantity:
                return jsonify({
                    "error": f"Insufficient stock for product {product_id}. Available: {current_stock}, Requested: {quantity}"
                }), 400
            
            new_quantity = current_stock - quantity
            cursor.execute(
                "UPDATE inventory SET quantity_available = %s, last_updated = CURRENT_TIMESTAMP WHERE product_id = %s",
                (new_quantity, product_id)
            )
            
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

# -------------------------------
# Optional: Add / Update Product Endpoints
# -------------------------------

@app.route('/api/inventory/add', methods=['POST'])
def add_product():
    """Add new product to inventory"""
    connection, cursor = None, None
    try:
        data = request.get_json()
        name = data.get("product_name")
        quantity = data.get("quantity_available")
        price = data.get("unit_price")
        
        if not name or not isinstance(quantity, int) or quantity < 0 or not isinstance(price, (int, float)) or price < 0:
            return jsonify({"error": "Invalid product data"}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO inventory (product_name, quantity_available, unit_price) VALUES (%s, %s, %s)",
            (name, quantity, price)
        )
        connection.commit()
        product_id = cursor.lastrowid
        return jsonify({
            "success": True,
            "message": f"Product added successfully with ID {product_id}"
        }), 201
    
    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/inventory/update_product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product details"""
    connection, cursor = None, None
    try:
        data = request.get_json()
        name = data.get("product_name")
        quantity = data.get("quantity_available")
        price = data.get("unit_price")
        
        if name is None and quantity is None and price is None:
            return jsonify({"error": "No update data provided"}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        updates = []
        params = []
        if name is not None:
            updates.append("product_name = %s")
            params.append(name)
        if quantity is not None:
            updates.append("quantity_available = %s")
            params.append(quantity)
        if price is not None:
            updates.append("unit_price = %s")
            params.append(price)
        
        updates.append("last_updated = CURRENT_TIMESTAMP")
        update_query = f"UPDATE inventory SET {', '.join(updates)} WHERE product_id = %s"
        params.append(product_id)
        
        cursor.execute(update_query, tuple(params))
        connection.commit()
        
        return jsonify({
            "success": True,
            "message": f"Product {product_id} updated successfully"
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

# -------------------------------
# Health Check
# -------------------------------

@app.route('/health', methods=['GET'])
def health_check():
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

# -------------------------------
# Main
# -------------------------------

if __name__ == '__main__':
    print("Starting Inventory Service on port 5002...")
    print("Available endpoints:")
    print("  GET     http://localhost:5002/api/inventory/check/<product_id>") 
    print("  GET     http://localhost:5002/api/inventory/all")
    print("  PUT     http://localhost:5002/api/inventory/update_after_order") 
    print("  POST    http://localhost:5002/api/inventory/add")
    print("  PUT     http://localhost:5002/api/inventory/update_product/<product_id>")
    print("  GET     http://localhost:5002/health")
    app.run(host='0.0.0.0', port=5002, debug=True)
