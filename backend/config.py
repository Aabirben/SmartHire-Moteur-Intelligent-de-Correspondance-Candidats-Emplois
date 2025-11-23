import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")  # For direct Postgres if needed
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # For sessions if needed
    CORS_ORIGINS = ["http://localhost:5173"]  # Your frontend URL (Vite default)