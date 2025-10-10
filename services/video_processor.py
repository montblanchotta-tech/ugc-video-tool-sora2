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
        self.fishaudio = FishAudioService(Config.FISHAUDIO_API_KEY)
        self.hedra = HedraService(Config.HEDRA_API_KEY)

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
                               voice_style: str = "friendly",
                               progress_callback=None) -> Dict[str, Any]:
        """
        UGC動画を生成するメイン処理
        """
        video_id = str(uuid.uuid4())
        temp_dir = os.path.join(Config.TEMP_DIR, video_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            logger.info(f"=== Starting UGC video generation for video {video_id} ===")
            logger.info(f"Product image path: {product_image_path}")
            logger.info(f"Script: {script}")
            logger.info(f"Model style: {model_style}")
            logger.info(f"Voice style: {voice_style}")
            
            # ステップ1: モデル画像生成
            logger.info(f"=== Step 1: Generating model image for video {video_id} ===")
            logger.info(f"Product image path: {product_image_path}")
            logger.info(f"Product image exists: {os.path.exists(product_image_path)}")
            
            if progress_callback:
                progress_callback(20, "モデル画像を生成中...")
            
            try:
                model_image_path = await self.gemini.generate_model_with_product(
                    product_image_path, model_style
                )
                logger.info(f"✓ Gemini API returned: {model_image_path}")
            except Exception as e:
                logger.error(f"✗ Exception in Gemini API call: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Gemini API exception: {str(e)}"}
            
            if not model_image_path:
                logger.error(f"✗ Failed to generate model image for video {video_id} - Gemini returned None")
                return {"success": False, "error": "Failed to generate model image - Gemini returned None"}
            
            logger.info(f"✓ Model image generated successfully: {model_image_path}")
            
            # ステップ2: 音声生成
            logger.info(f"=== Step 2: Generating voice for video {video_id} ===")
            if progress_callback:
                progress_callback(40, "音声を生成中...")
            
            audio_path = await self.fishaudio.generate_voice(script, voice_style)
            
            if not audio_path:
                logger.error(f"✗ Failed to generate voice for video {video_id}")
                return {"success": False, "error": "Failed to generate voice"}
            
            logger.info(f"✓ Voice generated successfully: {audio_path}")
            
            # ステップ3: リップシンク動画生成（新しいHedra APIを使用）
            logger.info(f"=== Step 3: Creating lipsync video for video {video_id} ===")
            if progress_callback:
                progress_callback(60, "リップシンク動画を生成中...")
            
            lipsync_video_path = await self.hedra.create_lipsync_video(
                image_path=model_image_path,
                audio_path=audio_path,
                quality="high"
            )

            if not lipsync_video_path:
                logger.error(f"✗ Failed to create lipsync video for video {video_id}")
                return {"success": False, "error": "Failed to create lipsync video"}

            logger.info(f"✓ Lipsync video created successfully: {lipsync_video_path}")

            # ステップ4: 最終動画をコピー
            logger.info(f"=== Step 4: Preparing final video for video {video_id} ===")
            if progress_callback:
                progress_callback(80, "最終動画を準備中...")
            
            final_video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")

            import shutil
            shutil.copy2(lipsync_video_path, final_video_path)

            logger.info(f"✓ Final video prepared successfully: {final_video_path}")
            
            # ステップ5: 動画の後処理（オプション）
            logger.info(f"=== Step 5: Post-processing video {video_id} ===")
            if progress_callback:
                progress_callback(90, "動画を最適化中...")
            
            processed_video_path = await self._post_process_video(final_video_path, video_id)
            
            logger.info(f"✓ Video post-processing completed: {processed_video_path}")
            
            # サムネイル生成
            if progress_callback:
                progress_callback(95, "サムネイルを生成中...")
            
            thumbnail_path = await self._generate_thumbnail(processed_video_path, video_id)
            
            if progress_callback:
                progress_callback(100, "完了！")
            
            logger.info(f"=== ✓ UGC video generation completed successfully for {video_id} ===")
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": f"/outputs/{os.path.basename(processed_video_path)}",
                "thumbnail_url": f"/outputs/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
            }
            
        except Exception as e:
            logger.error(f"✗ Error generating UGC video {video_id}: {str(e)}", exc_info=True)
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
                # moviepyが利用できない場合は実際の画像サムネイルを作成
                logger.warning("MoviePy not available, creating placeholder thumbnail image")
                thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")

                # PILで実際の画像を作成（プレースホルダー）
                from PIL import Image, ImageDraw, ImageFont

                # 1280x720の画像を作成
                img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
                d = ImageDraw.Draw(img)

                # テキストを追加
                text = "UGC Video Thumbnail"
                # フォントサイズを大きく設定
                try:
                    # システムフォントを試す
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                except:
                    # フォントが見つからない場合はデフォルトフォント
                    font = ImageFont.load_default()

                # テキストの位置を計算（中央）
                bbox = d.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((1280 - text_width) // 2, (720 - text_height) // 2)

                d.text(position, text, fill=(255, 255, 255), font=font)

                # 画像を保存
                img.save(thumbnail_path, "JPEG", quality=85)
                logger.info(f"Created placeholder thumbnail image at {thumbnail_path}")

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
            logger.error(f"Error generating thumbnail: {str(e)}", exc_info=True)
            # エラーの場合も実際の画像サムネイルを作成
            try:
                from PIL import Image, ImageDraw
                thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")

                # エラー用の赤い画像を作成
                img = Image.new('RGB', (1280, 720), color=(200, 50, 50))
                d = ImageDraw.Draw(img)
                d.text((500, 350), "Error Thumbnail", fill=(255, 255, 255))
                img.save(thumbnail_path, "JPEG", quality=85)

                logger.info(f"Created error thumbnail image at {thumbnail_path}")
                return thumbnail_path
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback thumbnail: {str(fallback_error)}")
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
