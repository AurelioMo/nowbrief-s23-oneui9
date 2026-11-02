# Native Now Bar and GenUI

[Tutorial](../../README.md) | [Portugues](../pt-BR/NOW_BAR.md)

In the audited ROM, AODService 8.9.66.1 requests
`com.samsung.android.smartsuggestions.permission.BIND_GENUI_SERVICE`.
Smart Suggestions 7.3.30.9 declares it and exposes
`.feature.aisuggestion.genui.service.GenUIService`. The shared AOD/SystemUI UID
received the permission and connected; no bridge or CorePatch was installed.

```sh
sh run.sh diagnose diagnostics/nowbar-01
adb shell 'su -mm -c "dumpsys activity services com.samsung.android.smartsuggestions"'
```

Check complete manifests, shared UID grants and service connections. The tested
connection has `requested=true received=true hasBound=true` with SystemUI as client.
An empty grep or `No services found` alone is not proof of a denial.

Open the actual settings Activity for the tested AOD version:

```sh
adb shell 'su -mm -c "am start -W -n com.samsung.android.app.aodservice/com.samsung.android.app.aod.common.settings.FaceWidgetNowBarSettingsActivity"'
```

Enable Now brief. The native policy tracks morning/evening consumption; opening
a Brief can consume its lock-screen presentation. The earlier state had morning
shown and `now_bar_updatable=0`; GenUI returned no view and AOD removed the item.
The awake lock-screen retest showed no Brief card. Connection is confirmed;
lock-screen card functionality is not. Test new content in its natural period
before opening Brief; do not fake the clock, enable shop-demo or clear databases.

Only investigate a bridge when the service exists and an actual permission
denial is demonstrated. `scripts/GenUIBridge.py` requires a genuine private key
and certificate matching AOD/SystemUI. A public certificate or copied Signing
Block cannot sign a modified APK. The experimental installer validates signer,
manifest, UID and permission, but its install path was not exercised here because
it was unnecessary. No private signing keys or signed bridges are distributed.
