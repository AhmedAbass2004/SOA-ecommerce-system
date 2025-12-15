<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="java.util.*" %>
<%@ page import="com.example.models.Product" %>

<%
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
        }
        table {
            width: 85%;
            margin: auto;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 10px;
            text-align: center;
        }
        th {
            background-color: #f4f4f4;
        }
        button {
            padding: 5px 10px;
            font-size: 14px;
            cursor: pointer;
        }
        .qty {
            margin: 0 10px;
            font-weight: bold;
        }
        .checkout-btn {
            display: block;
            margin: 30px auto;
            padding: 10px 20px;
            font-size: 16px;
        }
    </style>
</head>

<body>

<h2 align="center">🛒 Product Catalog</h2>

<table>
    <tr>
        <th>ID</th>
        <th>Product</th>
        <th>Available</th>
        <th>Price ($)</th>
        <th>Cart</th>
    </tr>

<%
    if (products != null) {
        for (Product p : products) {

            int qty = cart.getOrDefault(p.getProductId(), 0);
%>
    <tr>
        <td><%= p.getProductId() %></td>
        <td><%= p.getProductName() %></td>
        <td><%= p.getQuantityAvailable() %></td>
        <td><%= p.getUnitPrice() %></td>

        <td>
            <!-- REMOVE -->
            <form action="cart" method="post" style="display:inline;">
                <input type="hidden" name="product_id"
                       value="<%= p.getProductId() %>">
                <input type="hidden" name="action" value="remove">
                <button type="submit">−</button>
            </form>

            <span class="qty"><%= qty %></span>

            <!-- ADD -->
            <form action="cart" method="post" style="display:inline;">
                <input type="hidden" name="product_id"
                       value="<%= p.getProductId() %>">
                <input type="hidden" name="action" value="add">
                <button type="submit">+</button>
            </form>
        </td>
    </tr>
<%
        }
    }
%>

</table>

<form action="checkout" method="get">
    <button class="checkout-btn">Proceed to Checkout</button>
</form>

</body>
</html>
