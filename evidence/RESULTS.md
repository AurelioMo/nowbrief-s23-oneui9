# Resultados sanitizados - 2026-11-02

Este documento e um resumo manual, nao o dump original. Arquivos brutos ficam
privados no projeto de trabalho. Nenhuma captura com nome, notificacao ou dado
pessoal foi incluida no pacote publicavel.

## Confirmado

- APK Samsung 7.3.30.9 aceito pelo Package Manager com signer compativel.
- official.release restaurado, sem hook de assinatura ou SELinux permissivo.
- Flags por bind mount, sem escrita fisica em /system.
- Tela incompleta reproduzida antes do restart de zygote.
- Depois do restart: titulo e botao clicavel; onboarding respondeu.
- Logs: isNowBriefEnabled=true, onboarding=true, rank com sete entradas.
- Tela: saudacao, personalizacao, clima por hora e aviso de UV.
- Usuario confirmou que o Brief funcionou.
- GenUIService: binder recebido, hasBound=true, cliente SystemUI UID10048.
- Depois do soft reboot do usuario: bind preservado e Now Brief disponivel.
- Now Bar Settings: switch ligado, mas politica matinal marcada como exibida.
- Dados pessoais: permissao biometrica concedida por allowlist de assinatura
  direcionada; usuario confirmou abertura. Autenticacao nao foi contornada.

## Nao comprovado

- Cartao visivel na Now Bar/AOD e persistencia em ciclo bloquear/desbloquear.
- Now Nudge contextual, notificacoes de conversas e botao flutuante.
- Widget adicionado e atualizando na home.
- LLM/modelos e Notification Highlights.
- Downgrade e restauracao integral de dados privados.
- Replicacao em outro aparelho/ROM; fluxo Termux completo.

Nao apresentar menu, provider ou bind como prova desses testes funcionais.

## Reteste ADB - 2026-11-02, tarde

- Root, API 37, Smart Suggestions 7.3.30.9 e as quatro flags continuam ativos.
- Permissao SET_BIOMETRIC_DIALOG_ADVANCED permanece concedida.
- Tela Now nudge aberta; interruptor Ativado e pagina de tarefas acessiveis.
- AugmentedAutofillService configurado como servico Samsung; o historico do
  framework registra pedidos, mas isso nao comprova sugestoes contextuais visiveis.
- Brief aberto novamente; cards de personalizacao e clima horario atualizados
  foram vistos na tela. Nao foi necessario reinstalar nem reiniciar Android.
- GenUIService continua conectado ao SystemUI, requested/received/hasBound=true.
- Widget registrado, sem mascaramento; adicao na home ainda nao executada.
- Tela bloqueada acordada e inspecionada: nenhum cartao Now Brief visivel nesse
  teste. Nao chamamos isso de sucesso da Now Bar nem negacao de permissao.
- Nenhum consentimento, biometria ou politica de aplicativos foi contornado.
- `sh run.sh status` executado no aparelho. Help, argumentos e sintaxe do wrapper
  testados offline. O novo wrapper de ativacao nao foi reaplicado ao telefone
  ja ativado; o procedimento interno e o utilizado anteriormente.

As capturas e os dumps desse reteste permanecem somente no diretorio privado.
