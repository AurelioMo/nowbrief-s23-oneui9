#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MODULE=nowbrief-persistent
if [ "${NOWBRIEF_TERMUX:-0}" = 1 ]; then
  su -mm -c "rm -rf /data/adb/modules/$MODULE && mkdir -p /data/adb/modules/$MODULE"
  for file in module.prop post-fs-data.sh service.sh uninstall.sh; do
    su -mm -c "cat > /data/adb/modules/$MODULE/$file" < "$ROOT/kernelsu-module/$file"
    su -mm -c "chmod 755 /data/adb/modules/$MODULE/$file"
  done
else
  adb shell "su -mm -c 'rm -rf /data/adb/modules/$MODULE && mkdir -p /data/adb/modules/$MODULE'"
  adb push "$ROOT/kernelsu-module/module.prop" /data/local/tmp/nowbrief-module.prop >/dev/null
  adb push "$ROOT/kernelsu-module/post-fs-data.sh" /data/local/tmp/nowbrief-post-fs-data.sh >/dev/null
  adb push "$ROOT/kernelsu-module/service.sh" /data/local/tmp/nowbrief-service.sh >/dev/null
  adb push "$ROOT/kernelsu-module/uninstall.sh" /data/local/tmp/nowbrief-uninstall.sh >/dev/null
  adb shell "su -mm -c 'cp /data/local/tmp/nowbrief-module.prop /data/adb/modules/$MODULE/module.prop; cp /data/local/tmp/nowbrief-post-fs-data.sh /data/adb/modules/$MODULE/post-fs-data.sh; cp /data/local/tmp/nowbrief-service.sh /data/adb/modules/$MODULE/service.sh; cp /data/local/tmp/nowbrief-uninstall.sh /data/adb/modules/$MODULE/uninstall.sh; chmod 755 /data/adb/modules/$MODULE/*.sh; rm -f /data/local/tmp/nowbrief-*.sh /data/local/tmp/nowbrief-module.prop'"
fi
echo "KernelSU module installed at /data/adb/modules/$MODULE; reboot to activate."
