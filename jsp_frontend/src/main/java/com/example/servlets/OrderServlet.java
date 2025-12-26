package com.example.servlets;

import com.example.core.ApiConstants;
import com.example.core.HttpClientFactory;
import com.example.core.PageRoutes;
import com.example.models.*;

import jakarta.json.*;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import java.io.*;
import java.net.URI;
import java.net.http.*;
import java.util.*;

@WebServlet("/order")
public class OrderServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null) {
            response.sendRedirect(request.getContextPath() + "/");
            return;
        }


        @SuppressWarnings("unchecked")
        Map<Integer, Integer> cart =
                (Map<Integer, Integer>) session.getAttribute("cart");

        int customerId = Integer.parseInt(request.getParameter("customer_id"));

        session.setAttribute("customerId", customerId);

        if (cart == null || cart.isEmpty()) {
            response.sendRedirect(request.getContextPath() + "/");
            return;
        }

        JsonObject requestBody = buildRequestBody(new OrderRequestBody(
            customerId,
            cart
        ));

        try {
            OrderResponse orderResponse = sendOrder(requestBody);

            session.removeAttribute("cart");

            request.setAttribute("orderResponse", orderResponse);
            request.getRequestDispatcher(PageRoutes.CONFIRMATION_ROUTE)
                    .forward(request, response);

        } catch (Exception e) {
            request.setAttribute("error", e.getMessage());
            request.getRequestDispatcher(PageRoutes.CONFIRMATION_ROUTE)
                    .forward(request, response);
        }
    }

    private JsonObject buildRequestBody(OrderRequestBody body) {
        JsonArrayBuilder productsArray = Json.createArrayBuilder();

        for (Map.Entry<Integer, Integer> entry : body.getProducts().entrySet()) {
            productsArray.add(
                    Json.createObjectBuilder()
                            .add("product_id", entry.getKey())
                            .add("quantity", entry.getValue())
            );
        }

        return Json.createObjectBuilder()
                .add("customer_id", body.getCustomerId()) // temporary
                .add("products", productsArray)
                .build();
    }

    private OrderResponse sendOrder(JsonObject body) throws Exception {

        HttpClient client = HttpClientFactory.getClient();

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(ApiConstants.CREATE_ORDER_URL))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body.toString()))
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200 && response.statusCode() != 201) {
            throw new RuntimeException("Order service failed");
        }

        return parseOrderResponse(response.body());
    }

    private OrderResponse parseOrderResponse(String json) {

        JsonReader reader = Json.createReader(new StringReader(json));
        JsonObject root = reader.readObject();

        OrderResponse response = new OrderResponse();
        response.setSuccess(root.getBoolean("success"));
        response.setMessage(root.getString("message"));

        JsonObject orderObj = root.getJsonObject("order");

        Order order = new Order();
        order.setOrderId(orderObj.getInt("order_id"));
        order.setCustomerId(orderObj.getInt("customer_id"));
        order.setStatus(orderObj.getString("status"));
        order.setCreatedAt(orderObj.getString("created_at"));
        order.setTotalAmount(orderObj.getJsonNumber("total_amount").bigDecimalValue());

        List<OrderProduct> products = new ArrayList<>();
        for (JsonValue v : orderObj.getJsonArray("products")) {
            JsonObject p = v.asJsonObject();
            products.add(
                    new OrderProduct(
                            p.getInt("product_id"),
                            p.getInt("quantity")
                    )
            );
        }

        order.setProducts(products);
        response.setOrder(order);

        return response;
    }
}
