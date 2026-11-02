# Tested versions and integrity

[Tutorial](../../README.md) | [Portugues](../pt-BR/VERSIONS.md)

Audited November 2, 2026: SM-S911B/dm1q, One UI 9, Android 17/API 37,
build S911BXXUAGZIF. These hashes pin one tested environment, not universal APK
requirements. The profile validates the ROM identity as well.

| Artifact | SHA-256 |
| --- | --- |
| Original Smart Suggestions 7.3.21.9 | ccbeb639c5a2d433e3e669bbe5951e58b4828b96ee2feab35a6d51befb1a7702 |
| Tested Smart Suggestions 7.3.30.9 | 9e09fc48d5a85c0f1c98a811e2554255988601c9b6e54865e22b07f12fc1d378 |
| Active AODService 8.9.66.1 | 1d1b07db9855d7044e53b492106607ade40dd59b5ed41b5b85bfc1656cb52c52 |
| Active SystemUI | ddb92bdd9e00bbf6aef9f70ae53bca558a934629fcf1e1aff6efe8705ae35ff3 |
| Active Settings | 8e69d7105bdea8bdd8745ee64ad971bea1e9562909687e04d3267450ea5d3148 |
| Original Floating Features | d6f46fdc40a76ce23a3f4268cebc58aa3dd9023198f78e94455189197a020feb |

Common signer SHA-256 verified against the real APKs:
`34df0e7a9f1cf1892e45c056b4973cd81ccf148a4050d11aea4ac5a65f900a42`.

Updated package: `com.samsung.android.smartsuggestions`, versionCode 733009000,
arm64-v8a, minSdk 34, targetSdk 36. A matching file hash alone does not prove
provenance; check the signer, source and currently installed package.

No APKs, firmware, model files, private certificates or extracted phone data
are distributed. SHA256SUMS.json covers this public source package and is not
a cryptographic signature from the maintainer.
