import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('JWT_SECRET', 'dev-key-change-me')
    API_USER = os.getenv('API_USER', 'admin')
    API_PASS = os.getenv('API_PASS', 'admin')