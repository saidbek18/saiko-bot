import asyncio
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import bot, dp, get_data, save_data, CHANNELS, ADMINS

# Log konfiguratsiyasi
logging.basicConfig(level=logging.INFO)

# FSM holatlari
class UserState(StatesGroup):
    menu = State()
    waiting_for_movie_code = State()
    waiting_for_cartoon_code = State()
    waiting_for_premiere_code = State()

class AdminState(StatesGroup):
    add_movie = State()
    add_movie_text = State()
    add_movie_code = State()
    add_cartoon = State()
    add_cartoon_text = State()
    add_cartoon_code = State()
    add_premiere = State()
    add_premiere_text = State()
    add_premiere_code = State()
    add_ad = State()
    add_ad_text = State()
    add_ad_button = State()
    add_ad_button_link = State()
    add_admin = State()
    delete_content = State()
    delete_movie = State()
    delete_cartoon = State()
    delete_premiere = State()

# Start komandasi
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = get_data()
    
    # Foydalanuvchini ro'yxatga olish
    if str(user_id) not in data['users']:
        data['users'][str(user_id)] = {
            'subscribed': False,
            'premium': False
        }
        save_data(data)
    
    # Kanallarga obuna bo'lishni tekshirish
    not_subscribed = []
    builder = InlineKeyboardBuilder()
    
    for channel in CHANNELS:
        try:
            chat_member = await bot.get_chat_member(channel, user_id)
            if chat_member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
                builder.add(InlineKeyboardButton(
                    text=f"📢 {channel} kanaliga obuna bo'lish", 
                    url=f"https://t.me/{channel[1:]}" if channel.startswith('@') else f"https://t.me/{channel}"
                ))
        except Exception as e:
            logging.error(f"Xatolik: {e}")
    
    if not_subscribed:
        builder.add(InlineKeyboardButton(
            text="✅ Obunani tekshirish", 
            callback_data="check_subscription"
        ))
        builder.adjust(1)
        await message.answer(
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", 
            reply_markup=builder.as_markup()
        )
    else:
        data['users'][str(user_id)]['subscribed'] = True
        save_data(data)
        await show_main_menu(message, state)

# Obunani tekshirish
@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = get_data()
    
    not_subscribed = []
    builder = InlineKeyboardBuilder()
    
    for channel in CHANNELS:
        try:
            chat_member = await bot.get_chat_member(channel, user_id)
            if chat_member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
                builder.add(InlineKeyboardButton(
                    text=f"📢 {channel} kanaliga obuna bo'lish", 
                    url=f"https://t.me/{channel[1:]}" if channel.startswith('@') else f"https://t.me/{channel}"
                ))
        except Exception as e:
            logging.error(f"Xatolik: {e}")
    
    if not_subscribed:
        builder.add(InlineKeyboardButton(
            text="✅ Obunani tekshirish", 
            callback_data="check_subscription"
        ))
        builder.adjust(1)
        
        await callback_query.message.edit_text(
            "Siz hali barcha kanallarga obuna bo'lmagansiz. Iltimos, quyidagi kanallarga obuna bo'ling:", 
            reply_markup=builder.as_markup()
        )
    else:
        data['users'][str(user_id)]['subscribed'] = True
        save_data(data)
        await callback_query.message.delete()
        await show_main_menu(callback_query.message, state)

# Asosiy menyuni ko'rsatish
async def show_main_menu(message: types.Message, state: FSMContext):
    await state.set_state(UserState.menu)
    
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🎬 Qo'rqinchli kino"),
        KeyboardButton(text="📺 Multfilm"),
        KeyboardButton(text="🎭 Kino Premyera"),
    )
    
    # Admin panel tugmasini faqat adminlar uchun ko'rsatish
    if message.from_user.id in ADMINS:
        builder.add(KeyboardButton(text="👨‍💻 Admin panel"))
    
    builder.adjust(2, 2, 1)
    await message.answer("Asosiy menyu:", reply_markup=builder.as_markup(resize_keyboard=True))

# Bo'limlarni boshqarish - STATE SIZ handlerlar
@dp.message(F.text == "🎬 Qo'rqinchli kino")
async def handle_movies(message: types.Message, state: FSMContext):
    await message.answer("Kino kodini yuboring:")
    await state.set_state(UserState.waiting_for_movie_code)

@dp.message(F.text == "📺 Multfilm")
async def handle_cartoons(message: types.Message, state: FSMContext):
    await message.answer("Multfilm kodini yuboring:")
    await state.set_state(UserState.waiting_for_cartoon_code)

@dp.message(F.text == "🎭 Kino Premyera")
async def handle_premieres(message: types.Message, state: FSMContext):
    await message.answer("Premyera kodini yuboring:")
    await state.set_state(UserState.waiting_for_premiere_code)

@dp.message(F.text == "👨‍💻 Admin panel")
async def handle_admin_panel(message: types.Message):
    if message.from_user.id in ADMINS:
        await show_admin_panel(message)

# Kod orqali kontent qidirish
@dp.message(UserState.waiting_for_movie_code)
async def send_movie_by_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    movie = data['movies'].get(code)
    if movie:
        await message.answer_video(movie['video'], caption=movie['text'])
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")
    
    await show_main_menu(message, state)

@dp.message(UserState.waiting_for_cartoon_code)
async def send_cartoon_by_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    cartoon = data['cartoons'].get(code)
    if cartoon:
        await message.answer_video(cartoon['video'], caption=cartoon['text'])
    else:
        await message.answer("❌ Bunday kodli multfilm topilmadi.")
    
    await show_main_menu(message, state)

@dp.message(UserState.waiting_for_premiere_code)
async def send_premiere_by_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    premiere = data['premieres'].get(code)
    if premiere:
        await message.answer_video(premiere['video'], caption=premiere['text'])
    else:
        await message.answer("❌ Bunday kodli premyera topilmadi.")
    
    await show_main_menu(message, state)

# Admin panelini ko'rsatish
async def show_admin_panel(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🎬 Kino qo'shish"),
        KeyboardButton(text="📺 Multfilm qo'shish"),
        KeyboardButton(text="🎭 Premyera qo'shish"),
        KeyboardButton(text="🗑️ Kontent o'chirish"),
        KeyboardButton(text="📢 Reklama yuborish"),
        KeyboardButton(text="👨‍💻 Admin qo'shish"),
        KeyboardButton(text="🔙 Asosiy menyu")
    )
    builder.adjust(2, 2, 1)
    await message.answer("Admin panel:", reply_markup=builder.as_markup(resize_keyboard=True))

# Admin panelni boshqarish
@dp.message(F.text.in_([
    "🎬 Kino qo'shish", "📺 Multfilm qo'shish", "🎭 Premyera qo'shish",
    "🗑️ Kontent o'chirish", "📢 Reklama yuborish", "👨‍💻 Admin qo'shish", "🔙 Asosiy menyu"
]))
async def handle_admin_commands(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    
    text = message.text
    
    if text == "🎬 Kino qo'shish":
        await message.answer("Kino videosini yuboring:")
        await state.set_state(AdminState.add_movie)
    elif text == "📺 Multfilm qo'shish":
        await message.answer("Multfilm videosini yuboring:")
        await state.set_state(AdminState.add_cartoon)
    elif text == "🎭 Premyera qo'shish":
        await message.answer("Premyera videosini yuboring:")
        await state.set_state(AdminState.add_premiere)
    elif text == "🗑️ Kontent o'chirish":
        await show_delete_options(message, state)
    elif text == "📢 Reklama yuborish":
        await message.answer("Reklama uchun rasm yoki video yuboring:")
        await state.set_state(AdminState.add_ad)
    elif text == "👨‍💻 Admin qo'shish":
        await message.answer("Yangi admin ID sini yuboring:")
        await state.set_state(AdminState.add_admin)
    elif text == "🔙 Asosiy menyu":
        await show_main_menu(message, state)

# Kontent o'chirish menyusini ko'rsatish
async def show_delete_options(message: types.Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🎬 Kino o'chirish"),
        KeyboardButton(text="📺 Multfilm o'chirish"),
        KeyboardButton(text="🎭 Premyera o'chirish"),
        KeyboardButton(text="🔙 Admin panel")
    )
    builder.adjust(2, 1)
    await message.answer("Nimani o'chirmoqchisiz?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AdminState.delete_content)

# Kontent o'chirishni boshqarish
@dp.message(AdminState.delete_content)
async def handle_delete_content(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "🎬 Kino o'chirish":
        await message.answer("O'chirmoqchi bo'lgan kino kodini yuboring:")
        await state.set_state(AdminState.delete_movie)
    elif text == "📺 Multfilm o'chirish":
        await message.answer("O'chirmoqchi bo'lgan multfilm kodini yuboring:")
        await state.set_state(AdminState.delete_cartoon)
    elif text == "🎭 Premyera o'chirish":
        await message.answer("O'chirmoqchi bo'lgan premyera kodini yuboring:")
        await state.set_state(AdminState.delete_premiere)
    elif text == "🔙 Admin panel":
        await show_admin_panel(message)
        await state.clear()

# Kino o'chirish
@dp.message(AdminState.delete_movie)
async def delete_movie(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    if code in data['movies']:
        del data['movies'][code]
        save_data(data)
        await message.answer(f"✅ '{code}' kodli kino muvaffaqiyatli o'chirildi!")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")
    
    await show_delete_options(message, state)

# Multfilm o'chirish
@dp.message(AdminState.delete_cartoon)
async def delete_cartoon(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    if code in data['cartoons']:
        del data['cartoons'][code]
        save_data(data)
        await message.answer(f"✅ '{code}' kodli multfilm muvaffaqiyatli o'chirildi!")
    else:
        await message.answer("❌ Bunday kodli multfilm topilmadi.")
    
    await show_delete_options(message, state)

# Premyera o'chirish
@dp.message(AdminState.delete_premiere)
async def delete_premiere(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = get_data()
    
    if code in data['premieres']:
        del data['premieres'][code]
        save_data(data)
        await message.answer(f"✅ '{code}' kodli premyera muvaffaqiyatli o'chirildi!")
    else:
        await message.answer("❌ Bunday kodli premyera topilmadi.")
    
    await show_delete_options(message, state)

# Kino qo'shish
@dp.message(AdminState.add_movie, F.content_type.in_({'video'}))
async def add_movie_video(message: types.Message, state: FSMContext):
    await state.update_data(movie_video=message.video.file_id)
    await message.answer("Kino uchun matn qo'shing:")
    await state.set_state(AdminState.add_movie_text)

@dp.message(AdminState.add_movie_text)
async def add_movie_text(message: types.Message, state: FSMContext):
    await state.update_data(movie_text=message.text)
    await message.answer("Kino uchun kod yuboring (masalan: movie_123):")
    await state.set_state(AdminState.add_movie_code)

@dp.message(AdminState.add_movie_code)
async def add_movie_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    movie_code = message.text.strip()
    
    # Ma'lumotlarni saqlash
    db_data = get_data()
    db_data['movies'][movie_code] = {
        'video': data['movie_video'],
        'text': data['movie_text'],
        'code': movie_code
    }
    save_data(db_data)
    
    await message.answer(f"✅ Kino muvaffaqiyatli qo'shildi! Kod: {movie_code}")
    await state.clear()
    await show_admin_panel(message)

# Multfilm qo'shish
@dp.message(AdminState.add_cartoon, F.content_type.in_({'video'}))
async def add_cartoon_video(message: types.Message, state: FSMContext):
    await state.update_data(cartoon_video=message.video.file_id)
    await message.answer("Multfilm uchun matn qo'shing:")
    await state.set_state(AdminState.add_cartoon_text)

@dp.message(AdminState.add_cartoon_text)
async def add_cartoon_text(message: types.Message, state: FSMContext):
    await state.update_data(cartoon_text=message.text)
    await message.answer("Multfilm uchun kod yuboring (masalan: cartoon_123):")
    await state.set_state(AdminState.add_cartoon_code)

@dp.message(AdminState.add_cartoon_code)
async def add_cartoon_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cartoon_code = message.text.strip()
    
    # Ma'lumotlarni saqlash
    db_data = get_data()
    db_data['cartoons'][cartoon_code] = {
        'video': data['cartoon_video'],
        'text': data['cartoon_text'],
        'code': cartoon_code
    }
    save_data(db_data)
    
    await message.answer(f"✅ Multfilm muvaffaqiyatli qo'shildi! Kod: {cartoon_code}")
    await state.clear()
    await show_admin_panel(message)

# Premyera qo'shish
@dp.message(AdminState.add_premiere, F.content_type.in_({'video'}))
async def add_premiere_video(message: types.Message, state: FSMContext):
    await state.update_data(premiere_video=message.video.file_id)
    await message.answer("Premyera uchun matn qo'shing:")
    await state.set_state(AdminState.add_premiere_text)

@dp.message(AdminState.add_premiere_text)
async def add_premiere_text(message: types.Message, state: FSMContext):
    await state.update_data(premiere_text=message.text)
    await message.answer("Premyera uchun kod yuboring (masalan: premiere_123):")
    await state.set_state(AdminState.add_premiere_code)

@dp.message(AdminState.add_premiere_code)
async def add_premiere_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    premiere_code = message.text.strip()
    
    # Ma'lumotlarni saqlash
    db_data = get_data()
    db_data['premieres'][premiere_code] = {
        'video': data['premiere_video'],
        'text': data['premiere_text'],
        'code': premiere_code
    }
    save_data(db_data)
    
    await message.answer(f"✅ Premyera muvaffaqiyatli qo'shildi! Kod: {premiere_code}")
    await state.clear()
    await show_admin_panel(message)

# Reklama qo'shish
@dp.message(AdminState.add_ad, F.content_type.in_({'photo', 'video'}))
async def add_ad_media(message: types.Message, state: FSMContext):
    if message.photo:
        await state.update_data(ad_media=message.photo[-1].file_id, media_type='photo')
    else:
        await state.update_data(ad_media=message.video.file_id, media_type='video')
    
    await message.answer("Reklama uchun matn qo'shing:")
    await state.set_state(AdminState.add_ad_text)

@dp.message(AdminState.add_ad_text)
async def add_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(ad_text=message.text)
    await message.answer("Reklama uchun tugma nomini yuboring (agar kerak bo'lmasa 'skip' yozing):")
    await state.set_state(AdminState.add_ad_button)

@dp.message(AdminState.add_ad_button)
async def add_ad_button(message: types.Message, state: FSMContext):
    if message.text.lower() == 'skip':
        # Reklamani yuborish
        data = await state.get_data()
        ad_text = data['ad_text']
        ad_media = data['ad_media']
        media_type = data['media_type']
        
        db_data = get_data()
        for user_id in db_data['users']:
            try:
                if media_type == 'photo':
                    await bot.send_photo(int(user_id), ad_media, caption=ad_text)
                else:
                    await bot.send_video(int(user_id), ad_media, caption=ad_text)
            except Exception as e:
                logging.error(f"Foydalanuvchiga {user_id} reklama yuborishda xatolik: {e}")
        
        await message.answer("✅ Reklama barcha foydalanuvchilarga yuborildi!")
        await state.clear()
        await show_admin_panel(message)
    else:
        await state.update_data(ad_button=message.text)
        await message.answer("Tugma uchun link yuboring:")
        await state.set_state(AdminState.add_ad_button_link)

@dp.message(AdminState.add_ad_button_link)
async def add_ad_button_link(message: types.Message, state: FSMContext):
    # Reklamani yuborish
    data = await state.get_data()
    ad_text = data['ad_text']
    ad_media = data['ad_media']
    media_type = data['media_type']
    ad_button = data['ad_button']
    ad_button_link = message.text
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ad_button, url=ad_button_link)]
    ])
    
    db_data = get_data()
    for user_id in db_data['users']:
        try:
            if media_type == 'photo':
                await bot.send_photo(int(user_id), ad_media, caption=ad_text, reply_markup=keyboard)
            else:
                await bot.send_video(int(user_id), ad_media, caption=ad_text, reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Foydalanuvchiga {user_id} reklama yuborishda xatolik: {e}")
    
    await message.answer("✅ Reklama barcha foydalanuvchilarga yuborildi!")
    await state.clear()
    await show_admin_panel(message)

# Admin qo'shish
@dp.message(AdminState.add_admin)
async def add_admin(message: types.Message, state: FSMContext):
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id not in ADMINS:
            ADMINS.append(new_admin_id)
            await message.answer(f"✅ {new_admin_id} yangi admin qo'shildi!")
        else:
            await message.answer("❌ Bu ID allaqachon adminlar ro'yxatida.")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format. Faqat raqamlardan foydalaning.")
    
    await state.clear()
    await show_admin_panel(message)

# Asosiy funksiya
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())