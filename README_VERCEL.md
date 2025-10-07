# Vercelデプロイメントガイド

Sora 2 API統合動画生成SaaSアプリケーションのVercelデプロイメント手順です。

## 🚀 デプロイ手順

### 1. Vercel CLIのインストール

```bash
npm install -g vercel
```

### 2. プロジェクトの準備

```bash
cd /Users/montb/ugc_video_tool
```

### 3. Vercelにログイン

```bash
vercel login
```

### 4. 環境変数の設定

VercelダッシュボードまたはCLIで以下の環境変数を設定：

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# その他のAPIキー
GEMINI_API_KEY=your_gemini_api_key_here
FISHAUDIO_API_KEY=your_fishaudio_api_key_here
HEDRA_API_KEY=your_hedra_api_key_here

# Webhook設定
WEBHOOK_SECRET=your-webhook-secret-here

# アプリケーション設定
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### 5. デプロイ実行

```bash
vercel --prod
```

### 6. 環境変数の設定（CLI経由）

```bash
vercel env add OPENAI_API_KEY
# プロンプトでAPIキーを入力

vercel env add GEMINI_API_KEY
vercel env add FISHAUDIO_API_KEY
vercel env add HEDRA_API_KEY
vercel env add WEBHOOK_SECRET
```

## 📁 ファイル構成

```
├── api/
│   └── index.py          # Vercel用APIハンドラー
├── templates/
│   └── index.html        # Web UI
├── services/
│   ├── sora_service.py   # Sora 2 APIサービス
│   └── video_processor.py # 動画処理サービス
├── models.py             # データモデル
├── config.py             # 設定
├── vercel.json           # Vercel設定
├── requirements.txt      # Python依存関係
└── package.json          # Node.js設定
```

## ⚙️ Vercel設定の詳細

### vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.11"
  },
  "functions": {
    "api/index.py": {
      "maxDuration": 300
    }
  }
}
```

## 🔧 制限事項と注意点

### Vercelの制限

1. **実行時間**: 最大300秒（5分）
2. **ファイルサイズ**: アップロード/ダウンロード制限あり
3. **ストレージ**: 一時的なファイル保存のみ
4. **メモリ**: 1GB制限

### 対応策

1. **動画生成**: Sora 2 APIは非同期処理のため、ステータスポーリングを使用
2. **ファイル保存**: Vercelでは永続的なファイル保存ができないため、外部ストレージを使用することを推奨
3. **進行状況**: メモリ内の辞書で管理（再起動時はリセット）

## 🌐 デプロイ後の確認

### 1. ヘルスチェック

```bash
curl https://your-app.vercel.app/health
```

### 2. API文書

```
https://your-app.vercel.app/docs
```

### 3. メインUI

```
https://your-app.vercel.app/
```

## 🔄 継続的デプロイ

GitHubリポジトリと連携して自動デプロイを設定：

1. GitHubリポジトリにコードをプッシュ
2. VercelダッシュボードでプロジェクトをGitHubと連携
3. 自動デプロイが有効になる

## 📊 モニタリング

Vercelダッシュボードで以下を監視：

- 関数の実行時間
- エラーレート
- リクエスト数
- レスポンス時間

## 🛠️ トラブルシューティング

### よくある問題

1. **タイムアウト**: 動画生成が5分以内に完了しない場合
2. **メモリ不足**: 大きなファイル処理時のエラー
3. **環境変数**: APIキーが正しく設定されていない

### 解決方法

1. **タイムアウト**: より短い動画を生成するか、外部処理サービスを使用
2. **メモリ**: ファイルサイズを制限
3. **環境変数**: Vercelダッシュボードで再確認

## 💡 最適化のヒント

1. **キャッシュ**: 静的ファイルのキャッシュ設定
2. **CDN**: VercelのCDNを活用
3. **エッジ関数**: 軽量な処理はエッジ関数で実行

## 🔗 関連リンク

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI on Vercel](https://fastapi.tiangolo.com/deployment/serverless/)