# Native KernelSU module

The Xposed prototype was removed from the installation path because injecting into Samsung processes can destabilize the device. The supported implementation is now a native KernelSU module with no APK and no hooks.

Install it with:

```sh
sh run.sh kernelsu-install
```

Reboot once. `post-fs-data.sh` creates the audited Floating Features overlay before Android services start. `service.sh` waits for boot completion, restores the two profile settings, enables the four required components, and refreshes only the Samsung packages.

The module is stored at `/data/adb/modules/nowbrief-persistent`. Remove or disable it from KernelSU Manager to roll back on the next reboot. The profile remains specific to the tested SM-S911B / dm1q One UI 9 build.
