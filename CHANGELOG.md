# Changelog

## 1.4.0-rc1 - 2026-11-14

- Current KernelSU module and public source prerelease; prepared device ZIPs remain private.
- Added opt-in Home Up three-finger-down mapping to installed Save Memory.
- Preserved unrelated preferences, APK pins, conflict checks and conservative rollback.
- Fixed Android shell hash alias collision and bounded Package Manager/Settings readiness.
- Added early same-signer biometric allowlist and soft-reboot generation guards.
- Physical swipe recognition and rebuilt RC soft reboot remain unconfirmed.
- Updated profile to same-signer Smart Suggestions 7.3.31.4; installed hash verified.
- Both tested APK versions lack the ActiveMemory hint provider. No fake provider added.

## 1.2.0-dev - 2026-11-11

- Withdrew Xposed and KernelSU v1.1.x installation paths after device crashes.
- Replaced mutable shared XML generation with a device-pinned private ZIP builder.
- Added preflight guards, SELinux labeling, mount ownership, rollback and one-shot boot authorization.
- Added simulated failure-path regression tests. Real device boot validation remains pending.
- Made the repository private and removed automatic release uploads.

## 1.0.0 - 2026-11-10

- Added the `xposed-module` LSPosed/Xposed APK for reboot-persistent Now Brief activation.
- Added an idempotent KernelSU payload and `sh run.sh xposed-install`.
- Added bilingual installation docs and a GitHub tag release workflow.

## 2026-11-02 - bilingual documentation and policy audit

- English main tutorial and Portuguese README, both with executable steps.
- Language-specific instructions under docs/en and docs/pt-BR; publication notes
  under docs/maintainers and offline tests under tests.
- Added read-only `sh run.sh nudge-policy`: validates ROM and active APK hash
  before reporting explicit bundled policy entries. No policy bypass applied.
- Clarified that the observed messaging block is intentional code behavior;
  vendor rationale and other contextual Nudge paths remain unverified.
- Preserved strict activation guards, private snapshots and existing rollback.

## 2026-11-02 - live widget proof

- Added the native widget to Samsung's launcher, observed real content and
  confirmed tap-to-open Brief cards.
- Contextual Google Messages test reached the Samsung service but was blocked
  by its policy. No message was sent; synthetic draft cleared afterward.
- Lock-screen Brief card and periodic widget refresh remain unproven.

## 2026-11-02 - initial public guide

- Published audited scripts, explicit public-file inventory, source hashes,
  privacy exclusions and MIT license for original adaptation work.
- Documented same-signer Smart Suggestions update, temporary feature bind,
  biometric signature-permission fix and native GenUI connection.
