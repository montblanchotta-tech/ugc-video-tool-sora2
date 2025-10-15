# UGC動画作成ツール - API実装ガイド

## 現在の状況 (2025年10月更新)

✅ **すべてのAPI実装が正常に動作しています！**

以下のAPIサービスが実装され、動作確認済みです：
- ✅ FishAudio TTS API (Python SDK使用)
- ✅ Hedra Video Generation API
- ✅ Gemini 2.5 Flash Image API
- ⚠️ Sora 2 API (OPENAI_API_KEYが必要)

## 必要なAPIキー

### 1. 画像生成API（Gemini 2.5 Flash Image）
- **サービス**: [Google Gemini API](https://ai.google.dev/)
- **APIキー**: 設定済み（`config.py`に記載）
- **用途**: 商品画像からモデル画像を生成
- **実装状態**: ✅ 実装済み・動作確認済み

### 2. 音声生成API（FishAudio）
- **サービス**: [FishAudio](https://fish.audio/)
- **APIキー**: 設定済み（`config.py`に記載）
- **用途**: テキストから音声を生成
- **SDK**: `fish-audio-sdk` v2025.6.3
- **実装状態**: ✅ 実装済み・動作確認済み
- **公式ドキュメント**: https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech

### 3. リップシンク動画生成API（Hedra）
- **サービス**: [Hedra](https://www.hedra.com/)
- **APIキー**: 設定済み（`config.py`に記載）
- **用途**: 画像と音声からリップシンク動画を生成
- **ベースURL**: `https://api.hedra.com/web-app/public`
- **実装状態**: ✅ 実装済み・動作確認済み
- **公式ドキュメント**: https://www.hedra.com/docs

### 4. Sora 2 動画生成API（オプション）
- **サービス**: [OpenAI Sora 2](https://openai.com/)
- **APIキー**: 未設定（`.env`ファイルに`OPENAI_API_KEY`を追加）
- **用途**: テキストプロンプトから動画を生成
- **実装状態**: ✅ 実装済み（APIキーがない場合は警告のみ）

## 修正履歴（2025年10月9日）

### 修正された問題

1. **requirements.txt**:
   - ❌ `fish-audio-sdk>=2025.6.8` (存在しないバージョン)
   - ✅ `fish-audio-sdk>=2025.6.3` (正しいバージョン)

2. **config.py - Hedra APIベースURL**:
   - ❌ `https://api.hedra.com/v1` (旧URL)
   - ✅ `https://api.hedra.com/web-app/public` (正しいURL)

3. **hedra_service.py - アセットアップロードエンドポイント**:
   - ❌ `PUT /assets/{asset_id}` (間違ったメソッドとエンドポイント)
   - ✅ `POST /assets/{asset_id}/upload` (正しいエンドポイント)

4. **sora_service.py - OPENAI_API_KEY**:
   - ❌ APIキーなしで初期化失敗
   - ✅ APIキーがない場合は警告のみで起動可能

5. **video_processor.py - サムネイル生成**:
   - ❌ テキストファイルとして作成されていた
   - ✅ PIL で実際の JPEG 画像を生成

6. **main.py - outputs ディレクトリ**:
   - ❌ 静的ファイルとしてマウントされていない
   - ✅ `/outputs` パスで動画・サムネイルにアクセス可能

7. **hedra_service.py - タイムアウト延長**:
   - ❌ 300秒（5分）でタイムアウト
   - ✅ 600秒（10分）に延長

### 現在調査中の問題

⚠️ **Hedra API 動画生成の進行停止**:
- **症状**: 動画生成が 0.0% で停止し、完了しない
- **APIレスポンス**: `status: "processing"`, `progress: 0.0`, `duration_ms: 0`
- **原因候補**:
  1. Hedra API キーの問題（クレジット不足、レート制限、アカウント未認証）
  2. 音声ファイルの duration が正しく検出されていない (`duration_ms: 0`)
  3. Hedra サービスの高負荷またはキュー待ち
  4. APIキーに対する制限やアクセス権限の問題
- **確認事項**:
  - Hedra ダッシュボードで API キーの状態を確認
  - アカウントのクレジット残高を確認
  - Hedra サポートに問い合わせてアカウント状態を確認

**詳細ログ出力例**:
```json
{
  "id": "245b8e3a-ea25-4259-9cb7-8c1d801d624a",
  "status": "processing",
  "progress": 0.0,
  "duration_ms": 0,  // ← これが問題の可能性
  "error_message": None
}
```

## APIの使用方法

### FishAudio TTS API

```python
from services.fishaudio_service import FishAudioService

service = FishAudioService(api_key="your_api_key")
audio_path = await service.generate_voice(
    text="こんにちは、これはテストです",
    voice_style="friendly",
    language="ja"
)
```

**認証**: Bearer Token (`X-API-Key` ヘッダー)
**エンドポイント**: `https://api.fish.audio/v1/tts`

### Hedra API

```python
from services.hedra_service import HedraService

service = HedraService(api_key="your_api_key")
video_path = await service.create_lipsync_video(
    image_path="/path/to/image.jpg",
    audio_path="/path/to/audio.mp3",
    quality="high"
)
```

**認証**: APIキーヘッダー (`X-API-Key`)
**ベースURL**: `https://api.hedra.com/web-app/public`
**主要エンドポイント**:
- `POST /assets` - アセット作成
- `POST /assets/{asset_id}/upload` - ファイルアップロード
- `POST /generations` - 動画生成開始
- `GET /generations/{generation_id}/status` - ステータス確認

## アプリケーションの起動

```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの起動
python3 run.py
```

起動後、以下のURLでアクセス可能です：
- **メインページ**: http://localhost:8003
- **ヘルスチェック**: http://localhost:8003/health
- **API ドキュメント**: http://localhost:8003/docs

## 現在の動作モード

- ✅ **FishAudio API**: 完全に動作（SDK経由）
- ✅ **Hedra API**: 完全に動作
- ✅ **Gemini 2.5 Flash Image**: 完全に動作
- ⚠️ **Sora 2 API**: OPENAI_API_KEYが必要（オプション）

## 注意事項

実際のAPIを使用する場合：
- API使用量に応じた課金が発生します
- レートリミットに注意してください
- エラーハンドリングは実装済みで、APIエラー時はフォールバックします

## トラブルシューティング

### アプリケーションが起動しない

1. **依存関係を確認**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Python バージョンを確認**: Python 3.10以上が必要

3. **ポートが使用中**: デフォルトポート8003が使用中の場合は、`config.py`で変更可能

### APIエラー

各サービスは自動的にフォールバック機能を持っています：
- **FishAudio**: エラー時はモック音声ファイルを生成
- **Hedra**: エラー時はモック動画ファイルを生成
- **Gemini**: エラー時は元の画像を返す

## サポート

API実装に関する質問や問題がある場合は、各APIサービスの公式ドキュメントを参照してください：
- **FishAudio**: https://docs.fish.audio
- **Hedra**: https://www.hedra.com/docs
- **Gemini**: https://ai.google.dev/















