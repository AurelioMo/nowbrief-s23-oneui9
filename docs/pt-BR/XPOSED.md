# Modulo LSPosed persistente

Os scripts originais usam um bind mount, e o Android remove esse mount durante um reboot completo. O repositorio agora inclui `xposed-module`, um APK LSPosed/Xposed que executa um payload root auditavel quando `android`, SystemUI, Smart Suggestions ou AODService iniciam.

## Instalar

1. Compile ou baixe `nowbrief-xposed-release.apk` no release do GitHub.
2. Instale o APK e ative **Now Brief Persistent** no LSPosed para `android`, `com.android.systemui`, `com.samsung.android.smartsuggestions` e `com.samsung.android.app.aodservice`.
3. Em um computador com ADB e root KernelSU, execute uma vez `sh run.sh xposed-install`. Isso instala `/data/adb/nowbrief-xposed/apply.sh`.
4. Reinicie uma vez. O payload salva o XML original na primeira execucao, cria um overlay idempotente, restaura as flags do Now Brief e reinicia apenas os pacotes Samsung afetados.

O modulo requer LSPosed (ou Xposed compativel) e root KernelSU/Magisk com `su -mm`. Ele nao inclui APKs Samsung, nao ignora assinaturas e nao concede permissoes biometricas. Mantenha o snapshot original e use o rollback auditado antes de remover o modulo.

Para desativar a persistencia, desative o modulo no LSPosed e remova `/data/adb/nowbrief-xposed` em um shell root. Os scripts originais continuam disponiveis para diagnostico e rollback.
