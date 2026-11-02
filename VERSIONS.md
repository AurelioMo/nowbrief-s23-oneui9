# Versoes e integridade do caso testado

Data da validacao: 2026-11-02. Modelo SM-S911B, dm1q, One UI 9, Android 17/API37,
build S911BXXUAGZIF. Estes hashes identificam o teste, nao uma lista de APKs
obrigatorios para qualquer ROM. O perfil verifica tambem a identidade da ROM.

| Artefato | SHA-256 |
| --- | --- |
| Smart Suggestions original 7.3.21.9 | ccbeb639c5a2d433e3e669bbe5951e58b4828b96ee2feab35a6d51befb1a7702 |
| Smart Suggestions usado 7.3.30.9 | 9e09fc48d5a85c0f1c98a811e2554255988601c9b6e54865e22b07f12fc1d378 |
| AODService ativo 8.9.66.1 | 1d1b07db9855d7044e53b492106607ade40dd59b5ed41b5b85bfc1656cb52c52 |
| SystemUI ativo | ddb92bdd9e00bbf6aef9f70ae53bca558a934629fcf1e1aff6efe8705ae35ff3 |
| Settings ativo | 8e69d7105bdea8bdd8745ee64ad971bea1e9562909687e04d3267450ea5d3148 |
| Floating Features original | d6f46fdc40a76ce23a3f4268cebc58aa3dd9023198f78e94455189197a020feb |

Certificado SHA-256 comum verificado nos APKs reais e no Smart Suggestions novo:
`34df0e7a9f1cf1892e45c056b4973cd81ccf148a4050d11aea4ac5a65f900a42`.

Smart Suggestions novo: pacote com.samsung.android.smartsuggestions,
versionCode 733009000, arm64-v8a, minSdk34, targetSdk36.
O hash do arquivo nao prova sozinho a procedencia: verifique assinatura,
fonte e comparacao com o pacote realmente instalado.

Nao foram incluidos APKs, ROM, modelos de linguagem, certificados privados ou
arquivos extraidos do telefone. SHA256SUMS.json inventaria apenas este pacote
publicavel; nao e assinatura criptografica de um mantenedor.
