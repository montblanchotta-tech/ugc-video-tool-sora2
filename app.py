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

from models import VideoRequest, VideoResponse, APIResponse
from services.video_processor import VideoProcessor
from config import Config

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UGC動画作成ツール", version="1.0.0")

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 動画プロセッサーインスタンス
video_processor = VideoProcessor()

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

@app.get("/images", response_class=HTMLResponse)
async def view_images(request: Request):
    """生成画像一覧ページを表示"""
    try:
        return templates.TemplateResponse("images.html", {"request": request})
    except Exception as e:
        logger.error(f"Template error: {e}")
        # フォールバックとして直接HTMLを返す
        with open("templates/images.html", "r", encoding="utf-8") as f:
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
            "file_url": f"/static/uploads/{file.filename}",
            "absolute_path": file_path
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
            progress_store[video_id]["status"] = "completed"
            progress_store[video_id]["progress"] = 100
            progress_store[video_id]["message"] = "動画生成が完了しました"
            progress_store[video_id]["video_url"] = f"/api/download-video/{video_id}"
            progress_store[video_id]["thumbnail_url"] = f"/api/download-thumbnail/{video_id}"
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

@app.get("/api/list-generated-images")
async def list_generated_images():
    """生成された画像一覧を取得"""
    try:
        import glob
        image_files = glob.glob(os.path.join(Config.OUTPUT_DIR, "*.png"))
        image_files += glob.glob(os.path.join(Config.OUTPUT_DIR, "*.jpg"))
        
        images = []
        for img_path in sorted(image_files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(img_path)
            file_size = os.path.getsize(img_path)
            mod_time = os.path.getmtime(img_path)
            
            images.append({
                "filename": filename,
                "url": f"/api/view-image/{filename}",
                "size": file_size,
                "modified": mod_time
            })
        
        return {"images": images, "count": len(images)}
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/view-image/{filename}")
async def view_image(filename: str):
    """生成された画像を表示"""
    try:
        image_path = os.path.join(Config.OUTPUT_DIR, filename)
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # ファイル拡張子で画像タイプを判定
        if filename.endswith('.png'):
            media_type = "image/png"
        elif filename.endswith(('.jpg', '.jpeg')):
            media_type = "image/jpeg"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            image_path,
            media_type=media_type,
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "message": "UGC動画作成ツール is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )
