#!/system/bin/sh
MODDIR=${0%/*}
[ -f "$MODDIR/armed" ] || exit 0
# The wait is bounded. No action is taken if Android does not finish booting.
remaining=60
while [ "$(getprop sys.boot_completed)" != 1 ]; do
  remaining=$((remaining - 1))
  if [ "$remaining" -eq 0 ]; then
    rm -f "$MODDIR/armed"
    echo 'NowBrief: boot did not complete; authorization cancelled.' >> "$MODDIR/boot.log"
    exit 1
  fi
  sleep 2
done
sh "$MODDIR/control.sh" boot >> "$MODDIR/boot.log" 2>&1
