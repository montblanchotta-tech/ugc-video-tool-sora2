# UGC動画作成ツール - API実装ガイド

## 現在の状況

現在、すべてのAPI実装がモック実装を使用しています。実際のAPIを使用するには、以下の手順に従ってください。

## 必要なAPIキー

### 1. 画像生成API（Stable Diffusion / Replicate）
- **サービス**: [Replicate](https://replicate.com/)
- **APIキー形式**: `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **用途**: 商品画像からモデル画像を生成

### 2. 音声生成API（FishAudio）
- **サービス**: [FishAudio](https://fish.audio/)
- **APIキー**: 設定済み
- **用途**: テキストから音声を生成

### 3. リップシンク動画生成API（Hedra）
- **サービス**: [Hedra](https://hedra.com/)
- **APIキー**: 設定済み
- **用途**: 画像と音声からリップシンク動画を生成

## 実際のAPIを使用する方法

### ステップ1: 実際のAPIキーを取得

1. **Replicate API**:
   - https://replicate.com/ でアカウント作成
   - API tokens ページでAPIキーを取得
   - `.env`ファイルの`STABLE_DIFFUSION_API_KEY`を更新

2. **FishAudio API**:
   - 既に設定済み
   - エンドポイントとペイロード形式を確認

3. **Hedra API**:
   - 既に設定済み
   - エンドポイントとペイロード形式を確認

### ステップ2: APIエンドポイントの確認

各APIサービスの公式ドキュメントを参照して、正しいエンドポイントとペイロード形式を確認してください：

- **FishAudio**: https://fish.audio/docs/api
- **Hedra**: https://hedra.com/docs/api

### ステップ3: 実装の有効化

実際のAPIを使用するには、各サービスファイル（`services/`ディレクトリ内）のコメントアウトされたAPI実装部分を有効化してください。

## 現在の動作モード

- ✅ **モック実装**: 完全に動作（開発・テスト用）
- ⚠️ **実際のAPI**: 正しいエンドポイントとペイロード形式の設定が必要

## 注意事項

実際のAPIを使用する場合：
- API使用量に応じた課金が発生します
- レートリミットに注意してください
- エラーハンドリングを適切に実装してください

## サポート

API実装に関する質問や問題がある場合は、各APIサービスの公式ドキュメントを参照するか、サポートチームにお問い合わせください。

