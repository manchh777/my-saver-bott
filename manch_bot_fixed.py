#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Downloader Bot (YouTube / Instagram / TikTok)
Ամբողջությամբ ուղղված և կայուն տարբերակ — 2026
"""

import os
import json
import time
import traceback
from datetime import datetime

import telebot
from telebot import types
from yt_dlp import YoutubeDL

# ============================================================
# ⚠️ ՏԵՂԱԴՐԵՔ ՁԵՐ ՆՈՐ ՏՈԿԵՆԸ ԱՅՍՏԵՂ
# Հին տոկենը արդեն հանրային է դարձել — պարտադիր նորը վերցրեք BotFather-ից
# ============================================================
BOT_TOKEN = "8970606107:AAFiQqnhM7nnCAulC70glnHGItFDwjok530"
ADMIN_ID = 7639289885  # Ձեր Telegram ID-ն

# 📣 ԱԼԻՔԻ ԿԱՐԳԱՎՈՐՈՒՄՆԵՐ
CHANNEL_ID = "@utoplaa_777"
CHANNEL_URL = "https://t.me/utoplaa_777"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

DB_FILE = "users_db.json"
DAILY_LIMIT = 10
MAX_FILESIZE = 49 * 1024 * 1024  # ~49MB (Telegram սահման)


# ==================== ԲԱԶԱ ====================

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    data.setdefault("users", {})
    data.setdefault("dates", {})
    data.setdefault("last_urls", {})
    data.setdefault("custom_limits", {})
    return data


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


def check_user(user_id, username):
    db = load_db()
    str_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if str_id not in db["users"]:
        db["users"][str_id] = username if username else "NoName"

    if today not in db["dates"]:
        db["dates"][today] = {}

    if str_id not in db["dates"][today]:
        db["dates"][today][str_id] = 0

    save_db(db)
    return db


def get_user_max_limit(user_id):
    db = load_db()
    str_id = str(user_id)
    if str_id in db.get("custom_limits", {}):
        return int(db["custom_limits"][str_id])
    return DAILY_LIMIT


# ==================== ԲԱԺԱՆՈՐԴԱԳՐՈՒԹՅՈՒՆ ====================

def is_subscribed(user_id):
    """Ստուգում է՝ արդյոք օգտատերը բաժանորդագրված է ալիքին"""
    if user_id == ADMIN_ID:
        return True

    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "creator", "administrator", "restricted")
    except Exception as e:
        error_text = str(e).lower()
        if "member list is inaccessible" in error_text or "chat not found" in error_text:
            print("❌ ԿԱՐԵՎՈՐ. Բոտը ադմին չէ ալիքում կամ ալիքի անունը սխալ է։")
            print("   → Ավելացրեք բոտը որպես Administrator @utoplaa_777 ալիքում")
        else:
            print(f"❌ Բաժանորդագրության ստուգման սխալ: {e}")
        return False


def send_sub_request(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Բաժանորդագրվել Ալիքին", url=CHANNEL_URL))
    markup.add(types.InlineKeyboardButton("🔄 Հաստատել Բաժանորդագրությունը", callback_data="check_sub_again"))

    text = (
        "🔒 *Մուտքը սահմանափակ է*\n\n"
        "Բոտի անվճար ֆունկցիաներից օգտվելու համար անհրաժեշտ է բաժանորդագրվել մեր պաշտոնական ալիքին։\n\n"
        "✨ _Դա օգնում է մեզ զարգացնել բոտը և պահել այն միշտ ակտիվ։_\n"
        "Բաժանորդագրվելուց հետո սեղմեք ներքևի կոճակը 👇"
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("👤 Իմ Պրոֆիլը"),
        types.KeyboardButton("ℹ️ Օգնություն / Աջակցում"),
    )
    return markup


# ==================== /start ====================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    check_user(message.chat.id, message.from_user.username)

    if not is_subscribed(message.chat.id):
        send_sub_request(message.chat.id)
        return

    name = message.from_user.first_name or "Օգտատեր"
    welcome_text = (
        f"👋 *Ողջույն, {name}!*\n\n"
        "🚀 Ես մեդիա ներբեռնող բոտ եմ։ Կարող եմ բեռնել վիդեոներ և աուդիոներ հանրահայտ հարթակներից։\n\n"
        "📥 *Ինչպե՞ս օգտվել.*\n"
        "Պարզապես ուղարկիր *YouTube, Instagram կամ TikTok*-ի ցանկացած հղում, և ես կուղարկեմ ֆայլը։"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")


# ==================== ՊՐՈՖԻԼ ====================

@bot.message_handler(commands=["profile"])
@bot.message_handler(func=lambda m: m.text == "👤 Իմ Պրոֆիլը")
def show_profile(message):
    if not is_subscribed(message.chat.id):
        send_sub_request(message.chat.id)
        return

    user_id = message.chat.id
    str_id = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    db = check_user(user_id, message.from_user.username)
    used = db["dates"].get(today, {}).get(str_id, 0)
    max_limit = get_user_max_limit(user_id)
    remains = max(0, max_limit - used)

    remains_text = "Անսահմանափակ" if user_id == ADMIN_ID else str(remains)
    status = "Հիմնադիր/Ադմին" if user_id == ADMIN_ID else "Օգտատեր"

    profile_text = (
        "👤 *ՁԵՐ ԱՆՁՆԱԿԱՆ ՊՐՈՖԻԼԸ*\n\n"
        f"🆔 Ձեր ID: `{user_id}`\n"
        f"👑 Կարգավիճակ: {status}\n\n"
        f"📊 *Այսօրվա վիճակագրություն.*\n"
        f"📥 Ներբեռնված է: `{used}` ֆայլ\n"
        f"🔄 Մնացել է լիմիտից: `{remains_text}`"
    )
    bot.send_message(user_id, profile_text, parse_mode="Markdown")


# ==================== ՕԳՆՈՒԹՅՈՒՆ ====================

@bot.message_handler(func=lambda m: m.text == "ℹ️ Օգնություն / Աջակցում")
def help_request(message):
    if not is_subscribed(message.chat.id):
        send_sub_request(message.chat.id)
        return

    msg = bot.send_message(
        message.chat.id,
        "📝 *Կապ Հիմնադրի հետ*\n\n"
        "Հաջորդ հաղորդագրությամբ գրեք ձեր հարցը, առաջարկը կամ բողոքը։ "
        "Այն կփոխանցվի բոտի հիմնադրին։",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(msg, forward_to_admin)


def forward_to_admin(message):
    """Օգտատիրոջ նամակը ուղարկում է ադմինին (առանց Markdown՝ կայունության համար)"""
    text = message.text or ""
    if text in ("ℹ️ Օգնություն / Աջակցում", "👤 Իմ Պրոֆիլը") or text.startswith("/"):
        bot.send_message(message.chat.id, "❌ Հարցումը չեղարկվեց։")
        return

    username_text = f"@{message.from_user.username}" if message.from_user.username else "Չունի"

    # Առանց parse_mode — որպեսզի օգտատիրոջ տեքստը չկոտրի հաղորդագրությունը
    user_info = (
        f"👤 Նոր նամակ օգտատիրոջից:\n"
        f"🆔 ID: {message.chat.id}\n"
        f"🔗 Username: {username_text}\n\n"
        f"✉️ Հաղորդագրություն:\n{text}\n\n"
        f"📌 Պատասխանելու համար: /reply {message.chat.id} ՁԵՐ_ՊԱՏԱՍԽԱՆԸ"
    )

    try:
        bot.send_message(ADMIN_ID, user_info)
        bot.send_message(
            message.chat.id,
            "✨ Հաջողությամբ ուղարկվեց!\n\nՁեր նամակը հասավ հիմնադրին։",
        )
    except Exception as e:
        print(f"❌ Ադմինին ուղարկելու սխալ: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Չհաջողվեց կապ հաստատել։ Սխալը գրանցված է լոգում։",
        )


# ==================== ԱԴՄԻՆ ՀՐԱՄԱՆՆԵՐ ====================

@bot.message_handler(commands=["reply"])
def reply_to_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Սխալ ձևաչափ։\n\n`/reply [ID] [պատասխան]`", parse_mode="Markdown")
            return
        target_user = int(parts[1])
        reply_text = parts[2]
        bot.send_message(
            target_user,
            f"✉️ *Նոր պատասխան Հիմնադրի կողմից:*\n\n💬 {reply_text}",
            parse_mode="Markdown",
        )
        bot.reply_to(message, "✅ Պատասխանը հաջողությամբ ուղարկվեց։")
    except Exception as e:
        bot.reply_to(message, f"❌ Չհաջողվեց ուղարկել: {e}")


@bot.message_handler(commands=["setlimit"])
def set_user_limit(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(
                message,
                "⚠️ Սխալ ձևաչափ։\n\n`/setlimit [ID] [Ավելացվող_Քանակ]`",
                parse_mode="Markdown",
            )
            return

        target_id = int(parts[1])
        add_limit = int(parts[2])
        current_max = get_user_max_limit(target_id)
        new_max = current_max + add_limit

        db = load_db()
        db["custom_limits"][str(target_id)] = new_max
        save_db(db)

        bot.reply_to(
            message,
            f"✅ `{target_id}` օգտատիրոջ լիմիտին ավելացվեց *{add_limit}*։ "
            f"Նոր ընդհանուր լիմիտը՝ *{new_max}*։",
            parse_mode="Markdown",
        )
        try:
            bot.send_message(
                target_id,
                f"🎉 *Ուրախ լուր!*\n\n"
                f"Հիմնադիրը ձեր օրական լիմիտին ավելացրեց *{add_limit}* ներբեռնում։\n"
                f"📈 Նոր օրական լիմիտ՝ *{new_max}* ֆայլ։",
                parse_mode="Markdown",
            )
        except Exception:
            pass
    except Exception as e:
        bot.reply_to(message, f"❌ Սխալ՝ {e}")


@bot.message_handler(commands=["show"])
def show_all_users(message):
    if message.chat.id != ADMIN_ID:
        return
    db = load_db()
    today = datetime.now().strftime("%Y-%m-%d")

    if not db["users"]:
        bot.reply_to(message, "👥 Բոտում դեռ ոչ մի օգտատեր չկա։")
        return

    list_text = "👥 *ԲՈՏԻ ՕԳՏԱՏԵՐԵՐԻ ՑՈՒՑԱԿԸ*\n\n"
    for str_id, username in db["users"].items():
        max_lim = db["custom_limits"].get(str_id, DAILY_LIMIT)
        used_today = db["dates"].get(today, {}).get(str_id, 0)
        remains = max(0, int(max_lim) - int(used_today))
        uname_text = f"@{username}" if username != "NoName" else "Առանց Username"
        list_text += (
            f"• ID: `{str_id}` | User: {uname_text} | "
            f"Մնացել է: `{remains}/{max_lim}`\n"
        )
        if len(list_text) > 3500:
            bot.send_message(ADMIN_ID, list_text, parse_mode="Markdown")
            list_text = ""

    if list_text:
        bot.send_message(ADMIN_ID, list_text, parse_mode="Markdown")


@bot.message_handler(commands=["manch"])
def send_admin_manual(message):
    if message.chat.id != ADMIN_ID:
        return

    manual_text = (
        "📖 *ԱԴՄԻՆԻ ՀՐԱՄԱՆՆԵՐ*\n\n"
        "🎛 *Հիմնական.*\n"
        "• `/admin` — Ադմին պանել + գովազդ\n"
        "• `/show` — Օգտատերեր և լիմիտներ\n\n"
        "⚙️ *Կառավարում.*\n"
        "• `/setlimit [ID] [ՔԱՆԱԿ]` — լիմիտ գումարել\n"
        "  _Օր.`_ `/setlimit 12345678 5`\n\n"
        "✉️ *Կապ.*\n"
        "• `/reply [ID] [ՏԵՔՍՏ]` — պատասխանել օգտատիրոջը\n"
        "  _Օր.`_ `/reply 12345678 Ձեր հարցը լուծված է`"
    )
    bot.send_message(message.chat.id, manual_text, parse_mode="Markdown")


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    db = load_db()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Ուղարկել Գովազդ", callback_data="admin_spam"))
    bot.send_message(
        message.chat.id,
        f"📊 *ԱԴՄԻՆ ՊԱՆԵԼ*\n\n👥 Օգտատերեր՝ `{len(db['users'])}`",
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data == "admin_spam")
def admin_spam_start(call):
    if call.message.chat.id != ADMIN_ID:
        return
    msg = bot.send_message(call.message.chat.id, "✉️ Ուղարկեք գովազդի տեքստը.")
    bot.register_next_step_handler(msg, admin_spam_send)


def admin_spam_send(message):
    if message.chat.id != ADMIN_ID:
        return
    db = load_db()
    success = 0
    fail = 0
    for user_id in list(db["users"].keys()):
        try:
            bot.send_message(int(user_id), message.text)
            success += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
    bot.send_message(ADMIN_ID, f"✅ Գովազդը հասավ {success} հոգու։ ❌ Չհասավ՝ {fail}։")


@bot.callback_query_handler(func=lambda call: call.data == "check_sub_again")
def check_subscription_callback(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        try:
            bot.delete_message(user_id, call.message.message_id)
        except Exception:
            pass
        success_text = (
            "🎉 *Շնորհավորում ենք, մուտքը հաստատված է!*\n\n"
            "Բաժանորդագրությունը ստուգվեց։ Բոտի ֆունկցիաները *բաց են*։\n\n"
            "📥 Կարող եք ուղարկել ձեր առաջին հղումը։"
        )
        bot.send_message(user_id, success_text, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Դուք դեռ չեք բաժանորդագրվել ալիքին։", show_alert=True)


# ==================== ՆԵՐԲԵՌՆՈՒՄ ====================

SUPPORTED = ("youtube.com", "youtu.be", "instagram.com", "tiktok.com", "vm.tiktok.com")


def is_supported_url(text):
    if not text:
        return False
    lower = text.lower().strip()
    return any(s in lower for s in SUPPORTED) and (
        lower.startswith("http://") or lower.startswith("https://") or "youtube.com" in lower or "youtu.be" in lower
    )


def cleanup_prefix(prefix):
    for f in os.listdir("."):
        if f.startswith(prefix):
            try:
                os.remove(f)
            except OSError:
                pass


@bot.message_handler(func=lambda m: bool(m.text) and is_supported_url(m.text))
def download_media_auto(message):
    user_id = message.chat.id
    if not is_subscribed(user_id):
        send_sub_request(user_id)
        return

    url = message.text.strip()
    str_id = str(user_id)
    username = message.from_user.username

    db = check_user(user_id, username)
    today = datetime.now().strftime("%Y-%m-%d")

    used = db["dates"].get(today, {}).get(str_id, 0)
    max_limit = get_user_max_limit(user_id)

    if user_id != ADMIN_ID and used >= max_limit:
        bot.reply_to(
            message,
            f"❌ *Օրական լիմիտը սպառված է*\n\n"
            f"Դուք արդեն ներբեռնել եք {max_limit} ֆայլ։ Լիմիտը կթարմացվի կեսգիշերին։",
            parse_mode="Markdown",
        )
        return

    status_msg = bot.reply_to(
        message,
        "⏳ *Մեդիաֆայլը ներբեռնվում է...*\n\nԽնդրում ենք սպասել։",
        parse_mode="Markdown",
    )

    prefix = f"dl_{user_id}_{int(time.time())}"
    outtmpl = f"{prefix}_%(autonumber)s.%(ext)s"

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "best[filesize<49M]/best",
        "max_filesize": MAX_FILESIZE,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        db = load_db()
        db["last_urls"][str_id] = url
        save_db(db)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🎵 Ներբեռնել միայն Աուդիո (MP3)", callback_data="get_last_mp3"
            )
        )
        caption = (
            "🎬 *Ձեր մեդիաֆայլը պատրաստ է!*\n\n"
            "💡 _Հուշում. երգը ստանալու համար սեղմեք ներքևի կոճակը։_"
        )

        files = sorted(f for f in os.listdir(".") if f.startswith(prefix))
        if not files:
            raise FileNotFoundError("Ֆայլը չգտնվեց ներբեռնումից հետո")

        image_exts = {".jpg", ".jpeg", ".png", ".webp"}
        video_exts = {".mp4", ".mov", ".mkv", ".webm", ".3gp"}

        if len(files) > 1:
            media_group = []
            open_handles = []
            try:
                for f in files[:10]:
                    ext = os.path.splitext(f)[1].lower()
                    fh = open(f, "rb")
                    open_handles.append(fh)
                    if ext in image_exts:
                        media_group.append(types.InputMediaPhoto(fh))
                    elif ext in video_exts:
                        media_group.append(types.InputMediaVideo(fh))
                if media_group:
                    bot.send_media_group(user_id, media_group)
                bot.send_message(user_id, caption, reply_markup=markup, parse_mode="Markdown")
            finally:
                for fh in open_handles:
                    try:
                        fh.close()
                    except Exception:
                        pass
                for f in files:
                    try:
                        os.remove(f)
                    except OSError:
                        pass
        else:
            filename = files[0]
            ext = os.path.splitext(filename)[1].lower()
            with open(filename, "rb") as media_file:
                if ext in image_exts:
                    bot.send_photo(
                        user_id, media_file, caption=caption,
                        reply_markup=markup, parse_mode="Markdown",
                    )
                else:
                    bot.send_video(
                        user_id, media_file, caption=caption,
                        reply_markup=markup, parse_mode="Markdown",
                    )
            try:
                os.remove(filename)
            except OSError:
                pass

        try:
            bot.delete_message(user_id, status_msg.message_id)
        except Exception:
            pass

        # Լիմիտ +1
        db = load_db()
        if today not in db["dates"]:
            db["dates"][today] = {}
        db["dates"][today][str_id] = db["dates"][today].get(str_id, 0) + 1
        save_db(db)

        new_used = db["dates"][today][str_id]
        if user_id != ADMIN_ID and (max_limit - new_used) == 1:
            uname = f"@{username}" if username else "Չունի"
            alert_text = (
                f"🚨 *ԱՀԱԶԱՆԳ ԼԻՄԻՏԻ ՄԱՍԻՆ*\n\n"
                f"👤 Օգտատեր՝ {uname}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"⚠️ Մնացել է *1* ներբեռնում։\n"
                f"Ավելացնել՝ `/setlimit {user_id} 5`"
            )
            try:
                bot.send_message(ADMIN_ID, alert_text, parse_mode="Markdown")
            except Exception:
                pass

    except Exception as e:
        err = str(e)[:150]
        try:
            bot.edit_message_text(
                f"❌ *Ներբեռնման սխալ*\n\nՉհաջողվեց ներբեռնել։ "
                f"Հնարավոր է հղումը սխալ է կամ էջը փակ է։\n`{err}`",
                user_id,
                status_msg.message_id,
                parse_mode="Markdown",
            )
        except Exception:
            bot.send_message(user_id, f"❌ Ներբեռնման սխալ: `{err}`", parse_mode="Markdown")
        cleanup_prefix(prefix)
        print(traceback.format_exc())


@bot.message_handler(func=lambda m: bool(m.text) and not m.text.startswith("/") and m.text not in (
    "👤 Իմ Պրոֆիլը", "ℹ️ Օգնություն / Աջակցում"
))
def unknown_text(message):
    if not is_subscribed(message.chat.id):
        send_sub_request(message.chat.id)
        return
    bot.reply_to(
        message,
        "⚠️ *Անհայտ հղում*\n\n"
        "Ուղարկեք միայն վավեր հղումներ *YouTube, Instagram կամ TikTok*-ից։",
        parse_mode="Markdown",
    )


# ==================== MP3 ====================

@bot.callback_query_handler(func=lambda call: call.data == "get_last_mp3")
def process_mp3_callback(call):
    user_id = call.message.chat.id
    str_id = str(user_id)
    if not is_subscribed(user_id):
        bot.answer_callback_query(call.id, "Բաժանորդագրվեք ալիքին։", show_alert=True)
        return

    db = load_db()
    if str_id not in db.get("last_urls", {}):
        bot.send_message(user_id, "❌ Վերջին հղումը չգտնվեց։ Նորից ուղարկեք վիդեոյի հղումը։")
        return

    url = db["last_urls"][str_id]
    status_msg = bot.send_message(
        user_id,
        "🎵 *Երգը առանձնացվում է...*\n\nՍպասեք մի պահ։",
        parse_mode="Markdown",
    )

    prefix = f"aud_{user_id}_{int(time.time())}"
    outtmpl = f"{prefix}.%(ext)s"

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "max_filesize": MAX_FILESIZE,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared = ydl.prepare_filename(info)

        final_file = None
        candidates = [
            os.path.splitext(prepared)[0] + ".mp3",
            f"{prefix}.mp3",
            os.path.splitext(prepared)[0] + ".m4a",
            f"{prefix}.m4a",
            prepared,
        ]
        for p in candidates:
            if os.path.exists(p):
                final_file = p
                break

        if not final_file:
            for f in os.listdir("."):
                if f.startswith(prefix):
                    final_file = f
                    break

        if not final_file or not os.path.exists(final_file):
            raise FileNotFoundError("Աուդիո ֆայլը չգտնվեց (ստուգեք՝ ffmpeg տեղադրվա՞ծ է)")

        with open(final_file, "rb") as audio_file:
            bot.send_audio(
                user_id,
                audio_file,
                caption="🎵 *Ձեր աուդիոֆայլը պատրաստ է!*",
                parse_mode="Markdown",
            )

        try:
            os.remove(final_file)
        except OSError:
            pass
        cleanup_prefix(prefix)

        try:
            bot.delete_message(user_id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        err = str(e)[:150]
        try:
            bot.edit_message_text(
                f"❌ *Աուդիոյի սխալ*\n\n`{err}`\n\n"
                "_Հուշում. MP3-ի համար սերվերում պետք է լինի ffmpeg:_ `pkg install ffmpeg`",
                user_id,
                status_msg.message_id,
                parse_mode="Markdown",
            )
        except Exception:
            bot.send_message(user_id, f"❌ Աուդիոյի սխալ: `{err}`", parse_mode="Markdown")
        cleanup_prefix(prefix)
        print(traceback.format_exc())

# ==================== ԳՈՐԾԱՐԿՈՒՄ (24/7 ԱՆՎՃԱՐ ՀՈՍԹԻՆԳԻ ՀԱՄԱՐ) ====================
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Բոտը ակտիվ է և աշխատում է 24/7:"

def run_server():
    # Render-ը ավտոմատ տալիս է PORT միջավայրի փոփոխականը
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

if __name__ == "__main__":
    print("🚀 Վեբ-սերվերը գործարկվում է...")
    keep_alive()  # Միացնում է Flask սերվերը Render-ի համար
    
    print("🚀 Բոտը գործարկվում է...")
    print("📦 Պահանջներ: pip install pyTelegramBotAPI yt-dlp flask")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except KeyboardInterrupt:
        print("\n⏹ Բոտը կանգնեցվեց։")
    except Exception as e:
        print(f"❌ Կրիտիկական սխալ: {e}")
        traceback.print_exc()
