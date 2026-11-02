#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1

tool() {
    script=$1
    shift
    if [ "${NOWBRIEF_TERMUX:-0}" = 1 ]; then
        python3 "scripts/$script" "$@" --termux
    else
        python3 "scripts/$script" "$@"
    fi
}

remote() {
    if [ "${NOWBRIEF_TERMUX:-0}" = 1 ]; then
        su -mm -c "$1"
    else
        adb shell "su -mm -c '$1'"
    fi
}

need_state() {
    if [ "$#" -ne 1 ] || [ -z "$1" ]; then
        echo 'Informe uma pasta de snapshot. Exemplo: sh run.sh activate snapshots/features-01' >&2
        exit 2
    fi
}

action=${1:-help}
[ "$#" -eq 0 ] || shift
case "$action" in
    help|--help|-h)
        cat <<'HELP'
Uso: sh run.sh COMANDO [ARGUMENTOS]
  status                     Root, modelo, versao e estado atual (somente leitura)
  snapshot PASTA             Backup de XML, APKs, Settings e componentes
  backup-data PASTA           Backup privado CE/DE antes de atualizar APK
  install ARGUMENTOS         Instalador auditado; veja docs/pt-BR/INSTALLATION.md
  activate PASTA_NOVA         Coleta + plano + ativacao com perfil estrito
  biometric-fix PASTA_NOVA    Overlay especifico; apenas se a permissao faltar
  onboarding                 Abre a configuracao inicial original do Now Brief
  open-brief                 Abre os cards originais, sem aceitar consentimentos
  open-nudge                 Abre as configuracoes originais do Nudge
  diagnose PASTA_NOVA         Coleta privada de logs e conexao GenUI/Now Bar
  nudge-policy               Confere a politica no APK ativo, sem modificar dados
  rollback PASTA             Restaura flags, componentes e Settings da transacao
  rollback-biometric PASTA   Restaura o XML de assinatura da transacao

Computador: ADB + Python 3, um aparelho ou ANDROID_SERIAL definido.
Termux: NOWBRIEF_TERMUX=1 sh run.sh COMANDO ...
Nao instala APK sem revisao, nao reinicia Android e nao faz flash.
HELP
        ;;
    status)
        remote 'id; getprop ro.product.model; getprop ro.build.version.oneui; getprop ro.build.version.sdk; dumpsys package com.samsung.android.smartsuggestions | grep -E "versionName=|SET_BIOMETRIC_DIALOG_ADVANCED: granted="; settings get global sss_enabled; settings get global now_nudge_setting; grep -E "COMMON_CONFIG_AI_VERSION|SUPPORT_PERSONALIZED_DATA_CORE|CONFIG_NOW_NUDGE_VERSION|GENAI_CONFIG_LLM_VERSION" /system/etc/floating_feature.xml'
        ;;
    snapshot)
        need_state "$@"
        tool native.py collect --state "$1"
        ;;
    backup-data)
        need_state "$@"
        tool backup-private-data.py --state "$1"
        ;;
    install)
        tool install-smart-suggestions.py "$@"
        ;;
    activate)
        need_state "$@"
        tool native.py collect --state "$1"
        tool native.py plan --state "$1" --profile profiles/s23-oneui9-tested.json
        tool native.py enable --state "$1" --profile profiles/s23-oneui9-tested.json
        echo 'Flags aplicadas. Guarde esta pasta para rollback. Nao houve reinicio do Android.'
        ;;
    biometric-fix|rollback-biometric)
        need_state "$@"
        operation=apply
        [ "$action" != rollback-biometric ] || operation=rollback
        tool signature_permissions.py "$operation" --state "$1"
        ;;
    onboarding)
        remote 'am start -W -f 0x10008000 -n com.samsung.android.smartsuggestions/.feature.aisuggestion.ui.onboarding.OnboardingActivity'
        ;;
    open-brief)
        remote 'am start -W -f 0x10008000 -n com.samsung.android.smartsuggestions/.feature.aisuggestion.ui.activity.SuggestionUiContentActivity'
        ;;
    open-nudge)
        remote 'am start -W -n com.samsung.android.smartsuggestions/.nudgesettings.NudgeMainSettingsActivity'
        ;;
    diagnose)
        need_state "$@"
        tool diagnose-nowbar.py --output "$1"
        ;;
    nudge-policy)
        tool diagnose_nudge.py "$@"
        ;;
    rollback)
        need_state "$@"
        tool native.py rollback --state "$1"
        ;;
    *)
        echo 'Comando desconhecido. Use: sh run.sh help' >&2
        exit 2
        ;;
esac
