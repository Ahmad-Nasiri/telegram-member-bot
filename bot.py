import asyncio
import logging
import sqlite3
from datetime import datetime
import re
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from database import init_db, add_user, add_order, get_user_today_orders, get_source_groups, add_source_group, remove_source_group, get_all_source_groups
from member_adder import add_members_operation, client

logging.basicConfig(level=logging.INFO)
LINK, QUANTITY, CONFIRM = range(3)
user_data = {}

def get_bot_token():
    print("\n" + "="*55)
    print("🤖 **ربات افزایش ممبر**")
    print("="*55)
    print("\n📌 **لطفاً اطلاعات زیر را وارد کنید:**\n")
    
    while True:
        token = input("🔑 توکن ربات (از @BotFather): ").strip()
        if token:
            print(f"✅ توکن ثبت شد: {token[:10]}...\n")
            return token
        else:
            print("❌ توکن نمی‌تواند خالی باشد! لطفاً دوباره وارد کنید.\n")

def get_owner_info():
    print("\n📌 **اطلاعات مالک ربات:**\n")
    
    while True:
        phone = input("📱 شماره تلفن مالک (با کد کشور، مثل +98912xxxxxxx): ").strip()
        if phone:
            print(f"✅ شماره ثبت شد: {phone}\n")
            break
        else:
            print("❌ شماره نمی‌تواند خالی باشد! لطفاً دوباره وارد کنید.\n")
    
    while True:
        try:
            api_id = int(input("🆔 API_ID (از my.telegram.org): ").strip())
            if api_id:
                print(f"✅ API_ID ثبت شد: {api_id}\n")
                break
        except ValueError:
            print("❌ API_ID باید عدد باشد! لطفاً دوباره وارد کنید.\n")
    
    while True:
        api_hash = input("🔐 API_HASH (از my.telegram.org): ").strip()
        if api_hash:
            print(f"✅ API_HASH ثبت شد: {api_hash[:10]}...\n")
            break
        else:
            print("❌ API_HASH نمی‌تواند خالی باشد! لطفاً دوباره وارد کنید.\n")
    
    owner_id = input("👤 آیدی عددی مالک (اختیاری، Enter برای دریافت خودکار): ").strip()
    if owner_id:
        try:
            owner_id = int(owner_id)
            print(f"✅ آیدی مالک ثبت شد: {owner_id}\n")
        except ValueError:
            print("⚠️ آیدی عددی نیست! از شما خواسته می‌شود در تلگرام وارد کنید.\n")
            owner_id = None
    else:
        owner_id = None
        print("ℹ️ آیدی مالک بعداً از طریق ربات دریافت می‌شود.\n")
    
    return {
        'phone': phone,
        'api_id': api_id,
        'api_hash': api_hash,
        'owner_id': owner_id
    }

def save_config(token, owner_info):
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(f'''BOT_TOKEN = "{token}"
API_ID = {owner_info['api_id']}
API_HASH = "{owner_info['api_hash']}"
OWNER_ID = {owner_info['owner_id'] if owner_info['owner_id'] else "None"}
DELAY_BETWEEN_ADD = 3
MAX_MEMBERS_PER_REQUEST = 10000
MAX_ORDERS_PER_DAY = 5
''')
    print("✅ تنظیمات در فایل config.py ذخیره شد.\n")

def load_config():
    try:
        from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID
        return {
            'token': BOT_TOKEN,
            'api_id': API_ID,
            'api_hash': API_HASH,
            'owner_id': OWNER_ID
        }
    except ImportError:
        return None

def setup_bot():
    print("\n" + "="*55)
    print("🤖 **ربات افزایش ممبر - راه‌اندازی**")
    print("="*55)
    
    config = load_config()
    
    if config and config['token'] and config['api_id'] and config['api_hash']:
        print("\n📁 فایل تنظیمات قبلی پیدا شد!")
        use_previous = input("❓ آیا از تنظیمات قبلی استفاده می‌کنید؟ (y/n): ").strip().lower()
        if use_previous == 'y':
            print("\n✅ از تنظیمات قبلی استفاده می‌شود.\n")
            return config['token'], config['api_id'], config['api_hash'], config['owner_id']
    
    token = get_bot_token()
    owner_info = get_owner_info()
    save_config(token, owner_info)
    
    return token, owner_info['api_id'], owner_info['api_hash'], owner_info['owner_id']

RULES_TEXT = """
📜 **قوانین استفاده از ربات:**

1️⃣ **توسعه‌دهنده:** این ربات توسط [Ahmad-Nasiri](https://github.com/Ahmad-Nasiri) ساخته و توسعه داده شده است.

2️⃣ **مسئولیت:** سازنده این ربات هیچ‌گونه مسئولیتی در قبال نحوه استفاده کاربران از آن ندارد.

3️⃣ **ممنوعیت:** هرگونه استفاده از این ربات برای اسپم، آزار و اذیت، یا تخلف از قوانین تلگرام ممنوع است.

4️⃣ **هشدار:** اگر از این ربات برای ارسال ممبر به گروه‌ها یا کانال‌هایی که اجازه ندارید استفاده کنید، خودتان مسئول عواقب آن هستید.

5️⃣ **تعهد:** کاربر با استفاده از این ربات متعهد می‌شود که از آن فقط برای مقاصد قانونی و اخلاقی استفاده کند.

6️⃣ **پشتیبانی:** در صورت بروز هرگونه مشکل، از طریق گیت‌هاب با توسعه‌دهنده در ارتباط باشید.

✅ با کلیک روی دکمه زیر، قوانین را می‌پذیرید و متعهد به رعایت آن‌ها می‌شوید.
"""

async def start(update: Update, context):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    global OWNER_ID
    if OWNER_ID is None:
        OWNER_ID = user.id
        update_config_owner_id(OWNER_ID)
        await update.message.reply_text(
            f"✅ شما به عنوان مالک ربات ثبت شدید!\n"
            f"🆔 آیدی شما: `{OWNER_ID}`\n\n"
            "این آیدی در فایل تنظیمات ذخیره شد.",
            parse_mode="Markdown"
        )
    
    keyboard = [[InlineKeyboardButton("📜 قوانین", callback_data="show_rules")]]
    await update.message.reply_text(
        f"👋 سلام {user.first_name} عزیز!\n\n"
        "به **ربات افزایش ممبر** خوش آمدید.\n"
        "لطفاً ابتدا قوانین را مطالعه کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def update_config_owner_id(owner_id):
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open('config.py', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('OWNER_ID'):
                    f.write(f'OWNER_ID = {owner_id}\n')
                else:
                    f.write(line)
        print(f"✅ OWNER_ID به {owner_id} به‌روزرسانی شد.")
    except Exception as e:
        print(f"⚠️ خطا در به‌روزرسانی OWNER_ID: {e}")

async def show_rules(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✅ قبول میکنم", callback_data="accept_rules")]
    ]
    await query.message.edit_text(
        RULES_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def accept_rules(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("👥 افزودن ممبر", callback_data="type_member")]
    ]
    await query.message.edit_text(
        "✅ قوانین را پذیرفتید.\n\n"
        "حالا روی دکمه زیر کلیک کنید تا عملیات افزودن ممبر شروع شود:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def select_type(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if get_user_today_orders(user_id) >= MAX_ORDERS_PER_DAY:
        await query.message.edit_text("❌ امروز سهمیه شما پر شده!")
        return ConversationHandler.END
    
    user_data[user_id] = {"type": "member"}
    await query.message.edit_text(
        "🔗 لینک گروه/کانال هدف رو بفرست:\n"
        "مثال: https://t.me/your_channel"
    )
    return LINK

async def get_link(update: Update, context):
    user_id = update.effective_user.id
    link = update.message.text.strip()
    if not link.startswith(("https://t.me/", "@")):
        await update.message.reply_text("❌ لینک نامعتبر!")
        return LINK
    user_data[user_id]["link"] = link
    await update.message.reply_text("🔢 تعداد ممبر رو وارد کن (۱ تا ۱۰۰۰۰):")
    return QUANTITY

async def get_quantity(update: Update, context):
    user_id = update.effective_user.id
    try:
        quantity = int(update.message.text)
        if quantity < 1 or quantity > 10000:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ عدد بین ۱ تا ۱۰۰۰۰ وارد کن!")
        return QUANTITY
    user_data[user_id]["quantity"] = quantity
    data = user_data[user_id]
    
    await update.message.reply_text(
        f"🧾 **رسید سفارش:**\n\n"
        f"نوع: ممبر\n"
        f"لینک: {data['link']}\n"
        f"تعداد: {data['quantity']}\n\n"
        f"تأیید میکنی؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تأیید", callback_data="confirm_start"),
             InlineKeyboardButton("❌ لغو", callback_data="cancel_order")]
        ])
    )
    return CONFIRM

async def confirm_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = user_data.get(user_id)
    if not data:
        await query.message.edit_text("❌ خطا! دوباره شروع کن.")
        return ConversationHandler.END
    
    order_id = add_order(user_id, "member", data["link"], data["quantity"])
    await query.message.edit_text(f"⏳ سفارش #{order_id} ثبت شد!\nدر حال شروع...")
    
    asyncio.create_task(add_members_operation(
        order_id, user_id, data["link"], data["quantity"], query.message, context.bot
    ))
    
    return ConversationHandler.END

async def cancel_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("❌ لغو شد.")
    return ConversationHandler.END

async def cancel_conv(update: Update, context):
    await update.message.reply_text("❌ لغو شد.")
    return ConversationHandler.END

async def admin_panel(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return
    
    try:
        if not client.is_connected():
            await client.start()
    except:
        pass
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه منبع", callback_data="admin_add_source")],
        [InlineKeyboardButton("📋 لیست گروه‌های منبع", callback_data="admin_list_sources")],
        [InlineKeyboardButton("🗑️ حذف گروه منبع", callback_data="admin_remove_source")],
        [InlineKeyboardButton("📊 آمار کامل", callback_data="admin_stats")]
    ]
    
    await update.message.reply_text(
        "🔧 **پنل مدیریت**\n\n"
        "یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def save_contacts(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📥 عضویت در گروه و ذخیره خودکار", callback_data="save_auto")],
        [InlineKeyboardButton("📤 آپلود فایل مخاطب", callback_data="save_file")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        "👥 **ذخیره مخاطب از گروه‌های منبع**\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:\n\n"
        "1️⃣ **عضویت در گروه:** ربات شما را به گروه منبع اضافه می‌کند و مخاطب‌ها را ذخیره می‌کند.\n"
        "2️⃣ **آپلود فایل:** یک فایل `.txt` یا `.csv` از مخاطب‌ها را آپلود کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def save_contacts_auto(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    await query.message.edit_text(
        "🔗 **لطفاً لینک گروه منبع را ارسال کنید.**\n\n"
        "ربات شما را به گروه اضافه می‌کند و سپس مخاطب‌ها را ذخیره می‌کند.\n\n"
        "مثال: `https://t.me/your_group`",
        parse_mode="Markdown"
    )
    context.user_data['waiting_for_auto_save'] = True

async def save_contacts_file(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    await query.message.edit_text(
        "📤 **لطفاً فایل مخاطب را ارسال کنید.**\n\n"
        "فرمت‌های پشتیبانی شده: `.txt`, `.csv`\n"
        "هر خط یک مخاطب (شماره تلفن یا آیدی تلگرام)."
    )
    context.user_data['waiting_for_file_save'] = True

async def handle_auto_save_link(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    if not context.user_data.get('waiting_for_auto_save'):
        return
    
    link = update.message.text.strip()
    context.user_data['waiting_for_auto_save'] = False
    
    match = re.search(r'(?:https?://t\.me/|@)([a-zA-Z0-9_]+)', link)
    if not match:
        await update.message.reply_text("❌ لینک نامعتبر! لطفاً دوباره تلاش کنید.")
        return
    
    username = match.group(1)
    
    try:
        await update.message.reply_text(f"🔄 در حال اتصال به گروه `{username}` و ذخیره مخاطب‌ها...")
        
        if not client.is_connected():
            await client.start()
        
        entity = await client.get_entity(username)
        chat_id = str(entity.id)
        chat_title = entity.title if hasattr(entity, 'title') else username
        
        add_source_group(chat_id, chat_title, user_id)
        
        try:
            members_count = await client.get_participants_count(entity)
        except:
            members_count = "نامشخص"
        
        await update.message.reply_text(
            f"✅ **عملیات ذخیره مخاطب با موفقیت انجام شد!**\n\n"
            f"📌 گروه: {chat_title}\n"
            f"🆔 chat_id: `{chat_id}`\n"
            f"👤 تعداد اعضا: {members_count}\n\n"
            f"📊 این گروه به لیست منبع اضافه شد و برای تأمین ممبر استفاده خواهد شد.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **خطا در ذخیره مخاطب!**\n\n"
            f"دلیل: {str(e)}"
        )

async def handle_file_save(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    if not context.user_data.get('waiting_for_file_save'):
        return
    
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ لطفاً یک فایل ارسال کنید.")
        return
    
    file_name = document.file_name or ""
    if not file_name.endswith(('.txt', '.csv')):
        await update.message.reply_text("❌ فرمت فایل پشتیبانی نمی‌شود. فقط `.txt` و `.csv`")
        return
    
    try:
        await update.message.reply_text(f"🔄 در حال پردازش فایل `{file_name}`...")
        
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{file_name}"
        await file.download_to_drive(file_path)
        
        contacts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    contacts.append(line)
        
        os.remove(file_path)
        
        if not contacts:
            await update.message.reply_text("❌ فایل خالی است یا فرمت آن صحیح نیست.")
            return
        
        await update.message.reply_text(
            f"✅ **فایل با موفقیت پردازش شد!**\n\n"
            f"📄 نام فایل: {file_name}\n"
            f"👥 تعداد مخاطب: {len(contacts)}\n\n"
            f"📊 نمونه مخاطب‌ها:\n"
            f"{'', ''.join([f'• {c}\n' for c in contacts[:5]])}\n"
            f"{'...' if len(contacts) > 5 else ''}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش فایل: {str(e)}")

async def admin_add_source_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    await query.message.edit_text(
        "🔗 **لطفاً لینک گروه یا کانال را ارسال کنید.**\n\n"
        "مثال: `https://t.me/your_group`\n"
        "یا: `@your_group`\n\n"
        "⚠️ دقت کنید که:\n"
        "1️⃣ خودتان عضو گروه باشید\n"
        "2️⃣ گروه عمومی باشد",
        parse_mode="Markdown"
    )
    context.user_data['waiting_for_source_link'] = True

async def admin_add_source_link(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    if context.user_data.get('waiting_for_auto_save') or context.user_data.get('waiting_for_file_save'):
        return
    
    if not context.user_data.get('waiting_for_source_link'):
        return
    
    link = update.message.text.strip()
    context.user_data['waiting_for_source_link'] = False
    
    match = re.search(r'(?:https?://t\.me/|@)([a-zA-Z0-9_]+)', link)
    if not match:
        await update.message.reply_text("❌ لینک نامعتبر! لطفاً دوباره تلاش کنید.")
        return
    
    username = match.group(1)
    
    try:
        if not client.is_connected():
            await client.start()
        
        entity = await client.get_entity(username)
        chat_id = str(entity.id)
        chat_title = entity.title if hasattr(entity, 'title') else username
        
        add_source_group(chat_id, chat_title, user_id)
        
        await update.message.reply_text(
            f"✅ **گروه با موفقیت اضافه شد!**\n\n"
            f"📌 نام: {chat_title}\n"
            f"🆔 chat_id: `{chat_id}`\n\n"
            f"📊 از این گروه برای تأمین ممبر استفاده خواهد شد.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **خطا در دریافت اطلاعات گروه!**\n\n"
            f"دلیل: {str(e)}"
        )

async def admin_list_sources_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    groups = get_all_source_groups()
    
    if not groups:
        await query.message.edit_text("📋 **لیست گروه‌های منبع خالی است.**\n\nاز دکمه ➕ افزودن گروه استفاده کنید.")
        return
    
    text = "📋 **لیست گروه‌های منبع:**\n\n"
    for gid, chat_id, title, added_at in groups:
        title_display = title or chat_id
        text += f"📌 **{title_display}**\n"
        text += f"   🆔 `{chat_id}`\n"
        text += f"   📅 {added_at[:10] if added_at else 'نامشخص'}\n\n"
    
    text += f"\n🔢 تعداد کل: {len(groups)} گروه"
    
    await query.message.edit_text(text, parse_mode="Markdown")

async def admin_remove_source_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    groups = get_all_source_groups()
    
    if not groups:
        await query.message.edit_text("📋 **لیست گروه‌های منبع خالی است.**")
        return
    
    keyboard = []
    for gid, chat_id, title, _ in groups:
        display = title or chat_id
        keyboard.append([InlineKeyboardButton(f"🗑️ {display}", callback_data=f"admin_remove_{gid}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
    
    await query.message.edit_text(
        "🗑️ **انتخاب گروه برای حذف:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_remove_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    try:
        gid = int(query.data.split('_')[2])
        
        conn = sqlite3.connect("bot_database.db")
        c = conn.cursor()
        c.execute('SELECT chat_title, chat_id FROM source_groups_db WHERE id = ?', (gid,))
        group = c.fetchone()
        c.execute('DELETE FROM source_groups_db WHERE id = ?', (gid,))
        conn.commit()
        conn.close()
        
        if group:
            title = group[0] or group[1]
            await query.message.edit_text(
                f"✅ **گروه '{title}' با موفقیت حذف شد.**\n"
                f"🆔 `{group[1]}`",
                parse_mode="Markdown"
            )
        else:
            await query.message.edit_text("✅ گروه با موفقیت حذف شد.")
        
    except Exception as e:
        await query.message.edit_text(f"❌ خطا: {str(e)}")

async def admin_stats_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders WHERE status='done'")
    done_orders = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now')")
    today_orders = c.fetchone()[0]
    
    c.execute("SELECT SUM(quantity) FROM orders WHERE status='done'")
    total_members = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM source_groups_db")
    source_count = c.fetchone()[0]
    
    conn.close()
    
    await query.message.edit_text(
        f"📊 **آمار کامل ربات:**\n\n"
        f"👥 کل کاربران: {total_users}\n"
        f"📋 کل سفارشات: {total_orders}\n"
        f"✅ سفارشات انجام شده: {done_orders}\n"
        f"👤 کل ممبرهای اضافه شده: {total_members:,}\n"
        f"📅 سفارشات امروز: {today_orders}\n"
        f"📁 گروه‌های منبع: {source_count}"
    )

async def admin_back(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.message.edit_text("❌ شما دسترسی ندارید.")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه منبع", callback_data="admin_add_source")],
        [InlineKeyboardButton("📋 لیست گروه‌های منبع", callback_data="admin_list_sources")],
        [InlineKeyboardButton("🗑️ حذف گروه منبع", callback_data="admin_remove_source")],
        [InlineKeyboardButton("📊 آمار کامل", callback_data="admin_stats")]
    ]
    
    await query.message.edit_text(
        "🔧 **پنل مدیریت**\n\n"
        "یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_source_command(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return
    
    try:
        chat_id = context.args[0] if context.args else None
        if not chat_id:
            await update.message.reply_text(
                "❌ لطفاً chat_id گروه را وارد کنید.\n"
                "مثال: /add_source -1001234567890"
            )
            return
        
        if not client.is_connected():
            await client.start()
        
        entity = await client.get_entity(int(chat_id))
        chat_title = entity.title if hasattr(entity, 'title') else chat_id
        
        add_source_group(chat_id, chat_title, user_id)
        
        await update.message.reply_text(
            f"✅ گروه `{chat_title}` با موفقیت به لیست منبع اضافه شد.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def remove_source_command(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return
    
    try:
        chat_id = context.args[0] if context.args else None
        if not chat_id:
            await update.message.reply_text(
                "❌ لطفاً chat_id گروه را وارد کنید.\n"
                "مثال: /remove_source -1001234567890"
            )
            return
        
        remove_source_group(chat_id)
        
        await update.message.reply_text(
            f"✅ گروه `{chat_id}` از لیست منبع حذف شد.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def list_sources_command(update: Update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return
    
    groups = get_all_source_groups()
    
    if not groups:
        await update.message.reply_text("📋 لیست گروه‌های منبع خالی است.")
        return
    
    text = "📋 **لیست گروه‌های منبع:**\n\n"
    for gid, chat_id, title, added_at in groups:
        title_display = title or chat_id
        text += f"{title_display}\n"
        text += f"🆔 `{chat_id}`\n"
        text += f"📅 {added_at[:10] if added_at else 'نامشخص'}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats(update: Update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ دسترسی ندارید.")
        return
    
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders")
    orders = c.fetchone()[0]
    
    c.execute("SELECT SUM(quantity) FROM orders WHERE status='done'")
    total = c.fetchone()[0] or 0
    
    conn.close()
    
    await update.message.reply_text(
        f"📊 **آمار:**\n\n"
        f"👥 کاربران: {users}\n"
        f"📋 سفارشات: {orders}\n"
        f"👤 ممبر اضافه شده: {total}"
    )

def main():
    token, api_id, api_hash, owner_id = setup_bot()
    
    global OWNER_ID
    OWNER_ID = owner_id
    
    init_db()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = Application.builder().token(token).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_type, pattern="^(type_member)$")],
        states={
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_start$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(show_rules, pattern="^show_rules$"))
    app.add_handler(CallbackQueryHandler(accept_rules, pattern="^accept_rules$"))
    
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add_source", add_source_command))
    app.add_handler(CommandHandler("remove_source", remove_source_command))
    app.add_handler(CommandHandler("list_sources", list_sources_command))
    app.add_handler(CommandHandler("save_contacts", save_contacts))
    
    app.add_handler(CallbackQueryHandler(admin_add_source_callback, pattern="^admin_add_source$"))
    app.add_handler(CallbackQueryHandler(admin_list_sources_callback, pattern="^admin_list_sources$"))
    app.add_handler(CallbackQueryHandler(admin_remove_source_callback, pattern="^admin_remove_source$"))
    app.add_handler(CallbackQueryHandler(admin_remove_confirm, pattern="^admin_remove_"))
    app.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    
    app.add_handler(CallbackQueryHandler(save_contacts_auto, pattern="^save_auto$"))
    app.add_handler(CallbackQueryHandler(save_contacts_file, pattern="^save_file$"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_save))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auto_save_link))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_source_link))
    
    print("\n" + "="*50)
    print("✅ ربات با موفقیت راه‌اندازی شد!")
    print("📋 پنل مدیریت: /admin")
    print("➕ افزودن گروه: /add_source -1001234567890")
    print("👥 ذخیره مخاطب: /save_contacts")
    print("="*50 + "\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()
