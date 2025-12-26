<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="com.example.models.Order" %>
<%@ page import="com.example.models.OrderProduct" %>

<html>
<head>
    <title>Order History</title>
    <style>
        body { font-family: Arial; }
        .order-card {
            border: 1px solid #ccc;
            margin: 15px auto;
            padding: 15px;
            width: 80%;
            border-radius: 6px;
        }
        .header {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .products {
            margin-left: 15px;
        }
    </style>
</head>

<body>

<h2 align="center">📦 Order History</h2>

<%
    List<Order> orders = (List<Order>) request.getAttribute("orders");

    if (orders == null || orders.isEmpty()) {
%>
    <p style="text-align:center;">No orders found.</p>
<%
    } else {
        for (Order order : orders) {
%>
    <div class="order-card">
        <div class="header">
            Order #<%= order.getOrderId() %> |
            Status: <%= order.getStatus() %> |
            Date: <%= order.getCreatedAt() %>
        </div>

        <div class="products">
            <ul>
                <%
                    for (OrderProduct p : order.getProducts()) {
                %>
                <li>
                    Product ID: <%= p.getProductId() %> —
                    Quantity: <%= p.getQuantity() %>
                </li>
                <%
                    }
                %>
            </ul>
        </div>

        <strong>Total: $<%= order.getTotalAmount() %></strong>
    </div>
<%
        }
    }
%>

<div style="text-align:center;">
    <form action="<%= request.getContextPath() %>/" method="get">
        <button>⬅ Back to Home</button>
    </form>
</div>

</body>
</html>
