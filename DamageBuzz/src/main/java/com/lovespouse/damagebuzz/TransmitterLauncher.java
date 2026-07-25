package com.lovespouse.damagebuzz;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/**
 * Starts the BLE transmitter sidecar so the player never has to run it by hand.
 *
 * <p>Resolution order for the executable:
 * <ol>
 *   <li>an explicit {@code transmitter.path} from the config, if it exists;</li>
 *   <li>a copy bundled inside this mod jar at
 *       {@code /assets/damagebuzz/lovespouse-ble.exe}, extracted to
 *       {@code config/damagebuzz/};</li>
 *   <li>a copy already extracted there from a previous run.</li>
 * </ol>
 * If none is found, the mod logs how to start it manually and keeps working the
 * moment the backend appears (each hit retries the HTTP call).
 */
public final class TransmitterLauncher {

    private static final String BUNDLED_RESOURCE = "/assets/damagebuzz/lovespouse-ble.exe";
    private static final File OUTPUT_DIR = new File("config/damagebuzz");
    private static Process process;

    private TransmitterLauncher() {
    }

    public static void maybeStart(VibrationClient client) {
        if (!ModConfig.autoStartTransmitter) {
            return;
        }
        if (client.ping()) {
            log("BLE transmitter already running.");
            return;
        }

        File executable = resolveExecutable();
        if (executable == null) {
            log("BLE transmitter not found. Set transmitter.path in config/damagebuzz.cfg "
                + "or bundle lovespouse-ble.exe in the mod. Vibration will start once it is running.");
            return;
        }

        try {
            ProcessBuilder builder = new ProcessBuilder(
                executable.getAbsolutePath(),
                "--headless",
                "--port", String.valueOf(ModConfig.transmitterPort));
            builder.directory(executable.getParentFile());
            builder.redirectErrorStream(true);
            builder.redirectOutput(new File(executable.getParentFile(), "transmitter.log"));
            process = builder.start();
            log("Launched BLE transmitter: " + executable.getAbsolutePath());
            Runtime.getRuntime().addShutdownHook(new Thread(() -> shutdown(client)));
        } catch (Exception e) {
            log("Failed to launch BLE transmitter: " + e.getMessage());
        }
    }

    private static File resolveExecutable() {
        // 1) explicit path
        String configured = ModConfig.transmitterPath;
        if (configured != null && !configured.trim().isEmpty()) {
            File explicit = new File(configured.trim());
            if (explicit.isFile()) {
                return explicit;
            }
        }

        // 2) extract the bundled copy (if the jar carries one)
        OUTPUT_DIR.mkdirs();
        File extracted = new File(OUTPUT_DIR, "lovespouse-ble.exe");
        try (InputStream in = TransmitterLauncher.class.getResourceAsStream(BUNDLED_RESOURCE)) {
            if (in != null) {
                if (!extracted.isFile()) {
                    Files.copy(in, extracted.toPath(), StandardCopyOption.REPLACE_EXISTING);
                }
                return extracted;
            }
        } catch (Exception e) {
            log("Could not extract bundled transmitter: " + e.getMessage());
        }

        // 3) a copy left from a previous run
        return extracted.isFile() ? extracted : null;
    }

    private static void shutdown(VibrationClient client) {
        try {
            client.stopNow();
        } catch (Exception ignored) {
            // best effort
        }
        try {
            if (process != null && process.isAlive()) {
                process.destroy();
            }
        } catch (Exception ignored) {
            // best effort
        }
    }

    private static void log(String message) {
        System.out.println("[DamageBuzz] " + message);
    }
}
