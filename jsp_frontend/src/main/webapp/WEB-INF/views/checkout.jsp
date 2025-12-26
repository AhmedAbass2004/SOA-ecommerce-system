<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="java.math.BigDecimal" %>
<%@ page import="com.example.models.inventory_models.CartItem" %>

<html>
<head>
    <title>Checkout</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table {
            width: 80%;
            margin: auto;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            border: 1px solid #ccc;
            text-align: center;
        }
        th { background-color: #f4f4f4; }
        .total {
            font-size: 18px;
            font-weight: bold;
            text-align: right;
            margin-right: 10%;
            margin-top: 20px;
        }
        .actions {
            width: 80%;
            margin: 30px auto;
            text-align: right;
        }
        input[type="text"] {
            padding: 6px;
            width: 200px;
        }
        button {
            padding: 10px 18px;
            font-size: 15px;
        }
    </style>
</head>

<body>

<h2 align="center">🧾 Checkout Summary</h2>

<%
    List<CartItem> items = (List<CartItem>) request.getAttribute("items");
    BigDecimal total = (BigDecimal) request.getAttribute("total");
%>

<table>
    <tr>
        <th>Product</th>
        <th>Unit Price ($)</th>
        <th>Quantity</th>
        <th>Subtotal ($)</th>
    </tr>

<%
    if (items != null && !items.isEmpty()) {
        for (CartItem item : items) {
            BigDecimal subtotal =
                item.product().unitPrice()
                    .multiply(BigDecimal.valueOf(item.quantity()));
%>
    <tr>
        <td><%= item.product().productName() %></td>
        <td><%= item.product().unitPrice() %></td>
        <td><%= item.quantity() %></td>
        <td><%= subtotal %></td>
    </tr>
<%
        }
    } else {
%>
    <tr>
        <td colspan="4">Your cart is empty.</td>
    </tr>
<%
    }
%>
</table>

<div class="total">
    Total Amount: $<%= total != null ? total : "0.00" %>
</div>

<!-- CUSTOMER ID + ACTIONS -->
<div class="actions">

    <form action="order" method="post">
        <button type="submit">✅ Place Order</button>
    </form>

    <form action="<%= request.getContextPath() %>/main" method="get" style="margin-top:10px;">
       <button type="submit">⬅ Continue Shopping</button>
    </form>

</div>

</body>
</html>
