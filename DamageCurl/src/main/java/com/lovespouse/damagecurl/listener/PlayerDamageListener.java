package com.lovespouse.damagecurl.listener;

import com.lovespouse.damagecurl.config.PluginSettings;
import com.lovespouse.damagecurl.http.VibrationApiClient;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;

public final class PlayerDamageListener implements Listener {
    private final PluginSettings settings;
    private final VibrationApiClient apiClient;

    public PlayerDamageListener(PluginSettings settings, VibrationApiClient apiClient) {
        this.settings = settings;
        this.apiClient = apiClient;
    }

    @EventHandler
    public void onDamage(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player player)) {
            return;
        }
        if (!settings.isEnabledFor(player.getName())) {
            return;
        }

        apiClient.sendPulse(settings.baseUrl(), settings.power(), settings.durationSeconds());
    }
}
