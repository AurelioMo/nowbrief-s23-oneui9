# Native Samsung Now Brief on Galaxy S23

**[Portugues](README.pt-BR.md) | English**

An experimental adaptation of [Furkan-Tsc's original guide](https://github.com/Furkan-Tsc/Guide-to-Enabling-Now-Brief-and-Now-Nudge-on-S23Ultra)
for **SM-S911B / dm1q, One UI 9, Android 17 and KernelSU**.
Original Samsung features, not a replacement app. No flashing or physical writes
to the system partition. Samsung APKs, models and private device data are not included.

> Tested on one specific ROM. Now Brief cards and the home-screen widget work.
> Personal Data Intelligence settings were fixed. Contextual Now Nudge suggestions
> are **not confirmed**, and the lock-screen Now Brief card did not appear in the
> retest. Do not interpret a menu or a connected service as full functionality.

## Step-by-step setup

If your phone is already activated, **do not reinstall or reapply everything**.
Use `status`, `open-brief`, `open-nudge` and `nudge-policy` instead.

### 1. Get the scripts

On your computer, install Git, Python 3, ADB, Java and Android SDK Build Tools
(`aapt2` and `apksigner` on PATH). Enable USB debugging, authorize the computer
and allow root in KernelSU. Keep only the intended phone connected; otherwise
set `ANDROID_SERIAL` to its serial locally. Never publish that identifier.

```sh
git clone https://github.com/AurelioMo/nowbrief-s23-oneui9.git
cd nowbrief-s23-oneui9
adb devices -l
sh run.sh status
```

### 2. Install Smart Suggestions only if needed

The tested APK is **7.3.30.9 / 733009000**, arm64-v8a, minSdk 34, targetSdk 36.
Obtain it yourself from the [Smart Suggestions listing](https://www.apkmirror.com/apk/samsung-electronics-co-ltd/samsungsmartsuggestions/).
The version number alone does not establish compatibility. Compare the active
APK's signer, dependencies and data migration requirements. If the exact tested
APK is already installed, skip to step 3; do not downgrade blindly.

```sh
sh run.sh snapshot snapshots/preinstall-01
sh run.sh backup-data snapshots/preinstall-01
apksigner verify --verbose --print-certs /path/to/SmartSuggestions.apk
aapt2 dump badging /path/to/SmartSuggestions.apk
```

Complete the compatibility review in [Installation](docs/en/INSTALLATION.md).
Only after verifying the review and consistent private backup:

```sh
sh run.sh install \
  --state snapshots/preinstall-01 \
  --apk /path/to/SmartSuggestions.apk \
  --sha256 9e09fc48d5a85c0f1c98a811e2554255988601c9b6e54865e22b07f12fc1d378 \
  --source EXACT_DOWNLOAD_SOURCE_URL \
  --review /path/to/review.json \
  --reversible-trial
```

The installer temporarily applies the original guide's build-type workaround,
restores `ro.build.official.release`, and verifies the installed APK hash.
It does not bypass signatures or enable CorePatch. Stop on other installer errors.

### 3. Activate Floating Features and native components

```sh
sh run.sh activate snapshots/features-01
```

This creates a fresh snapshot, validates the strict profile, prepares the XML,
bind-mounts it, applies the recorded settings and enables selected components.
Keep that exact snapshot for rollback. A hash, ROM or XML mismatch means stop
and audit; do not weaken the checks. Do not run over an already activated state.

### 4. Fix Personal Data settings only when needed

If `status` reports `SET_BIOMETRIC_DIALOG_ADVANCED: granted=true`, skip this step.
For the audited environment with that exact missing-permission crash:

```sh
sh run.sh biometric-fix snapshots/biometric-01
```

The script checks the real Android/app signers and mounts a targeted signature
permission allowlist. It does not bypass biometric authentication or AI consent.

### 5. Refresh the Android cache, then open Samsung's interface

The scripts **never restart Android automatically**. Force-stop was insufficient
in the tested case. Save your work and perform **one KernelSU soft reboot** after
the required overlays are in place. Advanced alternative used in the test, only
after verifying mounts and rollback:

```sh
adb shell 'su -mm -c "sync; setprop ctl.restart zygote"'
```

This interrupts all Android apps and services. Do not use both methods or repeat
restarts in a loop. After the interface returns:

```sh
sh run.sh status
sh run.sh onboarding
sh run.sh open-nudge
```

Tap **Start Now brief** and personally review permissions and consent.
After initial setup, `sh run.sh open-brief` opens the cards. Check Now Nudge's
switch in its settings. To add the native widget: long-press the home screen,
select **Widgets -> Now brief -> Add**.

### 6. Check Now Bar and contextual Nudge separately

In Settings, search **Now bar** and enable **Now brief**. Then run:

```sh
sh run.sh diagnose diagnostics/nowbar-01
sh run.sh nudge-policy
```

GenUI already connects natively in the tested ROM; no bridge was installed.
If there is an actual permission denial, read [Now Bar](docs/en/NOW_BAR.md)
before generating any bridge. Copying a Signing Block is not valid APK signing.

**Should Nudge block messaging apps?** The installed APK explicitly blocks Google
Messages and WhatsApp's conversation Activity in this autofill path. That is
intentional code behavior, not proof of a broken permission or wrong language.
We cannot establish the vendor's rationale or whether another Nudge pipeline
supports those apps. Removing the list is an experimental change to which
screens are eligible for collection, not a proven compatibility fix. We have
not removed it. See [Nudge findings](docs/en/NUDGE.md).

Notification Highlights is separate and **not activated**: Language Core and
offline model dependencies have not been validated. Do not forge AI consent.

### Roll back

Use the exact directories created by your transaction:

```sh
sh run.sh rollback snapshots/features-01
# Only if you applied the biometric overlay:
sh run.sh rollback-biometric snapshots/biometric-01
```

Flags rollback does not undo an APK upgrade or onboarding choices. Permission
overlays require an Android restart to reevaluate grants. APK downgrade and
complete data restoration are not device-tested. Read [Rollback](docs/en/ROLLBACK.md).

## Tested environment and results

Validation date: **November 2, 2026**.

| Item | Observed result |
| --- | --- |
| Phone / OS | SM-S911B / dm1q; One UI 9.0; Android 17 / API 37 |
| Build / patch | S911BXXUAGZIF / 2026-10-05 |
| Smart Suggestions | 7.3.21.9 factory variant -> 7.3.30.9 / 733009000 |
| AODService / root | 8.9.66.1 in data; KernelSU with `su -mm -c` |
| Now Brief | Responsive onboarding, real cards and hourly weather |
| Personal Data settings | Missing biometric permission fixed; user confirmed opening |
| Widget | Added to home, real content and tap-to-open confirmed; periodic refresh unproven |
| GenUI | Connected to SystemUI with `hasBound=true` |
| Lock-screen card | Did not appear in the retest |
| Contextual Nudge | Request received, but messaging test blocked by app policy; no suggestion shown |
| Notification Highlights | Not activated |

LSPosed and Zygisk Next were present; that does not prove universal requirements.
CorePatch was not required for the tested same-signer update. The profile pins
ROM, XML and APK hashes. See [Versions](docs/en/VERSIONS.md) and [Results](evidence/RESULTS.en.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `run.sh` | Command entry point: setup, activation, diagnostics and rollback |
| `scripts/` | Device tools, including experimental bridge utilities |
| `profiles/` | Strict compatibility profile; not a universal device list |
| `tests/` | Offline tests; no phone changes |
| `docs/en/` / `docs/pt-BR/` | Language-specific instructions and troubleshooting |
| `docs/maintainers/` | Publication checklist |
| `evidence/` | Sanitized results only; never raw device captures or backups |

For local execution on the phone, see [Termux](docs/en/TERMUX.md).
For development:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_publication.py
```

Offline tests do not establish functional success on another phone. Preserve
identity/signature checks, mount ownership and rollback. Never flash firmware,
write physically to system, set SELinux permissive or clear Smart Suggestions data.
A full reboot removes temporary mounts; APK updates and Settings may persist.
Termux end-to-end setup, fresh installation via the wrapper, automatic widget
refresh and full rollback were not newly validated in these retests.

## Credits and license

Based on Furkan-Tsc's original method; reference commit
`b080f44e48bdff31901c69ee31a9b115736ffe95`. Independent project, not endorsed by
Samsung, KernelSU or the original author. Original adaptation code and documentation
use [MIT](LICENSE); it does not license Samsung APKs or referenced third-party work.
No Samsung binaries, upstream source dump, private logs or credentials are distributed.
