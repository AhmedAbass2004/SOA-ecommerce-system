package com.example.models.customer_models;

public record Customer(
        int customerId,
        String name,
        String email,
        String phone,
        int loyaltyPoints,
        String createdAt
    ) {}
