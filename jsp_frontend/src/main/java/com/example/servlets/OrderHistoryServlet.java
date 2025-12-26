package com.example.servlets;

import com.example.core.ApiConstants;
import com.example.core.HttpClientFactory;
import com.example.core.PageRoutes;

import com.example.core.ServletsRoutes;
import com.example.models.order_history_models.OrderHistoryResponse;
import com.example.models.order_history_models.OrderSummary;
import com.example.models.order_models.Order;
import com.example.models.order_models.OrderProduct;
import jakarta.json.*;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.*;
import java.util.*;

@WebServlet("/orders")
public class OrderHistoryServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null || session.getAttribute("customerId") == null) {
            response.sendRedirect(request.getContextPath() + ServletsRoutes.MAIN_ROUTE);
            return;
        }

        int customerId = (int) session.getAttribute("customerId");

        try {
            OrderHistoryResponse data = fetchOrders(customerId);

            request.setAttribute("orders", data.getOrders());
            request.setAttribute("summary", data.getSummary());

            request.getRequestDispatcher(PageRoutes.ORDER_HISTORY_ROUTE)
                    .forward(request, response);

        } catch (Exception e) {
            request.setAttribute("error", e.getMessage());
            request.getRequestDispatcher(PageRoutes.ORDER_HISTORY_ROUTE)
                    .forward(request, response);
        }
    }

    private OrderHistoryResponse fetchOrders(int customerId) throws Exception {

        String url = String.format(ApiConstants.CUSTOMER_ORDERS_URL, customerId);

        HttpClient client = HttpClientFactory.getClient();

        HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();

        HttpResponse<String> response =
                client.send(httpRequest, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("Failed to fetch order history");
        }

        return parseOrderHistory(response.body());
    }

    private OrderHistoryResponse parseOrderHistory(String json) {

        JsonReader reader = Json.createReader(new StringReader(json));
        JsonObject root = reader.readObject();

        JsonObject summaryJson = root.getJsonObject("order_summary");
        JsonArray ordersJson = root.getJsonArray("orders");

        OrderSummary summary = new OrderSummary(
                summaryJson.getInt("total_orders"),
                summaryJson.getJsonNumber("total_spent").doubleValue()
        );

        List<Order> orders = new ArrayList<>();

        for (JsonValue v : ordersJson) {
            JsonObject o = v.asJsonObject();

            Order order = new Order();
            order.setOrderId(o.getInt("order_id"));
            order.setCustomerId(o.getInt("customer_id"));
            order.setStatus(o.getString("status"));
            order.setTotalAmount(o.getJsonNumber("total_amount").bigDecimalValue());
            order.setCreatedAt(o.getString("created_at"));

            List<OrderProduct> products = new ArrayList<>();
            for (JsonValue pv : o.getJsonArray("items")) {
                JsonObject p = pv.asJsonObject();
                products.add(new OrderProduct(
                        p.getInt("product_id"),
                        p.getInt("quantity")
                ));
            }

            order.setProducts(products);
            orders.add(order);
        }

        return new OrderHistoryResponse(summary, orders);
    }
}
