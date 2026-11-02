# Como contribuir

## Relato util, sem expor seus dados

Informe modelo/codinome, Android/API, One UI, build, versao do Smart Suggestions,
AODService e metodo de root. Descreva a tela exata e a sequencia de reproducao.
Separe opcao no menu, abertura, geracao de conteudo e integracao na tela bloqueada.

Nao envie serial ADB, IMEI, contas, contatos, localizacao, mensagens, notificacoes,
tokens, bancos, backups, APKs ou logcat completo. Extraia somente a excecao
necessaria e remova dados pessoais. Nao use screenshots do aparelho sem revisao.

## Mudancas de codigo

- Preserve verificacoes de identidade, hashes, signer, namespace e propriedade do mount.
- Uma nova ROM/versao precisa de auditoria propria; nao afrouxe o perfil existente.
- Inclua teste offline quando houver parser ou transformacao de XML envolvido.
- Nao adicione downloads automaticos de APKs ou hooks indiscriminados de assinatura.
- Nao trate consentimento ou autenticacao como obstaculos a remover.
- Documente efeitos persistentes, reinicios, backup e limite do rollback.
- Declare explicitamente o que foi testado no telefone e o que e apenas inferencia.

## Antes de propor uma alteracao

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_publication.py
```

Alteracoes de arquivos exigem revisao de PUBLIC_FILES.json e SHA256SUMS.json.
Nao atualize a lista automaticamente a partir de uma pasta que contenha dados
coletados: escolha cada arquivo publicavel. Artefatos desconhecidos bloqueiam
o verificador, em vez de serem incluidos silenciosamente.
