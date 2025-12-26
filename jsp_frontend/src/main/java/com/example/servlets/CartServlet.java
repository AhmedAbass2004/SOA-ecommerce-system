package com.example.servlets;

import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import jakarta.servlet.ServletException;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@WebServlet("/cart")
public class CartServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(true);

        @SuppressWarnings("unchecked")
        Map<Integer, Integer> cart =
                (Map<Integer, Integer>) session.getAttribute("cart");

        if (cart == null) {
            cart = new HashMap<>();
        }

        int productId =
                Integer.parseInt(request.getParameter("product_id"));

        String action = request.getParameter("action");

        int quantity = cart.getOrDefault(productId, 0);

        if ("add".equalsIgnoreCase(action)) {
            quantity++;
        } else if ("remove".equalsIgnoreCase(action)) {
            quantity = Math.max(0, quantity - 1);
        }

        if (quantity == 0) {
            cart.remove(productId);
        } else {
            cart.put(productId, quantity);
        }

        session.setAttribute("cart", cart);

        // Redirect back to inventory catalog
        response.sendRedirect(request.getContextPath() + "/");
    }
}
