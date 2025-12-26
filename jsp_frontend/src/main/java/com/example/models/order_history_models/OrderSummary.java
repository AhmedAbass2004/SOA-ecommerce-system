package com.example.models.order_history_models;

public class OrderSummary {
    private final int totalOrders;
    private final double totalSpent;

    public OrderSummary(int totalOrders, double totalSpent) {
        this.totalOrders = totalOrders;
        this.totalSpent = totalSpent;
    }

    public int getTotalOrders() {
        return totalOrders;
    }

    public double getTotalSpent() {
        return totalSpent;
    }
}
