#!/system/bin/sh
MODDIR=${0%/*}
# KernelSU may invoke removal while our mount is still active.
sh "$MODDIR/control.sh" rollback >> "$MODDIR/boot.log" 2>&1
