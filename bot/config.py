import os
from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(' ', '').split(',') if x.strip().lstrip('-').isdigit()]


BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DB_PATH = os.getenv('DB_PATH', 'data/reports.db')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
ADMIN_HOST = os.getenv('ADMIN_HOST', '127.0.0.1')
ADMIN_PORT = int(os.getenv('ADMIN_PORT', '8000'))

# MAX user_id сотрудников, которым бот шлёт уведомление о новом обращении (через запятую)
NOTIFY_USER_IDS = _int_list(os.getenv('NOTIFY_USER_IDS', ''))
# Контакт поддержки для /privacy и карточки бота
SUPPORT_CONTACT = os.getenv('SUPPORT_CONTACT', '')
# Лимит обращений от одного пользователя в час
RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '5'))

MAX_DESCRIPTION_LEN = 3000
MAX_CONTACT_LEN = 200

# Пароли, с которыми админку запускать нельзя
WEAK_PASSWORDS = {'', 'admin', 'change_me', 'password', '123456'}
