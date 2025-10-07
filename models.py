from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class VideoRequest(BaseModel):
    product_image_url: str
    script: str
    model_style: Optional[str] = "realistic"
    voice_style: Optional[str] = "friendly"
    duration: Optional[int] = 30

class SoraVideoRequest(BaseModel):
    prompt: str
    model: Optional[str] = "sora-2"  # "sora-2" or "sora-2-pro"
    size: Optional[str] = "1280x720"  # "1280x720", "720x1280", "1024x1024"
    seconds: Optional[str] = "4"
    input_reference_url: Optional[str] = None  # 参照画像のURL

class SoraVideoRemixRequest(BaseModel):
    video_id: str
    prompt: str

class VideoGenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SoraModelType(str, Enum):
    SORA_2 = "sora-2"
    SORA_2_PRO = "sora-2-pro"

class VideoSize(str, Enum):
    SIZE_1280x720 = "1280x720"
    SIZE_720x1280 = "720x1280"
    SIZE_1024x1024 = "1024x1024"

class VideoResponse(BaseModel):
    video_id: str
    status: VideoGenerationStatus
    progress: int
    message: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    spritesheet_url: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    seconds: Optional[str] = None
    created_at: Optional[int] = None
    completed_at: Optional[int] = None
    expires_at: Optional[int] = None
    error: Optional[str] = None

class SoraVideoResponse(BaseModel):
    video_id: str
    status: VideoGenerationStatus
    progress: int
    message: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    spritesheet_url: Optional[str] = None
    model: str
    size: str
    seconds: str
    created_at: int
    completed_at: Optional[int] = None
    expires_at: Optional[int] = None
    error: Optional[str] = None

class VideoListResponse(BaseModel):
    videos: List[Dict[str, Any]]
    total_count: int

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class WebhookEvent(BaseModel):
    id: str
    object: str
    created_at: int
    type: str  # "video.completed" or "video.failed"
    data: Dict[str, Any]
