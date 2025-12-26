package com.example.models.order_models;

import java.math.BigDecimal;
import java.util.List;

public class Order {

    private int orderId;
    private int customerId;
    private String status;
    private String createdAt;
    private BigDecimal totalAmount;
    private List<OrderProduct> products;

    public int getOrderId() {
        return orderId;
    }

    public int getCustomerId() {
        return customerId;
    }

    public String getStatus() {
        return status;
    }

    public String getCreatedAt() {
        return createdAt;
    }

    public BigDecimal getTotalAmount() {
        return totalAmount;
    }

    public List<OrderProduct> getProducts() {
        return products;
    }

    public void setOrderId(int orderId) {
        this.orderId = orderId;
    }

    public void setCustomerId(int customerId) {
        this.customerId = customerId;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setCreatedAt(String createdAt) {
        this.createdAt = createdAt;
    }

    public void setTotalAmount(BigDecimal totalAmount) {
        this.totalAmount = totalAmount;
    }

    public void setProducts(List<OrderProduct> products) {
        this.products = products;
    }
}
