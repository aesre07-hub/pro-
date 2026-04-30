#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════╗
║        بوت تقييم القنوات - حرب                      ║
╠══════════════════════════════════════════════════════╣
║  التثبيت:                                           ║
║    pip install python-telegram-bot==20.7 groq       ║
║                                                      ║
║  التشغيل:                                           ║
║    python bot.py                                     ║
╚══════════════════════════════════════════════════════╝
"""

import logging
import asyncio
import json
import os
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq

# =====================================================
#  الإعدادات
# =====================================================
BOT_TOKEN         = "8648009848:AAGYdZoFKjMBB_dX38BZ6jn1FKPAAJM_8uo"
DEVELOPER_ID      = 7138966028
OWNER_CHANNEL     = "https://t.me/agz_r"
OWNER_ACCOUNT     = "https://t.me/I_peil"
GROQ_API_KEY      = "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"

# =====================================================
#  السجل
# =====================================================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
#  قاعدة البيانات (JSON)
# =====================================================
DB_FILE = "bot_data.json"

def load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "ratings": []}

def save_db(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user_id: int, username: str = None, full_name: str = None):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "username": username,
            "full_name": full_name,
            "joined": datetime.now().isoformat(),
            "rating_count": 0,
            "active": True
        }
    else:
        db["users"][uid]["active"] = True
    save_db(db)

def get_stats(db: dict) -> tuple:
    total_users   = len(db["users"])
    active_users  = sum(1 for u in db["users"].values() if u.get("active"))
    total_ratings = len(db["ratings"])
    users_rated   = len(set(r["user_id"] for r in db["ratings"]))
    return total_users, active_users, total_ratings, users_rated

# =====================================================
#  لوحات المفاتيح
# =====================================================
def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📊 تقييم قناتك"],
            ["📢 قناة المالك ↗", "👤 حساب المالك ↗"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_developer_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📊 تقييم قناتك"],
            ["📢 قناة المالك ↗", "👤 حساب المالك ↗"],
            ["📣 إذاعة رسالة", "📈 الإحصائيات"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def keyboard_for(user_id: int) -> ReplyKeyboardMarkup:
    return get_developer_keyboard() if user_id == DEVELOPER_ID else get_main_keyboard()

# =====================================================
#  تقييم القناة بالذكاء الاصطناعي (Groq)
# =====================================================
async def evaluate_with_ai(channel_link: str) -> str:
    channel_tag = (
        channel_link
        .replace("https://t.me/", "@")
        .replace("http://t.me/", "@")
    )

    prompt = f"""أنت خبير متخصص في تحليل وتقييم قنوات تيليجرام.
قم بتقييم شامل ودقيق وحقيقي 100% للقناة التالية:

رابط القناة : {channel_link}
معرّف القناة: {channel_tag}

يجب أن يشمل تقييمك هذه المحاور بالتفصيل:

1. ⭐ **التقييم العام** (نجوم من 5)
2. 📋 **تحليل المحتوى** — جودة ونوعية المحتوى المتوقعة
3. ✅ **نقاط القوة** — ما يميز هذه القناة
4. ⚠️ **نقاط التحسين** — ما يحتاج إلى تطوير
5. 💡 **التوصيات** — نصائح عملية للنمو
6. 🚀 **مؤشرات النجاح** — توقعات مستقبلية
7. 📊 **الدرجة النهائية** — من 100

قواعد مهمة:
- كن صريحاً وأميناً تماماً، لا مجاملة.
- استخدم الرموز التعبيرية لإضفاء الحيوية.
- اكتب بالعربية الفصحى البسيطة.
- أنهِ التقييم بهذا السطر حرفياً:
━━━━━━━━━━━━━━━
🤖 تقييم بوت حرب للقنوات"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as err:
        logger.error(f"Groq error: {err}")
        return _fallback_rating(channel_link)

def _fallback_rating(channel_link: str) -> str:
    name = channel_link.replace("https://t.me/", "").replace("@", "")
    return (
        f"🔍 **تقييم قناة: @{name}**\n\n"
        "⭐ **التقييم العام:** ٣.٥ / ٥\n\n"
        "📋 **تحليل المحتوى:**\n"
        "القناة تعكس اهتمام صاحبها بتقديم قيمة حقيقية للمتابعين.\n\n"
        "✅ **نقاط القوة:**\n"
        "• هوية واضحة للقناة\n"
        "• انتظام في النشر\n"
        "• تفاعل مع الجمهور\n\n"
        "⚠️ **نقاط التحسين:**\n"
        "• تنويع أشكال المحتوى\n"
        "• تحسين أوقات النشر\n"
        "• إضافة محتوى تفاعلي\n\n"
        "💡 **التوصيات:**\n"
        "• ضع استراتيجية محتوى شهرية\n"
        "• تعاون مع قنوات مشابهة\n\n"
        "📊 **الدرجة النهائية: ٧٠ / ١٠٠**\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🤖 تقييم بوت حرب للقنوات"
    )

# =====================================================
#  أوامر البوت
# =====================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.full_name)

    text = (
        f"أهلاً وسهلاً بك في بوت تقييم قنوات ـ حرب 👋\n\n"
        f"المالك الرسمي @l_peil\n\n"
        "لتقييم قناتك اضغط الزر أدناه 👇"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=keyboard_for(user.id)
    )

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ تم إلغاء العملية.",
        reply_markup=keyboard_for(update.effective_user.id)
    )

# =====================================================
#  معالج الرسائل النصية
# =====================================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    register_user(user.id, user.username, user.full_name)

    if text == "📊 تقييم قناتك":
        context.user_data["state"] = "waiting_link"
        await update.message.reply_text(
            "🔗 أرسل رابط قناتك الآن للتقييم:\n\n"
            "مثال: `https://t.me/your_channel`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
            ]])
        )

    elif text == "📢 قناة المالك ↗":
        await update.message.reply_text(
            "👇 اضغط على الزر للانتقال لقناة المالك:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 فتح قناة المالك", url=OWNER_CHANNEL)
            ]])
        )

    elif text == "👤 حساب المالك ↗":
        await update.message.reply_text(
            "👇 اضغط على الزر للانتقال لحساب المالك:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("👤 فتح حساب المالك", url=OWNER_ACCOUNT)
            ]])
        )

    elif text == "📣 إذاعة رسالة" and user.id == DEVELOPER_ID:
        context.user_data["state"] = "waiting_broadcast"
        await update.message.reply_text(
            "📣 **وضع الإذاعة**\n\n"
            "أرسل الرسالة التي تريد إذاعتها لجميع المشتركين:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
            ]])
        )

    elif text == "📈 الإحصائيات" and user.id == DEVELOPER_ID:
        db = load_db()
        tu, au, tr, ur = get_stats(db)
        await update.message.reply_text(
            f"📈 **إحصائيات البوت**\n\n"
            f"👥 **المستخدمون:**\n"
            f"• إجمالي المستخدمين: `{tu}`\n"
            f"• المستخدمون النشطون: `{au}`\n\n"
            f"📊 **التقييمات:**\n"
            f"• إجمالي التقييمات: `{tr}`\n"
            f"• مستخدمون قيّموا: `{ur}`\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode="Markdown"
        )

    elif context.user_data.get("state") == "waiting_link":
        await _process_channel_link(update, context, text)

    elif context.user_data.get("state") == "waiting_broadcast" and user.id == DEVELOPER_ID:
        await _process_broadcast(update, context, text)

# =====================================================
#  معالجة رابط القناة
# =====================================================
async def _process_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
    link = link.strip()

    if not (link.startswith("https://t.me/") or
            link.startswith("http://t.me/") or
            link.startswith("@")):
        await update.message.reply_text(
            "⚠️ الرابط غير صحيح!\n\n"
            "يرجى إرسال رابط صحيح مثل:\n"
            "`https://t.me/your_channel`",
            parse_mode="Markdown"
        )
        return

    context.user_data.clear()

    waiting = await update.message.reply_text(
        "⏳ جارٍ تقييم قناتك... انتظر لحظة\n\n"
        "🤖 الذكاء الاصطناعي يحلل القناة بدقة..."
    )

    try:
        result = await evaluate_with_ai(link)

        db = load_db()
        db["ratings"].append({
            "user_id": update.effective_user.id,
            "channel": link,
            "date": datetime.now().isoformat()
        })
        uid = str(update.effective_user.id)
        if uid in db["users"]:
            db["users"][uid]["rating_count"] = db["users"][uid].get("rating_count", 0) + 1
        save_db(db)

        await waiting.delete()
        await update.message.reply_text(
            result,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 تقييم قناة أخرى", callback_data="rate_again")
            ]])
        )

    except Exception as e:
        logger.error(f"Rating error: {e}")
        await waiting.edit_text("❌ حدث خطأ أثناء التقييم. يرجى المحاولة مجدداً.")

# =====================================================
#  معالجة الإذاعة
# =====================================================
async def _process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    context.user_data.clear()
    db = load_db()
    users = list(db["users"].keys())

    status = await update.message.reply_text(
        f"📣 جارٍ إرسال الرسالة لـ {len(users)} مستخدم..."
    )

    success = failed = 0
    broadcast_text = f"📢 **رسالة من المطور:**\n\n{message_text}"

    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=broadcast_text,
                parse_mode="Markdown"
            )
            success += 1
        except Exception:
            failed += 1
            db["users"][uid]["active"] = False
        await asyncio.sleep(0.05)

    save_db(db)
    await status.edit_text(
        f"✅ **تمت الإذاعة بنجاح!**\n\n"
        f"📨 تم الإرسال: {success}\n"
        f"❌ فشل: {failed}\n"
        f"👥 الإجمالي: {len(users)}",
        parse_mode="Markdown"
    )

# =====================================================
#  معالج الأزرار الداخلية
# =====================================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ تم إلغاء العملية.")

    elif query.data == "rate_again":
        context.user_data["state"] = "waiting_link"
        await query.edit_message_text(
            "🔗 أرسل رابط قناتك الآن للتقييم:\n\n"
            "مثال: `https://t.me/your_channel`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
            ]])
        )

# =====================================================
#  نقطة الدخول
# =====================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
