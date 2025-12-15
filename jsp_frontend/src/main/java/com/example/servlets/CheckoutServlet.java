package com.example.servlets;

import com.example.core.Routers;
import com.example.models.Product;
import com.example.models.CartItem;

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

        @SuppressWarnings("unchecked")
        Map<Integer, Integer> cart =
                (Map<Integer, Integer>) session.getAttribute("cart");

        if (cart == null || cart.isEmpty()) {
            response.sendRedirect(request.getContextPath() + "/");
            return;
        }

        // Get product list (mock inventory for now)
        List<Product> products = InventoryServlet.getProducts();

        List<CartItem> checkoutItems = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;

        for (Product p : products) {
            int qty = cart.getOrDefault(p.getProductId(), 0);
            if (qty > 0) {
                checkoutItems.add(new CartItem(p, qty));

                BigDecimal subtotal =
                        p.getUnitPrice()
                                .multiply(BigDecimal.valueOf(qty));

                total = total.add(subtotal);
            }
        }

        request.setAttribute("items", checkoutItems);
        request.setAttribute("total", total);

        request.getRequestDispatcher(Routers.checkoutRoute)
                .forward(request, response);
    }
}
