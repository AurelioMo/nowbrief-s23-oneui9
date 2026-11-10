#!/system/bin/sh
MODDIR=${0%/*}
TARGET=/system/etc/floating_feature.xml
BASE=/data/adb/nowbrief-persistent
ORIGINAL=$BASE/floating_feature.original.xml
MODIFIED=$BASE/floating_feature.xml
mkdir -p "$BASE"
chmod 700 "$BASE"
[ -s "$ORIGINAL" ] || cat "$TARGET" > "$ORIGINAL"
if [ ! -s "$MODIFIED" ]; then
  cat "$ORIGINAL" > "$MODIFIED"
  for pair in \
    'SEC_FLOATING_FEATURE_COMMON_CONFIG_AI_VERSION=20263' \
    'SEC_FLOATING_FEATURE_FRAMEWORK_SUPPORT_PERSONALIZED_DATA_CORE=TRUE' \
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
if ! grep -q ' /system/etc/floating_feature.xml ' /proc/self/mountinfo; then
  mount --bind "$MODIFIED" "$TARGET"
fi
