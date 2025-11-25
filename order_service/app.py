from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# In-memory storage for orders (you can add database later)
orders = {}
order_counter = 1

@app.route('/api/orders/create', methods=['POST'])
def create_order():
    """
    Create a new order
    Expected JSON format:
    {
        "customer_id": int,
        "products": [{"product_id": int, "quantity": int}],
        "total_amount": float
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if "customer_id" not in data:
            return jsonify({"error": "customer_id is required"}), 400
        
        if "products" not in data or not data["products"]:
            return jsonify({"error": "products list is required"}), 400
        
        if "total_amount" not in data:
            return jsonify({"error": "total_amount is required"}), 400
        
        # Validate products structure
        for product in data["products"]:
            if "product_id" not in product or "quantity" not in product:
                return jsonify({"error": "Each product must have product_id and quantity"}), 400
            if product["quantity"] <= 0:
                return jsonify({"error": "Quantity must be greater than 0"}), 400
        
        # Generate unique order ID
        global order_counter
        order_id = order_counter
        order_counter += 1
        
        # Create order object
        order = {
            "order_id": order_id,
            "customer_id": data["customer_id"],
            "products": data["products"],
            "total_amount": data["total_amount"],
            "status": "confirmed",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Store order
        orders[order_id] = order
        
        # Return success response
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": order
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """
    Retrieve order details by order ID
    """
    try:
        if order_id not in orders:
            return jsonify({"error": "Order not found"}), 404
        
        return jsonify({
            "success": True,
            "order": orders[order_id]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders_by_customer():
    """
    Get all orders for a specific customer
    Query parameter: customer_id
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        
        if not customer_id:
            return jsonify({"error": "customer_id query parameter is required"}), 400
        
        # Filter orders by customer_id
        customer_orders = [
            order for order in orders.values() 
            if order["customer_id"] == customer_id
        ]
        
        return jsonify({
            "success": True,
            "customer_id": customer_id,
            "orders": customer_orders,
            "count": len(customer_orders)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "service": "Order Service",
        "status": "runninggg",
        "port": 5001
    }), 200


if __name__ == '__main__':
    print("Starting Order Service on port 5001...")
    print("Available endpoints:")
    print("  POST   http://localhost:5001/api/orders/create")
    print("  GET    http://localhost:5001/api/orders/<order_id>")
    print("  GET    http://localhost:5001/api/orders?customer_id=<id>")
    print("  GET    http://localhost:5001/health")
    app.run(host='0.0.0.0', port=5001, debug=True)
