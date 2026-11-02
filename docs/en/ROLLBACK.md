# Rollback and limitations

[Tutorial](../../README.md) | [Portugues](../pt-BR/ROLLBACK.md)

```sh
sh run.sh rollback snapshots/features-01
# Only for the biometric transaction you actually applied:
sh run.sh rollback-biometric snapshots/biometric-01
```

Use your original transaction paths. Feature rollback restores its mount,
components and recorded Settings; it does not undo an APK update or manually
accepted onboarding choices. Android caches may require a controlled restart.
Biometric overlay rollback also needs restart to reevaluate permissions and
has not been device-tested. Never bypass authentication to test it.

The audited installer can attempt restoring its saved original APK:

```sh
sh run.sh install --state snapshots/preinstall-01 --restore
```

That downgrade path was not validated on the phone after the upgrade. Android
may reject it, and migrated data may be incompatible. Do not uninstall or clear
the app to force restoration. CE/DE data restoration needs an audited UID,
ownership, SELinux and database procedure with processes stopped; no generic
overwrite command or complete one-click rollback is provided.

Full reboot generally removes temporary bind mounts, but APKs installed in data,
Settings and onboarding state may remain. Never erase the original snapshot.
