# Cloud Run Deployment Guide

このドキュメントでは、Papers RAG Agentを2つのCloud Runサービス（FastAPIとChainlit）にデプロイする方法を説明します。

## アーキテクチャ

### サービス構成

- **FastAPI Service** (`papers-rag-api`): RAG APIサーバー
- **Chainlit Service** (`papers-rag-ui`): ユーザーインターフェース

### デプロイメントフロー

1. FastAPIサービスをデプロイ
1. FastAPIのURLを取得
1. Chainlitサービスをデプロイ（FastAPIのURLを環境変数として設定）

## 必要な設定

### GitHub Secrets

以下のシークレットをGitHubリポジトリに設定してください：

- `GCP_PROJECT_ID`: Google Cloud プロジェクトID
- `GCP_SA_KEY`: サービスアカウントのJSONキー
- `OPENAI_API_KEY`: OpenAI APIキー（必須）

### サービスアカウント権限

サービスアカウントには以下の権限が必要です：

- Cloud Run Admin
- Storage Admin
- Container Registry Service Agent

## ローカル開発

### Docker Composeを使用

```bash
# 両方のサービスを起動
docker-compose up

# 個別に起動
docker-compose up fastapi
docker-compose up chainlit
```

### アクセスURL

- FastAPI: <http://localhost:9000>
- Chainlit: <http://localhost:8000>

## デプロイメント

### 自動デプロイ

`main`または`develop`ブランチにプッシュすると自動的にデプロイされます。

### 手動デプロイ

```bash
# FastAPIサービスのデプロイ
cd fastapi
docker build -t gcr.io/$PROJECT_ID/papers-rag-api .
docker push gcr.io/$PROJECT_ID/papers-rag-api
gcloud run deploy papers-rag-api --image gcr.io/$PROJECT_ID/papers-rag-api

# Chainlitサービスのデプロイ
cd chainlit
docker build -t gcr.io/$PROJECT_ID/papers-rag-ui .
docker push gcr.io/$PROJECT_ID/papers-rag-ui
gcloud run deploy papers-rag-ui --image gcr.io/$PROJECT_ID/papers-rag-ui \
  --set-env-vars "PAPERS_API_BASE=https://papers-rag-api-xxx.run.app"
```

## トラブルシューティング

### よくある問題

1. **ChainlitがFastAPIに接続できない**

   - `PAPERS_API_BASE`環境変数が正しく設定されているか確認
   - FastAPIサービスが起動しているか確認

1. **デプロイが失敗する**

   - GitHub Actionsのログを確認
   - サービスアカウントの権限を確認

1. **メモリ不足エラー**

   - Cloud Runのメモリ設定を増やす（現在2Gi）

### ログの確認

```bash
# FastAPIサービスのログ
gcloud run services logs read papers-rag-api --region=asia-northeast1

# Chainlitサービスのログ
gcloud run services logs read papers-rag-ui --region=asia-northeast1
```
