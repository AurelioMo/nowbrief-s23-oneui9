#!/system/bin/sh
MODDIR=${0%/*}
# Opt-in only. No Package Manager calls, waits or Android restarts here.
sh "$MODDIR/control.sh" early >> "$MODDIR/boot.log" 2>&1
