package com.example.models.inventory_models;

import java.math.BigDecimal;

public record Product(
        int productId, String productName,
        int quantityAvailable,
        BigDecimal unitPrice
    ) {}
