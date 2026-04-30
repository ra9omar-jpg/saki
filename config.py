import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

    # Meta WhatsApp Business Cloud API
    WHATSAPP_ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
    WHATSAPP_PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"]
    WHATSAPP_VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]
    WHATSAPP_APP_SECRET = os.environ["WHATSAPP_APP_SECRET"]
    WHATSAPP_PHONE_NUMBER = os.environ.get("WHATSAPP_PHONE_NUMBER", "+4555228034")

    # WhatsApp Group IDs (internal code → live ID)
    WHATSAPP_GROUP_MARKETING = os.environ["WHATSAPP_GROUP_MARKETING"]
    WHATSAPP_GROUP_RD = os.environ["WHATSAPP_GROUP_RD"]
    WHATSAPP_GROUP_EXPERTISE_REVIEW = os.environ["WHATSAPP_GROUP_EXPERTISE_REVIEW"]
    WHATSAPP_GROUP_TEACHERS = os.environ.get("WHATSAPP_GROUP_TEACHERS", "")
    WHATSAPP_GROUP_COMMUNITY = os.environ.get("WHATSAPP_GROUP_COMMUNITY", "")

    # Microsoft Azure / Graph API
    AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]
    AZURE_CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
    AZURE_CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]

    # Microsoft Teams Channel IDs
    TEAMS_GROUP_ID = os.environ["TEAMS_GROUP_ID"]
    TEAMS_CHANNEL_MARKETING = os.environ["TEAMS_CHANNEL_MARKETING"]
    TEAMS_CHANNEL_RD = os.environ["TEAMS_CHANNEL_RD"]
    TEAMS_CHANNEL_EXPERTISE_REVIEW = os.environ["TEAMS_CHANNEL_EXPERTISE_REVIEW"]
    TEAMS_CHANNEL_TEACHERS = os.environ.get("TEAMS_CHANNEL_TEACHERS", "")

    # Microsoft Planner — bucket IDs
    PLANNER_PLAN_ID_RD = os.environ["PLANNER_PLAN_ID_RD"]
    PLANNER_PLAN_ID_MARKETING = os.environ["PLANNER_PLAN_ID_MARKETING"]
    PLANNER_BUCKET_TODO = os.environ.get("PLANNER_BUCKET_TODO", "")
    PLANNER_BUCKET_IN_PROGRESS = os.environ.get("PLANNER_BUCKET_IN_PROGRESS", "")
    PLANNER_BUCKET_READY_FOR_REVIEW = os.environ["PLANNER_BUCKET_READY_FOR_REVIEW"]
    PLANNER_BUCKET_APPROVED = os.environ.get("PLANNER_BUCKET_APPROVED", "")
    PLANNER_BUCKET_DONE = os.environ.get("PLANNER_BUCKET_DONE", "")

    # Rani
    RANI_WHATSAPP = os.environ["RANI_WHATSAPP"]
    RANI_TEAMS_USER_ID = os.environ["RANI_TEAMS_USER_ID"]
    RANI_NAME = os.environ.get("RANI_NAME", "Rani")

    # Telegram Bot API
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

    # Telegram Group IDs (negative integers as strings, e.g. "-1001234567890")
    TELEGRAM_GROUP_MARKETING = os.environ.get("TELEGRAM_GROUP_MARKETING", "")
    TELEGRAM_GROUP_RD = os.environ.get("TELEGRAM_GROUP_RD", "")
    TELEGRAM_GROUP_EXPERTISE_REVIEW = os.environ.get("TELEGRAM_GROUP_EXPERTISE_REVIEW", "")
    TELEGRAM_GROUP_TEACHERS = os.environ.get("TELEGRAM_GROUP_TEACHERS", "")
    TELEGRAM_GROUP_COMMUNITY = os.environ.get("TELEGRAM_GROUP_COMMUNITY", "")

    # Rani's Telegram user ID (positive integer as string, e.g. "123456789")
    RANI_TELEGRAM_ID = os.environ.get("RANI_TELEGRAM_ID", "")

    # Test Telegram groups
    TEST_TELEGRAM_GROUP_RD = os.environ.get("TEST_TELEGRAM_GROUP_RD", "")
    TEST_TELEGRAM_GROUP_MARKETING = os.environ.get("TEST_TELEGRAM_GROUP_MARKETING", "")
    TEST_TELEGRAM_GROUP_TEACHERS = os.environ.get("TEST_TELEGRAM_GROUP_TEACHERS", "")
    TEST_TELEGRAM_GROUP_EXPERTISE = os.environ.get("TEST_TELEGRAM_GROUP_EXPERTISE", "")

    # Mode: "test" | "shadow" | "live" (initial value — runtime value stored in DB)
    SAKI_MODE = os.environ.get("SAKI_MODE", "test")

    # Test groups — fake WhatsApp groups Rani creates for safe testing
    TEST_WHATSAPP_GROUP_RD = os.environ.get("TEST_WHATSAPP_GROUP_RD", "")
    TEST_WHATSAPP_GROUP_MARKETING = os.environ.get("TEST_WHATSAPP_GROUP_MARKETING", "")
    TEST_WHATSAPP_GROUP_TEACHERS = os.environ.get("TEST_WHATSAPP_GROUP_TEACHERS", "")
    TEST_WHATSAPP_GROUP_EXPERTISE = os.environ.get("TEST_WHATSAPP_GROUP_EXPERTISE", "")
    TEST_PLANNER_ID = os.environ.get("TEST_PLANNER_ID", "")

    # Secret control code (only Rani knows this)
    SAKI_SECRET_CODE = os.environ.get("SAKI_SECRET_CODE", "")
    SAKI_QUICK_PAUSE_TRIGGER = os.environ.get("SAKI_QUICK_PAUSE_TRIGGER", "Saki!!!")

    # Question escalation timing
    UNANSWERED_QUESTION_HOURS = int(os.environ.get("QUESTION_REMINDER_DELAY_HOURS", 4))
    QUESTION_ABANDONED_NOTIFY_HOURS = int(os.environ.get("QUESTION_ABANDONED_NOTIFY_DELAY_HOURS", 24))

    # To-do generation lookback window
    TODO_LOOKBACK_HOURS = int(os.environ.get("TODO_LOOKBACK_HOURS", 2))

    # Pattern escalation thresholds
    MISS_FIRST_FLAG = int(os.environ.get("MISS_FIRST_FLAG", 1))
    MISS_SECOND_NOTIFY = int(os.environ.get("MISS_SECOND_NOTIFY", 2))
    MISS_THIRD_ALERT = int(os.environ.get("MISS_THIRD_ALERT", 3))

    # Article review
    ARTICLE_REVIEW_DAYS = 7
    ARTICLE_REMINDER_DAYS_BEFORE = 2

    # Optional: OpenAI Whisper for audio transcription (Function 12)
    WHISPER_API_KEY = os.environ.get("WHISPER_API_KEY", "")

    # App
    SECRET_KEY = os.environ["SECRET_KEY"]
    DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "sakeena2026")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///saki.db")
    PORT = int(os.environ.get("PORT", 5000))
    WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:5000")


config = Config()
