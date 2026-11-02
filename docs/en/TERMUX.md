# Termux

[Tutorial](../../README.md) | [Portugues](../pt-BR/TERMUX.md)

Keep this repository and private snapshots in Termux's private storage. Authorize
Termux root in KernelSU. `NOWBRIEF_TERMUX=1` executes `su -mm -c` locally instead
of ADB. No pip packages are required for these Python standard-library scripts.

```sh
pkg install git python
git clone https://github.com/AurelioMo/nowbrief-s23-oneui9.git
cd nowbrief-s23-oneui9
export NOWBRIEF_TERMUX=1
sh run.sh status
sh run.sh nudge-policy
# Only after installing the audited APK and confirming the original XML/profile:
sh run.sh activate snapshots/features-01
sh run.sh onboarding
sh run.sh open-nudge
```

For an already activated phone, do not rerun `activate`. To roll back your own
transaction: `sh run.sh rollback snapshots/features-01`.

APK auditing/installation and the biometric fix require compatible `apksigner`
and, when used, `aapt2`. Desktop macOS/Linux binaries are not automatically
executable in Termux. Prefer computer-based APK auditing if those tools are not
available; never remove checks to work around missing tooling. The complete
Termux flow has not been device-tested; actual activation used computer ADB.
