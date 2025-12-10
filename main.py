import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# =======================
BOT_TOKEN = "8396702012:AAGb2naIeVgSFCF1jB9Ib2OMBcQc0rF3vWQ"
ADMIN_ID = 7323803925
# =======================

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_state = {}  # user_id → {"last_cat": "tarix", "lang": "uz"}

# =======================
places = {
    "tarix": {
        "fayoztepa": {"uz": "🌄 FAYOZTEPA BUDDA MAJMUASI\n\nII–IV asrlar • Ulkan haykal izlari • Rangli freskalar\nTermizdan 12 km shimol\nhttps://maps.app.goo.gl/Cg3pK3pV3sA1J2vz5", "photo": "https://i.imgur.com/5L8pZ9K.jpeg"},
        "dalvarzin": {"uz": "🏛 DALVARZINTEPA\n\nKushon davri • Oltin xazina topilgan joy\nSho‘rchi tumani\nhttps://maps.app.goo.gl/dalvarzin2025", "photo": "https://i.imgur.com/Q1wX9pL.jpeg"},
        "jarqorgon": {"uz": "🏰 JARQO‘RG‘ON MINORASI\n\n1108-yil • 22 metr\nJarqo‘rg‘on tumani\nhttps://maps.app.goo.gl/jarqorgon2025", "photo": "https://i.imgur.com/R8tY6uV.jpeg"}
    },
    "tabiat": {
        "sangardak": {"uz": "💦 SANGARDAK SHARSHARASI\n\n150+ metr • G‘ordan oqadi!\nSariosiyo tumani\nhttps://maps.app.goo.gl/sangardak2025", "photo": "https://i.imgur.com/X9pL2mV.jpeg"},
        "omonxona": {"uz": "🌿 OMONXONA\n\nShifobaxsh mineral buloqlar\nBoysun tumani\nhttps://maps.app.goo.gl/omonxona2025", "photo": "https://i.imgur.com/8K7pQ2x.jpeg"},
        "darband": {"uz": "⛰ DARBAND (Temir darvoza)\n\nIpak yo‘li darvozasi\nBoysun tog‘lari\nhttps://maps.app.goo.gl/darband2025", "photo": "https://i.imgur.com/L5vR9pM.jpeg"}
    },
    "ziyorat": {
        "sultan_saodat": {"uz": "🕌 SULTAN SAODAT MAJMUASI\n\nXI–XVII asrlar • Sayyidlar maqbarasi\nTermizdan 8 km janub\nhttps://maps.app.goo.gl/sultansaodat2025", "photo": "https://i.imgur.com/Mv2fK8P.jpeg"},
        "termiziy": {"uz": "📜 AL-HAKIM AT-TERMIZIY\n\nIX asr allomasi\nTermizdan 3 km\nhttps://maps.app.goo.gl/termiziy2025", "photo": "https://i.imgur.com/J3vXp1l.jpeg"},
        "kokildor": {"uz": "🏛 KOKILDOR OTA\n\nXVI asr xonaqohi\nTermiz yaqinida\nhttps://maps.app.goo.gl/kokildor2025", "photo": "https://i.imgur.com/P7qR2tY.jpeg"}
    }
}

# =======================
class AddPlace(StatesGroup):
    category = State()
    name = State()
    text = State()
    photo = State()

class EditPlace(StatesGroup):
    category = State()
    name = State()
    text = State()
    photo = State()

# =======================
# Tugmalar
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌄 Tarixiy joylar", callback_data="cat_tarix")],
        [InlineKeyboardButton(text="💦 Tabiat va sharsharalar", callback_data="cat_tabiat")],
        [InlineKeyboardButton(text="🕌 Ziyoratgohlar", callback_data="cat_ziyorat")],
        [InlineKeyboardButton(text="🌐 Tilni o‘zgartirish", callback_data="change_lang")]
    ])

def places_list_kb(category):
    kb = []
    for key, val in places[category].items():
        kb.append([InlineKeyboardButton(text=val["uz"].split("\n")[0], callback_data=f"show_{category}_{key}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back_to_cat_{category}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def place_detail_kb(gps_url, category):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Yo‘l ko‘rsatish", url=gps_url)],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back_to_cat_{category}")]
    ])

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi joy qo‘shish", callback_data="add_place")],
        [InlineKeyboardButton(text="✏️ Joylarni tahrirlash", callback_data="edit_place")],
        [InlineKeyboardButton(text="🗑 Joylarni o‘chirish", callback_data="delete_place")],
        [InlineKeyboardButton(text="📂 Bo‘limlarni boshqarish", callback_data="manage_categories")],
        [InlineKeyboardButton(text="📊 Qo‘shimcha bo‘limlar", callback_data="extra_admin")]
    ])

# =======================
# Start va til tanlash
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"lang": "uz"}
    await message.answer("👋 Assalomu alaykum!\n\n@Surxon_travel_bot – Surxondaryo turizm gid boti\n\nTilni tanlang:", reply_markup=lang_kb())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery):
    user_state[call.from_user.id]["lang"] = call.data.split("_")[1]
    await call.message.edit_text("🌐 Surxondaryo turizm boti", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "change_lang")
async def change_lang(call: types.CallbackQuery):
    await call.message.edit_text("Tilni tanlang:", reply_markup=lang_kb())

@dp.callback_query(F.data == "main_menu")
async def back_main(call: types.CallbackQuery):
    await call.message.edit_text("🏠 Asosiy menyu:", reply_markup=main_menu_kb())

# =======================
# Kategoriya va joylar
@dp.callback_query(F.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    cat = call.data.split("_")[1]
    user_state[call.from_user.id]["last_cat"] = cat
    await call.message.edit_text("📌 Tanlang:", reply_markup=places_list_kb(cat))

@dp.callback_query(F.data.startswith("show_"))
async def show_place(call: types.CallbackQuery):
    _, cat, key = call.data.split("_", 2)
    p = places[cat][key]
    gps = p["uz"].split("https://")[1].split()[0] if "https://" in p["uz"] else "maps.google.com"
    kb = place_detail_kb("https://" + gps, cat)
    await bot.send_photo(
        chat_id=call.message.chat.id,
        photo=p["photo"],
        caption=f"<b>{p['uz'].splitlines()[0]}</b>\n\n{p['uz']}",
        parse_mode="HTML",
        reply_markup=kb
    )
    await call.message.delete()

@dp.callback_query(F.data.startswith("back_to_cat_"))
async def back_to_cat(call: types.CallbackQuery):
    cat = call.data.split("_")[-1]
    # Rasm va matn qoladi, tugmalar qayta paydo bo'ladi
    await call.message.edit_reply_markup(reply_markup=places_list_kb(cat))

# =======================
# ADMIN PANEL
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ Admin panel", reply_markup=admin_panel_kb())

@dp.callback_query(F.data == "add_place")
async def add_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.edit_text("Bo‘limni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌄 Tarixiy", callback_data="addcat_tarix")],
        [InlineKeyboardButton(text="💦 Tabiat", callback_data="addcat_tabiat")],
        [InlineKeyboardButton(text="🕌 Ziyorat", callback_data="addcat_ziyorat")]
    ]))
    await state.set_state(AddPlace.category)

@dp.callback_query(F.data == "edit_place")
async def edit_place(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer("✏️ Joylarni tahrirlash bo‘limi ishlamoqda... (FSM orqali keyinchalik rasm, nom, malumot tahrirlash mumkin)")

@dp.callback_query(F.data == "delete_place")
async def delete_place(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer("🗑 Joylarni o‘chirish bo‘limi ishlamoqda... (FSM orqali keyinchalik ishlatiladi)")

@dp.callback_query(F.data == "manage_categories")
async def manage_categories(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer("📂 Bo‘limlarni boshqarish ishlamoqda...")

@dp.callback_query(F.data == "extra_admin")
async def extra_admin(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer("📊 Qo‘shimcha bo‘limlar ishlamoqda...")

# =======================
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
