<div align="center">

# Samsung Now Brief no Galaxy S23

**Portugues | [English](README.md)**

**Recursos nativos. One UI 9. KernelSU. Alteracoes reversiveis.**

Adaptacao experimental do procedimento de Furkan-Tsc para o **S23 comum**.
Sem aplicativo substituto, sem flash e sem escrita fisica na particao do sistema.

[Guia completo](docs/pt-BR/GUIDE.md) | [Resultados reais](evidence/RESULTS.pt-BR.md) | [Problemas conhecidos](docs/pt-BR/KNOWN_ISSUES.md) | [Rollback](docs/pt-BR/ROLLBACK.md)

</div>

---

> **Leia antes de executar:** validado em um SM-S911B/dm1q com uma ROM especifica.
> Now Brief funciona com cards reais. A abertura de Dados pessoais foi corrigida.
> **Now Nudge contextual e cartao visivel na Now Bar ainda nao foram validados.**
> Este projeto nao e um desbloqueio universal nem um instalador de um clique.

## Tutorial: faca nesta ordem

**No seu aparelho ja ativado, nao repita a instalacao.** Use `status`,
`open-brief`, `open-nudge` ou `diagnose`. Para uma instalacao nova, siga abaixo.
O perfil atende somente ao build e aos hashes da tabela deste README.

### 1. Baixe os scripts

No computador, instale Git, Python 3, ADB e Android SDK Build Tools
(`aapt2` e `apksigner` no PATH). Autorize depuracao USB e root no KernelSU.

```sh
git clone https://github.com/AurelioMo/nowbrief-s23-oneui9.git
cd nowbrief-s23-oneui9
adb devices -l
sh run.sh status
```

Deixe somente o S23 desejado conectado. Se houver varios, defina
`ANDROID_SERIAL` com o serial mostrado pelo seu ADB antes de continuar.

### 2. Smart Suggestions: confira antes de instalar

O caso testado usa **7.3.30.9 / 733009000**, arm64-v8a, minSdk 34.
Obtenha o APK voce mesmo na [pagina do Smart Suggestions](https://www.apkmirror.com/apk/samsung-electronics-co-ltd/samsungsmartsuggestions/).
Nao distribuimos APK Samsung. Se essa versao ja estiver instalada com o hash
testado, pule para a etapa 3. Versao diferente exige auditoria, nao downgrade cego.

```sh
sh run.sh snapshot snapshots/preinstall-01
sh run.sh backup-data snapshots/preinstall-01
apksigner verify --verbose --print-certs /caminho/SmartSuggestions.apk
aapt2 dump badging /caminho/SmartSuggestions.apk
```

Compare assinatura, hash e dependencias com o APK coletado. Prepare o registro
de revisao conforme [INSTALLATION.md](docs/pt-BR/INSTALLATION.md). **Nao marque
verificacoes como verdadeiras sem realiza-las.** Depois da revisao:

```sh
sh run.sh install \
  --state snapshots/preinstall-01 \
  --apk /caminho/SmartSuggestions.apk \
  --sha256 9e09fc48d5a85c0f1c98a811e2554255988601c9b6e54865e22b07f12fc1d378 \
  --source URL_EXATA_DE_ONDE_BAIXOU \
  --review /caminho/review.json \
  --reversible-trial
```

O instalador aplica temporariamente o bypass de build do guia original,
restaura `ro.build.official.release` e verifica o APK realmente instalado.
Nao burla assinatura e nao ativa CorePatch.

### 3. Ative as Floating Features e os componentes

```sh
sh run.sh activate snapshots/features-01
```

Esse comando **executa**, nao apenas explica: faz backup novo, valida o perfil,
prepara XML, aplica bind mount, configura Brief/Nudge e habilita os componentes
previstos. Se recusar hash, build ou XML, pare; nao remova a protecao.
Anote `snapshots/features-01`: e o estado necessario para desfazer a alteracao.

### 4. Corrija Dados pessoais, somente se a permissao faltar

Se `status` mostrar `SET_BIOMETRIC_DIALOG_ADVANCED: granted=true`, pule.
Se o aplicativo fechar com essa SecurityException no ambiente testado:

```sh
sh run.sh biometric-fix snapshots/biometric-01
```

Isso monta uma allowlist especifica depois de comparar os certificados do
Android e do APK. Nao remove nem contorna a autenticacao biometrica.

### 5. Atualize o cache e abra os recursos

Os scripts **nao reiniciam o Android automaticamente**. No caso testado,
force-stop nao atualizou o cache herdado do zygote. Depois de concluir as
etapas necessarias e salvar seu trabalho, faca **um soft reboot pelo KernelSU**.
Alternativa avancada usada no teste, apenas com rollback e mounts conferidos:

```sh
adb shell 'su -mm -c "sync; setprop ctl.restart zygote"'
```

Isso interrompe todos os apps. Nao execute os dois metodos nem repita em loop.
Depois que a interface voltar:

```sh
sh run.sh status
sh run.sh onboarding
sh run.sh open-nudge
```

Toque em **Iniciar Now brief** e conceda pessoalmente as permissoes desejadas.
Depois da configuracao inicial, use `sh run.sh open-brief` para abrir os cards.
No Nudge, confira o interruptor **Ativado**. No launcher, pressione a tela inicial,
abra **Widgets** e procure **Now brief** para adicionar o widget.

### 6. Now Bar: confira a conexao nativa

Em Configuracoes, procure **Now bar** e ligue **Now brief**. Depois:

```sh
sh run.sh diagnose diagnostics/nowbar-01
sh run.sh nudge-policy
```

No caso testado, GenUI ja conecta ao SystemUI, sem instalar bridge.
O cartao depende tambem da politica e do horario do Brief; bind nao prova cartao
visivel. Se nao conectar, siga [NowBarFix.md](docs/pt-BR/NOW_BAR.md), nao instale um APK
de bridge ou transplante assinaturas indiscriminadamente.
Notification Highlights continua separado e nao foi ativado neste aparelho.

**O Nudge deveria bloquear?** A politica embutida exclui explicitamente Google
Mensagens e a conversa do WhatsApp nesse caminho de autofill. O codigo separa
esse bloqueio da ativacao da feature e do idioma. Nao ha prova de que seja um
erro especifico do S23; remover a lista amplia telas elegiveis para coleta e
nao garante sugestoes. Nao a removemos. Veja [diagnostico do Nudge](docs/pt-BR/NUDGE.md).

### Desfazer

Use exatamente as pastas criadas na sua execucao:

```sh
sh run.sh rollback snapshots/features-01
# Apenas se voce aplicou a correcao biometrica:
sh run.sh rollback-biometric snapshots/biometric-01
```

O rollback de flags nao desfaz a atualizacao do APK ou escolhas do onboarding.
O overlay biometrico precisa de reinicio controlado para reavaliar permissoes.
Leia [ROLLBACK.md](docs/pt-BR/ROLLBACK.md) antes de tentar restaurar APK/dados.
Para Termux: [comandos locais](docs/pt-BR/TERMUX.md).

---

## Status real

Ultima validacao: **2 de novembro de 2026**. Uma opcao aparecer no menu nao e
considerada prova de funcionamento.

| Recurso | Estado | Evidencia do teste |
| --- | --- | --- |
| Now Brief | Confirmado | Onboarding responsivo, cards, clima horario e aviso UV |
| Dados pessoais | Corrigido | Permissao biometrica concedida; abertura confirmada pelo usuario |
| GenUI / Now Bar | Conexao confirmada | Binder recebido e `hasBound=true` para SystemUI |
| Now Brief na tela bloqueada | Nao apareceu no reteste | GenUI conectado, mas nenhum cartao visivel no bloqueio |
| Now Nudge contextual | Nao comprovado | Teste no Google Mensagens bloqueado pela politica interna do APK |
| Widget | Conteudo e toque confirmados | Adicionado na home, carregou dados e abriu o Brief; atualizacao periodica pendente |
| Notification Highlights | Nao ativado | Language Core e modelos nao comprovados |

Veja o [resumo sanitizado](evidence/RESULTS.pt-BR.md). Nao publicamos capturas ou logs
brutos que possam expor nomes, notificacoes, contas ou outros dados pessoais.

## Aparelho e software testados

| Item | Ambiente observado |
| --- | --- |
| Modelo / codinome | Galaxy S23 **SM-S911B / dm1q** |
| Sistema | **One UI 9.0 / Android 17 / API 37** |
| Compilacao / patch | S911BXXUAGZIF / 2026-10-05 |
| Smart Suggestions | 7.3.21.9 original -> **7.3.30.9 / 733009000** |
| AODService ativo | **8.9.66.1**, em `/data/app` |
| Root | KernelSU, `su -mm -c` funcional |

O perfil fixa identidade, hashes do XML e APKs. **Uma recusa do script e uma
protecao, nao um convite para remover a verificacao.** Outra ROM ou variante
exige nova auditoria. [Versoes, certificado e hashes](docs/pt-BR/VERSIONS.md).

LSPosed e Zygisk Next ja estavam instalados. Nao foi necessario instalar
CorePatch ou habilitar bypass de assinatura neste teste. Nao afirmamos que os
modulos encontrados sejam requisitos universais.

## Mapa do projeto

| Caminho | Conteudo |
| --- | --- |
| `run.sh` | Comandos de instalacao, ativacao, diagnostico e rollback |
| `docs/pt-BR/` | Guias em portugues, incluindo Nudge e Now Bar |
| `docs/en/` | Guias em ingles |
| `docs/README.md` | Indice bilingue por assunto |
| `scripts/` | Ferramentas de auditoria, ativacao, diagnostico e rollback |
| `profiles/` | Perfil restrito ao ambiente testado |
| `evidence/` | Resumo sanitizado e resultado de testes offline |
| `tests/` | Testes offline, separados das ferramentas do aparelho |
| `docs/maintainers/` | Revisao e limites de publicacao |
| `PUBLIC_FILES.json` | Lista fechada dos arquivos do pacote publico |

## Validacao local e contribuicoes

Estes comandos nao usam ADB nem alteram o telefone:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_publication.py
```

Os testes offline validam partes dos scripts, **nao substituem testes funcionais
no aparelho**. Para relatar problemas, leia [CONTRIBUTING.md](CONTRIBUTING.md).
Para dados sensiveis e vulnerabilidades, veja [SECURITY.md](SECURITY.md).

## Creditos, autoria e distribuicao

Baseado no trabalho de **[Furkan-Tsc](https://github.com/Furkan-Tsc/Guide-to-Enabling-Now-Brief-and-Now-Nudge-on-S23Ultra)**.
Referencia consultada: `b080f44e48bdff31901c69ee31a9b115736ffe95`.

Adaptacao independente para S23 comum/One UI 9; sem afiliacao ou endosso da
Samsung, do KernelSU ou do autor original. Recursos e aplicativos continuam
sendo da Samsung.

A consulta ao repositorio original nao retornou uma licenca declarada.
Este pacote inclui creditos e referencia, **nao uma copia integral do repositorio
ou de seus APKs**. O codigo e a documentacao originais desta adaptacao sao
distribuidos sob a [licenca MIT](LICENSE). Ela nao se aplica aos aplicativos
Samsung nem ao material de terceiros referenciado; nao presumimos permissao
para relicencia-los.
