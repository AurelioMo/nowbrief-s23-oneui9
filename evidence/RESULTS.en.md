# Sanitized device results - November 2, 2026

[Tutorial](../README.md) | [Detailed Portuguese record](RESULTS.pt-BR.md)

This is a manually sanitized summary. Original logs, captures, databases and
backups remain private and are not part of this repository.

## Confirmed on the phone

- Genuine Samsung Smart Suggestions 7.3.30.9 accepted by Package Manager with
  matching signer; installed hash verified and build property restored.
- Feature XML exposed by bind mount without physical system-partition writes.
- Initial incomplete Brief screen resolved after one controlled zygote restart;
  onboarding became responsive, and the user confirmed real cards worked.
- Retests showed afternoon Brief cards and current hourly weather on the screen.
- The targeted biometric signature permission was granted after allowlist reload;
  the user confirmed Personal Data settings opened. No authentication bypass.
- Native GenUIService binder received by SystemUI with `hasBound=true`.
- Samsung home-screen widget added through the widget picker, real content
  rendered and tap opened SuggestionUiContentActivity with Brief cards.

## Explicit negative result: contextual Nudge test

A synthetic unsent draft in Google Messages reached Samsung's `onFillRequest`.
The same test logged `isNudgeBlocked: true`, Portuguese allowed, and no keyboard
Nudge suggestion. The active APK was read again and its hash matched the profile.
Its bundled autofill policy explicitly blocks Google Messages and WhatsApp's
conversation Activity. Installed code checks that policy separately from feature
and switch gates. The test draft was erased; no message was sent.

This is evidence about that specific path, not a demonstrated vendor bug or a
claim that all Nudge integrations are unavailable. No app blocklist, collection
policy or developer allowlist bypass was changed. See [Nudge](../docs/en/NUDGE.md).

## Still not proven

- A visible native Brief card on the lock screen/AOD: absent in the awake
  lock-screen retest despite the established service connection.
- Any visible contextual Now Nudge suggestion or related floating button.
- A periodic automatic widget refresh cycle: a targeted update broadcast was
  accepted but the dump did not establish a new rendered RemoteViews instance.
- Language Core/offline models or Notification Highlights.
- Fresh activation through the new wrapper, complete Termux setup, APK downgrade,
  complete private-data restoration and biometric overlay rollback.

## Read-only policy follow-up

`sh run.sh nudge-policy` was run against the connected phone. It checked ROM
identity and the active APK hash and reported both explicit messaging blocks,
Portuguese allowed and `changes_applied=false`. The purpose is reproducibility,
not another claim of functional success. Offline tests only validate the tools.
