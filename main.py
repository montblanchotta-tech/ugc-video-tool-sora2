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

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
templates = Jinja2Templates(directory="templates")

# 動画プロセッサーインスタンス
video_processor = VideoProcessor()
sora_service = SoraService()

# 進行状況を保存するための辞書
progress_store: Dict[str, Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """メインページを表示"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template error: {e}")
        # フォールバックとして直接HTMLを返す
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)

@app.post("/api/generate-video", response_model=VideoResponse)
async def generate_video(
    video_request: VideoRequest,
    background_tasks: BackgroundTasks
):
    """UGC動画を生成するAPIエンドポイント"""
    try:
        video_id = str(uuid.uuid4())
        
        # 初期ステータスを設定
        progress_store[video_id] = {
            "status": "pending",
            "progress": 0,
            "message": "動画生成を開始しています..."
        }
        
        # バックグラウンドで動画生成を実行
        background_tasks.add_task(
            process_video_generation,
            video_id,
            video_request
        )
        
        return VideoResponse(
            video_id=video_id,
            status="pending",
            progress=0,
            message="動画生成を開始しました"
        )
        
    except Exception as e:
        logger.error(f"Error starting video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video-status/{video_id}", response_model=VideoResponse)
async def get_video_status(video_id: str):
    """動画生成のステータスを取得"""
    try:
        if video_id not in progress_store:
            raise HTTPException(status_code=404, detail="Video ID not found")
        
        status_info = progress_store[video_id]
        return VideoResponse(
            video_id=video_id,
            status=status_info["status"],
            progress=status_info["progress"],
            message=status_info.get("message"),
            video_url=status_info.get("video_url"),
            thumbnail_url=status_info.get("thumbnail_url")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-video/{video_id}")
async def download_video(video_id: str):
    """生成された動画をダウンロード"""
    try:
        # 処理済み動画を探す
        processed_video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_processed.mp4")
        if not os.path.exists(processed_video_path):
            processed_video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")
        
        if not os.path.exists(processed_video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            processed_video_path,
            media_type="video/mp4",
            filename=f"ugc_video_{video_id}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-thumbnail/{video_id}")
async def download_thumbnail(video_id: str):
    """生成されたサムネイルをダウンロード"""
    try:
        thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
        
        if not os.path.exists(thumbnail_path):
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            thumbnail_path,
            media_type="image/jpeg",
            filename=f"thumbnail_{video_id}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-product-image")
async def upload_product_image(file: UploadFile = File(...)):
    """商品画像をアップロード"""
    try:
        # ファイル拡張子をチェック
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in Config.SUPPORTED_IMAGE_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Supported: {Config.SUPPORTED_IMAGE_FORMATS}"
            )
        
        # ファイルを保存
        file_path = os.path.join(Config.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": file_path,
            "file_url": f"/static/uploads/{file.filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_generation(video_id: str, video_request: VideoRequest):
    """バックグラウンドで動画生成を実行"""
    try:
        # ステータスを更新
        progress_store[video_id]["status"] = "processing"
        progress_store[video_id]["progress"] = 10
        progress_store[video_id]["message"] = "モデル画像を生成中..."
        
        # ファイルパスを絶対パスに変換
        import os
        if video_request.product_image_url.startswith('/'):
            # 絶対パスの場合
            product_image_path = video_request.product_image_url
        else:
            # 相対パスの場合、絶対パスに変換
            product_image_path = os.path.join(os.getcwd(), video_request.product_image_url)
        
        # 動画生成を実行
        result = await video_processor.generate_ugc_video(
            product_image_path=product_image_path,
            script=video_request.script,
            model_style=video_request.model_style,
            voice_style=video_request.voice_style
        )
        
        if result["success"]:
            # 成功時のステータス更新
            actual_video_id = result.get("video_id", video_id)  # 実際のvideo_idを取得
            logger.info(f"✓ Video generation completed. Request ID: {video_id}, Actual video ID: {actual_video_id}")
            progress_store[video_id]["status"] = "completed"
            progress_store[video_id]["progress"] = 100
            progress_store[video_id]["message"] = "動画生成が完了しました"
            progress_store[video_id]["video_url"] = f"/api/download-video/{actual_video_id}"
            progress_store[video_id]["thumbnail_url"] = f"/api/download-thumbnail/{actual_video_id}"
            logger.info(f"✓ Download URL set to: /api/download-video/{actual_video_id}")
        else:
            # 失敗時のステータス更新
            progress_store[video_id]["status"] = "failed"
            progress_store[video_id]["progress"] = 0
            progress_store[video_id]["message"] = f"動画生成に失敗しました: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in background video generation: {str(e)}")
        progress_store[video_id]["status"] = "failed"
        progress_store[video_id]["progress"] = 0
        progress_store[video_id]["message"] = f"動画生成中にエラーが発生しました: {str(e)}"

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

@app.post("/api/sora/remix-video", response_model=SoraVideoResponse)
async def remix_sora_video(
    remix_request: SoraVideoRemixRequest,
    background_tasks: BackgroundTasks
):
    """Sora 2で動画をリミックス（編集）"""
    try:
        result = await sora_service.remix_video(
            video_id=remix_request.video_id,
            prompt=remix_request.prompt
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        new_video_id = result["video_id"]
        
        # 進行状況を保存
        progress_store[new_video_id] = {
            "status": result["status"],
            "progress": result["progress"],
            "message": "Sora 2で動画リミックス中...",
            "remixed_from": remix_request.video_id
        }
        
        # バックグラウンドで進行状況を監視
        background_tasks.add_task(
            monitor_sora_video_generation,
            new_video_id
        )
        
        return SoraVideoResponse(
            video_id=new_video_id,
            status=result["status"],
            progress=result["progress"],
            message="Sora 2で動画リミックスを開始しました",
            model="sora-2",
            size="1280x720",
            seconds="4",
            created_at=int(asyncio.get_event_loop().time())
        )
        
    except Exception as e:
        logger.error(f"Error remixing Sora video: {str(e)}")
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

@app.delete("/api/sora/videos/{video_id}")
async def delete_sora_video(video_id: str):
    """Sora 2で生成した動画を削除"""
    try:
        result = await sora_service.delete_video(video_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 進行状況ストアからも削除
        if video_id in progress_store:
            del progress_store[video_id]
        
        return {"success": True, "message": f"Video {video_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting Sora video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sora/download-video/{video_id}")
async def download_sora_video(video_id: str):
    """Sora 2で生成された動画をダウンロード"""
    try:
        video_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}.mp4")
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"sora_video_{video_id}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Sora video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sora/download-thumbnail/{video_id}")
async def download_sora_thumbnail(video_id: str):
    """Sora 2で生成されたサムネイルをダウンロード"""
    try:
        thumbnail_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_thumbnail.jpg")
        
        if not os.path.exists(thumbnail_path):
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            thumbnail_path,
            media_type="image/jpeg",
            filename=f"sora_thumbnail_{video_id}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Sora thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sora/download-spritesheet/{video_id}")
async def download_sora_spritesheet(video_id: str):
    """Sora 2で生成されたスプライトシートをダウンロード"""
    try:
        spritesheet_path = os.path.join(Config.OUTPUT_DIR, f"{video_id}_spritesheet.png")
        
        if not os.path.exists(spritesheet_path):
            raise HTTPException(status_code=404, detail="Spritesheet not found")
        
        return FileResponse(
            spritesheet_path,
            media_type="image/png",
            filename=f"sora_spritesheet_{video_id}.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Sora spritesheet: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== Webhook エンドポイント ==========

@app.post("/api/sora/webhook")
async def sora_webhook(webhook_event: WebhookEvent):
    """Sora 2 Webhook イベントを受信"""
    try:
        logger.info(f"Received webhook: {webhook_event.type} for video {webhook_event.data.get('id')}")
        
        video_id = webhook_event.data.get("id")
        if not video_id:
            logger.warning("Webhook event missing video ID")
            return {"status": "ignored"}
        
        # 進行状況を更新
        if video_id in progress_store:
            if webhook_event.type == "video.completed":
                progress_store[video_id]["status"] = "completed"
                progress_store[video_id]["progress"] = 100
                progress_store[video_id]["message"] = "動画生成が完了しました"
                
                # 動画とサムネイルをダウンロード
                video_download = await sora_service.download_video_content(video_id, "video")
                thumbnail_download = await sora_service.download_video_content(video_id, "thumbnail")
                spritesheet_download = await sora_service.download_video_content(video_id, "spritesheet")
                
                if video_download["success"]:
                    progress_store[video_id]["video_url"] = f"/api/sora/download-video/{video_id}"
                if thumbnail_download["success"]:
                    progress_store[video_id]["thumbnail_url"] = f"/api/sora/download-thumbnail/{video_id}"
                if spritesheet_download["success"]:
                    progress_store[video_id]["spritesheet_url"] = f"/api/sora/download-spritesheet/{video_id}"
                    
            elif webhook_event.type == "video.failed":
                progress_store[video_id]["status"] = "failed"
                progress_store[video_id]["progress"] = 0
                progress_store[video_id]["message"] = "動画生成に失敗しました"
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

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
                    
                    # 動画とサムネイルをダウンロード
                    video_download = await sora_service.download_video_content(video_id, "video")
                    thumbnail_download = await sora_service.download_video_content(video_id, "thumbnail")
                    spritesheet_download = await sora_service.download_video_content(video_id, "spritesheet")
                    
                    if video_download["success"]:
                        progress_store[video_id]["video_url"] = f"/api/sora/download-video/{video_id}"
                    if thumbnail_download["success"]:
                        progress_store[video_id]["thumbnail_url"] = f"/api/sora/download-thumbnail/{video_id}"
                    if spritesheet_download["success"]:
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

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "message": "UGC動画作成ツール with Sora 2 API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )
