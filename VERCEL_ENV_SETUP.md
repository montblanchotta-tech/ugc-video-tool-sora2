# Vercel環境変数設定ガイド

## 🔑 必要な環境変数

Vercelダッシュボードで以下の環境変数を設定してください：

### OpenAI API（必須）
```
OPENAI_API_KEY=your_openai_api_key_here
```

### その他のAPIキー
```
GEMINI_API_KEY=your_gemini_api_key_here
FISHAUDIO_API_KEY=your_fishaudio_api_key_here
HEDRA_API_KEY=your_hedra_api_key_here
```

### Webhook設定
```
WEBHOOK_SECRET=your-webhook-secret-here
```

### アプリケーション設定
```
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 📋 Vercelダッシュボードでの設定手順

1. **プロジェクトにアクセス**
   - https://vercel.com/dashboard
   - デプロイしたプロジェクトを選択

2. **環境変数の設定**
   - 「Settings」タブをクリック
   - 「Environment Variables」セクションを選択
   - 「Add New」をクリック

3. **各環境変数を追加**
   - Name: `OPENAI_API_KEY`
   - Value: `your_openai_api_key_here`
   - Environment: `Production`, `Preview`, `Development` すべてにチェック
   - 「Save」をクリック

4. **他の環境変数も同様に追加**

## 🔄 環境変数設定後の再デプロイ

環境変数を追加した後は、自動的に再デプロイが実行されます。
手動で再デプロイする場合は：

1. 「Deployments」タブをクリック
2. 最新のデプロイメントの「⋯」メニューをクリック
3. 「Redeploy」を選択

## ✅ 動作確認

環境変数設定後、以下で動作確認：

1. **ヘルスチェック**
   ```
   https://your-app.vercel.app/health
   ```

2. **API文書**
   ```
   https://your-app.vercel.app/docs
   ```

3. **Sora 2動画生成テスト**
   ```
   POST https://your-app.vercel.app/api/sora/generate-video
   ```

## 🚨 トラブルシューティング

### 環境変数が反映されない場合
- 環境変数追加後、必ず再デプロイを実行
- Environment設定で`Production`にチェックが入っているか確認

### APIキーエラーが発生する場合
- 環境変数の値に余分なスペースや改行がないか確認
- 環境変数名の大文字小文字を確認

### デプロイが失敗する場合
- Vercelダッシュボードの「Functions」タブでエラーログを確認
- `requirements.txt`の依存関係が正しいか確認