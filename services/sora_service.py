import os
import asyncio
import logging
from typing import Dict, Any, Optional, BinaryIO
from openai import OpenAI, AsyncOpenAI
from config import Config

logger = logging.getLogger(__name__)

class SoraService:
    """Sora 2 APIを使用した動画生成サービス"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)
        else:
            logger.warning("OPENAI_API_KEY not set, Sora 2 service will not be available")
            self.openai_client = None
            self.async_client = None
        
    async def generate_video_from_prompt(
        self,
        prompt: str,
        model: str = "sora-2",
        size: str = "1280x720",
        seconds: str = "4",
        input_reference: Optional[BinaryIO] = None
    ) -> Dict[str, Any]:
        """
        Sora 2 APIを使用して動画を生成
        
        Args:
            prompt: 動画生成のプロンプト
            model: 使用するモデル ("sora-2" または "sora-2-pro")
            size: 動画サイズ ("1280x720", "720x1280", "1024x1024" など)
            seconds: 動画の長さ（秒）
            input_reference: 参照画像（オプション）
        
        Returns:
            動画生成結果の辞書
        """
        try:
            logger.info(f"Starting video generation with Sora 2: {prompt[:100]}...")
            
            # 動画生成パラメータを準備
            create_params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "seconds": seconds
            }
            
            # 参照画像がある場合は追加
            if input_reference:
                create_params["input_reference"] = input_reference
            
            # 動画生成を開始
            video = self.openai_client.videos.create(**create_params)
            
            logger.info(f"Video generation started with ID: {video.id}")
            
            return {
                "success": True,
                "video_id": video.id,
                "status": video.status,
                "progress": getattr(video, "progress", 0),
                "model": video.model,
                "size": video.size,
                "seconds": video.seconds,
                "created_at": video.created_at
            }
            
        except Exception as e:
            logger.error(f"Error starting video generation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def poll_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        動画生成のステータスをポーリング
        
        Args:
            video_id: 動画ID
        
        Returns:
            動画ステータスの辞書
        """
        try:
            video = self.openai_client.videos.poll(video_id)
            
            return {
                "success": True,
                "video_id": video.id,
                "status": video.status,
                "progress": getattr(video, "progress", 0),
                "completed_at": video.completed_at,
                "error": video.error,
                "expires_at": video.expires_at
            }
            
        except Exception as e:
            logger.error(f"Error polling video status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_video_content(
        self,
        video_id: str,
        variant: str = "video",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        動画コンテンツをダウンロード
        
        Args:
            video_id: 動画ID
            variant: ダウンロードするコンテンツの種類 ("video", "thumbnail", "spritesheet")
            output_path: 保存先パス（指定しない場合は自動生成）
        
        Returns:
            ダウンロード結果の辞書
        """
        try:
            # コンテンツをダウンロード
            content = self.openai_client.videos.download_content(video_id, variant=variant)
            
            # 出力パスを生成
            if not output_path:
                if variant == "video":
                    output_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")
                elif variant == "thumbnail":
                    output_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
                elif variant == "spritesheet":
                    output_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_spritesheet.png")
            
            # ファイルに保存
            content.write_to_file(output_path)
            
            logger.info(f"Downloaded {variant} to {output_path}")
            
            return {
                "success": True,
                "output_path": output_path,
                "variant": variant,
                "video_id": video_id
            }
            
        except Exception as e:
            logger.error(f"Error downloading video content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_video_with_progress(
        self,
        prompt: str,
        model: str = "sora-2",
        size: str = "1280x720",
        seconds: str = "4",
        input_reference: Optional[BinaryIO] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        進行状況を追跡しながら動画を生成
        
        Args:
            prompt: 動画生成のプロンプト
            model: 使用するモデル
            size: 動画サイズ
            seconds: 動画の長さ
            input_reference: 参照画像
            progress_callback: 進行状況のコールバック関数
        
        Returns:
            完全な動画生成結果の辞書
        """
        try:
            # 動画生成を開始
            result = await self.generate_video_from_prompt(
                prompt=prompt,
                model=model,
                size=size,
                seconds=seconds,
                input_reference=input_reference
            )
            
            if not result["success"]:
                return result
            
            video_id = result["video_id"]
            
            # 進行状況をポーリング
            while True:
                status_result = await self.poll_video_status(video_id)
                
                if not status_result["success"]:
                    return status_result
                
                status = status_result["status"]
                progress = status_result["progress"]
                
                # 進行状況をコールバックで通知
                if progress_callback:
                    progress_callback(progress, status, status_result.get("message"))
                
                if status == "completed":
                    # 動画とサムネイルをダウンロード
                    video_download = await self.download_video_content(video_id, "video")
                    thumbnail_download = await self.download_video_content(video_id, "thumbnail")
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "status": status,
                        "progress": 100,
                        "video_path": video_download.get("output_path"),
                        "thumbnail_path": thumbnail_download.get("output_path"),
                        "model": result["model"],
                        "size": result["size"],
                        "seconds": result["seconds"]
                    }
                
                elif status == "failed":
                    return {
                        "success": False,
                        "error": status_result.get("error", "Video generation failed"),
                        "video_id": video_id
                    }
                
                # 1秒待機してから再ポーリング
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in video generation with progress: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remix_video(
        self,
        video_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        既存の動画をリミックス（編集）
        
        Args:
            video_id: 元の動画ID
            prompt: 編集のプロンプト
        
        Returns:
            リミックス結果の辞書
        """
        try:
            video = self.openai_client.videos.remix(
                video_id=video_id,
                prompt=prompt
            )
            
            logger.info(f"Video remix started with ID: {video.id}")
            
            return {
                "success": True,
                "video_id": video.id,
                "status": video.status,
                "progress": getattr(video, "progress", 0),
                "remixed_from_video_id": video_id
            }
            
        except Exception as e:
            logger.error(f"Error remixing video: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_videos(self) -> Dict[str, Any]:
        """
        過去に生成した動画のリストを取得
        
        Returns:
            動画リストの辞書
        """
        try:
            videos = self.openai_client.videos.list()
            
            video_list = []
            for video in videos.data:
                video_list.append({
                    "id": video.id,
                    "status": video.status,
                    "model": video.model,
                    "size": video.size,
                    "seconds": video.seconds,
                    "created_at": video.created_at,
                    "completed_at": video.completed_at
                })
            
            return {
                "success": True,
                "videos": video_list
            }
            
        except Exception as e:
            logger.error(f"Error listing videos: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_video(self, video_id: str) -> Dict[str, Any]:
        """
        動画を削除
        
        Args:
            video_id: 削除する動画ID
        
        Returns:
            削除結果の辞書
        """
        try:
            result = self.openai_client.videos.delete(video_id)
            
            return {
                "success": True,
                "video_id": video_id,
                "deleted": result.deleted
            }
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
