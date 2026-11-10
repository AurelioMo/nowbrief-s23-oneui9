#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PAYLOAD=/data/adb/nowbrief-xposed/apply.sh
if [ "${NOWBRIEF_TERMUX:-0}" = 1 ]; then
  su -mm -c "mkdir -p /data/adb/nowbrief-xposed && cat > $PAYLOAD" < "$ROOT/scripts/xposed/apply.sh"
  su -mm -c "chmod 700 $PAYLOAD"
else
  adb shell "su -mm -c 'mkdir -p /data/adb/nowbrief-xposed'"
  adb push "$ROOT/scripts/xposed/apply.sh" /data/local/tmp/nowbrief-apply.sh >/dev/null
  adb shell "su -mm -c 'cp /data/local/tmp/nowbrief-apply.sh $PAYLOAD && chmod 700 $PAYLOAD && rm /data/local/tmp/nowbrief-apply.sh'"
fi
echo "Payload instalado em $PAYLOAD"
