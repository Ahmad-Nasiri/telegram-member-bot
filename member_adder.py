import asyncio
import random
from telethon import TelegramClient, errors
from config import API_ID, API_HASH, DELAY_BETWEEN_ADD
from database import get_source_groups, update_progress, update_order_status

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('owner_session', API_ID, API_HASH, loop=loop)

async def scrape_members(quantity, exclude_ids=None):
    if exclude_ids is None:
        exclude_ids = []
    
    source_groups = get_source_groups()
    if not source_groups:
        raise Exception("هیچ گروه منبعی تعریف نشده! از پنل مدیریت گروه اضافه کنید.")
    
    all_members = []
    random.shuffle(source_groups)
    
    for group_id in source_groups:
        try:
            async for user in client.iter_participants(int(group_id), aggressive=True, limit=quantity*2):
                if user.id not in exclude_ids and not user.bot and user.id not in all_members:
                    all_members.append(user.id)
                    if len(all_members) >= quantity:
                        break
        except errors.FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"خطا در اسکرپ {group_id}: {e}")
            continue
        
        if len(all_members) >= quantity:
            break
    
    return all_members[:quantity]

async def add_members_to_chat(chat_id, user_ids, progress_msg, bot):
    added_count = 0
    total = len(user_ids)
    
    for idx, user_id in enumerate(user_ids, 1):
        try:
            await client.add_participants(int(chat_id), user_id)
            added_count += 1
            
            if idx % 5 == 0 or idx == total:
                await progress_msg.edit_text(f"🔄 در حال انجام: {added_count} از {total} ممبر اضافه شد ✅")
            
            await asyncio.sleep(DELAY_BETWEEN_ADD)
            
        except errors.FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except errors.UserPrivacyRestrictedError:
            continue
        except Exception as e:
            print(f"خطا در افزودن {user_id}: {e}")
            continue
    
    return added_count

def extract_chat_id(link):
    import re
    match = re.search(r'(?:https?://t\.me/|@)([a-zA-Z0-9_]+)', link)
    return match.group(1) if match else None

async def add_members_operation(order_id, user_id, target_link, quantity, progress_msg, bot):
    try:
        await client.start()
        await progress_msg.edit_text("🔍 در حال جستجوی ممبر...")
        
        members = await scrape_members(quantity, [user_id])
        
        if not members:
            await progress_msg.edit_text("❌ هیچ ممبری پیدا نشد! از پنل مدیریت گروه منبع اضافه کنید.")
            update_order_status(order_id, "failed")
            return
        
        chat_id = extract_chat_id(target_link)
        if not chat_id:
            await progress_msg.edit_text("❌ لینک نامعتبر!")
            update_order_status(order_id, "failed")
            return
        
        added = await add_members_to_chat(chat_id, members, progress_msg, bot)
        update_order_status(order_id, "done", added)
        await progress_msg.edit_text(f"✅ **عملیات کامل شد!**\n\n📊 {added} ممبر اضافه شد.\n🆔 شماره سفارش: {order_id}")
        
    except Exception as e:
        update_order_status(order_id, "failed")
        await progress_msg.edit_text(f"❌ خطا: {str(e)}")
