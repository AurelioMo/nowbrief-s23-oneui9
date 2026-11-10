package com.aureliomo.nowbriefxposed;

import android.app.Application;
import android.content.Context;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.concurrent.atomic.AtomicBoolean;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

/** LSPosed entry point. The payload is embedded in the APK; no companion command is required. */
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
                    applyOnce(lpparam.packageName, (Context) param.thisObject);
                }
            });
        } catch (Throwable t) { XposedBridge.log("NowBriefPersistent hook failed: " + t); }
        if ("android".equals(lpparam.packageName)) applyOnce("android", null);
    }

    private static boolean isTarget(String packageName) {
        for (String target : TARGETS) if (target.equals(packageName)) return true;
        return false;
    }

    private static void applyOnce(String source, Context context) {
        if (!STARTED.compareAndSet(false, true)) return;
        if (context != null) PayloadRunner.run(context.getApplicationContext(), source);
    }
}
