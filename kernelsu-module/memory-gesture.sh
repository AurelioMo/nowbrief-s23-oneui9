#!/system/bin/sh
# Optional transaction. Never overwrite preferences changed since preparation.
set -eu
MODDIR=${0%/*}
. "$MODDIR/lib.sh"
load_profile
[ -f "$MODDIR/payload/gesture.sh" ] || exit 0
. "$MODDIR/payload/gesture.sh"
PREFS=/data/user/0/com.samsung.android.app.homestar/shared_prefs/com.samsung.android.app.homestar.v2.preferences.xml
operation=${1:-status}
lock=$MODDIR/gesture.lock
mkdir "$lock" 2>/dev/null || fail 'Gesture transaction busy.'
trap 'rmdir "$lock"' EXIT

replace_prefs() {
  source=$1
  # Copy existing metadata and SELinux label; publish by atomic rename.
  temporary=$PREFS.nowbrief
  [ ! -e "$temporary" ] || fail 'Gesture temporary file exists.'
  cp -p "$PREFS" "$temporary"
  cat "$source" > "$temporary"
  chown "$(stat -c %u "$PREFS"):$(stat -c %g "$PREFS")" "$temporary"
  chmod 600 "$temporary"
  chcon "$(ls -Zd "$PREFS" | awk '{print $1}')" "$temporary"
  mv "$temporary" "$PREFS"
}

refresh_launcher() {
  # App restart only: no Android restart, reboot, data clear or consent changes.
  am force-stop --user 0 com.samsung.android.app.homestar
  am force-stop --user 0 com.sec.android.app.launcher
  am start --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME
}

case "$operation" in
  apply)
    check_identity
    check_apk com.samsung.android.app.homestar "$GESTURE_HOMEUP_SHA"
    check_apk com.incconutwo.savememory "$GESTURE_HELPER_SHA"
    [ "$(settings --user 0 get global navigation_bar_gesture_while_hidden)" = 1 ] ||
      fail 'Home Up requires swipe navigation.'
    [ "$(settings --user 0 get global navigation_bar_gesture_detail_type)" = 1 ] ||
      fail 'Home Up requires multiple-direction swipe navigation.'
    [ "$(nb_sha256 "$MODDIR/payload/gesture.original.xml")" = "$GESTURE_ORIGINAL_SHA" ] ||
      fail 'Gesture baseline corrupted.'
    [ "$(nb_sha256 "$MODDIR/payload/gesture.xml")" = "$GESTURE_MODIFIED_SHA" ] ||
      fail 'Gesture payload corrupted.'
    if [ -f "$MODDIR/gesture.changed" ]; then
      [ "$(nb_sha256 "$PREFS")" = "$GESTURE_MODIFIED_SHA" ] ||
        fail 'Home Up preferences changed; gesture not reapplied.'
      exit 0
    fi
    [ "$(nb_sha256 "$PREFS")" = "$GESTURE_ORIGINAL_SHA" ] ||
      fail 'Home Up preferences changed since preparation.'
    am force-stop --user 0 com.samsung.android.app.homestar
    [ "$(nb_sha256 "$PREFS")" = "$GESTURE_ORIGINAL_SHA" ] ||
      fail 'Home Up preferences changed while stopping.'
    touch "$MODDIR/gesture.changed"
    replace_prefs "$MODDIR/payload/gesture.xml"
    settings --user 0 put secure memory_three_finger_gesture 0
    settings --user 0 put secure home_up_multi_finger_gesture_enabled 1
    refresh_launcher
    ;;
  rollback)
    [ -f "$MODDIR/gesture.changed" ] || exit 0
    [ "$(nb_sha256 "$MODDIR/payload/gesture.original.xml")" = "$GESTURE_ORIGINAL_SHA" ] ||
      fail 'Gesture baseline corrupted; journal retained.'
    am force-stop --user 0 com.samsung.android.app.homestar
    current=$(nb_sha256 "$PREFS")
    if [ "$current" = "$GESTURE_MODIFIED_SHA" ]; then
      replace_prefs "$MODDIR/payload/gesture.original.xml"
    elif [ "$current" != "$GESTURE_ORIGINAL_SHA" ]; then
      fail 'Home Up preferences edited; journal retained to prevent data loss.'
    fi
    for entry in memory_three_finger_gesture home_up_multi_finger_gesture_enabled; do
      case "$entry" in
        memory_three_finger_gesture) old=$GESTURE_OLD_MEMORY; desired=0 ;;
        *) old=$GESTURE_OLD_HOMEUP; desired=1 ;;
      esac
      [ "$(settings --user 0 get secure "$entry")" = "$desired" ] || continue
      if [ "$old" = null ]; then
        settings --user 0 delete secure "$entry"
      else
        settings --user 0 put secure "$entry" "$old"
      fi
    done
    rm -f "$MODDIR/gesture.changed"
    refresh_launcher
    ;;
  status)
    printf 'Gesture journal: '
    if [ -f "$MODDIR/gesture.changed" ]; then echo present; else echo absent; fi
    settings --user 0 get secure home_up_multi_finger_gesture_enabled
    ;;
  *) fail 'Use apply, rollback or status.' ;;
esac
