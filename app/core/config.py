"""Application configuration"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""
    
    # Slack
    SLACK_TOKEN: str = os.getenv("SLACK_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Notion
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DB_ID: str = os.getenv("NOTION_DB_ID", "")
    
    # Server
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    TZ: str = os.getenv("TZ", "Asia/Tokyo")
    
    # Channel mapping
    CHANNEL_NAME_MAP = {
        "C09PT0PR0MV": "作業-研究",
        "C09QC16DAJY": "作業-epic",
        "C09Q6CYB8MU": "作業-kaggle",
        "C09R2PC3J7J": "作業-個人"
    }
    
    # Channel tag mapping
    CHANNEL_TAG_MAP = {
        "作業-研究": "研究",
        "作業-epic": "EpicAI",
        "作業-kaggle": "kaggle",
        "作業-個人": "個人作業"
    }


settings = Settings()
