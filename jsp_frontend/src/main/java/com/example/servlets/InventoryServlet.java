package com.example.servlets;

import com.example.core.Routers;
import com.example.models.Product;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.math.BigDecimal;

@WebServlet("/")
public class InventoryServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        // 🔹 Mock data (temporary)
        List<Product> products = getProducts();

        // Send to JSP
        request.setAttribute("products", products);
        request.getRequestDispatcher(Routers.indexRoute)
                .forward(request, response);
    }

    public static List<Product> getProducts() {
        List<Product> products = new ArrayList<>();

        products.add(new Product(1, "Laptop", 50, new BigDecimal("999.99")));
        products.add(new Product(2, "Mouse", 200, new BigDecimal("29.99")));
        products.add(new Product(3, "Keyboard", 150, new BigDecimal("79.99")));
        products.add(new Product(4, "Monitor", 75, new BigDecimal("299.99")));
        products.add(new Product(5, "Headphones", 100, new BigDecimal("149.99")));

        return products;
    }
}
