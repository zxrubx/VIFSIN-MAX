import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DB_PATH = os.getenv('DB_PATH', 'data/reports.db')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
ADMIN_HOST = os.getenv('ADMIN_HOST', '127.0.0.1')
ADMIN_PORT = int(os.getenv('ADMIN_PORT', '8000'))
