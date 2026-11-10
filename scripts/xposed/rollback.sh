#!/system/bin/sh
set -eu
BASE=/data/adb/nowbrief-xposed
TARGET=/system/etc/floating_feature.xml
if [ -s "$BASE/floating_feature.original.xml" ]; then
  mount --bind "$BASE/floating_feature.original.xml" "$TARGET"
fi
settings delete global sss_enabled || true
settings delete global nowbrief_enabled || true
settings delete global smart_suggestions_enabled || true
settings delete global now_nudge_enabled || true
settings delete global now_nudge_setting || true
echo "Now Brief persistent payload reverted"
