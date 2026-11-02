# Audited Smart Suggestions installation

[English tutorial](../../README.md) | [Portugues](../pt-BR/INSTALLATION.md)

The tested 7.3.21.9 factory variant lacked the complete Brief/GenUI components.
The genuine same-signer 7.3.30.9 update was tested with a consistent private backup.
That does not establish compatibility for another APK or ROM.

Before installing, audit manifest, dependencies, ABI, SDK, signer and data migration.
Create a new pre-install snapshot and run `backup-data` as shown in the README.
That backup utility is restricted to the audited appId 10132; do not replace the
UID blindly. Preserve ownership and SELinux metadata. The archive contains private data.

Prepare `review.json` outside Git:

```json
{
  "installed_sha256": "ORIGINAL_SNAPSHOT_APK_HASH",
  "candidate_sha256": "DOWNLOADED_APK_HASH",
  "dependencies_verified": false,
  "consistent_data_backup_verified": false,
  "data_compatibility_verified": false,
  "room_identities_preserved": false
}
```

These fields record human review, not automatic detection. Do not mark them true
without evidence. With `--reversible-trial`, verified Room identities and a hashed
consistent private backup are required; equal Room identities alone do not prove
all migrations safe. Without the flag, demonstrated data compatibility is required.
There is no safe unattended upgrade path without this review.

Run the complete installation command in the README. The installer compares
candidate and original signers, hashes, package, minimum SDK and ABI, temporarily
uses `resetprop ro.build.official.release false`, streams the APK into Package
Manager, restores the property in `finally` and verifies the installed hash.
KernelSU resetprop is detected at `/data/adb/ksu/bin/resetprop` when needed.

On a signature, shared UID, library or storage error, stop. Do not apply the
build-type workaround repeatedly or enable signature hooks indiscriminately.
An install success does not prove native feature functionality.
