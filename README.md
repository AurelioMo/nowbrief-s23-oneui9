<div align="center">

# Samsung Now Brief no Galaxy S23

**Recursos nativos. One UI 9. KernelSU. Alteracoes reversiveis.**

Adaptacao experimental do procedimento de Furkan-Tsc para o **S23 comum**.
Sem aplicativo substituto, sem flash e sem escrita fisica na particao do sistema.

[Guia completo](docs/GUIDE.md) | [Resultados reais](evidence/RESULTS.md) | [Problemas conhecidos](KNOWN_ISSUES.md) | [Rollback](docs/ROLLBACK.md)

</div>

---

> **Leia antes de executar:** validado em um SM-S911B/dm1q com uma ROM especifica.
> Now Brief funciona com cards reais. A abertura de Dados pessoais foi corrigida.
> **Now Nudge contextual e cartao visivel na Now Bar ainda nao foram validados.**
> Este projeto nao e um desbloqueio universal nem um instalador de um clique.

## O que este projeto faz

Documenta e automatiza partes do desbloqueio do Samsung Smart Suggestions:

1. Audita os APKs reais, assinaturas, versoes, componentes e ambiente root.
2. Atualiza Smart Suggestions **somente quando justificado e compativel**.
3. Apresenta Floating Features modificadas por **bind mount**, com backup.
4. Verifica a conexao nativa **SystemUI/AODService -> GenUIService**.
5. Corrige, no caso testado, a permissao de assinatura que derrubava a biometria
   da Inteligencia de dados pessoais, **sem contornar a autenticacao**.

Nao desenvolve outro Brief, nao simula Now Bar e nao altera assinaturas de APKs.
APKs, firmware e dados do telefone **nao sao redistribuidos**.

## Status real

Ultima validacao: **2 de novembro de 2026**. Uma opcao aparecer no menu nao e
considerada prova de funcionamento.

| Recurso | Estado | Evidencia do teste |
| --- | --- | --- |
| Now Brief | Confirmado | Onboarding responsivo, cards, clima horario e aviso UV |
| Dados pessoais | Corrigido | Permissao biometrica concedida; abertura confirmada pelo usuario |
| GenUI / Now Bar | Conexao confirmada | Binder recebido e `hasBound=true` para SystemUI |
| Now Brief na tela bloqueada | Pendente | Politica matinal ja marcada como exibida; cartao ainda nao comprovado |
| Now Nudge contextual | Pendente | Componentes habilitados; ha politicas por app/Activity a investigar |
| Widget | Parcial | Provider registrado; adicao e atualizacao na home nao testadas |
| Notification Highlights | Nao ativado | Language Core e modelos nao comprovados |

Veja o [resumo sanitizado](evidence/RESULTS.md). Nao publicamos capturas ou logs
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
exige nova auditoria. [Versoes, certificado e hashes](VERSIONS.md).

LSPosed e Zygisk Next ja estavam instalados. Nao foi necessario instalar
CorePatch ou habilitar bypass de assinatura neste teste. Nao afirmamos que os
modulos encontrados sejam requisitos universais.

## Por onde comecar

**Primeiro leia o [guia completo](docs/GUIDE.md).** Ele separa coleta inicial,
backup privado, revisao de APK, ativacao, cache do Android e testes funcionais.

Preparacao no computador: Python 3, ADB, Java e Android SDK Build Tools
(`aapt2` e `apksigner`). Os scripts Python nao exigem pacotes pip externos.
Para Termux, veja os [limites e comandos locais](docs/TERMUX.md).

Comece com uma coleta, sem aplicar modificacoes:

```sh
adb devices -l
adb shell 'su -mm -c id'
python3 scripts/native.py collect --state snapshots/preinstall
```

**Nao execute a instalacao inteira novamente em um telefone ja ativado.**
Nao ha APK incluso nem download automatico; a [instalacao auditada](docs/INSTALLATION.md)
exige verificar procedencia, signer, ABI, SDK, dependencias e dados.

### Duas correcoes importantes do caso testado

**Brief incompleto ou com botao sem resposta:** visibilidade do XML no namespace
nao comprova atualizacao do cache Java. No teste, force-stop nao bastou; um
restart controlado de zygote fez o onboarding inicializar. Ele **interrompe
apps, audio e servicos** e nao e executado automaticamente pelos scripts.

**Dados pessoais com falhas continuas:** a Activity biometrica exigia
`SET_BIOMETRIC_DIALOG_ADVANCED`. A correcao validou o signer real do Android e
do aplicativo e adicionou somente essa autorizacao na allowlist de assinatura,
por bind mount. Nao alterou biometria ou consentimentos. [Procedimento e limites](KNOWN_ISSUES.md).

## Now Bar: nao instale bridge por reflexo

O metodo original inclui o diagnostico e a correcao GenUI. Essa etapa foi mantida,
mas **neste aparelho a permissao ja foi concedida e a conexao nativa funciona**.
Nenhum bridge foi instalado. A ausencia de cartao, sozinha, nao prova falta de
permissao: ha politica de exibicao e consumo de conteudo.

[Leia NowBarFix.md](NowBarFix.md) antes de gerar ou instalar qualquer bridge.
As ferramentas de bridge sao experimentais e exigem assinatura realmente
compativel; copiar um Signing Block nao constitui uma assinatura valida.

## Reversibilidade e cuidados

- Nao fazer flash, editar boot/recovery/vbmeta ou escrever fisicamente em `/system`.
- Nao desabilitar SELinux, limpar dados ou desinstalar componentes criticos.
- **Reboot completo:** pode remover os overlays temporarios, mas nao o APK,
  Settings e escolhas do onboarding. Soft reboot preservou o bind no nosso teste;
  isso nao e garantia para toda ROM.
- **Rollback de flags nao e rollback de APK.** O downgrade e a restauracao integral
  de dados privados nao foram validados. Cada transacao tem seu proprio journal.
- Nao marcar consentimentos de IA ou permissoes pessoais em nome do usuario.

[Leia os procedimentos de rollback](docs/ROLLBACK.md). Nao ha promessa de
restauracao integral com um clique.

## Mapa do projeto

| Caminho | Conteudo |
| --- | --- |
| `docs/GUIDE.md` | Tutorial completo, em ordem de execucao |
| `docs/INSTALLATION.md` | Revisao e instalacao do APK Samsung |
| `KNOWN_ISSUES.md` | Correcao biometrica e limites do Nudge |
| `NowBarFix.md` | Permissao, bind e politica da Now Bar |
| `scripts/` | Ferramentas de auditoria, ativacao, diagnostico e rollback |
| `profiles/` | Perfil restrito ao ambiente testado |
| `evidence/` | Resumo sanitizado e resultado de testes offline |
| `PUBLISHING.md` | O que pode e o que nao pode ser publicado |
| `PUBLIC_FILES.json` | Lista fechada dos arquivos do pacote publico |

## Validacao local e contribuicoes

Estes comandos nao usam ADB nem alteram o telefone:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
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
