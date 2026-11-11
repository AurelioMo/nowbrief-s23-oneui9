#!/system/bin/sh
TARGET=/system/etc/floating_feature.xml
MOUNTINFO=/proc/self/mountinfo
SOURCE=$MODDIR/payload/floating_feature.xml
BASELINE=$MODDIR/payload/original.xml

fail() { echo "NowBrief: $*" >&2; exit 1; }
hash() { sha256sum "$1" | cut -d ' ' -f 1; }
mount_record() { awk -v target="$TARGET" '$5 == target {print}' "$MOUNTINFO"; }

load_profile() {
  [ -f "$MODDIR/payload/profile.sh" ] || fail 'Prepare a device-specific ZIP first.'
  . "$MODDIR/payload/profile.sh"
}

check_identity() {
  [ "$(id -u)" = 0 ] || fail 'Root required.'
  [ "$(getprop ro.build.fingerprint)" = "$EXPECTED_FINGERPRINT" ] || fail 'ROM changed.'
  [ "$(readlink /proc/1/ns/mnt)" = "$(readlink /proc/self/ns/mnt)" ] || fail 'Not in init mount namespace.'
  [ "$(hash "$BASELINE")" = "$ORIGINAL_SHA" ] || fail 'Baseline corrupted.'
  [ "$(hash "$SOURCE")" = "$MODIFIED_SHA" ] || fail 'Prepared XML corrupted.'
}

check_apk() {
  package=$1
  expected=$2
  paths=$(pm path "$package") || fail "Cannot inspect $package"
  case "$paths" in
    *'
'*|'') fail "Unexpected APK layout: $package" ;;
    package:*) apk=${paths#package:} ;;
    *) fail "Unexpected APK path: $package" ;;
  esac
  [ "$(hash "$apk")" = "$expected" ] || fail "APK changed: $package"
}

check_packages() {
  check_apk com.samsung.android.smartsuggestions "$APK_SMART"
  check_apk com.samsung.android.app.aodservice "$APK_AOD"
  check_apk com.android.systemui "$APK_SYSTEMUI"
  check_apk com.android.settings "$APK_SETTINGS"
}

check_settings() {
  [ "$(settings --user 0 get global sss_enabled)" = 1 ] || fail 'First complete the audited manual activation (sss_enabled).'
  [ "$(settings --user 0 get global now_nudge_setting)" = 1 ] || fail 'First complete the audited manual activation (now_nudge_setting).'
}

owns_mount() {
  [ -s "$MODDIR/mount.record" ] &&
  [ "$(mount_record)" = "$(cat "$MODDIR/mount.record")" ] &&
  [ "$(stat -c '%d:%i' "$TARGET")" = "$(stat -c '%d:%i' "$SOURCE")" ]
}
