#!/system/bin/sh
set -eu
BASE=/data/adb/nowbrief-xposed
TARGET=/system/etc/floating_feature.xml
ORIGINAL=$BASE/floating_feature.original.xml
MODIFIED=$BASE/floating_feature.xml
mkdir -p "$BASE"
chmod 700 "$BASE"

# Capture the ROM's file once; never overwrite the baseline on later boots.
if [ ! -s "$ORIGINAL" ]; then
  cat "$TARGET" > "$ORIGINAL"
fi
if [ ! -s "$MODIFIED" ]; then
  cat "$ORIGINAL" > "$MODIFIED"
  for pair in \
    'SEC_FLOATING_FEATURE_FRAMEWORK_SUPPORT_PERSONALIZED_DATA_CORE=TRUE' \
    'SEC_FLOATING_FEATURE_COMMON_CONFIG_AI_VERSION=20263' \
    'SEC_FLOATING_FEATURE_FRAMEWORK_CONFIG_NOW_NUDGE_VERSION=2' \
    'SEC_FLOATING_FEATURE_GENAI_CONFIG_LLM_VERSION=1.70'; do
    key=${pair%%=*}; value=${pair#*=}
    if grep -q "<$key>" "$MODIFIED"; then
      sed -i "s#<$key>[^<]*</$key>#<$key>$value</$key>#" "$MODIFIED"
    else
      sed -i "s#</SecFloatingFeatureSet>#<$key>$value</$key></SecFloatingFeatureSet>#" "$MODIFIED"
    fi
  done
  chmod 644 "$MODIFIED"
fi

# KernelSU's -mm keeps the bind mount in init's namespace across app processes.
if ! awk '$5 == "/system/etc/floating_feature.xml" {found=1} END {exit !found}' /proc/self/mountinfo; then
  mount --bind "$MODIFIED" "$TARGET"
fi

settings put global sss_enabled 1
settings put global now_nudge_setting 1
pm enable --user 0 com.samsung.android.smartsuggestions/.feature.aisuggestion.ui.appwidget.AiSuggestionAppWidgetReceiver || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.NudgeMainSettingsActivity || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.action.NudgeActionSettingsActivity || true
pm enable --user 0 com.samsung.android.smartsuggestions/.nudgesettings.recall.NudgeRecallSettingsActivity || true

# Let Samsung reread the flags. Failures are logged but do not break boot.
am force-stop --user 0 com.samsung.android.smartsuggestions || true
am force-stop --user 0 com.android.settings || true
am force-stop --user 0 com.samsung.android.app.aodservice || true
echo "Now Brief persistent payload applied"
