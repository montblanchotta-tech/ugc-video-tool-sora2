#!/usr/bin/env python3
"""
UGC動画作成ツールの起動スクリプト
"""

import uvicorn
import os
import sys
from config import Config

def main():
    """アプリケーションを起動"""
    print("🎬 UGC動画作成ツールを起動中...")
    print(f"📍 URL: http://{Config.HOST}:{Config.PORT}")
    print("🛑 停止するには Ctrl+C を押してください")
    
    try:
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=Config.DEBUG,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 アプリケーションを停止しました")
        sys.exit(0)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
