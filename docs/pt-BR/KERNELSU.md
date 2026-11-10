# Modulo KernelSU nativo

O prototipo Xposed foi retirado do caminho de instalacao porque a injecao em processos Samsung pode desestabilizar o aparelho. A implementacao suportada agora e um modulo KernelSU nativo, sem APK e sem hooks.

Instale com:

```sh
sh run.sh kernelsu-install
```

Reinicie uma vez. `post-fs-data.sh` cria o overlay auditado de Floating Features antes dos servicos Android iniciarem. `service.sh` espera o boot terminar, restaura as duas configuracoes do perfil, ativa os quatro componentes necessarios e atualiza apenas os pacotes Samsung.

O modulo fica em `/data/adb/modules/nowbrief-persistent`. Remova ou desative pelo KernelSU Manager para desfazer no proximo reboot. O perfil continua especifico para o build testado SM-S911B / dm1q One UI 9.
