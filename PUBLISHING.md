# Revisao de publicacao

## Pode ir para o GitHub

- README e guias escritos para esta adaptacao, com creditos e limitacoes.
- Scripts Python/shell, testes offline e perfil de hashes do ambiente testado.
- Resumo sanitizado dos testes e problemas conhecidos.
- Regras de privacidade, modelo de issue e verificacoes automatizadas.
- PUBLIC_FILES.json e SHA256SUMS.json: lista fechada e integridade dos arquivos.

Build, modelo e hashes publicos identificam a compatibilidade. O perfil nao
contem serial, IMEI, conta ou dados pessoais do aparelho.

## Nao vai

- Nenhum APK Samsung, APK do bridge, firmware, imagem de particao ou modelo LLM.
- Nenhum snapshot, backup CE/DE, banco, WAL/SHM, heap ou arquivo de configuracao privado.
- Nenhum logcat/dumpsys bruto, captura de tela, notificacao, contato ou conversa.
- Nenhum token do GitHub/conta Samsung, chave privada, keystore ou credencial.
- Nenhum serial ADB, IMEI, caminho pessoal do computador ou arquivo de ambiente.
- Nenhuma decompilacao integral ou copia do codigo do repositorio original.
- Nenhum cache Python, grafo de trabalho ou artefato gerado por ferramentas locais.

## Destino e licenca

O GitHub CLI foi verificado e tem autenticacao ativa. Nenhum token foi exportado
para a pasta. Destino autorizado: repositorio publico
`AurelioMo/nowbrief-s23-oneui9`, branch `main`. A publicacao usa somente a
lista explicita de arquivos aprovados, nunca a pasta privada de trabalho.
O codigo e a documentacao originais desta adaptacao usam [MIT](LICENSE).
A licenca nao abrange aplicativos Samsung ou material de terceiros.

O repositorio de Furkan-Tsc nao retornou uma licenca declarada na consulta de
2026-11-02. Mantemos atribuicao e referencia; nao redistribuimos seu repositorio
integral nem presumimos autorizacao para relicencia-lo.

## Verificacoes

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
python3 tools/check_publication.py
```

O verificador compara os arquivos com uma lista explicita, procura padroes comuns
de segredo/dado privado, verifica links locais e hashes e recusa symlinks.
Nao e uma garantia absoluta de ausencia de dados sensiveis. Revise o diff antes
de qualquer push. Nunca use git add . sem conferir exatamente o que sera enviado.

Para gerar um arquivo de distribuicao SOMENTE com os arquivos aprovados:

```sh
python3 tools/check_publication.py --archive /caminho/fora/do/projeto/nowbrief-source.zip
```

O arquivo nao pode ficar dentro do projeto e nao sobrescreve um arquivo existente.
Esse comando cria um ZIP local; nao envia nada ao GitHub.
