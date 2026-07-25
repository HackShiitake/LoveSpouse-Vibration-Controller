package com.lovespouse.damagebuzz;

import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.event.FMLInitializationEvent;
import net.minecraftforge.fml.common.event.FMLPreInitializationEvent;

/**
 * DamageBuzz — a client-side Minecraft 1.12.2 mod that fires a Bluetooth LE
 * vibration whenever the local player takes damage.
 *
 * <p>The mod itself only handles Minecraft: it watches the player's health,
 * works out a strength (fixed or scaled to the hit), and sends a command over
 * local HTTP to the BLE transmitter — a small sidecar process it launches
 * automatically (see {@link TransmitterLauncher}). That keeps this jar tiny and
 * dependency-free while the proven Windows BLE code lives in the transmitter.
 *
 * <p>It is {@code clientSideOnly} because the Bluetooth hardware is on the
 * player's PC, and {@code acceptableRemoteVersions = "*"} so it can join any
 * server, vanilla or modded.
 */
@Mod(
    modid = DamageBuzz.MODID,
    name = "DamageBuzz",
    version = "1.0.0",
    clientSideOnly = true,
    acceptableRemoteVersions = "*"
)
public class DamageBuzz {

    public static final String MODID = "damagebuzz";

    private VibrationClient client;

    @Mod.EventHandler
    public void preInit(FMLPreInitializationEvent event) {
        ModConfig.load(event.getSuggestedConfigurationFile());
    }

    @Mod.EventHandler
    public void init(FMLInitializationEvent event) {
        client = new VibrationClient(ModConfig.backendUrl);
        TransmitterLauncher.maybeStart(client);
        MinecraftForge.EVENT_BUS.register(new ClientDamageHandler(client));
    }
}
