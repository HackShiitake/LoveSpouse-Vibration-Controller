package com.example;

import org.bukkit.Bukkit;
import org.bukkit.command.*;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.*;

public class DamageCurl extends JavaPlugin implements Listener, TabCompleter {

    private final HttpClient client = HttpClient.newHttpClient();
    private Map<String, Boolean> playerSettings = new HashMap<>();
    private FileConfiguration config;

    private String baseUrl = "http://localhost:4545/API/";
    private int power = 9;
    private double time = 0.4;

    private final List<String> subcommands = Arrays.asList("player", "url", "power", "time");

    @Override
    public void onEnable() {
        saveDefaultConfig();
        config = getConfig();

        if (config.contains("players")) {
            for (String name : config.getConfigurationSection("players").getKeys(false)) {
                playerSettings.put(name, config.getBoolean("players." + name, false));
            }
        }

        baseUrl = config.getString("server.url", baseUrl);
        power = config.getInt("server.power", power);
        time = config.getDouble("server.time", time);

        getServer().getPluginManager().registerEvents(this, this);

        // TabCompleterを登録
        this.getCommand("damagecurl").setTabCompleter(this);

        getLogger().info("DamageCurl Plugin Enabled!");
    }

    @EventHandler
    public void onDamage(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player)) return;
        Player player = (Player) event.getEntity();

        if (!playerSettings.getOrDefault(player.getName(), false)) return;

        String finalUrl = String.format("%s%d-%.1fs", baseUrl, power, time);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(finalUrl))
                .GET()
                .build();

        client.sendAsync(request, HttpResponse.BodyHandlers.discarding());
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!command.getName().equalsIgnoreCase("damagecurl")) return false;

        if (args.length < 1) {
            sender.sendMessage("Usage: /damagecurl <player/url/power/time> ...");
            return true;
        }

        switch (args[0].toLowerCase()) {
            case "player":
                if (args.length != 3) {
                    sender.sendMessage("Usage: /damagecurl player <PlayerName> <True|False>");
                    return true;
                }
                String playerName = args[1];
                boolean value = Boolean.parseBoolean(args[2]);
                playerSettings.put(playerName, value);
                config.set("players." + playerName, value);
                saveConfig();
                sender.sendMessage("DamageCurl for " + playerName + " set to " + value);
                break;

            case "url":
                if (args.length != 2) {
                    sender.sendMessage("Usage: /damagecurl url <URL>");
                    return true;
                }
                baseUrl = args[1];
                config.set("server.url", baseUrl);
                saveConfig();
                sender.sendMessage("Base URL set to " + baseUrl);
                break;

            case "power":
                if (args.length != 2) {
                    sender.sendMessage("Usage: /damagecurl power <1-9>");
                    return true;
                }
                try {
                    int p = Integer.parseInt(args[1]);
                    if (p < 1 || p > 9) throw new NumberFormatException();
                    power = p;
                    config.set("server.power", power);
                    saveConfig();
                    sender.sendMessage("Power set to " + power);
                } catch (NumberFormatException e) {
                    sender.sendMessage("Power must be an integer between 1 and 9");
                }
                break;

            case "time":
                if (args.length != 2) {
                    sender.sendMessage("Usage: /damagecurl time <seconds>");
                    return true;
                }
                try {
                    time = Double.parseDouble(args[1]);
                    config.set("server.time", time);
                    saveConfig();
                    sender.sendMessage("Time set to " + time);
                } catch (NumberFormatException e) {
                    sender.sendMessage("Time must be a number");
                }
                break;

            default:
                sender.sendMessage("Unknown subcommand");
                break;
        }

        return true;
    }

    // ======================
    // Tab補完の実装
    // ======================
    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        List<String> completions = new ArrayList<>();

        if (args.length == 1) {
            // 最初の引数 → サブコマンド候補
            for (String sub : subcommands) {
                if (sub.toLowerCase().startsWith(args[0].toLowerCase())) {
                    completions.add(sub);
                }
            }
        } else if (args.length == 2) {
            String sub = args[0].toLowerCase();
            switch (sub) {
                case "player":
                    // 2番目の引数 → オンラインプレイヤー名候補
                    for (Player p : Bukkit.getOnlinePlayers()) {
                        if (p.getName().toLowerCase().startsWith(args[1].toLowerCase())) {
                            completions.add(p.getName());
                        }
                    }
                    break;

                case "url":
                    // URL は自由入力 → 空リスト返す
                    break;

                case "power":
                    // 1-9 の候補
                    for (int i = 1; i <= 9; i++) {
                        String s = String.valueOf(i);
                        if (s.startsWith(args[1])) completions.add(s);
                    }
                    break;

                case "time":
                    // 0.1~1.0 までの候補（任意で増やせる）
                    for (double t = 0.1; t <= 1.0; t += 0.1) {
                        String s = String.format("%.1f", t);
                        if (s.startsWith(args[1])) completions.add(s);
                    }
                    break;
            }
        }

        return completions;
    }
}
