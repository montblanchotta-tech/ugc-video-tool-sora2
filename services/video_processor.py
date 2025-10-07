import os
import uuid
import asyncio
from typing import Optional, Dict, Any
# moviepyを無効化（問題があるため）
VideoFileClip = None
ImageClip = None
CompositeVideoClip = None
concatenate_videoclips = None
from PIL import Image
import logging

from .nanobanana_service import GeminiImageService
from .fishaudio_service import FishAudioService
from .hedra_service import HedraService
from config import Config

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.gemini = GeminiImageService()
        self.fishaudio = FishAudioService()
        self.hedra = HedraService()
        
        # ディレクトリを作成
        self._ensure_directories()
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        for directory in [Config.UPLOAD_DIR, Config.OUTPUT_DIR, Config.TEMP_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    async def generate_ugc_video(self, 
                               product_image_path: str,
                               script: str,
                               model_style: str = "realistic",
                               voice_style: str = "friendly") -> Dict[str, Any]:
        """
        UGC動画を生成するメイン処理
        """
        video_id = str(uuid.uuid4())
        temp_dir = os.path.join(Config.TEMP_DIR, video_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            logger.info(f"Starting UGC video generation for video {video_id}")
            logger.info(f"Product image path: {product_image_path}")
            logger.info(f"Script: {script}")
            logger.info(f"Model style: {model_style}")
            logger.info(f"Voice style: {voice_style}")
            
            # ステップ1: モデル画像生成
            logger.info(f"Step 1: Generating model image for video {video_id}")
            logger.info(f"Product image path: {product_image_path}")
            logger.info(f"Product image exists: {os.path.exists(product_image_path)}")
            
            try:
                model_image_path = await self.gemini.generate_model_with_product(
                    product_image_path, model_style
                )
                logger.info(f"Gemini API returned: {model_image_path}")
            except Exception as e:
                logger.error(f"Exception in Gemini API call: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Gemini API exception: {str(e)}"}
            
            if not model_image_path:
                logger.error(f"Failed to generate model image for video {video_id} - Gemini returned None")
                return {"success": False, "error": "Failed to generate model image - Gemini returned None"}
            
            logger.info(f"Model image generated successfully: {model_image_path}")
            
            # ステップ2: 音声生成
            logger.info(f"Step 2: Generating voice for video {video_id}")
            audio_path = await self.fishaudio.generate_voice(script, voice_style)
            
            if not audio_path:
                logger.error(f"Failed to generate voice for video {video_id}")
                return {"success": False, "error": "Failed to generate voice"}
            
            logger.info(f"Voice generated successfully: {audio_path}")
            
            # ステップ3: ファイルを準備
            logger.info(f"Step 3: Preparing files for video {video_id}")
            final_model_image_path = os.path.join(temp_dir, "model_image.jpg")
            final_audio_path = os.path.join(temp_dir, "audio.wav")
            
            # 画像ファイルをコピー
            model_copied = await self.gemini.download_image(model_image_path, final_model_image_path)
            # 音声ファイルをコピー
            audio_copied = await self.fishaudio.download_audio(audio_path, final_audio_path)
            
            if not model_copied or not audio_copied:
                logger.error(f"Failed to prepare generated files for video {video_id}")
                return {"success": False, "error": "Failed to prepare generated files"}
            
            logger.info(f"Files prepared successfully for video {video_id}")
            
            # ステップ4: リップシンク動画生成
            logger.info(f"Step 4: Creating lipsync video for video {video_id}")
            lipsync_video_path = await self.hedra.create_lipsync_video(final_model_image_path, final_audio_path)
            
            if not lipsync_video_path:
                logger.error(f"Failed to create lipsync video for video {video_id}")
                return {"success": False, "error": "Failed to create lipsync video"}
            
            logger.info(f"Lipsync video created successfully: {lipsync_video_path}")
            
            # ステップ5: 最終動画をコピー
            logger.info(f"Step 5: Preparing final video for video {video_id}")
            final_video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")
            video_copied = await self.hedra.download_video(lipsync_video_path, final_video_path)
            
            if not video_copied:
                logger.error(f"Failed to prepare final video for video {video_id}")
                return {"success": False, "error": "Failed to prepare final video"}
            
            logger.info(f"Final video prepared successfully: {final_video_path}")
            
            # ステップ6: 動画の後処理（オプション）
            logger.info(f"Step 6: Post-processing video {video_id}")
            processed_video_path = await self._post_process_video(final_video_path, video_id)
            
            logger.info(f"Video post-processing completed: {processed_video_path}")
            
            # サムネイル生成
            thumbnail_path = await self._generate_thumbnail(processed_video_path, video_id)
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": f"/outputs/{os.path.basename(processed_video_path)}",
                "thumbnail_url": f"/outputs/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
            }
            
        except Exception as e:
            logger.error(f"Error generating UGC video {video_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"動画生成に失敗しました: {str(e)}"}
        
        finally:
            # 一時ファイルをクリーンアップ
            await self._cleanup_temp_files(temp_dir)
    
    async def _post_process_video(self, video_path: str, video_id: str) -> str:
        """
        動画の後処理（品質向上、エフェクト追加など）
        """
        try:
            if VideoFileClip is None:
                # moviepyが利用できない場合は元のファイルをそのまま返す
                logger.warning("MoviePy not available, skipping post-processing")
                return video_path
                
            # 動画を読み込み
            video = VideoFileClip(video_path)
            
            # 基本的な品質向上処理
            processed_video = video.resize(height=1080) if video.h < 1080 else video
            
            # 出力パス
            processed_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_processed.mp4")
            
            # 動画を書き出し
            processed_video.write_videofile(
                processed_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # リソースを解放
            video.close()
            processed_video.close()
            
            return processed_path
            
        except Exception as e:
            logger.error(f"Error in post-processing: {str(e)}")
            return video_path  # 処理に失敗した場合は元のファイルを返す
    
    async def _generate_thumbnail(self, video_path: str, video_id: str) -> str:
        """
        動画からサムネイルを生成
        """
        try:
            if VideoFileClip is None:
                # moviepyが利用できない場合はダミーサムネイルを作成
                logger.warning("MoviePy not available, creating dummy thumbnail")
                thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
                
                # ダミーサムネイルファイルを作成
                with open(thumbnail_path, 'w') as f:
                    f.write("dummy thumbnail")
                
                return thumbnail_path
                
            video = VideoFileClip(video_path)
            
            # 動画の中間フレームをサムネイルとして使用
            thumbnail_time = video.duration / 2
            thumbnail = video.get_frame(thumbnail_time)
            
            # PIL画像に変換
            thumbnail_image = Image.fromarray(thumbnail)
            
            # サムネイルパス
            thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
            
            # サムネイルを保存
            thumbnail_image.save(thumbnail_path, "JPEG", quality=85)
            
            video.close()
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            # エラーの場合もダミーサムネイルを作成
            try:
                thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
                with open(thumbnail_path, 'w') as f:
                    f.write("error thumbnail")
                return thumbnail_path
            except:
                return ""
    
    async def _cleanup_temp_files(self, temp_dir: str):
        """
        一時ファイルをクリーンアップ
        """
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
    
    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        動画生成のステータスを取得
        """
        try:
            video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_processed.mp4")
            if not os.path.exists(video_path):
                video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")
            
            if os.path.exists(video_path):
                thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
                return {
                    "status": "completed",
                    "video_path": video_path,
                    "thumbnail_path": thumbnail_path if os.path.exists(thumbnail_path) else None
                }
            else:
                return {"status": "processing"}
                
        except Exception as e:
            logger.error(f"Error getting video status: {str(e)}")
            return {"status": "error", "message": str(e)}
