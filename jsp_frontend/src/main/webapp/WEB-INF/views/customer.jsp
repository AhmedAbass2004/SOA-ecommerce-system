<%@ page contentType="text/html;charset=UTF-8" %>
<%@ page import="com.example.models.customer_models.Customer" %>

<%
    Customer c = (Customer) request.getAttribute("customer");
%>

<html>
<head>
    <title>Customer Profile</title>
</head>
<body>

<h2>👤 Customer Profile</h2>

<table border="1" cellpadding="10">
    <tr><th>ID</th><td><%= c.customerId() %></td></tr>
    <tr><th>Name</th><td><%= c.name() %></td></tr>
    <tr><th>Email</th><td><%= c.email() %></td></tr>
    <tr><th>Phone</th><td><%= c.phone() %></td></tr>
    <tr><th>Loyalty Points</th><td><%= c.loyaltyPoints() %></td></tr>
    <tr><th>Created At</th><td><%= c.createdAt() %></td></tr>
</table>

<br>

<div style="text-align:center;">
    <form action="<%= request.getContextPath() %>/main" method="get">
        <button>⬅ Back to Home</button>
    </form>
</div>

</body>
</html>
