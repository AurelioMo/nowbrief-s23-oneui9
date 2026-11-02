# Guia completo de instalacao e ativacao

Adaptacao experimental do metodo de Furkan-Tsc para o **Galaxy S23 comum
(SM-S911B / dm1q), Android 17 / One UI 9 e KernelSU**.

Nao e um aplicativo alternativo. O procedimento desbloqueia componentes originais
do Samsung Smart Suggestions, usando APK Samsung compativel, Floating Features
por bind mount e configuracoes restauraveis.

> **Estado em 2 de novembro de 2026:** Now Brief confirmado na tela, com cards,
> clima e aviso UV, e confirmado pelo usuario. Now Nudge contextual e cartao da
> Now Bar na tela bloqueada ainda NAO foram comprovados. Nao anunciar suporte
> completo a esses recursos antes dos testes funcionais.

**Correcao adicional confirmada:** a falha de dados pessoais na autenticacao
biometrica foi corrigida com allowlist de assinatura especifica, sem bypass de
biometria. Leia [KNOWN_ISSUES.md](KNOWN_ISSUES.md) para condicoes e rollback.

## Creditos

Projeto original de **Furkan-Tsc**:
https://github.com/Furkan-Tsc/Guide-to-Enabling-Now-Brief-and-Now-Nudge-on-S23Ultra

Referencia consultada: commit
`b080f44e48bdff31901c69ee31a9b115736ffe95`.
Este material e uma adaptacao independente, nao uma publicacao oficial Samsung
ou uma versao aprovada pelo autor original. Nao reproduzimos APKs nem arquivos
privados do telefone. Nao atribuimos uma licenca ao codigo de terceiros.

## O que realmente foi testado

| Item | Resultado |
| --- | --- |
| Smart Suggestions 7.3.30.9 | Instalado; assinatura e hash conferidos |
| Now Brief / onboarding | Funcionando apos atualizar cache do ambiente Android |
| Cards | Personalizacao, clima horario e protecao UV observados |
| Widget | Adicionado na home; conteudo real e abertura por toque confirmados; atualizacao periodica pendente |
| Now Nudge | Teste contextual no Google Mensagens bloqueado pela politica interna; sugestao visivel nao comprovada |
| GenUI / Now Bar | Bind ativo do SystemUI ao GenUIService |
| Cartao na tela bloqueada | Ainda nao confirmado; politica matinal ja consumida |
| Soft reboot do KernelSU | Usuario executou; bind e Brief permaneceram no teste |
| Notification Highlights | Nao ativado; Language Core ausente |

## Ambiente validado, nao uma lista universal de compatibilidade

| Componente | Versao |
| --- | --- |
| Aparelho | SM-S911B / dm1q |
| One UI / Android / API | 9.0 / 17 / 37 |
| Build / patch | S911BXXUAGZIF / 2026-10-05 |
| Smart Suggestions original | 7.3.21.9 |
| Smart Suggestions usado | 7.3.30.9 / 733009000 |
| AODService ativo | 8.9.66.1, instalado em /data/app |
| AODService da particao | 8.9.65.90 |
| Root | KernelSU; su -mm -c funcional |
| Modulos encontrados | LSPosed 2.2.1 e Zygisk Next 1.5.2 |

CorePatch nao foi confirmado nem alterado. Nao foi necessario bypass de assinatura.
Os modulos existentes foram inventariados; isso nao demonstra que sejam todos
indispensaveis. Nao recomendamos reinstala-los se o ambiente ja funciona.

## Antes de comecar

- Este e um procedimento experimental de root. Tenha backup independente.
- Nao faca flash, nao altere boot/vbmeta, nao escreva fisicamente em /system.
- Nao deixe SELinux permissivo, nao limpe dados e nao desinstale apps criticos.
- Um reboot completo remove o bind; APK atualizado e Settings podem persistir.
- Reiniciar zygote interrompe apps, audio e servicos. Nao e uma etapa automatica.
- O perfil recusa hashes, XML e build diferentes. Nao remova essas verificacoes.
- **Nao execute novamente no aparelho ja ativado apenas para seguir o tutorial.**

Requisitos no computador: Python 3, ADB, Java e Android SDK Build Tools
(`aapt2`, `apksigner`; ferramentas devem estar no PATH ou passadas por argumento).
Os scripts usam a biblioteca padrao Python. Nao ha pip install obrigatorio.

## 1. Identificar e preservar o estado original

Execute a partir da raiz do projeto (nao de docs/), com somente o aparelho desejado conectado. Se houver
mais de um, acrescente `--serial SEU_SERIAL` aos scripts e `adb -s SEU_SERIAL`.

```sh
adb devices -l
adb shell 'su -mm -c id'
adb shell 'su -mm -c "getprop ro.product.model; getprop ro.product.device; getprop ro.build.version.oneui; getprop ro.build.version.sdk"'
python3 scripts/native.py collect --state snapshots/preinstall
```

A coleta preserva XML, APKs, dumps, identidade, Settings e estado de componentes.
Use uma pasta NOVA por transacao. `snapshots/before` e reservado como imutavel.
**Snapshots sao privados e nao devem ser enviados ao GitHub.**

Antes de atualizar o APK, o caso testado tambem preservou dados CE/DE com
proprietarios e metadados SELinux e conferiu hashes de bancos durante pausa breve:

```sh
python3 scripts/backup-private-data.py --state snapshots/preinstall
```

Esse utilitario e deliberadamente restrito ao appId 10132 observado no teste.
Se o UID diferir, ele para: audite o aparelho, nao substitua o numero a esmo.
O arquivo gerado contem dados pessoais. Guarde-o somente em local privado.

## 2. Samsung Smart Suggestions

O 7.3.21.9 instalado neste S23 era uma variante sem GenUIService, onboarding
completo e widget nos manifests/classes. Flags sozinhas nao adicionam codigo.
Por isso foi feita uma atualizacao genuina Samsung para 7.3.30.9.

Fonte de referencia para obter o APK por conta propria:
https://www.apkmirror.com/apk/samsung-electronics-co-ltd/samsungsmartsuggestions/

Nao afirmamos que 7.3.30.9 seja a versao mais recente disponivel. E a versao
efetivamente testada, arm64-v8a, minSdk 34, targetSdk 36.
Hashes e certificado: [VERSIONS.md](VERSIONS.md).

```sh
apksigner verify --verbose --print-certs /caminho/SmartSuggestions.apk
aapt2 dump badging /caminho/SmartSuggestions.apk
```

Compare com o APK ativo coletado, nao com uma imagem de ROM offline.
Mesmo certificado nao prova compatibilidade de bancos e dependencias.

O instalador exige revisao de compatibilidade, hash, assinatura e backup. Nao
fornecemos um review.json com verificacoes verdadeiras inventadas para terceiros.
Consulte [Instalacao](INSTALLATION.md) antes de usar o instalador.

No teste, o metodo foi `resetprop ro.build.official.release false` seguido de
`pm install -r -d -i com.sec.android.app.samsungapps -S TAMANHO`, com APK por stdin.
O script restaurou official.release para seu valor original no finally e
confirmou o hash instalado. O resetprop real era `/data/adb/ksu/bin/resetprop`.
Nao e necessario manter essa propriedade falsa depois da instalacao.

## 3. Habilitar Brief e Nudge

Depois da instalacao auditada, faca OUTRA coleta: a transacao das flags deve
registrar o APK novo e nao misturar rollback de APK com rollback de configuracao.

```sh
python3 scripts/native.py collect --state snapshots/features
python3 scripts/native.py plan --state snapshots/features --profile profiles/s23-oneui9-tested.json
sh scripts/enable-nowbrief-s23.sh --state snapshots/features --profile profiles/s23-oneui9-tested.json
```

O `plan` nao altera o telefone. O enable verifica novamente o estado real.
Se o XML, APK ou build divergir, pare para auditar: nao afrouxe o perfil.

Flags utilizadas e verificadas no Rune do APK testado:

| Floating Feature | Valor |
| --- | --- |
| SEC_FLOATING_FEATURE_COMMON_CONFIG_AI_VERSION | 20263 |
| SEC_FLOATING_FEATURE_FRAMEWORK_SUPPORT_PERSONALIZED_DATA_CORE | TRUE |
| SEC_FLOATING_FEATURE_FRAMEWORK_CONFIG_NOW_NUDGE_VERSION | 2 |
| SEC_FLOATING_FEATURE_GENAI_CONFIG_LLM_VERSION | 1.70 |

O LLM V3 verifica a parte decimal textual; nao compare 0.81 e 1.70 como floats.
A flag nao instala modelos nem garante que funcoes LLM estejam operacionais.
SUPPORT_AI_BRIEF_FOR_UT e SUPPORT_NOW_BRIEF nao foram necessarias nesta ativacao.
O perfil registra os componentes reais e as chaves `sss_enabled` e
`now_nudge_setting`. Nao habilita Activities inventadas ou consentimentos de IA.

O script faz bind de uma copia em /data/local/tmp, verifica namespace de init
e visibilidade nos consumidores e reinicia processos selecionados. Nao escreve
na particao e nao reinicia zygote automaticamente.

### Se a tela abrir incompleta ou o botao nao responder

No teste, o arquivo correto estava visivel, mas o processo ainda usava flags
antigas em cache. Force-stop nao bastou. Depois de conferir init, rollback,
hashes e namespace, executamos UMA vez:

```sh
adb shell 'su -mm -c "sync; setprop ctl.restart zygote"'
```

**Isso e um reinicio amplo do ambiente Android e interrompe apps/audio.** Nao
repita em loop nem execute com atividades importantes em andamento. Espere a
interface voltar e confirme novamente o bind e a estabilidade. Se nao voltar,
nao dispare reinicios sucessivos. O KernelSU soft reboot tambem preservou o bind
no nosso teste; nao prometemos isso para qualquer ROM ou implementacao.

Depois, abra o onboarding ORIGINAL e prossiga na interface:

```sh
adb shell 'su -mm -c "am start -W -n com.samsung.android.smartsuggestions/.feature.aisuggestion.ui.onboarding.OnboardingActivity"'
```

Conceda voce mesmo as permissoes e consentimentos apresentados. No caso testado,
o botao "Iniciar Now brief" passou a responder e gerou os cards reais.

## 4. Now Bar e GenUI

Veja [Now Bar](NOW_BAR.md). Nao pule a auditoria de permissao e bind, mas
**nao instale um bridge quando a permissao ja esta concedida**.
Neste S23, o AODService e SystemUI compartilham UID 10048 e o GenUI conectou
nativamente apos atualizar o Smart Suggestions. Nenhum bridge foi instalado.

## 5. Notification Highlights - separado

Nao ativado neste aparelho. O pacote `com.samsung.android.offline.languagemodel`
estava ausente. Nao instalamos Language Core arbitrario, nao marcamos consentimento
e nao tratamos flags como substituto de modelos/dependencias.
O script separado mantem suas verificacoes; esta etapa nao e requisito para os
cards de clima do Brief que foram confirmados.

## Validacao real

- Brief: onboarding responsivo, cards carregados e atualizados; nao apenas menu.
- Nudge: testar sugestoes em apps compativeis; menu nao comprova funcionamento.
- Widget: adicionar pelo launcher e verificar atualizacao; registro nao basta.
- Now Bar: bind, dados nao nulos e cartao VISIVEL; repetir bloquear/desbloquear.
- Highlights: modelos/idioma e notificacao realmente resumida, com consentimento.

Diagnostico somente leitura (pasta de saida nova):

```sh
python3 scripts/diagnose-nowbar.py --output diagnostics/nowbar
python3 scripts/native.py logs --state snapshots/features
```

Logs podem conter notificacoes e dados pessoais. Nao publique dumps crus.
O resumo sanitizado dos resultados esta em [evidence/RESULTS.md](../../evidence/RESULTS.pt-BR.md).

## Rollback

```sh
sh scripts/rollback-nowbrief-s23.sh --state snapshots/features
```

Restaura mount, componentes e Settings da transacao. **Nao rebaixa o APK nem
desfaz escolhas feitas manualmente no onboarding.** Cache antigo tambem pode
exigir reinicio controlado para refletir a restauracao. Veja
[Rollback](ROLLBACK.md) antes de mexer em APK ou dados privados.

## Termux e desenvolvimento

Instrucoes locais: [Termux](TERMUX.md).
Testes offline: `PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'`.
O pacote publico contem somente arquivos revisados. Snapshots, APKs e dados
privados devem permanecer fora do Git. Veja [a revisao de publicacao](../maintainers/PUBLISHING.md).
