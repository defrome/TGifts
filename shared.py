# Общие переменные
from typing import Dict, Any

# shared.py
import json
import pathlib
from typing import Dict, Optional

# Определяем корневую директорию проекта и папку для данных
BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class JSONStorage:
    def __init__(self, file_path: str = "paid_users.json"):
        self.file_path = DATA_DIR / file_path
        print(f"Инициализация хранилища по пути: {self.file_path}")
        self.data: Dict[str, str] = self._load_or_create()

    def _load_or_create(self) -> Dict[str, str]:
        try:
            if not self.file_path.exists():
                print("Файл не существует, создаём новый")
                self._save_data({})
                return {}

            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Загружаем существующие данные")
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return {}

    def _save_data(self, data: dict):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Данные успешно сохранены")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def __setitem__(self, user_id: int, value: str):
        self.data[str(user_id)] = value
        self._save_data(self.data)

    def __getitem__(self, user_id: int) -> Optional[str]:
        return self.data.get(str(user_id))

    def __contains__(self, user_id: int) -> bool:
        return str(user_id) in self.data


# Инициализация
paid_users = JSONStorage()

user_inventory: Dict[int, Dict[str, list]] = {}
referral_users = set()
gifts = [
    {"telegram_id": "5170145012310081615", "gift_id": "1", "emoji": "💝", "image_path": "https://i.ibb.co/83crdxt/heart.png", "star": 15},
    {"telegram_id": "5170233102089322756", "gift_id": "2", "emoji": "🧸", "image_path": "https://i.ibb.co/MyYTrssS/bear.png", "star": 15},
    {"telegram_id": "5170250947678437525", "gift_id": "3", "emoji": "🎁", "image_path": "https://i.ibb.co/9HbdKTST/gift.png", "star": 25},
    {"telegram_id": "5168103777563050263", "gift_id": "4", "emoji": "🌹", "image_path": "https://i.ibb.co/tMrm9G4F/rose.png", "star": 25},
    {"telegram_id": "5170144170496491616", "gift_id": "5", "emoji": "🎂", "image_path": "https://i.ibb.co/h1Tqg4T9/cake.png", "star": 50},
    {"telegram_id": "5170314324215857265", "gift_id": "6", "emoji": "💐", "image_path": "https://i.ibb.co/zTqgSHWt/flowers.png", "star": 50},
    {"telegram_id": "5170564780938756245", "gift_id": "7", "emoji": "🚀", "image_path": "https://i.ibb.co/MDzMjStr/rocket.png", "star": 50},
    {"telegram_id": "5168043875654172773", "gift_id": "8", "emoji": "🏆", "image_path": "https://i.ibb.co/Rk3kQxB2/cup.png", "star": 100},
    {"telegram_id": "5170690322832818290", "gift_id": "9", "emoji": "💍", "image_path": "https://i.ibb.co/9mdyLZb2/ring.png", "star": 100},
    {"telegram_id": "5170521118301225164", "gift_id": "10", "emoji": "💎", "image_path": "https://i.ibb.co/Zz9pX6cP/brilliant.png", "star": 100},
    {"telegram_id": "6028601630662853006", "gift_id": "11", "emoji": "🍾", "image_path": "https://i.ibb.co/9mpvjS0m/shampane.png", "star": 50}
]

spin_gifts = [
    {"id": "5170145012310081615", "img": "https://i.ibb.co/83crdxt/heart.png", "name": "heart", "value": "15", "rarity": "rare", "probability": "21.37"},
    {"id": "5170233102089322756", "img": "https://i.ibb.co/MyYTrssS/bear.png", "name": "bear", "value": "15", "rarity": "common", "probability": "25.81"},
    {"id": "5170250947678437525", "img": "https://i.ibb.co/9HbdKTST/gift.png", "name": "gift", "value": "25", "rarity": "rare", "probability": "20.81"},
    {"id": "5168103777563050263", "img": "https://i.ibb.co/tMrm9G4F/rose.png", "name": "rose", "value": "25", "rarity": "rare", "probability": "25"},
    {"id": "5170144170496491616", "img": "https://i.ibb.co/h1Tqg4T9/cake.png", "name": "cake", "value": "50", "rarity": "epic", "probability": "10"},
    {"id": "5170314324215857265", "img": "https://i.ibb.co/zTqgSHWt/flowers.png", "name": "flowers", "value": "50", "rarity": "epic", "probability": "10"},
    {"id": "5170564780938756245", "img": "https://i.ibb.co/MDzMjStr/rocket.png", "name": "rocket", "value": "50", "rarity": "epic", "probability": "10"},
    {"id": "5168043875654172773", "img": "https://i.ibb.co/Rk3kQxB2/cup.png", "name": "cup", "value": "100", "rarity": "legendarity", "probability": "0.8"},
    {"id": "5170690322832818290", "img": "https://i.ibb.co/9mdyLZb2/ring.png", "name": "ring", "value": "100", "rarity": "epic", "probability": "5"},
    {"id": "5170521118301225164", "img": "https://i.ibb.co/Zz9pX6cP/brilliant.png", "name": "brilliant", "value": "100", "rarity": "epic", "probability": "5"},
    {"id": "6028601630662853006", "img": "https://i.ibb.co/9mpvjS0m/shampane.png", "name": "shampane", "value": "50", "rarity": "epic", "probability": "1.21"}
]

referral_gifts = [
    {"telegram_id": "5170145012310081615", "gift_id": "1", "emoji": "💝", "image_path": "https://i.ibb.co/83crdxt/heart.png", "star": 15},
    {"telegram_id": "5170233102089322756", "gift_id": "2", "emoji": "🧸", "image_path": "https://i.ibb.co/MyYTrssS/bear.png", "star": 15},
    {"telegram_id": "6028601630662853006", "gift_id": "11", "emoji": "🍾", "image_path": "https://i.ibb.co/9mpvjS0m/shampane.png", "star": 50},
    {"telegram_id": "5170250947678437525", "gift_id": "3", "emoji": "🎁", "image_path": "https://i.ibb.co/9HbdKTST/gift.png", "star": 25},
]

async def init_user(user_id: int):
    if user_id not in user_inventory:
        user_inventory[user_id] = {'gifts': []}

async def get_user_inventory(user_id: int):
    await init_user(user_id)
    return user_inventory.get(user_id)