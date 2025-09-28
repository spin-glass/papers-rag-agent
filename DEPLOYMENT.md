# Cloud Run デプロイメント設定

このプロジェクトは既存のGitHub Actionsワークフロー（`.github/workflows/deploy.yml`）を拡張して、Cloud Runデプロイ後にREADMEのURLが自動更新されるようになっています。

## 自動更新の仕組み

既存のデプロイワークフローに以下の機能を追加しました：

1. **デプロイ後のURL取得**: `google-github-actions/deploy-cloudrun@v2` の出力 `url` を使用
2. **README自動更新**: デプロイ後に該当セクションを新しいURLで更新
3. **自動コミット**: 変更があった場合のみREADMEをコミット・プッシュ

## 必要な設定

### GitHub Secrets

既存の設定に追加で必要なもの：
- `contents: write` 権限（既に設定済み）

### README URLセクション

以下のコメントブロックがREADME内に必要です：

```markdown
<!-- CLOUDRUN_URL_START -->
🚀 **Live Demo**: [https://your-url.run.app](https://your-url.run.app)
<!-- CLOUDRUN_URL_END -->
```

## カスタマイズ

### URL表示位置の変更

コメントブロック `<!-- CLOUDRUN_URL_START -->` と `<!-- CLOUDRUN_URL_END -->` を任意の場所に移動することで、URL表示位置を調整できます。

### デプロイ設定の変更

既存の `.github/workflows/deploy.yml` で以下を調整可能：

- `SERVICE`: Cloud Runサービス名
- `REGION`: デプロイリージョン  
- `flags`: リソース設定やタイムアウト設定

## トラブルシューティング

### よくある問題

1. **URL更新が動作しない**
   - READMEにコメントブロックが正しく配置されているか確認
   - ワークフローの `contents: write` 権限が設定されているか確認

2. **コミットループ**
   - 変更がない場合はコミットをスキップする仕組みが組み込まれています

### ログの確認

GitHub ActionsのWorkflowsタブ > "Deploy to Cloud Run" で実行ログを確認できます。
