package com.aureliomo.nowbriefxposed;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        PayloadRunner.run(context.getApplicationContext(), "boot");
    }
}
