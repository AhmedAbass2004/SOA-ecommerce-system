<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="java.util.*" %>
<%@ page import="com.example.models.inventory_models.Product" %>

<%
    String error = (String) request.getAttribute("error");

    List<Product> products =
        (List<Product>) request.getAttribute("products");

    Map<Integer, Integer> cart =
        (Map<Integer, Integer>) session.getAttribute("cart");

    if (cart == null) {
        cart = new HashMap<>();
    }
%>

<html>
<head>
    <title>Product Catalog</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f7f7f7;
        }

        h2 {
            text-align: center;
            margin-top: 20px;
        }

        .product-list {
            width: 85%;
            margin: 30px auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .product-row {
            display: flex;
            align-items: center;
            background: white;
            padding: 14px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        }

        .product-name {
            flex: 8;
            font-size: 18px;
            font-weight: 600;
        }

        .product-price {
            flex: 3;
            text-align: center;
            font-size: 16px;
            color: #333;
        }

        .product-actions {
            flex: 3;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
        }

        .product-actions button {
            padding: 6px 12px;
            font-size: 16px;
            cursor: pointer;
        }

        .qty {
            font-weight: bold;
            min-width: 20px;
            text-align: center;
        }

        .checkout-btn {
            display: block;
            margin: 40px auto;
            padding: 12px 24px;
            font-size: 16px;
            cursor: pointer;
        }

        .error-box, .info-box {
            width: 60%;
            margin: 30px auto;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }

        .error-box {
            border: 1px solid #ff9999;
            background-color: #ffe6e6;
            color: #b30000;
        }

        .info-box {
            border: 1px solid #cccccc;
            background-color: #f9f9f9;
        }
    </style>
</head>

<body>

<h2>🛒 Product Catalog</h2>

<% if (error != null) { %>

    <div class="error-box">
        <strong><%= error %></strong>
    </div>

<% } else if (products == null || products.isEmpty()) { %>

    <div class="info-box">
        <em>No products available.</em>
    </div>

<% } else { %>

<div class="product-list">

<%
    for (Product p : products) {
        int qty = cart.getOrDefault(p.productId(), 0);
%>

    <div class="product-row">

        <div class="product-name">
            <%= p.productName() %>
        </div>

        <div class="product-price">
            $<%= p.unitPrice() %>
        </div>

        <div class="product-actions">

            <form action="cart" method="post">
                <input type="hidden" name="product_id" value="<%= p.productId() %>">
                <input type="hidden" name="action" value="remove">
                <button type="submit">−</button>
            </form>

            <span class="qty"><%= qty %></span>

            <form action="cart" method="post">
                <input type="hidden" name="product_id" value="<%= p.productId() %>">
                <input type="hidden" name="action" value="add">
                <button type="submit">+</button>
            </form>

        </div>

    </div>

<% } %>

</div>

<form action="checkout" method="get">
    <button class="checkout-btn">Proceed to Checkout</button>
</form>

<% } %>

</body>
</html>
