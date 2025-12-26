package com.example.models;

import java.util.Map;

public class OrderRequestBody {

    private int customerId;
    private Map<Integer, Integer> products;

    public OrderRequestBody(int customerId, Map<Integer, Integer> products) {
        this.customerId = customerId;
        this.products = products;
    }

    public void setCustomerId(int customerId) {
        this.customerId = customerId;
    }

    public void setProducts(Map<Integer, Integer> products) {
        this.products = products;
    }

    public int getCustomerId() {
        return customerId;
    }

    public Map<Integer, Integer> getProducts() {
        return products;
    }
}
