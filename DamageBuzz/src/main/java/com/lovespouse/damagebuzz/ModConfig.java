package com.lovespouse.damagebuzz;

import java.io.File;

import net.minecraftforge.common.config.Configuration;

/**
 * All tunables, backed by a plain {@code config/damagebuzz.cfg} file so players
 * can edit them with any text editor.
 */
public final class ModConfig {

    // --- general ---
    public static boolean enabled = true;
    public static String backendUrl = "http://127.0.0.1:4545/API/";

    // --- strength ---
    /** "FIXED" = always {@link #fixedStrength}; "SCALED" = scale to damage. */
    public static String mode = "SCALED";
    public static int fixedStrength = 6;
    public static int minStrength = 2;
    public static int maxStrength = 9;
    /** Damage (in health points; 2 = one heart) that maps to {@link #maxStrength}. */
    public static double damageForMax = 20.0;

    // --- output ---
    public static double pulseSeconds = 0.6;
    public static int cooldownMs = 250;

    // --- transmitter (BLE sidecar) ---
    public static boolean autoStartTransmitter = true;
    /** Explicit path to lovespouse-ble.exe; blank = use bundled/auto-detected. */
    public static String transmitterPath = "";
    public static int transmitterPort = 4545;

    private ModConfig() {
    }

    public static void load(File file) {
        Configuration cfg = new Configuration(file);
        try {
            cfg.load();

            enabled = cfg.getBoolean("enabled", "general", enabled,
                "Master on/off switch for DamageBuzz.");
            backendUrl = cfg.getString("backendUrl", "general", backendUrl,
                "Base URL of the BLE transmitter HTTP API (must end with /API/).");

            mode = cfg.getString("mode", "strength", mode,
                "FIXED = constant strength; SCALED = scale strength with damage taken.",
                new String[] {"FIXED", "SCALED"});
            fixedStrength = cfg.getInt("fixedStrength", "strength", fixedStrength, 0, 9,
                "Strength used in FIXED mode (0-9).");
            minStrength = cfg.getInt("minStrength", "strength", minStrength, 0, 9,
                "Lowest strength in SCALED mode (a light hit).");
            maxStrength = cfg.getInt("maxStrength", "strength", maxStrength, 0, 9,
                "Highest strength in SCALED mode (a hit of damageForMax or more).");
            damageForMax = cfg.get("strength", "damageForMax", damageForMax,
                "Damage in health points (2 = 1 heart) that reaches maxStrength.").getDouble();

            pulseSeconds = cfg.get("output", "pulseSeconds", pulseSeconds,
                "How long each vibration lasts, in seconds.").getDouble();
            cooldownMs = cfg.getInt("cooldownMs", "output", cooldownMs, 0, 10000,
                "Minimum time between vibrations, in milliseconds (rate limit).");

            autoStartTransmitter = cfg.getBoolean("autoStart", "transmitter", autoStartTransmitter,
                "Launch the BLE transmitter automatically if it is not already running.");
            transmitterPath = cfg.getString("path", "transmitter", transmitterPath,
                "Explicit path to lovespouse-ble.exe. Blank = use the copy bundled in the mod.");
            transmitterPort = cfg.getInt("port", "transmitter", transmitterPort, 1, 65535,
                "Port the transmitter listens on (must match backendUrl).");
        } finally {
            if (cfg.hasChanged()) {
                cfg.save();
            }
        }
    }
}
