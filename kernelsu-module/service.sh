#!/system/bin/sh
MODDIR=${0%/*}
# Wait for Android settings and package manager, then apply only the audited state.
until [ "$(getprop sys.boot_completed)" = "1" ]; do sleep 2; done
settings put global sss_enabled 1
settings put global now_nudge_setting 1
pm enable --user 0 com.samsung.android.smartsuggestions/.feature.aisuggestion.ui.appwidget.AiSuggestionAppWidgetReceiver || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.NudgeMainSettingsActivity || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.action.NudgeActionSettingsActivity || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.recall.NudgeRecallSettingsActivity || true
am force-stop --user 0 com.samsung.android.smartsuggestions || true
am force-stop --user 0 com.samsung.android.app.aodservice || true
echo 'Now Brief KernelSU module applied' > /dev/kmsg 2>/dev/null || true
