"""
Vercel用のAPIハンドラー
Sora 2 API統合動画生成SaaS
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os
import asyncio
import uuid
import logging
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    VideoRequest, VideoResponse, APIResponse,
    SoraVideoRequest, SoraVideoResponse, SoraVideoRemixRequest,
    VideoListResponse, WebhookEvent
)
from services.video_processor import VideoProcessor
from services.sora_service import SoraService
from config import Config

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UGC動画作成ツール", version="1.0.0")

# 動画プロセッサーインスタンス
video_processor = VideoProcessor()
sora_service = SoraService()

# 進行状況を保存するための辞書
progress_store: Dict[str, Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """メインページを表示"""
    try:
        # Vercel用の静的ファイルパス
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template error: {e}")
        return HTMLResponse(content="<h1>UGC動画作成ツール</h1><p>アプリケーションが起動しています。</p>")

# ========== Sora 2 API エンドポイント ==========

@app.post("/api/sora/generate-video", response_model=SoraVideoResponse)
async def generate_sora_video(
    sora_request: SoraVideoRequest,
    background_tasks: BackgroundTasks
):
    """Sora 2 APIを使用して動画を生成"""
    try:
        # 参照画像の処理
        input_reference = None
        if sora_request.input_reference_url:
            try:
                import requests
                response = requests.get(sora_request.input_reference_url)
                if response.status_code == 200:
                    from io import BytesIO
                    input_reference = BytesIO(response.content)
            except Exception as e:
                logger.warning(f"Failed to load reference image: {e}")
        
        # Sora 2 APIで動画生成を開始
        result = await sora_service.generate_video_from_prompt(
            prompt=sora_request.prompt,
            model=sora_request.model,
            size=sora_request.size,
            seconds=sora_request.seconds,
            input_reference=input_reference
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        video_id = result["video_id"]
        
        # 進行状況を保存
        progress_store[video_id] = {
            "status": result["status"],
            "progress": result["progress"],
            "message": "Sora 2で動画生成中...",
            "model": result["model"],
            "size": result["size"],
            "seconds": result["seconds"],
            "created_at": result["created_at"]
        }
        
        # バックグラウンドで進行状況を監視
        background_tasks.add_task(
            monitor_sora_video_generation,
            video_id
        )
        
        return SoraVideoResponse(
            video_id=video_id,
            status=result["status"],
            progress=result["progress"],
            message="Sora 2で動画生成を開始しました",
            model=result["model"],
            size=result["size"],
            seconds=result["seconds"],
            created_at=result["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error starting Sora video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sora/video-status/{video_id}", response_model=SoraVideoResponse)
async def get_sora_video_status(video_id: str):
    """Sora 2動画生成のステータスを取得"""
    try:
        if video_id not in progress_store:
            raise HTTPException(status_code=404, detail="Video ID not found")
        
        status_info = progress_store[video_id]
        return SoraVideoResponse(
            video_id=video_id,
            status=status_info["status"],
            progress=status_info["progress"],
            message=status_info.get("message"),
            video_url=status_info.get("video_url"),
            thumbnail_url=status_info.get("thumbnail_url"),
            spritesheet_url=status_info.get("spritesheet_url"),
            model=status_info.get("model", "sora-2"),
            size=status_info.get("size", "1280x720"),
            seconds=status_info.get("seconds", "4"),
            created_at=status_info.get("created_at", 0),
            completed_at=status_info.get("completed_at"),
            expires_at=status_info.get("expires_at"),
            error=status_info.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Sora video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sora/videos", response_model=VideoListResponse)
async def list_sora_videos():
    """Sora 2で生成した動画のリストを取得"""
    try:
        result = await sora_service.list_videos()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return VideoListResponse(
            videos=result["videos"],
            total_count=len(result["videos"])
        )
        
    except Exception as e:
        logger.error(f"Error listing Sora videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "message": "UGC動画作成ツール with Sora 2 API is running on Vercel"}

# ========== ヘルパー関数 ==========

async def monitor_sora_video_generation(video_id: str):
    """Sora 2動画生成の進行状況を監視"""
    try:
        while True:
            status_result = await sora_service.poll_video_status(video_id)
            
            if not status_result["success"]:
                logger.error(f"Error polling video status: {status_result['error']}")
                break
            
            status = status_result["status"]
            progress = status_result["progress"]
            
            # 進行状況を更新
            if video_id in progress_store:
                progress_store[video_id]["status"] = status
                progress_store[video_id]["progress"] = progress
                progress_store[video_id]["completed_at"] = status_result.get("completed_at")
                progress_store[video_id]["expires_at"] = status_result.get("expires_at")
                
                if status == "completed":
                    progress_store[video_id]["message"] = "動画生成が完了しました"
                    
                    # Vercelではファイルダウンロードは制限があるため、URLのみ保存
                    progress_store[video_id]["video_url"] = f"/api/sora/download-video/{video_id}"
                    progress_store[video_id]["thumbnail_url"] = f"/api/sora/download-thumbnail/{video_id}"
                    progress_store[video_id]["spritesheet_url"] = f"/api/sora/download-spritesheet/{video_id}"
                    
                    break
                elif status == "failed":
                    progress_store[video_id]["message"] = "動画生成に失敗しました"
                    progress_store[video_id]["error"] = status_result.get("error")
                    break
            
            # 2秒待機してから再ポーリング
            await asyncio.sleep(2)
            
    except Exception as e:
        logger.error(f"Error monitoring Sora video generation: {str(e)}")
        if video_id in progress_store:
            progress_store[video_id]["status"] = "failed"
            progress_store[video_id]["message"] = f"監視中にエラーが発生しました: {str(e)}"

# Vercel用のハンドラー
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "index:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
