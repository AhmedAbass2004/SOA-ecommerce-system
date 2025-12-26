package com.example.servlets;

import com.example.core.ApiConstants;
import com.example.core.HttpClientFactory;
import com.example.core.PageRoutes;
import com.example.core.ServletsRoutes;
import com.example.models.customer_models.Customer;

import jakarta.json.*;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@WebServlet("/customer")
public class CustomerServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);
        if (session == null || session.getAttribute("customerId") == null) {
            response.sendRedirect(request.getContextPath() + ServletsRoutes.MAIN_ROUTE);
            return;
        }

        int customerId = (Integer) session.getAttribute("customerId");

        try {
            Customer customer = fetchCustomer(customerId);
            request.setAttribute("customer", customer);
        } catch (Exception e) {
            request.setAttribute("error", "Unable to load customer data");
        }

        request.getRequestDispatcher(PageRoutes.CUSTOMER_ROUTE)
                .forward(request, response);
    }

    private Customer fetchCustomer(int customerId) throws Exception {

        HttpClient client = HttpClientFactory.getClient();

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(ApiConstants.CUSTOMER_URL + "/" + customerId))
                .GET()
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        JsonObject root = Json.createReader(new StringReader(response.body()))
                .readObject();

        JsonObject c = root.getJsonObject("customer");

        return new Customer(
                c.getInt("customer_id"),
                c.getString("name"),
                c.getString("email"),
                c.getString("phone"),
                c.getInt("loyalty_points"),
                c.getString("created_at")
        );
    }
}
