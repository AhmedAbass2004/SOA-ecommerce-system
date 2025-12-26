package com.example.servlets;

import com.example.core.ApiConstants;
import com.example.core.HttpClientFactory;
import com.example.core.PageRoutes;
import com.example.core.ServletsRoutes;
import com.example.models.inventory_models.Product;
import com.example.models.inventory_models.InventoryResponse;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import jakarta.json.*;

import java.io.IOException;
import java.io.StringReader;
import java.net.URI;
import java.net.http.*;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@WebServlet("/main")
public class InventoryServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        String customerId = request.getParameter("customer_id");

        if (customerId == null || customerId.isBlank()) {
            response.sendRedirect(request.getContextPath() + "/");
            return;
        }

        HttpSession session = request.getSession(true);
        session.setAttribute("customerId", Integer.parseInt(customerId));

        // redirect to GET
        response.sendRedirect(request.getContextPath() + "/main");
    }


    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        try {
            InventoryResponse inventory = fetchInventory();
            request.setAttribute("products",
                    inventory.getProducts());

            request.getSession().setAttribute(
                    "inventoryMap",
                    inventory.getProducts()
                            .stream()
                            .collect(Collectors.toMap(
                                    Product::productId,
                                    p -> p
                            ))
            );
        } catch (Exception e) {
            request.setAttribute("products",
                    List.of());
            request.setAttribute("error",
                    "Inventory service is currently unavailable.");

        }


        request.getRequestDispatcher(
                        PageRoutes.INDEX_ROUTE)
                .forward(request, response);
    }


    private InventoryResponse fetchInventory() throws Exception {

        HttpClient client = HttpClientFactory.getClient();

        HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(ApiConstants.GET_ALL_PRODUCTS_URL))
                .GET()
                .build();

        HttpResponse<String> httpResponse =
                client.send(httpRequest,
                        HttpResponse.BodyHandlers.ofString());

        if (httpResponse.statusCode() != 200) {
            throw new RuntimeException(
                    "Inventory service returned status "
                            + httpResponse.statusCode()
            );
        }

        return parseInventoryResponse(httpResponse.body());
    }


    private InventoryResponse parseInventoryResponse(String json) {

        InventoryResponse response = new InventoryResponse();
        List<Product> products = new ArrayList<>();

        JsonReader reader =
                Json.createReader(new StringReader(json));
        JsonObject root = reader.readObject();

        response.setSuccess(root.getBoolean("success"));
        response.setCount(root.getInt("count"));

        JsonArray productsArray = root.getJsonArray("products");

        for (JsonValue value : productsArray) {

            JsonObject obj = value.asJsonObject();

            Product product = new Product(
                    obj.getInt("product_id"),
                    obj.getString("product_name"),
                    obj.getInt("quantity_available"),
                    obj.getJsonNumber("unit_price")
                            .bigDecimalValue()
            );

            products.add(product);
        }

        response.setProducts(products);
        return response;
    }
}
