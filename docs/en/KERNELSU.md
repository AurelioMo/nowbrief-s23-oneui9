# KernelSU — controlled activation

Xposed v1.0.x and KernelSU v1.1.x caused reported device crashes and are withdrawn from the supported installation path. v1.2.0-dev has simulated regression tests. Installation and soft reboot on the S23 remain unverified. This private repository uses commits for versioning.

Prepare a private ZIP outside the repository with an already stable, rooted and manually activated device:

```sh
python3 scripts/prepare-kernelsu.py --output /private/path/nowbrief-private.zip
```

Preparation validates the exact ROM, original XML hash, APK hashes, settings, enabled components and init mount namespace. Existing XML mounts are rejected. The resulting ZIP contains the device XML and must remain private.

Install the prepared ZIP in KernelSU Manager. Installation validates the device again. Automatic activation defaults to OFF. Action applies only the prepared XML overlay, checking SELinux context, hashes and mount ownership. Existing settings and component overrides are preserved. Android and Samsung apps are never restarted by this module.

Root controls:

```sh
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh apply'
# After personally checking Android and Now Brief:
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh confirm'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh rollback'
```

Test the actual soft reboot method with automatic activation OFF first. A zygote restart does not guarantee KernelSU stage execution. Check mount visibility and stability after restart. The Samsung fork and temporary root flow require separate device validation.

After a successful manual activation and confirmation, `control.sh arm` permits ONE automatic attempt. Authorization is consumed before validation. An attempt marker prevents automatic repetition after a crash or interrupted transaction. Further attempts require manual verification and authorization. See the [KernelSU module guide](https://kernelsu.org/guide/module.html).

Rollback only unmounts an owned mount. All new state is inside the module directory. Old `/data/adb/nowbrief-persistent` data is ignored. Restoring persistent Settings/component changes from older versions requires their original snapshots.

The post-fs-data stage is inert. The service waits up to 120 seconds for Android boot completion before an authorized attempt. Samsung processes may already cache XML flags. Mount success alone does not establish functionality; cache refresh and soft reboot require separate manual validation.
