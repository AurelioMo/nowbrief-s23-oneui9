# Now Bar: diagnosticar antes de instalar bridge

## Resultado no S23 testado

AODService 8.9.66.1 solicita
`com.samsung.android.smartsuggestions.permission.BIND_GENUI_SERVICE`.
Smart Suggestions 7.3.30.9 declara essa permissao signatureOrSystem e expoe
`.feature.aisuggestion.genui.service.GenUIService`.
O UID compartilhado de AODService/SystemUI recebeu a permissao e conectou.
Nao foi necessario GenUIBridge nem CorePatch.

```sh
python3 scripts/diagnose-nowbar.py --output diagnostics/nowbar
adb shell 'su -mm -c "dumpsys activity services com.samsung.android.smartsuggestions"'
```

Procure GenUIService, binder recebido, hasBound=true e cliente SystemUI.
Um grep sem resultado ou `No services found` isolado nao prova negacao.
Confirme manifests, dumps completos, UID e logs do mesmo APK instalado.

Activity real de configuracao na versao AOD testada:

```sh
adb shell 'su -mm -c "am start -W -n com.samsung.android.app.aodservice/com.samsung.android.app.aod.common.settings.FaceWidgetNowBarSettingsActivity"'
```

Confira o switch Now brief. Nao presuma o mesmo nome em outras versoes.

## Conectado, mas sem cartao

O texto da interface Samsung informa que o Brief permanece na Now Bar ate ser
aberto e reaparece com novos conteudos. A classe instalada
BriefUiPolicyRepositoryImpl acompanha as exibicoes matinal e noturna.
No teste: morning=1, evening=0, now_bar_updatable=0. O callback GenUI retornava
view/type null e o AOD removia o item: nao havia Permission Denial no bind.

Proximo teste: novo periodo/conteudo, antes de abrir o Brief. Ainda falta
comprovar o cartao na tela bloqueada. Nao falsifique horario, nao habilite modo
loja e nao limpe bancos para obter uma captura de sucesso.

## Quando avaliar GenUIBridge

Somente se o servico existe e uma negacao real da permissao foi demonstrada.
O codigo `scripts/GenUIBridge.py` exige a chave privada e certificado que
correspondem ao signer de AOD/SystemUI. Certificado publico sozinho nao assina
um APK novo. Copiar Signing Block nao substitui uma assinatura valida.
Nao distribuimos chave, bridge assinado ou APK de assinatura incompatível.

`scripts/install-bridge.py` verifica signer, manifest, UID e permissao e evita
instalacao se a concessao ja existe. E uma ferramenta experimental: seu caminho
de instalacao nao foi exercitado neste S23, pois nao era necessario.
Para ROM Samsung com chave privada indisponivel, nao invente compatibilidade.

Credito do diagnostico original: Furkan-Tsc, NowBarFix.md no projeto original.
