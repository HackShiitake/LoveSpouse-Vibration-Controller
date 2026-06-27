package com.lovespouse.damagecurl.http;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Locale;
import java.util.logging.Logger;

public final class VibrationApiClient {
    private final HttpClient client;
    private final Logger logger;

    public VibrationApiClient(HttpClient client, Logger logger) {
        this.client = client;
        this.logger = logger;
    }

    public void sendPulse(String baseUrl, int power, double seconds) {
        String url = String.format(Locale.ROOT, "%s%d-%.2fs", baseUrl, power, seconds);
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .GET()
            .build();

        client.sendAsync(request, HttpResponse.BodyHandlers.discarding())
            .exceptionally(error -> {
                logger.warning("Failed to call vibration API: " + error.getMessage());
                return null;
            });
    }
}
