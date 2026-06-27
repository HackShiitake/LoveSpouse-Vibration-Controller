package com.lovespouse.damagecurl;

import com.lovespouse.damagecurl.command.DamageCurlCommand;
import com.lovespouse.damagecurl.config.PluginSettings;
import com.lovespouse.damagecurl.http.VibrationApiClient;
import com.lovespouse.damagecurl.listener.PlayerDamageListener;
import org.bukkit.command.PluginCommand;
import org.bukkit.plugin.java.JavaPlugin;

import java.net.http.HttpClient;

public final class DamageCurlPlugin extends JavaPlugin {
    private PluginSettings settings;
    private VibrationApiClient apiClient;

    @Override
    public void onEnable() {
        saveDefaultConfig();

        settings = PluginSettings.load(this);
        apiClient = new VibrationApiClient(HttpClient.newHttpClient(), getLogger());

        getServer().getPluginManager().registerEvents(
            new PlayerDamageListener(settings, apiClient),
            this
        );

        DamageCurlCommand commandExecutor = new DamageCurlCommand(settings);
        PluginCommand command = getCommand("damagecurl");
        if (command != null) {
            command.setExecutor(commandExecutor);
            command.setTabCompleter(commandExecutor);
        }

        getLogger().info("DamageCurl enabled");
    }

    @Override
    public void onDisable() {
        getLogger().info("DamageCurl disabled");
    }
}
