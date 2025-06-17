import random

gifts = [
    {"telegram_id": "5170145012310081615", "gift_id": "1"},
    {"telegram_id": "5170233102089322756", "gift_id": "2"},
    {"telegram_id": "5170250947678437525", "gift_id": "3"},
    {"telegram_id": "5168103777563050263", "gift_id": "4"},
    {"telegram_id": "5170144170496491616", "gift_id": "5"},
    {"telegram_id": "5170314324215857265", "gift_id": "6"},
    {"telegram_id": "5170564780938756245", "gift_id": "7"},
    {"telegram_id": "5168043875654172773", "gift_id": "8"},
    {"telegram_id": "5170690322832818290", "gift_id": "9"},
    {"telegram_id": "5170521118301225164", "gift_id": "10"},
    {"telegram_id": "6028601630662853006", "gift_id": "11"}
]

random_gift = random.choice(gifts)  # Выбираем случайный словарь из списка
print(random_gift['telegram_id'])