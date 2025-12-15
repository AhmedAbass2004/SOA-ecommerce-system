package com.example.core;

import java.net.http.HttpClient;
import java.time.Duration;


public class HttpClientFactory {

    private static final HttpClient CLIENT =
            HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(5))
                    .build();

    private HttpClientFactory() {}

    public static HttpClient getClient() {
        return CLIENT;
    }
}
