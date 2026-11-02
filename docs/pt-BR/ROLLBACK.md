# Rollback e limites

1. Restaure a transacao das flags com rollback-nowbrief-s23.sh e o snapshot
   correspondente. A transacao de APK deve ser separada.
2. Confira XML, Settings e componentes. O cache do ambiente Android pode exigir
   reinicio controlado mesmo depois da restauracao do arquivo.
3. Se for necessario restaurar o APK original, o instalador aceita:

```sh
python3 scripts/install-smart-suggestions.py --state snapshots/preinstall --restore
```

Esse caminho NAO foi validado no aparelho depois da atualizacao. Android pode
recusar downgrade mesmo com -d, e dados migrados podem ser incompatíveis com a
versao antiga. Nao desinstale ou limpe o pacote para forcar o processo.

O backup CE/DE com metadados esta disponivel somente para quem o coletou. Sua
restauracao precisa de procedimento especifico de UID, SELinux e bancos, com
processos parados. Nao fornecemos um comando generico de sobrescrita dos dados.

Bind mount e propriedades em memoria nao sao equivalentes a alteracoes de APK,
Settings e onboarding: estes ultimos podem persistir depois do reboot.
Nao existe promessa de rollback integral com um clique.
