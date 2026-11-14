# Sourced by KernelSU's installer, with MODPATH provided by the manager.
MODDIR=$MODPATH
. "$MODDIR/lib.sh"
fail() { abort "$*"; }
[ -f "$MODDIR/payload/profile.sh" ] || abort 'Build a device-specific ZIP with scripts/prepare-kernelsu.py first.'
. "$MODDIR/payload/profile.sh"
check_identity
check_packages
bio_preflight
[ -z "$(bio_record)" ] || abort 'Rollback existing biometric allowlist mount first.'
if [ ! -f "$MODDIR/payload/activate.sh" ]; then check_settings; fi
[ -z "$(mount_record)" ] || abort 'Remove the existing Floating Features mount first.'
[ "$(nb_sha256 "$TARGET")" = "$ORIGINAL_SHA" ] || abort 'Active XML does not match the audited baseline.'
# These files are deliberately not stored outside the module directory.
[ ! -f "$MODDIR/apps.changed" ] || abort 'Rollback existing app activation before replacing this module.'
[ ! -f "$MODDIR/gesture.changed" ] || abort 'Rollback existing gesture activation before replacing this module.'
rm -f "$MODDIR/armed" "$MODDIR/attempt" "$MODDIR/confirmed" "$MODDIR/persistent" "$MODDIR/mount.record"
if [ "${SOFT_REBOOT_MODE:-0}" = 1 ]; then
  check_apk_files
  touch "$MODDIR/persistent"
fi
set_perm_recursive "$MODDIR" 0 0 0755 0644
for script in "$MODDIR"/*.sh; do set_perm "$script" 0 0 0755; done
set_perm "$MODDIR/payload/original.xml" 0 0 0600
set_perm "$MODDIR/payload/floating_feature.xml" 0 0 0644 u:object_r:system_file:s0
if [ "${SOFT_REBOOT_MODE:-0}" = 1 ]; then
  ui_print 'Soft-reboot build: early activation authorized. Use KernelSU soft reboot, not a zygote-only restart.'
else
  ui_print 'Installed with automatic activation OFF. Use Action for a manual attempt.'
fi
