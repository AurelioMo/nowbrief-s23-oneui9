# Atualizacao auditada do Smart Suggestions

Nao e um instalador universal. Inspecione os manifests, DEX, SDK, ABI, signer,
dependencias e migracao de dados antes da atualizacao. A variante 7.3.21.9 sem
GenUI foi a instalada no nosso caso; nao extrapole somente pelo numero da versao.

O instalador requer `--review` com os campos:

- installed_sha256 e candidate_sha256 correspondentes aos arquivos auditados;
- dependencies_verified e consistent_data_backup_verified;
- data_compatibility_verified para caminho de migracao comprovada;
- alternativamente, --reversible-trial exige room_identities_preserved e
  private-data-backup.json consistente, com hash do arquivo local conferido.

Esses campos sao um registro da revisao humana, nao uma deteccao automatica.
Crie `review.json` FORA do Git, com esta estrutura inicial. Substitua os hashes
e so altere false para true depois de verificar cada requisito:

```json
{
  "installed_sha256": "HASH_DO_APK_ORIGINAL_NO_SNAPSHOT",
  "candidate_sha256": "HASH_DO_APK_BAIXADO",
  "dependencies_verified": false,
  "consistent_data_backup_verified": false,
  "data_compatibility_verified": false,
  "room_identities_preserved": false
}
```

No caminho `--reversible-trial`, `data_compatibility_verified` pode continuar
false, mas as identidades Room e o backup consistente precisam estar comprovados.
Sem essa auditoria, este projeto nao oferece uma instalacao automatica segura
de uma versao diferente do Smart Suggestions.

Identidades Room iguais nao provam toda migracao. Nao os marque true sem provas.
O teste original foi uma tentativa controlada com backup, nao prova universal de
compatibilidade ou de downgrade. Nunca use assinatura incompatível.

Depois de satisfazer os requisitos, a sintaxe e:

```sh
python3 scripts/install-smart-suggestions.py \
  --state snapshots/preinstall \
  --apk /caminho/SmartSuggestions.apk \
  --sha256 HASH_CONFERIDO \
  --source URL_DA_ORIGEM \
  --review /caminho/review.json \
  --reversible-trial
```

Use --reversible-trial somente no caminho correspondente de backup/revisao.
Se surgir outro erro do Package Manager, pare para investigar. Nao repita bypass
de build em erros de assinatura, UID, biblioteca ou armazenamento.

O instalador usa `adb shell -T` para enviar bytes por stdin: exec-out nao foi
adequado para esse envio no ambiente testado. A saida deve ser Success e o APK
ativo deve apresentar o hash esperado. A propriedade de build deve ser restaurada.
