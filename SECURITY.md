# Seguranca e privacidade

Estas ferramentas usam root e podem interromper o ambiente Android. Nao sao
um produto oficial Samsung e nao oferecem garantia de compatibilidade universal.

## Nao publique dados do telefone

Snapshots, bancos, dumps, screenshots e logcat podem conter informacoes privadas.
O .gitignore ajuda, mas NAO remove dados ja rastreados pelo Git e nao substitui
uma revisao. Use a lista fechada PUBLIC_FILES.json e o verificador antes do push.
O verificador identifica classes comuns de vazamento; nao garante detectar tudo.

Se uma credencial real tiver sido publicada, remova-a da divulgacao, revogue-a
no servico correspondente e trate tambem o historico do repositorio. Apagar
apenas o arquivo da ultima versao nao elimina a exposicao.

## Relatar uma vulnerabilidade

Nao abra uma issue publica contendo tokens, dados pessoais ou um exploit contra
um aparelho de terceiro. Quando o repositorio remoto oferecer relato privado de
vulnerabilidades, use esse canal; se nao houver, contate o mantenedor sem incluir
dados sensiveis na primeira mensagem. Nenhum endereco ou canal privado foi
inventado nesta preparacao local.

## Limites de seguranca

Nao desabilitamos autenticacao biometrica, SELinux, verificacao de assinatura ou
consentimento de IA para declarar sucesso. Um bind mount temporario ainda altera
o que o sistema enxerga e merece backup, journal e teste de restauracao.
