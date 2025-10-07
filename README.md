# UGC動画作成ツール

商品写真とスクリプトから自動的にUGC（User Generated Content）動画を生成するツールです。

## 機能

- **画像生成**: Gemini 2.0 Flash Expモデルを使用（現在はモック実装）
  - 商品写真からモデル画像を生成予定
  - 注: Gemini APIは画像生成に対応していないため、現在はモック実装を使用
- **音声生成**: FishAudio APIを使用してテキストスクリプトから音声を生成（実装済み）
- **動画生成**: Hedra APIを使用して画像と音声からリップシンク動画を生成（実装済み）
- **Web UI**: 直感的な操作で動画作成が可能
- **リアルタイム進行状況**: 動画生成の進行状況をリアルタイムで表示

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下のAPIキーを設定してください（既に設定済み）：

```env
# API Keys
GEMINI_API_KEY=AIzaSyBrNcN0bw5XnJAKm-hY7AmQkLNHKYDh4v8
FISHAUDIO_API_KEY=039531ba736b44e1b2d382b6a6d23d1d
HEDRA_API_KEY=sk_hedra_c3G3486VsukI24iuTBi0vd9wQ4QvwCMz1BFcwBiNMSiPABZzswAKAw6uL7FfS4wA

# API Endpoints
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
FISHAUDIO_BASE_URL=https://api.fish.audio/v1
HEDRA_BASE_URL=https://api.hedra.com/v1

# Application Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. 仮想環境の作成と依存関係のインストール

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. アプリケーションの起動

```bash
# 仮想環境をアクティベート後
python run.py
```

または

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 使用方法

1. ブラウザで `http://localhost:8000` にアクセス
2. 商品画像をアップロード
3. 動画で話すスクリプトを入力
4. モデルスタイルと音声スタイルを選択
5. 「動画を生成」ボタンをクリック
6. 生成完了まで待機
7. 完成した動画をダウンロード

## API エンドポイント

### POST /api/generate-video
動画生成を開始します。

**リクエスト:**
```json
{
  "product_image_url": "string",
  "script": "string",
  "model_style": "realistic",
  "voice_style": "friendly"
}
```

**レスポンス:**
```json
{
  "video_id": "string",
  "status": "pending",
  "progress": 0,
  "message": "string"
}
```

### GET /api/video-status/{video_id}
動画生成の進行状況を取得します。

**レスポンス:**
```json
{
  "video_id": "string",
  "status": "processing|completed|failed",
  "progress": 50,
  "message": "string",
  "video_url": "string",
  "thumbnail_url": "string"
}
```

### GET /api/download-video/{video_id}
生成された動画をダウンロードします。

### GET /api/download-thumbnail/{video_id}
生成されたサムネイルをダウンロードします。

### POST /api/upload-product-image
商品画像をアップロードします。

## 設定オプション

### モデルスタイル
- `realistic`: リアルなモデル
- `anime`: アニメスタイル
- `artistic`: アーティスティック

### 音声スタイル
- `friendly`: 親しみやすい
- `professional`: プロフェッショナル
- `energetic`: エネルギッシュ
- `calm`: 落ち着いた

## 対応ファイル形式

### 入力画像
- JPG/JPEG
- PNG
- WebP

### 出力動画
- MP4 (H.264)

## トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - `.env`ファイルのAPIキーが正しく設定されているか確認
   - APIキーの権限と有効期限を確認

2. **メモリ不足**
   - 大きな画像ファイルは事前にリサイズしてください
   - システムのメモリ使用量を監視してください

3. **生成時間が長い**
   - 各APIサービスの処理時間に依存します
   - ネットワーク接続を確認してください

### ログの確認

アプリケーションのログは標準出力に表示されます。デバッグ情報が必要な場合は、`DEBUG=True`に設定してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要求は、GitHubのIssueでお知らせください。

## サポート

技術的な質問やサポートが必要な場合は、開発者にお問い合わせください。
