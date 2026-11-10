# Persistent LSPosed module

The original scripts use a bind mount, so Android removes that mount during a full reboot. The repository now includes `xposed-module`, an LSPosed/Xposed APK that runs an audited root payload when `android`, SystemUI, Smart Suggestions, or AODService starts.

## Install

1. Build or download `nowbrief-xposed-release.apk` from the GitHub release.
2. Install the APK and enable **Now Brief Persistent** in LSPosed for `android`, `com.android.systemui`, `com.samsung.android.smartsuggestions`, and `com.samsung.android.app.aodservice`.
3. From a computer with ADB and KernelSU root, run `sh run.sh xposed-install` once. This installs `/data/adb/nowbrief-xposed/apply.sh`.
4. Reboot once. The payload captures the ROM XML baseline on first run, creates an idempotent overlay, restores the Now Brief flags, and restarts only the affected Samsung packages.

The module requires LSPosed or a compatible Xposed implementation and KernelSU/Magisk root with `su -mm`. It does not include Samsung APKs, bypass signatures, or grant biometric permissions. Keep the original snapshot and use the existing rollback flow before removing the module.

To disable persistence, disable the module in LSPosed and remove `/data/adb/nowbrief-xposed` from a root shell. The original scripts remain available for diagnostics and audited rollback.
