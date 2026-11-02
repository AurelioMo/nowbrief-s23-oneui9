# Known issues

[Tutorial](../../README.md) | [Portugues](../pt-BR/KNOWN_ISSUES.md)

## Personal Data settings crash

The updated 7.3.30.9 APK requests `android.permission.SET_BIOMETRIC_DIALOG_ADVANCED`,
but the factory APK did not. The observed crash in BioMetricAuthenticationActivity
was `SecurityException: Must have SET_BIOMETRIC_DIALOG_ADVANCED permission`.
The existing privileged allowlist alone did not grant it to the updated app;
`pm grant` cannot grant this non-runtime permission.

The real framework-res APK and updated app had the same audited signer. A copy
of `/system/etc/permissions/signature-permissions-downloadable.xml` was extended
with only that permission, bind-mounted and reloaded through a controlled Android
restart. Package Manager then reported `granted=true`, and the user confirmed
the screen opened. Authentication and AI consent were not bypassed.

Only for the pinned, missing-permission case:

```sh
sh run.sh biometric-fix snapshots/biometric-01
# To undo your own transaction:
sh run.sh rollback-biometric snapshots/biometric-01
```

The script verifies model/API, APK hash, real signers, mount namespace and mount
ownership. It saves the original XML and journal in a new private directory.
It does not restart Android; reevaluating the allowlist requires a controlled
restart. Do not reapply when already granted. Overlay rollback was not device-tested.

## Other boundaries

- [Nudge](NUDGE.md): explicit app policy block; no visible contextual suggestion
  confirmed. Fixing the biometric screen does not remove that separate gate.
- [Now Bar](NOW_BAR.md): GenUI connected, but the lock-screen card did not appear
  in the retest. Native content-consumption policy is a separate condition.
- Widget: home placement, real content and tap-to-open confirmed; a periodic
  automatic refresh cycle has not been proven.
- Notification Highlights: not activated; Language Core/models not validated.
- Full Termux setup, fresh wrapper activation, APK downgrade and complete private
  data restoration were not validated by these retests.
