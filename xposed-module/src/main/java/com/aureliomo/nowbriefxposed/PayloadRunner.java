package com.aureliomo.nowbriefxposed;

import android.content.Context;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import de.robv.android.xposed.XposedBridge;

final class PayloadRunner {
    private static final String INSTALL = "mkdir -p /data/adb/nowbrief-xposed && cat > /data/adb/nowbrief-xposed/apply.sh && chmod 700 /data/adb/nowbrief-xposed/apply.sh && /data/adb/nowbrief-xposed/apply.sh";
    static void run(Context context, String source) {
        new Thread(() -> {
            try (InputStream payload = context.getAssets().open("payload.sh")) {
                Process process = new ProcessBuilder("su", "-mm", "-c", INSTALL).redirectErrorStream(true).start();
                try (OutputStream stdin = process.getOutputStream()) {
                    byte[] buffer = new byte[4096]; int count;
                    while ((count = payload.read(buffer)) != -1) stdin.write(buffer, 0, count);
                }
                BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line; while ((line = reader.readLine()) != null) XposedBridge.log("NowBriefPersistent: " + line);
                XposedBridge.log("NowBriefPersistent applied from " + source + " (exit " + process.waitFor() + ")");
            } catch (Throwable t) { XposedBridge.log("NowBriefPersistent apply failed: " + t); }
        }, "nowbrief-payload-" + source).start();
    }
}
