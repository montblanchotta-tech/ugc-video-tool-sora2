# Sora 2 API統合動画生成SaaS

OpenAIの最新動画生成技術「Sora 2」を使用した高品質動画生成SaaSアプリケーションです。

## 🚀 主な機能

### Sora 2動画生成
- **プロンプトベース動画生成**: テキストプロンプトから高品質な動画を生成
- **参照画像対応**: 初期フレームとして画像を指定可能
- **複数モデル対応**: Sora 2（高速）とSora 2 Pro（高品質）
- **複数解像度**: 1280x720、720x1280、1024x1024
- **動画リミックス**: 既存動画の編集・変更機能

### 従来のUGC動画生成
- **AIモデル生成**: 商品画像からAIモデルを生成
- **音声合成**: スクリプトから自然な音声を生成
- **リップシンク**: AIモデルと音声を同期

## 📋 前提条件

- Python 3.8以上
- OpenAI APIキー（Sora 2 APIアクセス権限）
- その他のAPIキー（従来機能用）

## 🛠️ セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の設定を行います：

```env
# OpenAI API（Sora 2動画生成）
OPENAI_API_KEY=your_openai_api_key_here

# Webhook設定
WEBHOOK_SECRET=your_webhook_secret_here

# その他のAPIキー（従来機能用）
GEMINI_API_KEY=your_gemini_api_key_here
FISHAUDIO_API_KEY=your_fishaudio_api_key_here
HEDRA_API_KEY=your_hedra_api_key_here

# アプリケーション設定
HOST=0.0.0.0
PORT=8003
DEBUG=True
```

### 3. アプリケーションの起動

```bash
python main.py
```

または

```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

## 🎬 Sora 2 API エンドポイント

### 動画生成

```http
POST /api/sora/generate-video
Content-Type: application/json

{
  "prompt": "美しい夕日の中で、若い女性が新しいスマートフォンを紹介しながら、ゆっくりと歩いている動画",
  "model": "sora-2",
  "size": "1280x720",
  "seconds": "4",
  "input_reference_url": "https://example.com/image.jpg"
}
```

### ステータス確認

```http
GET /api/sora/video-status/{video_id}
```

### 動画リミックス

```http
POST /api/sora/remix-video
Content-Type: application/json

{
  "video_id": "video_abc123",
  "prompt": "コーギーを猫に変えて下さい"
}
```

### 動画リスト取得

```http
GET /api/sora/videos
```

### 動画ダウンロード

```http
GET /api/sora/download-video/{video_id}
GET /api/sora/download-thumbnail/{video_id}
GET /api/sora/download-spritesheet/{video_id}
```

### 動画削除

```http
DELETE /api/sora/videos/{video_id}
```

## 🔗 Webhook設定

Sora 2 APIは動画生成完了時にWebhookを送信します。

### Webhookエンドポイント

```http
POST /api/sora/webhook
```

### Webhookペイロード例

```json
{
  "id": "evt_abc123",
  "object": "event",
  "created_at": 1758941485,
  "type": "video.completed",
  "data": {
    "id": "video_abc123"
  }
}
```

### OpenAI側でのWebhook設定

OpenAIの設定ページで以下のURLをWebhookエンドポイントとして登録してください：

```
https://your-domain.com/api/sora/webhook
```

## 📝 プロンプトのコツ

### 効果的なプロンプトの書き方

1. **ショットの種類を指定**
   - ワイドショット、クローズアップ、パン、ティルトなど

2. **被写体を具体的に**
   - 人物、商品、環境を詳細に記述

3. **動作を明確に**
   - 歩く、微笑む、商品を見る、話すなど

4. **背景と環境**
   - 公園、オフィス、家、街など

5. **照明条件**
   - 夕日、朝の光、室内照明、自然光など

### プロンプト例

```
芝生の公園で、黄金色の夕焼け空を背景に、赤い凧を飛ばす子どものワイドショット。カメラがゆっくりと上方にパンしていく様子
```

```
木製テーブルの上にある湯気を立てるコーヒーカップのクローズアップ。ブラインド越しの朝の光、柔らかな被写界深度
```

## ⚠️ 制限事項

### コンテンツ制限
- 18歳未満向けの適切なコンテンツのみ対象
- 著作権で保護されたキャラクターや楽曲は拒否される
- 著名人などの実在の人物は生成できない
- 現在、人間の顔を含む画像の入力は拒否される

### 技術的制限
- 動画の長さは最大16秒
- 生成には数分から数十分かかる場合があります
- APIの利用料金が発生します

## 💰 料金について

Sora 2の動画生成は秒数ごとの課金となります：

- **Sora 2**: より高速で柔軟性に優れる
- **Sora 2 Pro**: より高品質でプロダクションレベル

詳細な料金は[OpenAIの料金ページ](https://openai.com/pricing)をご確認ください。

## 🔧 開発・カスタマイズ

### 新しいモデルの追加

`services/sora_service.py`を編集して、新しい動画生成モデルを追加できます。

### UIのカスタマイズ

`templates/index.html`を編集して、フロントエンドのUIをカスタマイズできます。

### APIの拡張

`main.py`に新しいエンドポイントを追加して、機能を拡張できます。

## 📚 参考資料

- [OpenAI Sora 2 API Documentation](https://platform.openai.com/docs/guides/video-generation)
- [Sora 2 Prompting Guide](https://cookbook.openai.com/examples/sora/sora2_prompting_guide)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 サポート

問題が発生した場合は、以下をご確認ください：

1. APIキーが正しく設定されているか
2. インターネット接続が安定しているか
3. OpenAI APIの利用制限に達していないか

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
