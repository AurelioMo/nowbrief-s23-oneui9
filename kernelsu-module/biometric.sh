#!/system/bin/sh
# Optional, same-signer signature allowlist; never bypasses authentication.
BIO_TARGET=/system/etc/permissions/signature-permissions-downloadable.xml
BIO_SOURCE=$MODDIR/payload/biometric.xml
BIO_BASELINE=$MODDIR/payload/biometric.original.xml

bio_record() { awk -v target="$BIO_TARGET" '$5 == target {print}' "$MOUNTINFO"; }
bio_owns() {
  [ -s "$MODDIR/biometric.record" ] &&
  [ "$(bio_record)" = "$(cat "$MODDIR/biometric.record")" ] &&
  [ "$(stat -c '%d:%i' "$BIO_TARGET")" = "$(stat -c '%d:%i' "$BIO_SOURCE")" ]
}
bio_payload() {
  [ -n "${BIO_ORIGINAL_SHA:-}" ] || return 0
  [ "$(nb_sha256 "$BIO_BASELINE")" = "$BIO_ORIGINAL_SHA" ] || fail 'Biometric baseline corrupted.'
  [ "$(nb_sha256 "$BIO_SOURCE")" = "$BIO_MODIFIED_SHA" ] || fail 'Biometric payload corrupted.'
  [ "$(nb_sha256 /system/framework/framework-res.apk)" = "$APK_PLATFORM" ] || fail 'Verified platform APK changed.'
}
bio_preflight() {
  [ -n "${BIO_ORIGINAL_SHA:-}" ] || return 0
  bio_payload
  if [ -n "$(bio_record)" ]; then
    bio_owns || fail 'Foreign biometric allowlist mount.'
    [ "$(nb_sha256 "$BIO_TARGET")" = "$BIO_MODIFIED_SHA" ] || fail 'Biometric overlay changed.'
  else
    [ "$(nb_sha256 "$BIO_TARGET")" = "$BIO_ORIGINAL_SHA" ] || fail 'Biometric allowlist baseline changed.'
  fi
}
bio_apply() {
  [ -n "${BIO_ORIGINAL_SHA:-}" ] || return 0
  bio_preflight
  [ -z "$(bio_record)" ] || return 0
  chown 0:0 "$BIO_SOURCE" || fail 'Cannot set biometric XML owner.'
  chmod 644 "$BIO_SOURCE" || fail 'Cannot set biometric XML permissions.'
  chcon u:object_r:system_file:s0 "$BIO_SOURCE" || fail 'Cannot set biometric XML context.'
  mount --bind "$BIO_SOURCE" "$BIO_TARGET" || fail 'Biometric allowlist mount failed; rollback required.'
  bio_record > "$MODDIR/biometric.record"
  if ! bio_owns || [ "$(nb_sha256 "$BIO_TARGET")" != "$BIO_MODIFIED_SHA" ]; then
    umount "$BIO_TARGET" || fail 'Biometric verification failed and unmount failed.'
    rm -f "$MODDIR/biometric.record"
    fail 'Biometric mount verification failed; overlay unmounted.'
  fi
}
bio_confirm() {
  [ -n "${BIO_ORIGINAL_SHA:-}" ] || return 0
  bio_payload
  bio_owns || fail 'No owned biometric allowlist mount.'
  [ "$(nb_sha256 "$BIO_TARGET")" = "$BIO_MODIFIED_SHA" ] || fail 'Biometric overlay changed.'
}
bio_rollback() {
  [ -n "${BIO_ORIGINAL_SHA:-}" ] || return 0
  if [ -n "$(bio_record)" ]; then
    bio_owns || fail 'Refusing to unmount foreign biometric allowlist.'
    umount "$BIO_TARGET" || fail 'Biometric unmount failed.'
  fi
  [ "$(nb_sha256 "$BIO_TARGET")" = "$BIO_ORIGINAL_SHA" ] || fail 'Biometric baseline was not restored.'
  rm -f "$MODDIR/biometric.record"
}
