#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/payload/profile.sh"
[ "${SOFT_REBOOT_MODE:-0}" = 1 ] || exit 0
# Some ksud versions suppress a repeated services event on a soft reboot.
# service.sh serializes duplicate callbacks and only finishes a pending stage.
sh "$MODDIR/service.sh"
