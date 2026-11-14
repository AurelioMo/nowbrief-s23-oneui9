#!/system/bin/sh
set -eu
MODDIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$MODDIR/lib.sh"
load_profile
operation=${1:-status}

if [ "$operation" = early ]; then
  [ "${SOFT_REBOOT_MODE:-0}" = 1 ] && [ -f "$MODDIR/persistent" ] || exit 0
  if [ -f "$MODDIR/attempt" ]; then
    rm -f "$MODDIR/early.pending"
    fail 'Previous attempt unconfirmed; automatic retry blocked. Inspect and rollback.'
  fi
fi

# Boot stages normally run once per kernel boot. A zygote restart does not
# imply another KernelSU stage. A boot authorization is consumed BEFORE mounting.
if [ "$operation" = boot ]; then
  [ -f "$MODDIR/armed" ] || [ -f "$MODDIR/persistent" ] || exit 0
  [ ! -f "$MODDIR/attempt" ] || exit 0
fi
mkdir "$MODDIR/lock" 2>/dev/null || fail 'Another operation is running.'
trap 'rmdir "$MODDIR/lock"' EXIT
case "$operation" in
  preflight)
    check_identity
    check_packages
    bio_preflight
    if [ -n "$(mount_record)" ]; then
      owns_mount || fail 'Foreign XML mount.'
      [ "$(nb_sha256 "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
    else
      [ "$(nb_sha256 "$TARGET")" = "$ORIGINAL_SHA" ] || fail 'Active XML changed.'
    fi
    echo 'NowBrief: ROM, XML, namespace and installed APK hashes verified. No activation performed.'
    ;;
  apply|boot|early)
    if [ "$operation" = boot ]; then
      rm -f "$MODDIR/armed"
      touch "$MODDIR/attempt"
    fi
    if [ "$operation" = early ]; then
      [ "$(getprop sys.boot_completed)" != 1 ] || fail 'Early stage requires Android stopped.'
      [ -z "$(pidof system_server)" ] || fail 'Refusing early mount while framework is running.'
      touch "$MODDIR/attempt"
    else
      [ "$(getprop sys.boot_completed)" = 1 ] || fail 'Android boot is incomplete.'
    fi
    check_identity
    if [ "$operation" = early ]; then
      check_apk_files
    else
      check_packages
      if [ ! -f "$MODDIR/payload/activate.sh" ]; then check_settings; fi
    fi
    if [ -n "$(mount_record)" ]; then
      owns_mount || fail 'An existing mount belongs to another transaction.'
      [ "$(nb_sha256 "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
      bio_apply
      if [ "$operation" = early ]; then
        printf '%s-%s\n' "$(date +%s)" "$$" > "$MODDIR/early.pending"
        echo 'NowBrief: existing owned overlay verified before framework start.'
        exit 0
      fi
      activate_apps
      check_settings
      echo 'NowBrief: own overlay already active.'
      exit 0
    fi
    [ "$(nb_sha256 "$TARGET")" = "$ORIGINAL_SHA" ] || fail 'Active XML differs from the audited baseline.'
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
    if [ "$(nb_sha256 "$TARGET")" != "$MODIFIED_SHA" ]; then
      umount "$TARGET" || fail 'Verification failed and unmount failed.'
      fail 'Verification failed; overlay unmounted.'
    fi
    bio_apply
    if [ "$operation" = early ]; then
      printf '%s-%s\n' "$(date +%s)" "$$" > "$MODDIR/early.pending"
      echo 'NowBrief: XML mounted before framework start; app activation deferred.'
      exit 0
    fi
    activate_apps
    check_settings
    echo 'NowBrief: overlay mounted. Verify Android and Now Brief, then confirm manually.'
    ;;
  finish)
    [ "${SOFT_REBOOT_MODE:-0}" = 1 ] || fail 'Not a soft-reboot build.'
    [ -f "$MODDIR/early.pending" ] && [ -f "$MODDIR/attempt" ] || fail 'No successful early stage to finish.'
    [ "$(getprop sys.boot_completed)" = 1 ] || fail 'Android boot is incomplete.'
    check_identity
    check_packages
    bio_confirm
    owns_mount || fail 'Early overlay is no longer owned.'
    [ "$(nb_sha256 "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
    activate_apps
    check_settings
    echo 'NowBrief: post-start app activation complete; liveness confirmation pending.'
    ;;
  confirm)
    if [ -n "${2:-}" ]; then
      [ -f "$MODDIR/early.pending" ] &&
        [ "$(cat "$MODDIR/early.pending")" = "$2" ] || fail 'Early-stage generation changed.'
    fi
    check_identity
    check_packages
    bio_confirm
    owns_mount || fail 'No verified owned mount to confirm.'
    [ "$(nb_sha256 "$TARGET")" = "$MODIFIED_SHA" ] || fail 'Mounted XML changed.'
    touch "$MODDIR/confirmed"
    rm -f "$MODDIR/attempt" "$MODDIR/early.pending"
    echo 'NowBrief: mount confirmed; automatic activation policy unchanged.'
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
  persist)
    check_identity
    check_packages
    check_settings
    [ -f "$MODDIR/confirmed" ] || fail 'Verify and confirm manual activation first.'
    [ ! -f "$MODDIR/attempt" ] || fail 'An unconfirmed attempt exists.'
    owns_mount || fail 'A verified active overlay is required.'
    touch "$MODDIR/persistent"
    echo 'NowBrief: persistent boot activation enabled; interrupted attempts block retry.'
    ;;
  rollback)
    rm -f "$MODDIR/armed" "$MODDIR/confirmed" "$MODDIR/persistent"
    bio_rollback
    if [ -n "$(mount_record)" ]; then
      owns_mount || fail 'Refusing to unmount a foreign mount.'
      umount "$TARGET" || fail 'Unmount failed.'
    fi
    [ "$(nb_sha256 "$TARGET")" = "$ORIGINAL_SHA" ] || fail 'Overlay is off, but active ROM XML differs from baseline.'
    restore_apps
    rm -f "$MODDIR/attempt" "$MODDIR/early.pending" "$MODDIR/mount.record"
    echo 'NowBrief: baseline restored.'
    ;;
  status)
    if [ -n "$(mount_record)" ]; then
      owns_mount && echo 'overlay=owned' || echo 'overlay=foreign'
    else
      echo 'overlay=absent'
    fi
    if [ -f "$MODDIR/biometric.record" ]; then
      if [ -n "$(bio_record)" ] && bio_owns; then
        echo 'biometric=owned'
      else
        echo 'biometric=stale'
      fi
    fi
    for flag in armed attempt confirmed persistent apps.changed early.pending; do
      [ ! -f "$MODDIR/$flag" ] || echo "$flag=present"
    done
    ;;
  *) fail 'Use status, preflight, apply, confirm, arm, persist or rollback.' ;;
esac
