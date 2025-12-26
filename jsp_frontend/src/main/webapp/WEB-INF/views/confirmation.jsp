<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="com.example.models.OrderResponse" %>
<%@ page import="com.example.models.OrderProduct" %>

<%
    OrderResponse orderResponse =
        (OrderResponse) request.getAttribute("orderResponse");

    String error = (String) request.getAttribute("error");
%>

<html>
<head>
    <title>Order Confirmation</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
        }
        .box {
            width: 60%;
            margin: 30px auto;
            padding: 20px;
            border: 1px solid #ccc;
        }
        .success {
            background-color: #e6ffe6;
            border-color: #66cc66;
        }
        .error {
            background-color: #ffe6e6;
            border-color: #ff6666;
        }
    </style>
</head>

<body>

<h2>📦 Order Confirmation</h2>

<% if (error != null) { %>

    <div class="box error">
        <strong><%= error %></strong>
    </div>

<% } else if (orderResponse != null && orderResponse.isSuccess()) { %>

    <div class="box success">
        <p><strong><%= orderResponse.getMessage() %></strong></p>

        <p>Order ID: <%= orderResponse.getOrder().getOrderId() %></p>
        <p>Status: <%= orderResponse.getOrder().getStatus() %></p>
        <p>Total: $<%= orderResponse.getOrder().getTotalAmount() %></p>
        <p>Created At: <%= orderResponse.getOrder().getCreatedAt() %></p>
    </div>

<% } %>

<form action="<%= request.getContextPath() %>/" method="get">
    <button>Back to Catalog</button>
</form>

<div style="margin-top: 15px; text-align: center;">
    <form action="<%= request.getContextPath() %>/orders" method="get">
        <button type="submit">📦 View Order History</button>
    </form>
</div>

</body>
</html>
