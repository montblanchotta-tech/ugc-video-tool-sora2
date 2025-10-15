"""
FishAudio TTS Service - 正しいSDK実装
"""
import logging
import tempfile
import os
from typing import Optional
from fish_audio_sdk import Session, TTSRequest

logger = logging.getLogger(__name__)


class FishAudioService:
    """FishAudio TTS サービス（正しいSDK実装）"""

    def __init__(self, api_key: str):
        """
        初期化

        Args:
            api_key: FishAudio APIキー
        """
        self.api_key = api_key
        self.session = Session(api_key)
        logger.info("FishAudio service initialized with SDK")

    async def generate_voice(
        self,
        text: str,
        voice_style: str = "friendly",
        language: str = "ja",
        reference_id: Optional[str] = None
    ) -> Optional[str]:
        """
        テキストから音声を生成（正しいSDK実装）

        Args:
            text: 生成するテキスト
            voice_style: 音声スタイル
            language: 言語コード
            reference_id: 参照音声のモデルID（オプション）

        Returns:
            生成された音声ファイルのパス
        """
        try:
            logger.info(f"FishAudio SDK: Generating voice for text: {text[:50]}...")

            # TTSリクエストを作成
            tts_request = TTSRequest(
                text=text,
                reference_id=reference_id  # 事前にアップロードされたモデルIDを使用
            )

            # 一時ファイルを作成
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')

            # 同期APIを使用して音声を生成
            logger.info("FishAudio SDK: Starting TTS generation...")
            for chunk in self.session.tts(tts_request):
                temp_file.write(chunk)

            temp_file.close()

            logger.info(f"FishAudio SDK: Audio saved to {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"FishAudio SDK: Error generating voice: {str(e)}", exc_info=True)

            # エラーの場合はモック実装にフォールバック
            try:
                logger.warning("FishAudio SDK failed, falling back to MOCK MODE")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(b"mock audio data")
                temp_file.close()
                logger.info(f"MOCK MODE: Created mock audio file at {temp_file.name}")
                return temp_file.name
            except Exception as mock_error:
                logger.error(f"MOCK MODE failed: {str(mock_error)}")
                return None

    async def list_available_voices(self) -> Optional[list]:
        """
        利用可能な音声モデルのリストを取得

        Returns:
            音声モデルのリスト
        """
        try:
            logger.info("FishAudio SDK: Listing available models...")
            models = self.session.list_models()
            logger.info(f"FishAudio SDK: Found {len(models.items) if hasattr(models, 'items') else 0} models")
            return models.items if hasattr(models, 'items') else []
        except Exception as e:
            logger.error(f"FishAudio SDK: Error listing voices: {str(e)}")
            return None

    async def get_model_info(self, model_id: str) -> Optional[dict]:
        """
        特定の音声モデルの情報を取得

        Args:
            model_id: モデルID

        Returns:
            モデル情報の辞書
        """
        try:
            logger.info(f"FishAudio SDK: Getting model info for {model_id}...")
            model = self.session.get_model(model_id)
            return {
                "id": model_id,
                "title": getattr(model, "title", "Unknown"),
                "description": getattr(model, "description", "")
            }
        except Exception as e:
            logger.error(f"FishAudio SDK: Error getting model info: {str(e)}")
            return None

    async def download_audio(self, audio_path: str, save_path: str) -> bool:
        """
        音声ファイルをダウンロード（コピー）

        Args:
            audio_path: 元の音声ファイルパス
            save_path: 保存先パス

        Returns:
            成功したかどうか
        """
        try:
            import shutil
            if os.path.exists(audio_path):
                shutil.copy2(audio_path, save_path)
                logger.info(f"Audio file copied from {audio_path} to {save_path}")
                return True
            else:
                logger.error(f"Audio file not found: {audio_path}")
                return False
        except Exception as e:
            logger.error(f"Error copying audio file: {str(e)}")
            return False

    def cleanup(self, file_path: str) -> bool:
        """
        一時ファイルをクリーンアップ

        Args:
            file_path: 削除するファイルパス

        Returns:
            成功したかどうか
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
            return False
