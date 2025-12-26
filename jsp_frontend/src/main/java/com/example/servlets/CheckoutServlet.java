package com.example.servlets;

import com.example.core.PageRoutes;
import com.example.core.ServletsRoutes;
import com.example.models.inventory_models.Product;
import com.example.models.inventory_models.CartItem;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.*;

@WebServlet("/checkout")
public class CheckoutServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null) {
            response.sendRedirect(request.getContextPath() + ServletsRoutes.MAIN_ROUTE);
            return;
        }


        @SuppressWarnings("unchecked")
        Map<Integer, Integer> cart =
                (Map<Integer, Integer>) session.getAttribute("cart");

        if (cart == null || cart.isEmpty()) {
            response.sendRedirect(request.getContextPath() + ServletsRoutes.MAIN_ROUTE);
            return;
        }

        @SuppressWarnings("unchecked")
        Map<Integer, Product> inventory =
                (Map<Integer, Product>) session.getAttribute("inventoryMap");


        List<CartItem> checkoutItems = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;

        for (Map.Entry<Integer, Integer> entry : cart.entrySet()) {
            Product product = inventory.get(entry.getKey());
            int qty = entry.getValue();

            if (product != null && qty > 0) {
                checkoutItems.add(new CartItem(product, qty));
                total = total.add(
                        product.unitPrice()
                                .multiply(BigDecimal.valueOf(qty))
                );
            }
        }

        request.setAttribute("items", checkoutItems);
        request.setAttribute("total", total);

        request.getRequestDispatcher(PageRoutes.CHECKOUT_ROUTE)
                .forward(request, response);
    }
}
