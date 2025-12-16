package com.example.models;

import java.util.List;

public class OrderRequestBody {

    private int customerId;
    private List<OrderProduct> products;

    public OrderRequestBody(int customerId, List<OrderProduct> products) {
        this.customerId = customerId;
        this.products = products;
    }

    public void setCustomerId(int customerId) {
        this.customerId = customerId;
    }

    public void setProducts(List<OrderProduct> products) {
        this.products = products;
    }

    public int getCustomerId() {
        return customerId;
    }

    public List<OrderProduct> getProducts() {
        return products;
    }
}
