#!/system/bin/sh
TARGET=/system/etc/floating_feature.xml
MOUNTINFO=/proc/self/mountinfo
SOURCE=$MODDIR/payload/floating_feature.xml
BASELINE=$MODDIR/payload/original.xml
. "$MODDIR/biometric.sh"

fail() { echo "NowBrief: $*" >&2; exit 1; }
nb_sha256() { sha256sum "$1" | cut -d ' ' -f 1; }
mount_record() { awk -v target="$TARGET" '$5 == target {print}' "$MOUNTINFO"; }

load_profile() {
  [ -f "$MODDIR/payload/profile.sh" ] || fail 'Prepare a device-specific ZIP first.'
  . "$MODDIR/payload/profile.sh"
}

check_identity() {
  [ "$(id -u)" = 0 ] || fail 'Root required.'
  [ "$(getprop ro.build.fingerprint)" = "$EXPECTED_FINGERPRINT" ] || fail 'ROM changed.'
  [ "$(readlink /proc/1/ns/mnt)" = "$(readlink /proc/self/ns/mnt)" ] || fail 'Not in init mount namespace.'
  [ "$(nb_sha256 "$BASELINE")" = "$ORIGINAL_SHA" ] || fail 'Baseline corrupted.'
  [ "$(nb_sha256 "$SOURCE")" = "$MODIFIED_SHA" ] || fail 'Prepared XML corrupted.'
  bio_payload
}

check_apk() {
  package=$1
  expected=$2
  paths=$(pm path --user 0 "$package" 2>&1) || fail "Cannot inspect $package: $paths"
  case "$paths" in
    *'
'*|'') fail "Unexpected APK layout: $package" ;;
    package:*) apk=${paths#package:} ;;
    *) fail "Unexpected APK path: $package" ;;
  esac
  [ "$(nb_sha256 "$apk")" = "$expected" ] || fail "APK changed: $package"
}

# Package Manager is unavailable between ksud's stop and start. Paths are pinned
# by the read-only preparer; changed/missing APKs fail closed before mounting.
check_apk_files() {
  [ "$(nb_sha256 "$PATH_SMART")" = "$APK_SMART" ] || fail 'Smart Suggestions APK changed.'
  [ "$(nb_sha256 "$PATH_AOD")" = "$APK_AOD" ] || fail 'AOD APK changed.'
  [ "$(nb_sha256 "$PATH_SYSTEMUI")" = "$APK_SYSTEMUI" ] || fail 'SystemUI APK changed.'
  [ "$(nb_sha256 "$PATH_SETTINGS")" = "$APK_SETTINGS" ] || fail 'Settings APK changed.'
  if [ -n "${APK_MEMORY:-}" ]; then
    [ "$(nb_sha256 "$PATH_MEMORY")" = "$APK_MEMORY" ] || fail 'Memory APK changed.'
  fi
}

check_packages() {
  check_apk com.samsung.android.smartsuggestions "$APK_SMART"
  check_apk com.samsung.android.app.aodservice "$APK_AOD"
  check_apk com.android.systemui "$APK_SYSTEMUI"
  check_apk com.android.settings "$APK_SETTINGS"
  [ -z "${APK_MEMORY:-}" ] || check_apk com.samsung.android.app.memory "$APK_MEMORY"
}

activate_apps() {
  [ -f "$MODDIR/payload/activate.sh" ] || return 0
  # Journal precedes writes: interrupted activation remains recoverable.
  touch "$MODDIR/apps.changed"
  sh "$MODDIR/payload/activate.sh" || fail 'App activation failed; run rollback.'
  if [ -f "$MODDIR/payload/gesture.sh" ] && [ ! -f "$MODDIR/gesture.changed" ]; then
    sh "$MODDIR/memory-gesture.sh" apply || fail 'Gesture activation failed; run rollback.'
  fi
}

restore_apps() {
  if [ -f "$MODDIR/gesture.changed" ]; then
    sh "$MODDIR/memory-gesture.sh" rollback || fail 'Gesture restore failed; journal retained.'
  fi
  [ -f "$MODDIR/apps.changed" ] || return 0
  sh "$MODDIR/payload/restore.sh" || fail 'App restore failed; journal retained.'
  rm -f "$MODDIR/apps.changed"
}

check_settings() {
  [ "$(settings --user 0 get global sss_enabled)" = 1 ] || fail 'First complete the audited manual activation (sss_enabled).'
  [ "$(settings --user 0 get global now_nudge_setting)" = 1 ] || fail 'First complete the audited manual activation (now_nudge_setting).'
}

# SettingsProvider can still reject transactions after sys.boot_completed; the
# first boot attempt observed a failed settings transaction. Bound the wait.
wait_settings() {
  remaining=${1:-30}
  while :; do
    value=$(settings --user 0 get global device_provisioned 2>&1) || value=''
    case "$value" in 0|1|null) return 0 ;; esac
    remaining=$((remaining - 1))
    [ "$remaining" -gt 0 ] || return 1
    sleep 2 || return 1
  done
}

owns_mount() {
  [ -s "$MODDIR/mount.record" ] &&
  [ "$(mount_record)" = "$(cat "$MODDIR/mount.record")" ] &&
  [ "$(stat -c '%d:%i' "$TARGET")" = "$(stat -c '%d:%i' "$SOURCE")" ]
}
