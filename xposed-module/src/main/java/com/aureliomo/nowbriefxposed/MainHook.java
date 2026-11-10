package com.aureliomo.nowbriefxposed;

import android.app.Application;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.atomic.AtomicBoolean;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

/** LSPosed entry point. The privileged work remains in a small auditable shell payload. */
public final class MainHook implements IXposedHookLoadPackage {
    private static final AtomicBoolean STARTED = new AtomicBoolean(false);
    private static final String[] TARGETS = {
        "android", "com.android.systemui", "com.samsung.android.smartsuggestions",
        "com.samsung.android.app.aodservice"
    };

    @Override public void handleLoadPackage(final XC_LoadPackage.LoadPackageParam lpparam) {
        if (!isTarget(lpparam.packageName)) return;
        try {
            XposedHelpers.findAndHookMethod(Application.class, "onCreate", new XC_MethodHook() {
                @Override protected void afterHookedMethod(MethodHookParam param) {
                    applyOnce(lpparam.packageName);
                }
            });
        } catch (Throwable t) {
            XposedBridge.log("NowBriefPersistent hook failed: " + t);
        }
        if ("android".equals(lpparam.packageName)) applyOnce("android");
    }

    private static boolean isTarget(String packageName) {
        for (String target : TARGETS) if (target.equals(packageName)) return true;
        return false;
    }

    private static void applyOnce(String source) {
        if (!STARTED.compareAndSet(false, true)) return;
        new Thread(() -> {
            try {
                Process process = new ProcessBuilder("su", "-mm", "-c", "/data/adb/nowbrief-xposed/apply.sh")
                        .redirectErrorStream(true).start();
                BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line; while ((line = reader.readLine()) != null) XposedBridge.log("NowBriefPersistent: " + line);
                int exit = process.waitFor();
                XposedBridge.log("NowBriefPersistent applied from " + source + " (exit " + exit + ")");
            } catch (Throwable t) { XposedBridge.log("NowBriefPersistent apply failed: " + t); }
        }, "nowbrief-xposed-apply").start();
    }
}
