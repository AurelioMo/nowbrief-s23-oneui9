#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/lib.sh"
. "$MODDIR/payload/profile.sh"
[ -f "$MODDIR/armed" ] || [ -f "$MODDIR/persistent" ] || exit 0
if [ "${SOFT_REBOOT_MODE:-0}" = 1 ]; then
  [ -f "$MODDIR/early.pending" ] && [ -f "$MODDIR/attempt" ] || exit 0
  generation=$(cat "$MODDIR/early.pending")
  case "$generation" in ''|*[!0-9-]*) exit 1 ;; esac
  # A new stage gets a new lock even if an old worker was killed.
  worker=$MODDIR/worker.$generation
  mkdir "$worker" 2>/dev/null || exit 0
  trap 'rmdir "$worker"' EXIT
else
  [ ! -f "$MODDIR/attempt" ] || exit 0
fi
# The wait is bounded. No action is taken if Android does not finish booting.
remaining=60
while [ "$(getprop sys.boot_completed)" != 1 ]; do
  remaining=$((remaining - 1))
  if [ "$remaining" -eq 0 ]; then
    rm -f "$MODDIR/armed"
    touch "$MODDIR/attempt"
    echo 'NowBrief: boot did not complete; authorization cancelled.' >> "$MODDIR/boot.log"
    exit 1
  fi
  sleep 2
done
# sys.boot_completed alone was insufficient on the observed Samsung soft reboot:
# the first pm path failed, while the identical command worked later. Bound the
# readiness wait; do not retry failed activation or hash mismatches.
remaining=30
while :; do
  if packages=$(pm path --user 0 com.samsung.android.smartsuggestions 2>&1); then
    case "$packages" in package:*) break ;; esac
  fi
  remaining=$((remaining - 1))
  if [ "$remaining" -eq 0 ]; then
    printf 'NowBrief: Package Manager unavailable: %s\n' "$packages" >> "$MODDIR/boot.log"
    exit 1
  fi
  sleep 2 || exit 1
done
if ! wait_settings 30; then
  printf 'NowBrief: Settings service unavailable.\n' >> "$MODDIR/boot.log"
  exit 1
fi
if [ "${SOFT_REBOOT_MODE:-0}" = 1 ]; then
  sh "$MODDIR/control.sh" finish >> "$MODDIR/boot.log" 2>&1
else
  sh "$MODDIR/control.sh" boot >> "$MODDIR/boot.log" 2>&1
fi
[ "$?" -eq 0 ] || exit 1
[ -f "$MODDIR/persistent" ] || exit 0
# Keep the crash marker until Android has stayed up for a bounded observation
# window. This is a liveness check, NOT proof that Samsung features work.
boot=$(cat /proc/sys/kernel/random/boot_id)
sleep 120 || exit 1
[ "$(cat /proc/sys/kernel/random/boot_id)" = "$boot" ] || exit 1
[ "$(getprop sys.boot_completed)" = 1 ] || exit 1
[ -n "$(pidof system_server)" ] || exit 1
if [ "${SOFT_REBOOT_MODE:-0}" = 1 ]; then
  sh "$MODDIR/control.sh" confirm "$generation" >> "$MODDIR/boot.log" 2>&1
else
  sh "$MODDIR/control.sh" confirm >> "$MODDIR/boot.log" 2>&1
fi
