# Problemas conhecidos

## Dados pessoais / Now Nudge: crash na biometria corrigido no caso testado

Confirmado no caso testado em 2026-11-02, depois da publicacao local inicial
do tutorial. A interface de dados pessoais pode fechar com falhas continuas.

Excecao observada em BioMetricAuthenticationActivity, processo :moneta:

```text
SecurityException: Must have SET_BIOMETRIC_DIALOG_ADVANCED permission
```

O APK 7.3.30.9 solicita essa permissao signature|privileged, mas o APK original
do caso testado nao. A allowlist da ROM ja a inclui, sem concessao efetiva ao
pacote atualizado. pm grant nao resolve: nao e uma permissao de runtime.

A assinatura criptografica do framework-res.apk REAL foi comparada com o APK
novo: ambos possuem o certificado Samsung indicado em VERSIONS.md.
Isso permite corrigir a lista de permissoes de ASSINATURA, sem alterar APKs,
conceder permissoes a outros signers ou contornar a autenticacao.

Foi adicionada somente SET_BIOMETRIC_DIALOG_ADVANCED em uma copia de
/system/etc/permissions/signature-permissions-downloadable.xml, por bind mount.
Depois de um restart controlado de zygote, o dump confirmou granted=true.
O usuario confirmou a abertura e a Activity de gerenciamento de dados pessoais
foi observada. Nenhum consentimento foi marcado automaticamente.

O script verifica modelo/API, hash do APK, certificados do aplicativo e Android,
namespace e propriedade do mount. Cria backup e journal privados em pasta nova.
Nao executar em outro ambiente removendo as protecoes:

```sh
python3 scripts/signature_permissions.py apply --state snapshots/signature-biometric
```

APPLY NAO REINICIA O ANDROID. A lista so e recarregada no reinicio do ambiente;
veja os avisos sobre restart de zygote no README. Nao e preciso reaplicar se a
permissao ja estiver concedida. O script para nesse caso.

Rollback especifico:

```sh
python3 scripts/signature_permissions.py rollback --state snapshots/signature-biometric
```

Rollback desse overlay ainda nao foi testado no telefone e tambem requer restart
controlado para reavaliar a concessao. Um reboot completo pode remover o bind.
Nao desligue biometria, nao altere manualmente o banco de permissoes e nao
modifique o APK para saltar autenticacao.

O Nudge contextual permanece nao validado. Ha pedidos de autofill em execucao,
mas a politica do APK pode bloquear Activities especificas mesmo com idioma
pt-BR permitido. Nao confundir esse bloqueio com a excecao de biometria.

Now Brief com cards e abertura de dados pessoais sao confirmados. Este tutorial
nao oferece ainda uma ativacao contextual completa e validada do Now Nudge.
