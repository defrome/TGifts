# Общие переменные
paid_users = {}
user_inventory = {}
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


async def init_user(user_id: int):
    if user_id not in user_inventory:
        user_inventory[user_id] = {'gifts': []}

async def get_user_inventory(user_id: int):
    await init_user(user_id)
    return user_inventory.get(user_id)