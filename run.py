"""
Run script for the Honeypot API.
"""

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print("🍯 Starting Agentic Honey-Pot API...")
    print(f"📡 Host: {settings.api_host}")
    print(f"🔌 Port: {settings.api_port}")
    print(f"🤖 AI Provider: {settings.ai_provider}")
    print("")
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
