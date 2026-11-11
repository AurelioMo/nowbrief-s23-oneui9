# Sourced by KernelSU's installer, with MODPATH provided by the manager.
MODDIR=$MODPATH
. "$MODDIR/lib.sh"
fail() { abort "$*"; }
[ -f "$MODDIR/payload/profile.sh" ] || abort 'Build a device-specific ZIP with scripts/prepare-kernelsu.py first.'
. "$MODDIR/payload/profile.sh"
check_identity
check_packages
check_settings
[ -z "$(mount_record)" ] || abort 'Remove the existing Floating Features mount first.'
[ "$(hash "$TARGET")" = "$ORIGINAL_SHA" ] || abort 'Active XML does not match the audited baseline.'
# These files are deliberately not stored outside the module directory.
rm -f "$MODDIR/armed" "$MODDIR/attempt" "$MODDIR/confirmed" "$MODDIR/mount.record"
set_perm_recursive "$MODDIR" 0 0 0755 0644
for script in "$MODDIR"/*.sh; do set_perm "$script" 0 0 0755; done
set_perm "$MODDIR/payload/original.xml" 0 0 0600
set_perm "$MODDIR/payload/floating_feature.xml" 0 0 0644 u:object_r:system_file:s0
ui_print 'Installed with automatic activation OFF. Use Action for a manual attempt.'
