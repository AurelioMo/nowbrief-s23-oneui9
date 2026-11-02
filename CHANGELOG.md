# Changelog

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
