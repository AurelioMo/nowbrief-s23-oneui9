# KernelSU — ativacao controlada

As versoes Xposed v1.0.x e KernelSU v1.1.x tiveram relatos de travamento neste aparelho e foram retiradas do fluxo suportado. A v1.2.0-dev foi revisada e tem testes simulados. A instalacao e o soft reboot no S23 ainda precisam ser validados. O repositorio e privado e usa commits para versionamento.

## Preparar o ZIP

Com o Android estavel, root ja disponivel e a ativacao manual auditada concluida, prepare um ZIP privado fora do repositorio:

```sh
python3 scripts/prepare-kernelsu.py --output /caminho/privado/nowbrief-private.zip
```

A preparacao le identidade da ROM, hashes do XML e APKs, configuracoes e componentes. Recusa mount preexistente, ROM diferente, layout de APK inesperado ou ativacao manual incompleta. O ZIP inclui o XML original do aparelho. Mantenha-o privado.

Instale o ZIP preparado pelo KernelSU Manager. A instalacao confere novamente ROM, APKs, XML e configuracoes. A execucao automatica inicia DESLIGADA.

## Validar manualmente

O botao Action do modulo monta apenas o XML preparado. Verifica hash, namespace de montagem, contexto SELinux e propriedade do mount. As configuracoes e os componentes que ja foram ativados permanecem como estavam. O modulo nao reinicia o Android nem para aplicativos.

Com root existente, estes comandos oferecem controle explicito:

```sh
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh status'
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh apply'
# Depois de verificar que Android e Now Brief estao funcionando:
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh confirm'
# Para desfazer o mount e desligar autorizacoes futuras:
su -mm -c 'sh /data/adb/modules/nowbrief-persistent/control.sh rollback'
```

Antes do teste de soft reboot, mantenha a execucao automatica desligada. Um reinicio apenas do zygote nao garante nova execucao dos estagios KernelSU. Primeiro verifique a estabilidade e se o mount permanece visivel apos o seu tipo de soft reboot.

## Tentativa automatica opcional

Somente depois de uma ativacao manual confirmada, `control.sh arm` autoriza UMA tentativa automatica. A autorizacao e consumida antes da validacao. Uma marca persistente impede repeticao automatica apos falha ou travamento. Cada nova tentativa exige verificacao e autorizacao manual. Isso limita a persistencia automatica em favor de recuperacao.

O fluxo de root temporario e a versao instalada do KernelSU precisam de validacao propria. A documentacao upstream nao confirma o comportamento do fork Samsung usado no aparelho. Consulte o [guia KernelSU](https://kernelsu.org/guide/module.html).

O modulo guarda os arquivos da transacao dentro da propria pasta. Dados deixados pelas versoes antigas em `/data/adb/nowbrief-persistent` sao ignorados. O rollback verifica a propriedade do mount antes de desmontar. Mudancas persistentes das versoes antigas em Settings/componentes exigem os snapshots originais para restauracao.

A etapa post-fs-data permanece inativa. O service aguarda o Android terminar o boot por ate 120 segundos antes da tentativa autorizada. O XML pode ja estar em cache nos processos Samsung; a montagem isolada nao comprova funcionamento. Atualizacao do cache e soft reboot exigem validacao manual separada.
