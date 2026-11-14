# KernelSU v1.4.0-rc1

Current experimental module for SM-S911B / dm1q, Android 17 / One UI 9.
Old Xposed v1.0.x and KernelSU v1.1.x releases are withdrawn.

## Prepare and install

Public releases contain source, not a universal flashable ZIP. A prepared ZIP
contains device XML, rollback state and private Home Up preferences. Never upload it.
Obtain compatible Samsung Memory, Home Up and Save Memory yourself; no APKs are bundled.

With an already rooted, stable device and the Android SDK `apksigner` on PATH:

```sh
python3 scripts/prepare-kernelsu.py \
  --with-memory --soft-reboot --with-biometric --with-homeup-gesture \
  --output /private/path/nowbrief-s23-v1.4.0-rc1.zip
```

Preparation is read-only. Exact ROM/APK hashes, original XML and init mount
namespace are checked. Existing overlay mounts must first be rolled back.
Do not overwrite an active module or erase journals to force an upgrade.
Keep the previous private ZIP and transaction state until migration succeeds.

Install your private ZIP in KernelSU Manager. This explicit soft-reboot mode
authorizes early mounting on the next KernelSU soft reboot.
Only use KernelSU **Soft reboot** / `ksud soft-reboot` when you choose to restart.
A full reboot loses ephemeral DirtyFrag root. The module never initiates a reboot.

## What the module does

- Validates pinned payloads before mounting Floating Features and the optional
  same-signer biometric allowlist before framework startup.
- Waits for Android, Package Manager and SettingsProvider, with bounded waits.
- Enables audited components and requested Memory `WRITE_SECURE_SETTINGS`.
- With `--with-homeup-gesture`, pins installed Home Up and Save Memory, preserves
  unrelated preferences and maps three-finger swipe down to Save Memory.
  Requires multiple-direction swipe navigation; navigation mode is not changed.
- Selects Home Up's gesture path instead of the competing native Memory toggle.
  Restarts Home Up and One UI Home only when applying/restoring the mapping.
  It does not clear app data, fake onboarding or bypass capture restrictions.

Home Up and Save Memory must already be installed. An existing different
three-finger-down assignment is rejected. Preferences changed since preparation
are not overwritten. Rollback restores the prepared snapshot only if still owned;
subsequent edits cause a safe refusal with the journal retained.

## Controls and rollback

```sh
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh preflight'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/memory-gesture.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh rollback'
```

Action/manual activation and boot activation use the same module-owned gesture
transaction. Interrupted attempts block automatic retries. Do not delete
`attempt`, `apps.changed` or `gesture.changed` to silence errors.
The 120-second confirmation checks liveness, not feature functionality.

## Evidence and limits

On the tested S23, the user reports Brief, Nudge, Memory and biometric settings
working. Save Memory was observed opening the Memory capture activity. The
module-owned Home Up mapping was applied, but physical swipe recognition and
the rebuilt RC soft-reboot flow still need confirmation.

Current profile pins Smart Suggestions 7.3.31.4 (733104000), installed with verified
Samsung signer and file hash. Both 7.3.30.9 and 7.3.31.4 lack `ActiveMemoryProvider`.
Memory calls `getActiveMemoryHintsByTime` at
`content://com.samsung.android.moneta.feature.activememory.ActiveMemoryProvider`,
passing `query_time_start`, `query_time_end` and `query_limit`, and expects
`active_memory_hints_by_time`. This is a hint feed, not proof that every other
Memory AI function depends on the same endpoint.
No empty/fake provider is supplied. Enabling preferences is not proof of AI.
Test swipe down with three fingers on an ordinary page, then confirm capture and
save manually. No automated test proves the physical gesture.
