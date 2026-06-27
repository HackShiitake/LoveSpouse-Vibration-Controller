package com.lovespouse.damagecurl.command;

import com.lovespouse.damagecurl.config.PluginSettings;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

public final class DamageCurlCommand implements CommandExecutor, TabCompleter {
    private static final List<String> SUBCOMMANDS = Arrays.asList("player", "url", "power", "time", "status");

    private final PluginSettings settings;

    public DamageCurlCommand(PluginSettings settings) {
        this.settings = settings;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sendUsage(sender);
            return true;
        }

        switch (args[0].toLowerCase(Locale.ROOT)) {
            case "player":
                return handlePlayer(sender, args);
            case "url":
                return handleUrl(sender, args);
            case "power":
                return handlePower(sender, args);
            case "time":
                return handleTime(sender, args);
            case "status":
                sender.sendMessage(String.format(
                    Locale.ROOT,
                    "DamageCurl: url=%s power=%d time=%.2fs",
                    settings.baseUrl(),
                    settings.power(),
                    settings.durationSeconds()
                ));
                return true;
            default:
                sender.sendMessage("Unknown subcommand.");
                sendUsage(sender);
                return true;
        }
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (args.length == 1) {
            return startsWith(SUBCOMMANDS, args[0]);
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("player")) {
            List<String> names = new ArrayList<>();
            for (Player player : Bukkit.getOnlinePlayers()) {
                names.add(player.getName());
            }
            return startsWith(names, args[1]);
        }
        if (args.length == 3 && args[0].equalsIgnoreCase("player")) {
            return startsWith(Arrays.asList("true", "false"), args[2]);
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("power")) {
            return startsWith(Arrays.asList("1", "2", "3", "4", "5", "6", "7", "8", "9"), args[1]);
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("time")) {
            return startsWith(Arrays.asList("0.1", "0.2", "0.4", "0.8", "1.0"), args[1]);
        }
        return Collections.emptyList();
    }

    private boolean handlePlayer(CommandSender sender, String[] args) {
        if (args.length != 3) {
            sender.sendMessage("Usage: /damagecurl player <player> <true|false>");
            return true;
        }
        if (!args[2].equalsIgnoreCase("true") && !args[2].equalsIgnoreCase("false")) {
            sender.sendMessage("Value must be true or false.");
            return true;
        }
        boolean enabled = Boolean.parseBoolean(args[2]);
        settings.setEnabledFor(args[1], enabled);
        sender.sendMessage("DamageCurl for " + args[1] + " set to " + enabled);
        return true;
    }

    private boolean handleUrl(CommandSender sender, String[] args) {
        if (args.length != 2) {
            sender.sendMessage("Usage: /damagecurl url <url>");
            return true;
        }
        settings.setBaseUrl(args[1]);
        sender.sendMessage("Base URL set to " + settings.baseUrl());
        return true;
    }

    private boolean handlePower(CommandSender sender, String[] args) {
        if (args.length != 2) {
            sender.sendMessage("Usage: /damagecurl power <1-9>");
            return true;
        }
        try {
            settings.setPower(Integer.parseInt(args[1]));
            sender.sendMessage("Power set to " + settings.power());
        } catch (NumberFormatException error) {
            sender.sendMessage("Power must be an integer between 1 and 9.");
        }
        return true;
    }

    private boolean handleTime(CommandSender sender, String[] args) {
        if (args.length != 2) {
            sender.sendMessage("Usage: /damagecurl time <seconds>");
            return true;
        }
        try {
            settings.setDurationSeconds(Double.parseDouble(args[1]));
            sender.sendMessage(String.format(Locale.ROOT, "Time set to %.2fs", settings.durationSeconds()));
        } catch (NumberFormatException error) {
            sender.sendMessage("Time must be a number.");
        }
        return true;
    }

    private void sendUsage(CommandSender sender) {
        sender.sendMessage("Usage: /damagecurl <player|url|power|time|status> ...");
    }

    private List<String> startsWith(List<String> values, String prefix) {
        String normalized = prefix.toLowerCase(Locale.ROOT);
        List<String> matches = new ArrayList<>();
        for (String value : values) {
            if (value.toLowerCase(Locale.ROOT).startsWith(normalized)) {
                matches.add(value);
            }
        }
        return matches;
    }
}
