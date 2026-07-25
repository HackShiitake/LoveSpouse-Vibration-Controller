package com.lovespouse.damagebuzz;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Fire-and-forget HTTP client for the BLE transmitter's local API
 * ({@code GET /API/{strength}-{duration}{unit}}).
 *
 * <p>Requests run on a single daemon thread so a slow or missing backend can
 * never stall the Minecraft render/tick thread. Failures are swallowed — if the
 * transmitter is not up yet, the next hit simply tries again.
 */
public class VibrationClient {

    private final String baseUrl;
    private final ExecutorService executor = Executors.newSingleThreadExecutor(runnable -> {
        Thread thread = new Thread(runnable, "damagebuzz-http");
        thread.setDaemon(true);
        return thread;
    });

    public VibrationClient(String baseUrl) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl : baseUrl + "/";
    }

    /** Queue a vibration of the given strength (0-9) for {@code seconds}. */
    public void pulse(int strength, double seconds) {
        int ms = (int) Math.round(seconds * 1000.0);
        final String url = baseUrl + strength + "-" + ms + "ms";
        executor.submit(() -> get(url, 400));
    }

    /** Immediately request a stop (strength 0). Runs synchronously for shutdown. */
    public void stopNow() {
        get(baseUrl + "0-50ms", 300);
    }

    /** @return true if the backend answered — used to avoid double-launching it. */
    public boolean ping() {
        return get(baseUrl, 300);
    }

    private boolean get(String url, int timeoutMs) {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setConnectTimeout(timeoutMs);
            connection.setReadTimeout(timeoutMs);
            connection.setRequestMethod("GET");
            connection.getResponseCode();
            return true;
        } catch (Exception ignored) {
            return false;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }
}
