# KernelSU v1.4.0-rc1

Modulo experimental atual: SM-S911B / dm1q, Android 17 / One UI 9.
Xposed v1.0.x e KernelSU v1.1.x permanecem retirados.

## Preparar e instalar

A release publica contem fontes, nao um ZIP universal instalavel. O ZIP preparado
inclui XML do aparelho, estado de rollback e preferencias privadas do Home Up.
Nunca publique esse ZIP. Memory, Home Up e Save Memory devem estar instalados;
nenhum APK Samsung ou de terceiros acompanha a release.

Com Android estavel, root existente e `apksigner` do Android SDK no PATH:

```sh
python3 scripts/prepare-kernelsu.py \
  --with-memory --soft-reboot --with-biometric --with-homeup-gesture \
  --output /caminho/privado/nowbrief-s23-v1.4.0-rc1.zip
```

Preparacao somente le o aparelho. Confere ROM/APKs exatos, XML original e namespace
do init. Mounts existentes exigem rollback antes de preparar outro ZIP.
Nao substitua modulo ativo nem apague journals para forcar atualizacao.
Guarde ZIP privado anterior e estado da transacao ate concluir a migracao.

Instale seu ZIP privado pelo KernelSU Manager. Esse modo opt-in autoriza montagem
antecipada no proximo soft reboot. Quando decidir reiniciar, use **Soft reboot
do KernelSU** / `ksud soft-reboot`. Reboot completo perde root efemero DirtyFrag.
O modulo nunca inicia reboot.

## Correcoes desta versao

- Floating Features e allowlist biometrica opcional montados antes do framework,
  com hashes fixados. Allowlist do mesmo signer, sem contornar autenticacao.
- Espera limitada por Android, Package Manager e SettingsProvider.
- Ativacao dos componentes auditados e `WRITE_SECURE_SETTINGS` solicitado por Memory.
- `--with-homeup-gesture`: fixa APKs Home Up/Save Memory e mapeia tres dedos para
  baixo para Save Memory, preservando outros ajustes.
- Exige navegacao por gestos em varias direcoes; nao muda navegacao automaticamente.
- Usa caminho Home Up em vez do toggle nativo concorrente do Memory.
- Aplicacao/restauracao do mapeamento reinicia somente Home Up e One UI Home.
  Nao limpa dados, nao fabrica onboarding e nao contorna bloqueios de captura.

Recusa substituir outra acao ja atribuida a tres dedos para baixo. Preferencias
alteradas desde a preparacao nao sao sobrescritas. Rollback so restaura snapshot
se ainda pertencer a transacao; edicoes posteriores causam recusa segura,
preservando journal para evitar perda de dados.

## Controle e rollback

```sh
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh preflight'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/memory-gesture.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh rollback'
```

Action/ativacao manual e boot usam a mesma transacao de gesto dentro do modulo.
Tentativas interrompidas bloqueiam repeticao automatica. Nao apague `attempt`,
`apps.changed` ou `gesture.changed` para esconder falhas.
Confirmacao apos 120 segundos comprova liveness, nao funcionamento dos recursos.

## Validacao e limites

Usuario relata Brief, Nudge, Memory e ajustes biometricos funcionando no S23.
Foi observado Save Memory abrindo a activity de captura. Mapeamento Home Up foi
aplicado pelo modulo, mas reconhecimento do gesto fisico e soft reboot do RC
recriado ainda precisam de confirmacao.

Perfil atual fixa Smart Suggestions 7.3.31.4 (733104000), instalado com assinatura
Samsung e hash conferidos. Tanto 7.3.30.9 quanto 7.3.31.4 nao incluem `ActiveMemoryProvider`.
Memory chama `getActiveMemoryHintsByTime` em
`content://com.samsung.android.moneta.feature.activememory.ActiveMemoryProvider`,
envia `query_time_start`, `query_time_end`, `query_limit` e espera
`active_memory_hints_by_time`. E um feed de sugestoes; isso nao prova que todas
as outras funcoes de IA dependem desse mesmo endpoint.
Nao fornecemos provider vazio/falso. Preferencia habilitada nao comprova IA.
Teste tres dedos para baixo numa pagina comum, confirme captura e salve manualmente.
Nenhum teste automatizado comprova gesto fisico.
