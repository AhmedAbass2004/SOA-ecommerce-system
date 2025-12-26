package com.example.models.order_history_models;

import com.example.models.order_models.Order;

import java.util.List;

public class OrderHistoryResponse {
    private final OrderSummary summary;
    private final List<Order> orders;

    public OrderHistoryResponse(OrderSummary summary, List<Order> orders) {
        this.summary = summary;
        this.orders = orders;
    }

    public OrderSummary getSummary() {
        return summary;
    }

    public List<Order> getOrders() {
        return orders;
    }
}
