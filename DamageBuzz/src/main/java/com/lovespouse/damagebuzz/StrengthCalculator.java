package com.lovespouse.damagebuzz;

/**
 * Turns an amount of damage into a 0–9 strength using the configured mode.
 */
public final class StrengthCalculator {

    private StrengthCalculator() {
    }

    public static int compute(double damage) {
        if ("FIXED".equalsIgnoreCase(ModConfig.mode)) {
            return clamp(ModConfig.fixedStrength);
        }

        int lo = clamp(ModConfig.minStrength);
        int hi = clamp(ModConfig.maxStrength);
        double span = Math.max(0.0001, ModConfig.damageForMax);
        double t = Math.max(0.0, Math.min(1.0, damage / span));
        int scaled = (int) Math.round(lo + (hi - lo) * t);

        // Any real hit should buzz at least minStrength.
        return clamp(Math.max(lo, scaled));
    }

    private static int clamp(int value) {
        return Math.max(0, Math.min(9, value));
    }
}
