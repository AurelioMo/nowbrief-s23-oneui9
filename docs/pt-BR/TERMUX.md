# Uso pelo Termux

Os scripts suportam `--termux` para executar `su -mm -c` localmente, sem ADB.
O Python precisa estar instalado e o Termux autorizado no KernelSU.
Mantenha esta pasta no armazenamento privado do Termux, nao em pasta publica.

Exemplos, somente depois das verificacoes descritas no README:

Com Git e Python instalados no Termux, baixe a pasta e autorize o Termux no
KernelSU. O `run.sh` usa o mesmo procedimento, sem ADB:

```sh
pkg install git python
git clone https://github.com/AurelioMo/nowbrief-s23-oneui9.git
cd nowbrief-s23-oneui9
export NOWBRIEF_TERMUX=1
sh run.sh status
# Somente com APK compativel instalado e XML original correspondente ao perfil:
sh run.sh activate snapshots/features-01
sh run.sh open-brief
sh run.sh open-nudge
```

Para a correcao biometrica e auditoria de APK, `apksigner` precisa funcionar
localmente. O wrapper nao instala ferramentas nem pula essa verificacao.

```sh
python3 scripts/native.py collect --termux --state snapshots/features
python3 scripts/native.py plan --termux --state snapshots/features --profile profiles/s23-oneui9-tested.json
sh scripts/enable-nowbrief-s23.sh --termux --state snapshots/features --profile profiles/s23-oneui9-tested.json
python3 scripts/diagnose-nowbar.py --termux --output diagnostics/nowbar
sh scripts/rollback-nowbrief-s23.sh --termux --state snapshots/features
```

O fluxo Termux completo nao foi executado nesta validacao; os testes reais foram
pelo computador com ADB. Ferramentas Android Build Tools de macOS/Linux desktop
nao sao automaticamente executaveis no Termux. Para auditoria e instalacao de
APK com aapt2/apksigner, prefira o computador ou prepare ferramentas compativeis.
Nao remova as verificacoes para contornar ferramenta ausente.
