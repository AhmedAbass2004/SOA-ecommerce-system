package com.example.models;

public class OrderResponse {

    private boolean success;
    private String message;
    private Order order;

    public boolean isSuccess() {
        return success;
    }

    public String getMessage() {
        return message;
    }

    public Order getOrder() {
        return order;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setOrder(Order order) {
        this.order = order;
    }
}
