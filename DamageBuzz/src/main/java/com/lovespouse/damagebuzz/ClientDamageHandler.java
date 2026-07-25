package com.lovespouse.damagebuzz;

import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraftforge.fml.common.gameevent.TickEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Detects when the local player takes damage by watching their health each
 * client tick, then fires a vibration.
 *
 * <p>Watching the health delta (rather than a server-side damage event) means it
 * works identically in single-player and on any multiplayer server: the client
 * always receives the player's current health. A drop in health is a hit; the
 * size of the drop is the damage amount fed to {@link StrengthCalculator}.
 */
public class ClientDamageHandler {

    private static final float EPSILON = 0.01f;

    private final VibrationClient client;
    private float lastHealth = Float.NaN;
    private long lastTriggerMs = 0L;

    public ClientDamageHandler(VibrationClient client) {
        this.client = client;
    }

    @SubscribeEvent
    public void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        if (!ModConfig.enabled) {
            lastHealth = Float.NaN;
            return;
        }

        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP player = mc.player;
        if (player == null || mc.world == null) {
            // Not in a world (menu / loading). Reset so re-entry doesn't
            // register the initial health as a huge "hit".
            lastHealth = Float.NaN;
            return;
        }

        float health = player.getHealth();
        if (Float.isNaN(lastHealth)) {
            lastHealth = health;
            return;
        }

        if (health < lastHealth - EPSILON) {
            double damage = lastHealth - health;
            long now = System.currentTimeMillis();
            if (now - lastTriggerMs >= ModConfig.cooldownMs) {
                lastTriggerMs = now;
                int strength = StrengthCalculator.compute(damage);
                if (strength > 0) {
                    client.pulse(strength, ModConfig.pulseSeconds);
                }
            }
        }

        lastHealth = health;
    }
}
