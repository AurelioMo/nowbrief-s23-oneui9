# Now Nudge: intentional block versus broken activation

[Tutorial](../../README.md) | [Portugues](../pt-BR/NUDGE.md)

## What was actually established

The active, hash-verified Smart Suggestions 7.3.30.9 bundles an autofill Nudge
policy that explicitly blocks Google Messages and WhatsApp's conversation
Activity. In the installed code, AutofillPolicyManager checks package/Activity
blocks separately from input language. AutofillNudgeManager only collects through
this path when the feature, policy and switch/onboarding gates allow it.

The controlled Google Messages test reached Samsung's `onFillRequest`, but logged
`isNudgeBlocked: true`, `isLocaleAllowed: true (pt-BR)` and no keyboard suggestion.
This establishes a block in this specific native autofill path, not that all
forms of Now Nudge are disabled or that the vendor intended all messaging
features to be unavailable.

## Should it be unblocked?

According to the installed policy, these screens **are intentionally excluded**.
The reason is not established: compatibility, privacy, another processing path
or a release-specific limitation are possibilities, not verified explanations.
There is no evidence that the policy is an S23-specific corruption.

Removing entries or enabling `DISABLE_AUTOFILL_ALLOWLIST` expands the set of
screens eligible for data collection and does not supply missing contextual
models, dependencies or a compatible input pipeline. We do not present that as
a proven activation fix. No global bypass, APK repack, policy edit or automatic
consent change has been applied.

## Reproduce the read-only check

```sh
sh run.sh nudge-policy
```

The script validates ROM identity and active APK hash, reads only the bundled
policy and prints booleans for the tested explicit entries. It does not save
the APK, expose conversations or modify files on the phone. Downloaded runtime
policies may differ, so the output alone is not proof of actual runtime gating.
Correlate it with the same-app logs and a visible suggestion.

For a functional test, use synthetic content in a supported, policy-eligible
screen. Never send a message solely for testing, collect private conversations,
or call an absent suggestion a success. The previous test draft was erased.
