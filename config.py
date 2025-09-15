import os
import json
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties  # ← BU QATORNI QO'SHING

# Bot tokeni
TOKEN = "7782418983:AAFw1FYb-ESFb-1abiSudFlzhukTAkylxFA"

# Adminlar ro'yxati
ADMINS = [8165064673]

# Kanallar ro'yxati (username yoki ID)
CHANNELS = ["@Tarjimakinolar_bizda"]

# Ma'lumotlar bazasi
def get_data():
    if not os.path.exists('data.json'):
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump({
                "users": {},
                "movies": {},
                "cartoons": {},
                "premieres": {},
                "admins": ADMINS,
                "channels": CHANNELS
            }, f, ensure_ascii=False, indent=4)
    
    with open('data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Bot va dispatcher yaratish (YANGI USUL)
storage = MemoryStorage()
bot = Bot(
    token=TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # ← YANGI USUL
)
dp = Dispatcher(storage=storage)