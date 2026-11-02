# Now Nudge: bloqueio intencional nao e permissao quebrada

[Tutorial](../../README.pt-BR.md) | [English](../en/NUDGE.md)

## O que foi comprovado

O APK ativo 7.3.30.9, com hash conferido, inclui uma politica de Nudge autofill
que bloqueia explicitamente Google Mensagens e a Activity de conversa do WhatsApp.
AutofillPolicyManager verifica pacote/Activity separadamente do idioma.
AutofillNudgeManager exige que feature, politica e switch/onboarding permitam
antes de coletar dados por esse caminho.

No teste controlado, o servico recebeu onFillRequest, mas registrou
`isNudgeBlocked: true`, `isLocaleAllowed: true (pt-BR)` e nenhuma sugestao
visivel. Isso comprova o bloqueio desse caminho, nao que todas as integracoes
do Now Nudge estejam desativadas.

## Deveria bloquear?

**Segundo a politica instalada, sim: essas telas foram excluidas explicitamente.**
Nao foi determinado por que: compatibilidade, privacidade, processamento por
outro caminho ou limitacao dessa versao sao hipoteses, nao conclusoes.
Nao ha evidencia de que seja um erro especifico do S23.

Remover entradas ou ativar DISABLE_AUTOFILL_ALLOWLIST amplia as telas elegiveis
para coleta; nao instala modelos, dependencias ou um pipeline compativel.
Por isso nao aplicamos bypass global, repack de APK ou edicao de politica como
se fosse uma correcao comprovada. Nenhum consentimento foi aceito automaticamente.

## Conferir no proprio aparelho, sem modificar

```sh
sh run.sh nudge-policy
```

O script valida identidade da ROM e hash do APK ativo, le a politica embutida
e imprime indicadores das entradas explicitas. Nao salva o APK nem acessa
conversas. Politicas de runtime baixadas podem divergir: confronte com logs do
mesmo app e uma sugestao realmente visivel antes de declarar funcionamento.

Teste funcional deve usar conteudo sintetico em tela elegivel e compativel.
Nao envie mensagens so para testar e nao amplie coleta em conversas privadas.
O rascunho do teste anterior foi apagado.
