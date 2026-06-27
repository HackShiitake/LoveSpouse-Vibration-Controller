package com.lovespouse.damagecurl.config;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public final class PluginSettings {
    private static final String DEFAULT_BASE_URL = "http://localhost:4545/API/";

    private final JavaPlugin plugin;
    private final Map<String, Boolean> playerSettings = new ConcurrentHashMap<>();
    private volatile String baseUrl;
    private volatile int power;
    private volatile double durationSeconds;

    private PluginSettings(JavaPlugin plugin, String baseUrl, int power, double durationSeconds) {
        this.plugin = plugin;
        this.baseUrl = normalizeBaseUrl(baseUrl);
        this.power = power;
        this.durationSeconds = durationSeconds;
    }

    public static PluginSettings load(JavaPlugin plugin) {
        FileConfiguration config = plugin.getConfig();
        String baseUrl = readString(config, "server.url", "url").orElse(DEFAULT_BASE_URL);
        int power = readInt(config, "server.power", "power").orElse(9);
        double durationSeconds = readDouble(config, "server.time", "time").orElse(0.4D);

        PluginSettings settings = new PluginSettings(plugin, baseUrl, clampPower(power), durationSeconds);
        ConfigurationSection players = config.getConfigurationSection("players");
        if (players != null) {
            for (String name : players.getKeys(false)) {
                settings.playerSettings.put(name, players.getBoolean(name, false));
            }
        }
        settings.persist();
        return settings;
    }

    public boolean isEnabledFor(String playerName) {
        return playerSettings.getOrDefault(playerName, false);
    }

    public void setEnabledFor(String playerName, boolean enabled) {
        playerSettings.put(playerName, enabled);
        plugin.getConfig().set("players." + playerName, enabled);
        plugin.saveConfig();
    }

    public String baseUrl() {
        return baseUrl;
    }

    public int power() {
        return power;
    }

    public double durationSeconds() {
        return durationSeconds;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = normalizeBaseUrl(baseUrl);
        persist();
    }

    public void setPower(int power) {
        this.power = clampPower(power);
        persist();
    }

    public void setDurationSeconds(double durationSeconds) {
        this.durationSeconds = Math.max(0.05D, durationSeconds);
        persist();
    }

    private void persist() {
        FileConfiguration config = plugin.getConfig();
        config.set("server.url", baseUrl);
        config.set("server.power", power);
        config.set("server.time", durationSeconds);
        config.set("url", null);
        config.set("power", null);
        config.set("time", null);
        plugin.saveConfig();
    }

    private static int clampPower(int value) {
        return Math.max(1, Math.min(9, value));
    }

    private static String normalizeBaseUrl(String baseUrl) {
        return baseUrl.endsWith("/") ? baseUrl : baseUrl + "/";
    }

    private static Optional<String> readString(FileConfiguration config, String primary, String legacy) {
        if (config.contains(primary)) {
            return Optional.ofNullable(config.getString(primary));
        }
        return Optional.ofNullable(config.getString(legacy));
    }

    private static Optional<Integer> readInt(FileConfiguration config, String primary, String legacy) {
        if (config.contains(primary)) {
            return Optional.of(config.getInt(primary));
        }
        return config.contains(legacy) ? Optional.of(config.getInt(legacy)) : Optional.empty();
    }

    private static Optional<Double> readDouble(FileConfiguration config, String primary, String legacy) {
        if (config.contains(primary)) {
            return Optional.of(config.getDouble(primary));
        }
        return config.contains(legacy) ? Optional.of(config.getDouble(legacy)) : Optional.empty();
    }
}
