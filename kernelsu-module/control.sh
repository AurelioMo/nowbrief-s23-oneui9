#!/system/bin/sh
set -eu
MODDIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$MODDIR/lib.sh"
load_profile
operation=${1:-status}

# Boot stages normally run once per kernel boot. A zygote restart does not
# imply another KernelSU stage. A boot authorization is consumed BEFORE mounting.
if [ "$operation" = boot ]; then
  [ -f "$MODDIR/armed" ] || exit 0
  [ ! -f "$MODDIR/attempt" ] || exit 0
fi
mkdir "$MODDIR/lock" 2>/dev/null || fail 'Another operation is running.'
trap 'rmdir "$MODDIR/lock"' EXIT
case "$operation" in
  apply|boot)
    if [ "$operation" = boot ]; then rm -f "$MODDIR/armed"; fi
    [ "$(getprop sys.boot_completed)" = 1 ] || fail 'Android boot is incomplete.'
    check_identity
    check_packages
    check_settings
    if [ -n "$(mount_record)" ]; then
      owns_mount || fail 'An existing mount belongs to another transaction.'
      [ "$(hash "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
      echo 'NowBrief: own overlay already active.'
      exit 0
    fi
    [ "$(hash "$TARGET")" = "$ORIGINAL_SHA" ] || fail 'Active XML differs from the audited baseline.'
    chown 0:0 "$SOURCE" || fail 'Cannot set XML owner.'
    chmod 644 "$SOURCE" || fail 'Cannot set XML permissions.'
    chcon u:object_r:system_file:s0 "$SOURCE" || fail 'Cannot set XML SELinux context.'
    ls -Zd "$SOURCE" | grep -q 'u:object_r:system_file:s0' || fail 'XML SELinux context did not match.'
    # The persistent marker blocks a second automatic attempt after any failure,
    # including a process kill, userspace crash or interrupted mount.
    touch "$MODDIR/attempt"
    rm -f "$MODDIR/armed"
    sync
    mount --bind "$SOURCE" "$TARGET" || fail 'Mount failed; automatic activation remains off.'
    mount_record > "$MODDIR/mount.record"
    owns_mount || fail 'Cannot verify mount ownership; inspect before rollback.'
    if [ "$(hash "$TARGET")" != "$MODIFIED_SHA" ]; then
      umount "$TARGET" || fail 'Verification failed and unmount failed.'
      fail 'Verification failed; overlay unmounted.'
    fi
    echo 'NowBrief: overlay mounted. Verify Android and Now Brief, then confirm manually.'
    ;;
  confirm)
    check_identity
    check_packages
    owns_mount || fail 'No verified owned mount to confirm.'
    [ "$(hash "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
    touch "$MODDIR/confirmed"
    rm -f "$MODDIR/attempt"
    echo 'NowBrief: confirmed. Automatic activation remains off.'
    ;;
  arm)
    check_identity
    check_packages
    check_settings
    [ -f "$MODDIR/confirmed" ] || fail 'Verify and confirm a manual activation first.'
    [ ! -f "$MODDIR/attempt" ] || fail 'An unconfirmed attempt exists.'
    owns_mount || fail 'A verified active overlay is required.'
    touch "$MODDIR/armed"
    echo 'NowBrief: ONE automatic attempt authorized. It will not rearm itself.'
    ;;
  rollback)
    rm -f "$MODDIR/armed" "$MODDIR/confirmed"
    if [ -n "$(mount_record)" ]; then
      owns_mount || fail 'Refusing to unmount a foreign mount.'
      umount "$TARGET" || fail 'Unmount failed.'
    fi
    [ "$(hash "$TARGET")" = "$ORIGINAL_SHA" ] || fail 'Overlay is off, but active ROM XML differs from baseline.'
    rm -f "$MODDIR/attempt" "$MODDIR/mount.record"
    echo 'NowBrief: baseline restored.'
    ;;
  status)
    if [ -n "$(mount_record)" ]; then
      owns_mount && echo 'overlay=owned' || echo 'overlay=foreign'
    else
      echo 'overlay=absent'
    fi
    for flag in armed attempt confirmed; do
      [ ! -f "$MODDIR/$flag" ] || echo "$flag=present"
    done
    ;;
  *) fail 'Use status, apply, confirm, arm or rollback.' ;;
esac
