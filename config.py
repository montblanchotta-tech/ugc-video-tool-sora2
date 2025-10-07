import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAr1BulEINuBtwbLEoMNULjzTwIvLO24B4")
    FISHAUDIO_API_KEY = os.getenv("FISHAUDIO_API_KEY", "039531ba736b44e1b2d382b6a6d23d1d")
    HEDRA_API_KEY = os.getenv("HEDRA_API_KEY", "sk_hedra_c3G3486VsukI24iuTBi0vd9wQ4QvwCMz1BFcwBiNMSiPABZzswAKAw6uL7FfS4wA")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # API Endpoints
    GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    FISHAUDIO_BASE_URL = os.getenv("FISHAUDIO_BASE_URL", "https://api.fish.audio/v1")
    HEDRA_BASE_URL = os.getenv("HEDRA_BASE_URL", "https://api.hedra.com/v1")
    
    # Application Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8003))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # File paths
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    
    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov"]
    
    # Webhook settings
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-webhook-secret-here")
