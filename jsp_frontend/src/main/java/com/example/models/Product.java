package com.example.models;

import java.math.BigDecimal;

public class Product {
    private final int productId;
    private final String productName;
    private final int quantityAvailable;
    private final BigDecimal unitPrice;

    public Product(int productId, String productName,
                   int quantityAvailable, BigDecimal unitPrice) {
        this.productId = productId;
        this.productName = productName;
        this.quantityAvailable = quantityAvailable;
        this.unitPrice = unitPrice;
    }

    public int getProductId() {
        return productId;
    }

    public String getProductName() {
        return productName;
    }

    public int getQuantityAvailable() {
        return quantityAvailable;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }
}
