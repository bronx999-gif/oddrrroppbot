#!/usr/bin/env python3
"""
Aadhaar Info Bot — ULTIMATE v6 FINAL
+ STRICT FORCE JOIN (fail-closed)
+ Single live message flow
+ Full OTP flow
+ Admin: Cracked All PDFs viewer + ZIP download
+ Welcome / Boy / Girl images
+ Custom name input
+ Credit: @dimpiiix | @dimpiii_modz
+ Owner: @dimpiiix
"""

import os
import sys
import importlib
import asyncio
import telebot
import json
import threading
import time
import sqlite3
import random
import string
import re
import shutil
import zipfile
from datetime import datetime, date, timedelta
from telebot import types, apihelper
from dotenv import load_dotenv

# ===================== GLOBAL STATE =====================
user_states = {}
loop = None
loading_state = {}

# --- REQUIREMENT CHECKER ---
REQUIRED_MODULES = {
    "telebot": "pyTelegramBotAPI",
    "requests": "requests",
    "urllib3": "urllib3",
    "dotenv": "python-dotenv",
    "ddddocr": "ddddocr",
    "fitz": "pymupdf",
    "phonenumbers": "phonenumbers"
}

REQUIRED_FILES = {
    "stats_manager.py": "Core stats registry manager",
    "aadhaar_engine.py": "Core Aadhaar backend engine",
    "retrive-eid.py": "Phase 1 bypass subprocess",
    "aadhar-downlaod.py": "Phase 2 download subprocess",
    "pdf_processor.py": "PDF processing engine"
}


def check_startup_requirements():
    print("=" * 60)
    print("        AADHAAR TELEGRAM BOT - STARTUP VERIFICATION")
    print("=" * 60)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n[PKG] Verifying Python Package Dependencies:")
    print("-" * 60)
    missing_packages = []
    for module_name, pip_name in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {pip_name:<20} -> PRESENT")
        except ImportError:
            print(f"  [!!] {pip_name:<20} -> MISSING")
            missing_packages.append(pip_name)

    print("\n[FILE] Verifying Core Codebase Files:")
    print("-" * 60)
    missing_files = []
    for file_name, desc in REQUIRED_FILES.items():
        full_path = os.path.join(base_dir, file_name)
        if os.path.exists(full_path):
            print(f"  [OK] {file_name:<22} -> PRESENT")
        else:
            print(f"  [!!] {file_name:<22} -> MISSING")
            missing_files.append(file_name)

    print("\n[ENV] Verifying Environment Settings (.env):")
    print("-" * 60)
    env_path = os.path.join(base_dir, ".env")
    env_exists = os.path.exists(env_path)
    token_found = False
    if env_exists:
        print("  [OK] .env Configuration File -> FOUND")
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()
        for line in env_content.splitlines():
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                val = line.split("=", 1)[1].strip().replace("'", "").replace('"', '')
                if val:
                    token_found = True
        print("  [OK] TELEGRAM_BOT_TOKEN -> CONFIGURED" if token_found else "  [!!] TELEGRAM_BOT_TOKEN -> MISSING")
    else:
        print("  [!!] .env Configuration File -> MISSING")

    print("=" * 60 + "\n")
    if len(missing_packages) > 0 or len(missing_files) > 0 or not env_exists or not token_found:
        print("[ERROR] STARTUP ERROR: Critical requirements missing!")
        if missing_packages:
            print(f"pip install {' '.join(missing_packages)}\n")
        if missing_files:
            for f in missing_files:
                print(f"   - {f}")
        if not env_exists or not token_found:
            print("   Create .env with: TELEGRAM_BOT_TOKEN=xxx")
        sys.exit(1)
    else:
        print("[OK] All requirements met! Starting Aadhaar Bot...\n")


check_startup_requirements()
# --- REQUIREMENT CHECKER END ---

load_dotenv()
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    import aadhaar_engine
    from aadhaar_engine import user_page_registry
except Exception as e:
    print(f"[ERROR] Failed to import aadhaar_engine: {e}")
    sys.exit(1)

# ===================== CONFIG =====================
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("[ERROR] TELEGRAM_BOT_TOKEN missing in .env")
    sys.exit(1)

ADMIN_USERNAME = "dimpiiix"
DEVELOPER_LINK = f"https://t.me/{ADMIN_USERNAME}"

FORCE_JOIN_CHANNELS_RAW = os.getenv('FORCE_JOIN_CHANNELS', '@dimpiii_modz')
FORCE_JOIN_CHANNELS = []
for ch in FORCE_JOIN_CHANNELS_RAW.split(','):
    ch = ch.strip()
    if not ch:
        continue
    if ch.lstrip('-').isdigit():
        FORCE_JOIN_CHANNELS.append(int(ch))
    else:
        FORCE_JOIN_CHANNELS.append(ch)

FORCE_JOIN_PRIMARY = FORCE_JOIN_CHANNELS[0] if FORCE_JOIN_CHANNELS else '@dimpiii_modz'
FORCE_JOIN_URL = os.getenv('FORCE_JOIN_CHANNEL_URL', 'https://t.me/dimpiii_modz')

SRC_PRICE = 1499
AUTO_DELETE_SECONDS = 30
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bot_data.db')
CRACKED_DIR = os.path.join(BASE_DIR, 'cracked_aadhar')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')

WELCOME_IMAGE = os.path.join(BASE_DIR, 'welcome.png')
BOY_IMAGE = os.path.join(BASE_DIR, 'boy.png')
GIRL_IMAGE = os.path.join(BASE_DIR, 'girl.png')

ADMIN_IDS_RAW = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(',') if x.strip().isdigit()]
if not ADMIN_IDS:
    print("[WARN] ADMIN_IDS is empty. Set ADMIN_IDS=123456789 in .env")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(CRACKED_DIR, exist_ok=True)

print(f"[FORCE JOIN] Channels: {FORCE_JOIN_CHANNELS}")


# ===================== DB INIT =====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT, first_name TEXT, last_name TEXT,
                  custom_name TEXT,
                  gender TEXT, banned INTEGER DEFAULT 0,
                  ban_reason TEXT,
                  join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS src_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, username TEXT, first_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  admin_id INTEGER, total INTEGER, success INTEGER, failed INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS error_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, error TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS downloads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, username TEXT, first_name TEXT,
                  custom_name TEXT, mobile TEXT, prefix TEXT,
                  pdf_filename TEXT, pdf_path TEXT,
                  status TEXT DEFAULT 'success',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

    try:
        conn = sqlite3.connect(DB_PATH)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'custom_name' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN custom_name TEXT")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB MIGRATE] {e}")

    try:
        conn = sqlite3.connect(DB_PATH)
        defaults = {
            'maintenance': '0',
            'force_join': '1',
            'auto_delete': str(AUTO_DELETE_SECONDS),
            'notify_admin_on_download': '1',
        }
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", (k, v))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB INIT] {e}")


init_db()


# ===================== BOT INIT =====================
class BotExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print(f"[TELEBOT EXC] {exception}")
        err = str(exception)
        if "getaddrinfo failed" in err or "NewConnectionError" in err or "Max retries exceeded" in err:
            time.sleep(5)
        return True


apihelper.SESSION_TIME_TO_LIVE = 5 * 60
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', exception_handler=BotExceptionHandler())

orig_send_message = bot.send_message
orig_edit_message_text = bot.edit_message_text


def safe_send_message(*args, **kwargs):
    kwargs.pop('timeout', None)
    last_exc = None
    for attempt in range(3):
        try:
            return orig_send_message(*args, **kwargs)
        except Exception as e:
            es = str(e)
            last_exc = e
            if ("blocked" in es or "Forbidden" in es or "chat not found" in es
                    or "user is deactivated" in es):
                raise e
            print(f"[SEND RETRY {attempt+1}/3]: {e}")
            if attempt < 2:
                time.sleep(1)
    if last_exc:
        raise last_exc


def safe_edit_message_text(*args, **kwargs):
    kwargs.pop('timeout', None)
    last_exc = None
    for attempt in range(3):
        try:
            return orig_edit_message_text(*args, **kwargs)
        except Exception as e:
            es = str(e)
            last_exc = e
            if "message is not modified" in es:
                return True
            if "blocked" in es or "Forbidden" in es or "chat not found" in es:
                raise e
            print(f"[EDIT RETRY {attempt+1}/3]: {e}")
            if attempt < 2:
                time.sleep(1)
    if last_exc:
        raise last_exc


bot.send_message = safe_send_message
bot.edit_message_text = safe_edit_message_text


# ===================== SMALL CAPS FONT =====================
SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
    'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
    's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ',
    'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
    'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
}


def scp(text):
    return ''.join(SMALL_CAPS_MAP.get(ch, ch) for ch in str(text))


LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━"


# ===================== DB HELPERS =====================
def db_get(key, default=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row[0] if row else default
    except Exception:
        return default


def db_set(key, value):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def is_maintenance():
    return db_get('maintenance', '0') == '1'


def save_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute('SELECT user_id FROM users WHERE user_id=?', (user_id,)).fetchone()
        if row:
            conn.execute(
                'UPDATE users SET username=?, first_name=?, last_name=?, last_seen=CURRENT_TIMESTAMP WHERE user_id=?',
                (username, first_name, last_name, user_id))
        else:
            conn.execute('INSERT INTO users (user_id, username, first_name, last_name) VALUES (?,?,?,?)',
                         (user_id, username, first_name, last_name))
        conn.commit()
    finally:
        conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_custom_name(user_id):
    u = get_user(user_id)
    return u.get('custom_name') if u else None


def set_custom_name(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET custom_name=? WHERE user_id=?', (name, user_id))
    conn.commit()
    conn.close()


def get_gender(user_id):
    u = get_user(user_id)
    return u.get('gender') if u else None


def set_gender(user_id, gender):
    conn = sqlite3.connect(DB_PATH)
    if gender is None:
        conn.execute('UPDATE users SET gender=NULL WHERE user_id=?', (user_id,))
    else:
        conn.execute('UPDATE users SET gender=? WHERE user_id=?', (gender, user_id))
    conn.commit()
    conn.close()


def is_banned(user_id):
    u = get_user(user_id)
    return bool(u and u.get('banned'))


def ban_user(user_id, reason):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET banned=1, ban_reason=? WHERE user_id=?', (reason, user_id))
    conn.commit()
    conn.close()


def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE users SET banned=0, ban_reason=NULL WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()
    return [r[0] for r in rows]


def log_error(user_id, error):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT INTO error_logs (user_id, error) VALUES (?,?)', (user_id, str(error)[:500]))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ===================== CRACKED PDFs SCANNER =====================
def get_all_cracked_pdfs():
    """
    Scan CRACKED_DIR for all PDFs.
    Returns list of dicts: [{'index': i, 'filename': ..., 'path': ..., 'size': bytes, 'mtime': ...}]
    Sorted by newest first.
    """
    pdfs = []
    if not os.path.exists(CRACKED_DIR):
        return pdfs

    try:
        for f in os.listdir(CRACKED_DIR):
            if f.lower().endswith('.pdf'):
                path = os.path.join(CRACKED_DIR, f)
                try:
                    stat = os.stat(path)
                    pdfs.append({
                        'filename': f,
                        'path': path,
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                    })
                except Exception:
                    pass
    except Exception as e:
        print(f"[CRACKED SCAN ERR] {e}")
        return []

    # Sort by mtime (newest first)
    pdfs.sort(key=lambda x: x['mtime'], reverse=True)

    # Add index
    for i, p in enumerate(pdfs):
        p['index'] = i

    return pdfs


# ===================== STRICT FORCE JOIN =====================
def get_force_join():
    return db_get('force_join', '1') == '1'


def check_membership(user_id):
    """
    STRICT: Returns (is_member, missing_channels).
    Fail-CLOSED — if bot can't verify, treat as NOT joined.
    """
    if not FORCE_JOIN_CHANNELS:
        return (True, [])

    missing = []

    for channel in FORCE_JOIN_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            status = member.status
            if status in ['member', 'administrator', 'creator']:
                continue
            else:
                missing.append(channel)
        except telebot.apihelper.ApiTelegramException as e:
            err = str(e).lower()
            if ("user not found" in err or "user_not_participant" in err
                    or "participant" in err or "user is banned" in err):
                missing.append(channel)
            elif ("chat not found" in err or "not enough rights" in err
                  or "bot is not a member" in err or "chat_admin_required" in err):
                print(f"[FJ STRICT] Cannot verify {channel}: {e} — treating as NOT JOINED")
                missing.append(channel)
            else:
                print(f"[FJ ERR] {channel}: {e}")
                missing.append(channel)
        except Exception as e:
            print(f"[FJ GENERIC] {channel}: {e}")
            missing.append(channel)

    return (len(missing) == 0, missing)


def is_member(user_id):
    if not get_force_join():
        return True
    if user_id in ADMIN_IDS:
        return True
    ok, _ = check_membership(user_id)
    return ok


def get_missing_channels(user_id):
    _, missing = check_membership(user_id)
    return missing


def enforce_force_join(uid, chat_id):
    if is_banned(uid):
        return False
    if uid in ADMIN_IDS:
        return True
    if not get_force_join():
        return True

    if not is_member(uid):
        ok, missing = check_membership(uid)
        send_force_join(chat_id, missing)
        return False
    return True


# ===================== SINGLE-MESSAGE LOADER =====================
def start_loading(chat_id, title="Processing", subtitle="", mobile="", step_label=""):
    stop_loading(chat_id, delete=True)

    stop_event = threading.Event()

    state = {
        'stop': stop_event,
        'msg_id': None,
        'title': title,
        'step_label': step_label or title,
        'subtitle': subtitle,
        'mobile': mobile,
    }
    loading_state[chat_id] = state

    try:
        msg = bot.send_message(
            chat_id,
            f"<b>{state['step_label']}...</b>",
            parse_mode='HTML'
        )
        state['msg_id'] = msg.message_id
    except Exception as e:
        print(f"[LOADER ERR] {e}")
        return None

    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    bars = [
        "▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱▱▱",
        "▰▰▰▱▱▱▱▱▱▱", "▰▰▰▰▱▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱▱",
        "▰▰▰▰▰▰▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▰▰▱▱",
        "▰▰▰▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰▰▰▰",
    ]

    def animate():
        i = 0
        while not stop_event.is_set():
            try:
                frame = frames[i % len(frames)]
                bar = bars[i % len(bars)]
                pct = min(99, (i * 7) % 100)

                text = (
                    f"        ✦ ✦ ✦\n"
                    f"     {frame} <b>{state['step_label']}</b>\n"
                    f"        ✦ ✦ ✦\n\n"
                    f"  ╭────────────────────╮\n"
                    f"  │  📱  <code>{state['mobile']}</code>\n"
                    f"  ╰────────────────────╯\n\n"
                    f"  <code>{bar}</code>  {pct}%\n\n"
                    f"  ⚡ <i>{state['subtitle'] or 'Please wait...'}</i>\n"
                    f"  ⏳ <i>Don't close this chat</i>"
                )

                bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=state['msg_id'],
                    parse_mode='HTML'
                )
                i += 1
                time.sleep(0.9)
            except Exception:
                time.sleep(1)

    t = threading.Thread(target=animate, daemon=True)
    t.start()
    return state['msg_id']


def update_loading(chat_id, title=None, subtitle=None, step_label=None, mobile=None):
    state = loading_state.get(chat_id)
    if not state:
        return
    if title is not None:
        state['title'] = title
    if subtitle is not None:
        state['subtitle'] = subtitle
    if step_label is not None:
        state['step_label'] = step_label
    if mobile is not None:
        state['mobile'] = mobile


def stop_loading(chat_id, delete=True):
    state = loading_state.pop(chat_id, None)
    if not state:
        return
    try:
        state['stop'].set()
    except Exception:
        pass

    if delete and state.get('msg_id'):
        try:
            bot.delete_message(chat_id, state['msg_id'])
        except Exception:
            pass


# ===================== DOWNLOADS TRACKING =====================
def save_download_record(user_id, username, first_name, custom_name, mobile, prefix, pdf_filename, pdf_path):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            '''INSERT INTO downloads (user_id, username, first_name, custom_name, mobile, prefix, pdf_filename, pdf_path)
               VALUES (?,?,?,?,?,?,?,?)''',
            (user_id, username, first_name, custom_name, mobile, prefix, pdf_filename, pdf_path)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DOWNLOAD REC ERR] {e}")
        return False


def get_all_downloads(limit=200):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?', (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_user_downloads(user_id, limit=100):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM downloads WHERE user_id=? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def notify_admin_download(user_id, first_name, username, custom_name, mobile, prefix, pdf_path, pdf_filename):
    if db_get('notify_admin_on_download', '1') != '1':
        return
    for admin_id in ADMIN_IDS:
        try:
            caption = (
                f"📥 <b>NEW AADHAAR DOWNLOAD</b>\n"
                f"{LINE}\n"
                f"👤 <b>Name:</b> {custom_name or first_name or 'User'}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"💬 <b>Username:</b> @{username or 'N/A'}\n"
                f"⚧ <b>Gender:</b> {prefix or 'N/A'}\n"
                f"📱 <b>Mobile:</b> <code>{mobile}</code>\n"
                f"📄 <b>File:</b> {pdf_filename}\n"
                f"🕐 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            )
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    bot.send_document(admin_id, f, caption=caption, parse_mode='HTML')
            else:
                bot.send_message(admin_id, caption, parse_mode='HTML')
        except Exception as e:
            print(f"[ADMIN NOTIFY ERR {admin_id}] {e}")


# ===================== AUTO DELETE =====================
def auto_delete(chat_id, message_id, seconds=None):
    if seconds is None:
        try:
            seconds = int(db_get('auto_delete', str(AUTO_DELETE_SECONDS)))
        except Exception:
            seconds = AUTO_DELETE_SECONDS
    if seconds <= 0:
        return

    def _del():
        time.sleep(seconds)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

    threading.Thread(target=_del, daemon=True).start()


def wrapped_send(chat_id, text, *args, **kwargs):
    is_admin = chat_id in ADMIN_IDS
    no_delete = kwargs.pop('permanent', False) or kwargs.pop('is_announcement', False)
    msg = bot.send_message(chat_id, text, *args, **kwargs)
    if not is_admin and not no_delete:
        auto_delete(chat_id, msg.message_id)
    return msg


# ===================== BUTTONS =====================
BTN_DOWNLOAD = "📥 ᴅᴏᴡɴʟᴏᴀᴅ ᴀᴀᴅʜᴀᴀʀ"
BTN_PROFILE = "👤 ᴘʀᴏꜰɪʟᴇ"
BTN_CHANGE_G = "🔄 ᴄʜᴀɴɢᴇ ɢᴇɴᴅᴇʀ"
BTN_CHANGE_NAME = "✏️ ᴄʜᴀɴɢᴇ ɴᴀᴍᴇ"
BTN_SRC = "💻 ʙᴜʏ sᴏᴜʀᴄᴇ"
BTN_MALE = "👦 ᴍᴀʟᴇ"
BTN_FEMALE = "👧 ꜰᴇᴍᴀʟᴇ"
BTN_CANCEL = "🚫 ᴄᴀɴᴄᴇʟ"
BTN_DEV = "👨‍💻 ᴅᴇᴠ"
BTN_MAIN_MENU = "🏠 ᴍᴀɪɴ ᴍᴇɴᴜ"
BTN_ADMIN = "👑 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ"


# ===================== KEYBOARDS =====================
def rkb(text, style=None):
    try:
        return types.KeyboardButton(text, style=style) if style else types.KeyboardButton(text)
    except Exception:
        return types.KeyboardButton(text)


def ikb(text, style=None, url=None, callback_data=None):
    try:
        if url:
            return types.InlineKeyboardButton(text, url=url, style=style) if style else types.InlineKeyboardButton(text, url=url)
        if callback_data:
            return types.InlineKeyboardButton(text, callback_data=callback_data, style=style) if style else types.InlineKeyboardButton(text, callback_data=callback_data)
    except Exception:
        if url:
            return types.InlineKeyboardButton(text, url=url)
        return types.InlineKeyboardButton(text, callback_data=callback_data)


def get_main_keyboard(user_id):
    gender = get_gender(user_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not gender:
        kb.row(rkb(BTN_MALE, 'primary'), rkb(BTN_FEMALE, 'primary'))
        return kb
    kb.row(rkb(BTN_DOWNLOAD, 'primary'))
    kb.row(rkb(BTN_PROFILE, 'success'), rkb(BTN_CHANGE_NAME, 'primary'))
    kb.row(rkb(BTN_CHANGE_G, 'danger'), rkb(BTN_SRC, 'success'))
    if user_id in ADMIN_IDS:
        kb.row(rkb(BTN_ADMIN, 'danger'))
    return kb


def get_cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(rkb(BTN_CANCEL, 'danger'))
    return kb


def get_otp_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(rkb(BTN_CANCEL, 'danger'), rkb(BTN_DEV, 'primary'))
    return kb


def get_join_kb(missing_channels=None):
    kb = types.InlineKeyboardMarkup(row_width=1)

    channels_to_show = missing_channels if missing_channels else FORCE_JOIN_CHANNELS

    for i, ch in enumerate(channels_to_show, 1):
        if isinstance(ch, int):
            url = FORCE_JOIN_URL
            label = f"📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {i}"
        else:
            username = ch.lstrip('@')
            url = f"https://t.me/{username}"
            label = f"📢 ᴊᴏɪɴ @{username}"

        kb.row(ikb(label, style='primary', url=url))

    kb.row(ikb("✅ ɪ'ᴠᴇ ᴊᴏɪɴᴇᴅ — ᴠᴇʀɪꜰʏ", style='success', callback_data="check_join"))
    return kb


def send_photo_safe(chat_id, image_path, caption, reply_markup=None, parse_mode='Markdown'):
    try:
        if os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                return bot.send_photo(chat_id, img, caption=caption,
                                     reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        print(f"[IMG SEND ERR] {image_path}: {e}")
    return bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode=parse_mode)


# ===================== GENDER + NAME FLOW =====================
def send_gender_selection(chat_id, first_name=None):
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   👤 *{scp('SELECT YOUR GENDER')}* 👤\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"✨ *{scp('Choose your gender to continue')}*\n\n"
        f"{LINE}\n"
        f"👦 *{scp('Male')}* — {scp('Tap to select')}\n"
        f"👧 *{scp('Female')}* — {scp('Tap to select')}\n\n"
        f"{LINE}\n"
        f"⚡ _{scp('You can change this later from menu')}_"
    )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(rkb(BTN_MALE, 'primary'), rkb(BTN_FEMALE, 'primary'))
    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")


def send_name_input(chat_id, gender):
    emoji = "👦" if gender == 'boy' else "👧"
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   ✏️ *{scp('ENTER YOUR NAME')}* ✏️\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{emoji} *{scp('Gender')}:* {gender.title()}\n\n"
        f"{LINE}\n"
        f"💬 *{scp('Please send your full name')}*\n\n"
        f"📌 *{scp('Example')}:* `Rahul Sharma`\n\n"
        f"{LINE}\n"
        f"⚡ _{scp('This name will be used in Aadhaar PDF')}_"
    )
    msg = bot.send_message(chat_id, text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_name_input)


def process_name_input(m):
    uid = m.from_user.id
    chat_id = m.chat.id

    if not enforce_force_join(uid, chat_id):
        return

    text = m.text.strip() if m.text else ''

    if text == BTN_CANCEL or text.lower() in ['/cancel', 'cancel']:
        set_gender(uid, None)
        send_gender_selection(chat_id)
        return

    clean = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if len(clean) < 2 or len(clean) > 60:
        msg = bot.send_message(chat_id,
            f"❌ *{scp('Invalid Name')}*\n\n📌 Use 2-60 letters only",
            reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_name_input)
        return

    set_custom_name(uid, clean.title())
    save_user(uid, m.from_user.username or '', m.from_user.first_name or '', m.from_user.last_name or '')
    send_welcome(chat_id, uid, clean)


def get_prefix_from_gender(user_id):
    g = get_gender(user_id)
    if g == 'boy':
        return 'Mr.'
    if g == 'girl':
        return 'Mrs.'
    return ''


# ===================== FORCE JOIN MESSAGE =====================
def send_force_join(chat_id, missing_channels=None):
    channels_text = ""
    show_channels = missing_channels if missing_channels else FORCE_JOIN_CHANNELS

    for i, ch in enumerate(show_channels, 1):
        if isinstance(ch, int):
            name = f"Channel {i}"
        else:
            name = ch if ch.startswith('@') else f"@{ch}"
        channels_text += f"  {i}. {name}\n"

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   🔒 *{scp('JOIN REQUIRED')}* 🔒\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"⚠️ *{scp('Please join our channel(s) to continue')}*\n\n"
        f"{LINE}\n"
        f"📢 *{scp('Required Channels')}:*\n"
        f"{channels_text}\n"
        f"{LINE}\n\n"
        f"➡️ _{scp('Click JOIN, then tap VERIFY')}_\n\n"
        f"👑 *{scp('Owner')}:* @{ADMIN_USERNAME}"
    )

    try:
        bot.send_message(
            chat_id, text,
            reply_markup=get_join_kb(missing_channels),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[FJ SEND ERR] {e}")


def send_maintenance_msg(chat_id):
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   🔧 *{scp('MAINTENANCE MODE')}* 🔧\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"⚠️ *{scp('Bot is under maintenance')}*\n\n"
        f"{LINE}\n"
        f"🔄 *{scp('Please try again later')}*\n\n"
        f"👑 *{scp('Owner')}:* @{ADMIN_USERNAME}"
    )
    try:
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
        pass


# ===================== WELCOME =====================
def build_welcome_text(display_name, user_id, gender=None):
    name = (display_name or "User").upper()
    gender_line = ""
    if gender:
        e = "👦" if gender == 'boy' else "👧"
        gender_line = f"{e} *{scp('Gender')}:* {gender.title()}\n"
    return (
        f"👋 *{scp('WELCOME')}, {name}!*\n\n"
        f"🤖 ɪ ᴀᴍ 𓆩 *𝐀𝐀𝐃𝐇𝐀𝐀𝐑 𝐈𝐍𝐅𝐎 𝐁𝐎𝐓* 𓆪\n\n"
        f"📥 ᴅᴏᴡɴʟᴏᴀᴅ ᴀᴀᴅʜᴀᴀʀ ᴘᴅꜰ\n"
        f"👤 ᴜꜱᴇʀ ᴘʀᴏꜰɪʟᴇ\n\n"
        f"{LINE}\n"
        f"⭐ *{scp('User ID')}:* `{user_id}`\n"
        f"{gender_line}"
        f"👑 *{scp('Owner')}:* @{ADMIN_USERNAME}\n"
        f"{LINE}"
    )


def send_welcome(chat_id, user_id, display_name=None):
    gender = get_gender(user_id)
    custom_name = get_custom_name(user_id)
    name = custom_name or display_name or "User"
    text = build_welcome_text(name, user_id, gender)

    if gender == 'boy' and os.path.exists(BOY_IMAGE):
        send_photo_safe(chat_id, BOY_IMAGE, text,
                       reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")
    elif gender == 'girl' and os.path.exists(GIRL_IMAGE):
        send_photo_safe(chat_id, GIRL_IMAGE, text,
                       reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")
    elif os.path.exists(WELCOME_IMAGE):
        send_photo_safe(chat_id, WELCOME_IMAGE, text,
                       reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")
    else:
        try:
            bot.send_message(chat_id, text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")
        except Exception as e:
            print(f"[WELCOME ERR] {e}")


# ===================== /start =====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_banned(user_id):
        bot.send_message(chat_id, f"🚫 *{scp('YOU ARE BANNED')}*\n\n👑 @{ADMIN_USERNAME}", parse_mode="Markdown")
        return
    if is_maintenance() and user_id not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    save_user(user_id, message.from_user.username or '',
              message.from_user.first_name or '', message.from_user.last_name or '')

    if not enforce_force_join(user_id, chat_id):
        return

    gender = get_gender(user_id)
    custom_name = get_custom_name(user_id)
    if not gender:
        send_gender_selection(chat_id, message.from_user.first_name)
    elif not custom_name:
        send_name_input(chat_id, gender)
    else:
        send_welcome(chat_id, user_id)


# ===================== GENDER HANDLERS =====================
@bot.message_handler(func=lambda m: m.text == BTN_MALE)
def gender_male(m):
    uid = m.from_user.id
    if not enforce_force_join(uid, m.chat.id):
        return
    save_user(uid, m.from_user.username or '', m.from_user.first_name or '', m.from_user.last_name or '')
    set_gender(uid, 'boy')
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   👦 *{scp('MALE SELECTED')}* 👦\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"✅ *{scp('Gender set to Male')}*\n\n"
        f"{LINE}\n"
        f"➡️ _{scp('Now enter your name')}_"
    )
    if os.path.exists(BOY_IMAGE):
        send_photo_safe(m.chat.id, BOY_IMAGE, text, parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, text, parse_mode="Markdown")
    send_name_input(m.chat.id, 'boy')


@bot.message_handler(func=lambda m: m.text == BTN_FEMALE)
def gender_female(m):
    uid = m.from_user.id
    if not enforce_force_join(uid, m.chat.id):
        return
    save_user(uid, m.from_user.username or '', m.from_user.first_name or '', m.from_user.last_name or '')
    set_gender(uid, 'girl')
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   👧 *{scp('FEMALE SELECTED')}* 👧\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"✅ *{scp('Gender set to Female')}*\n\n"
        f"{LINE}\n"
        f"➡️ _{scp('Now enter your name')}_"
    )
    if os.path.exists(GIRL_IMAGE):
        send_photo_safe(m.chat.id, GIRL_IMAGE, text, parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, text, parse_mode="Markdown")
    send_name_input(m.chat.id, 'girl')


@bot.message_handler(func=lambda m: m.text == BTN_CHANGE_G)
def gender_change(m):
    uid = m.from_user.id
    if not enforce_force_join(uid, m.chat.id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(m.chat.id)
        return
    set_gender(uid, None)
    send_gender_selection(m.chat.id)


@bot.message_handler(func=lambda m: m.text == BTN_CHANGE_NAME)
def change_name_handler(m):
    uid = m.from_user.id
    if not enforce_force_join(uid, m.chat.id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(m.chat.id)
        return
    msg = bot.send_message(m.chat.id,
        f"✏️ *{scp('Enter new name')}*\n\n📌 Example: `Rahul Sharma`",
        reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_name_input)


# ===================== CHECK JOIN CALLBACK =====================
@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def check_join_cb(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id

    if is_maintenance() and uid not in ADMIN_IDS:
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        send_maintenance_msg(chat_id)
        return

    ok, missing = check_membership(uid)

    if ok:
        try:
            bot.answer_callback_query(call.id, "✅ Verified! Welcome.")
        except Exception:
            pass
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        save_user(uid, call.from_user.username or '',
                  call.from_user.first_name or '', call.from_user.last_name or '')

        gender = get_gender(uid)
        custom_name = get_custom_name(uid)
        if not gender:
            send_gender_selection(chat_id)
        elif not custom_name:
            send_name_input(chat_id, gender)
        else:
            send_welcome(chat_id, uid)
    else:
        try:
            bot.answer_callback_query(
                call.id,
                f"❌ Please join all {len(missing)} channel(s) first!",
                show_alert=True
            )
        except Exception:
            pass

        channels_text = ""
        for i, ch in enumerate(missing, 1):
            if isinstance(ch, int):
                name = f"Channel {i}"
            else:
                name = ch if ch.startswith('@') else f"@{ch}"
            channels_text += f"  {i}. {name}\n"

        text = (
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"   🔒 *{scp('STILL NOT JOINED')}* 🔒\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"⚠️ *{scp('You still need to join')}:*\n\n"
            f"{LINE}\n"
            f"{channels_text}\n"
            f"{LINE}\n\n"
            f"➡️ _{scp('Join above, then tap VERIFY again')}_"
        )
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=get_join_kb(missing),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[FJ EDIT ERR] {e}")


# ===================== DOWNLOAD AADHAAR (FULL OTP FLOW) =====================
@bot.message_handler(func=lambda m: m.text == BTN_DOWNLOAD)
def download_start(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    if not enforce_force_join(uid, chat_id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    gender = get_gender(uid)
    custom_name = get_custom_name(uid)
    if not gender:
        send_gender_selection(chat_id)
        return
    if not custom_name:
        send_name_input(chat_id, gender)
        return

    user_states[uid] = {'step': 'AWAITING_MOBILE'}
    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   📥 *{scp('DOWNLOAD AADHAAR')}* 📥\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"💬 *{scp('Send 10-digit mobile number')}*\n\n"
        f"📌 *{scp('Example')}:* `9876543210`\n\n"
        f"{LINE}\n"
        f"💡 _{scp('Send /cancel to abort')}_"
    )
    msg = bot.send_message(chat_id, text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_mobile_input)


def process_mobile_input(m):
    uid = m.from_user.id
    chat_id = m.chat.id

    if not enforce_force_join(uid, chat_id):
        user_states[uid] = {'step': 'IDLE'}
        return

    text = m.text.strip() if m.text else ''

    if text == BTN_CANCEL or text.lower() in ['/cancel', 'cancel']:
        user_states[uid] = {'step': 'IDLE'}
        bot.send_message(chat_id, f"❌ *{scp('Cancelled')}*",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        return

    clean = re.sub(r'\D', '', text)
    if len(clean) > 10 and (text.startswith('+91') or clean.startswith(('91', '0'))):
        clean = clean[-10:]
    if len(clean) != 10 or clean[0] not in '6789':
        msg = bot.send_message(chat_id, f"❌ *{scp('Invalid Mobile Number')}*\n\n📌 Example: `9876543210`",
                               reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_mobile_input)
        return

    prefix = get_prefix_from_gender(uid)
    custom_name = get_custom_name(uid) or m.from_user.first_name or "User"
    user_info = {
        'username': m.from_user.username or 'N/A',
        'first_name': m.from_user.first_name or 'N/A',
        'custom_name': custom_name,
        'gender': get_gender(uid),
    }

    state_obj = {
        'mobile': clean,
        'prefix': prefix,
        'custom_name': custom_name,
        'user_info': user_info,
        'stage': 'finding',
    }
    user_states[uid] = {'step': 'PROCESSING', 'mobile': clean, 'flow': state_obj}

    start_loading(
        chat_id,
        title="FINDING AADHAAR",
        step_label="ꜰɪɴᴅɪɴɢ ᴀᴀᴅʜᴀᴀʀ",
        subtitle="Searching database...",
        mobile=clean
    )

    def _stage1():
        try:
            if loop is None or not loop.is_running():
                raise RuntimeError("Async loop not running")

            fut = asyncio.run_coroutine_threadsafe(
                aadhaar_engine.execute_task(
                    bot, chat_id, prefix, clean, None,
                    user_info=user_info,
                    stage_callback=lambda stage, extra=None: on_engine_stage(
                        uid, chat_id, stage, clean, state_obj, extra
                    )
                ),
                loop
            )
            result = fut.result(timeout=900)
            print(f"[ENGINE DONE] user={uid} mobile={clean} result={result}")

            time.sleep(3)
            pdf_path, pdf_filename = find_latest_pdf_for_user(uid, clean, custom_name)

            stop_loading(chat_id, delete=True)

            for key in list(loading_state.keys()):
                stop_loading(key, delete=True)

            if pdf_path:
                save_download_record(
                    uid, m.from_user.username or 'N/A', m.from_user.first_name or 'N/A',
                    custom_name, clean, prefix, pdf_filename, pdf_path
                )
                notify_admin_download(
                    uid, m.from_user.first_name or 'User', m.from_user.username or 'N/A',
                    custom_name, clean, prefix, pdf_path, pdf_filename
                )

                success_text = (
                    f"╭━━━━━━━━━━━━━━━━━━╮\n"
                    f"   ✅ *{scp('PDF READY')}* ✅\n"
                    f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
                    f"📄 *{scp('File')}:* {pdf_filename}\n"
                    f"📱 *{scp('Mobile')}:* `{clean}`\n\n"
                    f"{LINE}\n"
                    f"💡 _{scp('PDF sent to admin successfully')}_"
                )
                bot.send_message(chat_id, success_text,
                                reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
            else:
                bot.send_message(chat_id,
                    f"⚠️ *{scp('Process ended but no PDF found')}*\n\n"
                    f"📱 Mobile: `{clean}`\n\n"
                    f"Contact admin if issue persists.",
                    reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        except Exception as e:
            print(f"[ENGINE EXC] {e}")
            log_error(uid, f"execute_task failed: {e}")
            stop_loading(chat_id, delete=True)
            bot.send_message(chat_id, f"❌ *{scp('Error')}*: {e}",
                            reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        finally:
            user_states[uid] = {'step': 'IDLE'}

    threading.Thread(target=_stage1, daemon=True).start()


def on_engine_stage(uid, chat_id, stage, mobile, state_obj, extra=None):
    try:
        extra = extra or {}

        if stage == 'finding':
            update_loading(chat_id, step_label="ꜰɪɴᴅɪɴɢ ᴀᴀᴅʜᴀᴀʀ", subtitle="Searching database...")

        elif stage == 'aadhaar_found':
            update_loading(chat_id, step_label="ᴀᴀᴅʜᴀᴀʀ ꜰᴏᴜɴᴅ ✅", subtitle="Now sending OTP...")
            time.sleep(1.2)

        elif stage == 'otp_sent':
            stop_loading(chat_id, delete=True)
            text = (
                f"╭━━━━━━━━━━━━━━━━━━╮\n"
                f"   📲 *{scp('OTP SENT')}* 📲\n"
                f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
                f"✅ *{scp('OTP successfully sent')}*\n\n"
                f"📱 *{scp('Mobile')}:* `{mobile}`\n\n"
                f"{LINE}\n"
                f"💬 *{scp('Enter the OTP received on SMS')}*\n\n"
                f"⚡ _{scp('Check your SMS inbox')}_"
            )
            bot.send_message(chat_id, text, reply_markup=get_otp_keyboard(), parse_mode="Markdown")
            user_states[uid] = {'step': 'AWAITING_OTP', 'mobile': mobile, 'flow': state_obj}
            state_obj['stage'] = 'waiting_otp'

        elif stage == 'otp_verified':
            start_loading(chat_id, title="VERIFYING OTP",
                         step_label="ᴠᴇʀɪꜰʏɪɴɢ ᴏᴛᴘ",
                         subtitle="Checking OTP...", mobile=mobile)
            time.sleep(1.2)

        elif stage == 'downloading':
            update_loading(chat_id, step_label="ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀᴀᴅʜᴀᴀʀ", subtitle="Fetching Aadhaar PDF...")

        elif stage == 'downloaded':
            update_loading(chat_id, step_label="ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ✅", subtitle="Now cracking PDF...")
            time.sleep(1.2)

        elif stage == 'cracking':
            update_loading(chat_id, step_label="ᴄʀᴀᴄᴋɪɴɢ ᴘᴅꜰ", subtitle="Decrypting Aadhaar PDF...")

        elif stage == 'otp2_sent':
            update_loading(chat_id, step_label="ᴏᴛᴘ 2 sᴇɴᴛ", subtitle="Enter second OTP...")

        elif stage == 'otp2_waiting':
            stop_loading(chat_id, delete=True)
            bot.send_message(chat_id,
                f"📲 *{scp('OTP 2 SENT')}*\n\n"
                f"📱 `{mobile}`\n\n"
                f"💬 *{scp('Enter the second OTP')}*",
                reply_markup=get_otp_keyboard(), parse_mode="Markdown")
            user_states[uid] = {'step': 'AWAITING_OTP', 'mobile': mobile, 'flow': state_obj}

        elif stage == 'otp2_verified':
            start_loading(chat_id, title="VERIFYING",
                         step_label="ᴠᴇʀɪꜰʏɪɴɢ ᴏᴛᴘ 2",
                         subtitle="Checking second OTP...", mobile=mobile)

        elif stage == 'ready':
            update_loading(chat_id, step_label="ꜰɪɴᴀʟɪᴢɪɴɢ ✅", subtitle="Preparing your PDF...")

        elif stage == 'error':
            stop_loading(chat_id, delete=True)
            err_msg = extra.get('message', 'Unknown error')
            bot.send_message(chat_id,
                f"❌ *{scp('Task Failed')}*\n\n{err_msg}",
                reply_markup=get_main_keyboard(uid), parse_mode="Markdown")

    except Exception as e:
        print(f"[STAGE CB ERR] {stage}: {e}")


# ===================== OTP INPUT HANDLER =====================
@bot.message_handler(
    func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'AWAITING_OTP'
)
def otp_input_handler(m):
    uid = m.from_user.id
    chat_id = m.chat.id

    if not enforce_force_join(uid, chat_id):
        return

    text = m.text.strip() if m.text else ''

    if text == BTN_CANCEL or text.lower() in ['/cancel', 'cancel']:
        uid_str = str(uid)
        registry = getattr(aadhaar_engine, 'user_page_registry', {})
        if uid_str in registry:
            try:
                registry[uid_str]['value'] = '__CANCEL__'
            except Exception:
                pass
        user_states[uid] = {'step': 'IDLE'}
        stop_loading(chat_id, delete=True)
        bot.send_message(chat_id, f"❌ *{scp('Cancelled')}*",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        return

    if text == BTN_DEV:
        bot.send_message(chat_id,
            f"👨‍💻 *{scp('Developer')}*\n\n👑 @{ADMIN_USERNAME}",
            parse_mode="Markdown")
        return

    clean = re.sub(r'\D', '', text)
    if len(clean) < 4 or len(clean) > 8:
        bot.send_message(chat_id,
            f"❌ *{scp('Invalid OTP')}*\n\n📌 Enter 4-8 digit OTP",
            reply_markup=get_otp_keyboard(), parse_mode="Markdown")
        return

    uid_str = str(uid)
    registry = getattr(aadhaar_engine, 'user_page_registry', {})
    if uid_str in registry:
        try:
            registry[uid_str]['value'] = clean
        except Exception:
            pass
    else:
        buffered = getattr(aadhaar_engine, 'buffered_inputs', None)
        if buffered is not None:
            buffered[uid_str] = clean

    start_loading(
        chat_id,
        title="VERIFYING OTP",
        step_label="ᴠᴇʀɪꜰʏɪɴɢ ᴏᴛᴘ",
        subtitle="Checking OTP...",
        mobile=user_states.get(uid, {}).get('mobile', '')
    )

    flow = user_states.get(uid, {}).get('flow', {})
    user_states[uid] = {'step': 'PROCESSING_OTP', 'flow': flow}


# ===================== CAPTCHA INTERCEPTOR =====================
@bot.message_handler(
    content_types=['text'],
    func=lambda m: str(m.from_user.id) in aadhaar_engine.user_page_registry
    and aadhaar_engine.user_page_registry[str(m.from_user.id)].get('value') is None
)
def captcha_otp_interceptor(m):
    uid_str = str(m.from_user.id)
    try:
        aadhaar_engine.user_page_registry[uid_str]['value'] = m.text.strip()
    except Exception:
        return
    try:
        if m.chat.id < 0:
            bot.delete_message(m.chat.id, m.message_id)
    except Exception:
        pass


# ===================== PDF FINDER =====================
def find_latest_pdf_for_user(uid, mobile, custom_name):
    candidates = []

    user_folder = os.path.join(DOWNLOADS_DIR, str(uid))
    if os.path.exists(user_folder):
        for f in os.listdir(user_folder):
            if f.lower().endswith('.pdf'):
                p = os.path.join(user_folder, f)
                candidates.append((p, f, os.path.getmtime(p)))

    if os.path.exists(CRACKED_DIR):
        for f in os.listdir(CRACKED_DIR):
            if f.lower().endswith('.pdf'):
                p = os.path.join(CRACKED_DIR, f)
                candidates.append((p, f, os.path.getmtime(p)))

    for f in os.listdir(BASE_DIR):
        if f.lower().endswith('.pdf'):
            p = os.path.join(BASE_DIR, f)
            candidates.append((p, f, os.path.getmtime(p)))

    if not candidates:
        return None, None

    matching = [c for c in candidates if mobile in c[1]]
    if matching:
        matching.sort(key=lambda x: x[2], reverse=True)
        return matching[0][0], matching[0][1]

    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[0][0], candidates[0][1]


# ===================== PROFILE =====================
@bot.message_handler(func=lambda m: m.text == BTN_PROFILE)
def profile_handler(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    if not enforce_force_join(uid, chat_id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    save_user(uid, m.from_user.username or '', m.from_user.first_name or '', m.from_user.last_name or '')
    user = get_user(uid) or {}
    gender = (user.get('gender') or 'Not set').title()
    custom_name = user.get('custom_name') or 'Not set'
    joined = user.get('join_date', 'N/A')
    last_seen = user.get('last_seen', 'N/A')
    downloads = get_user_downloads(uid, limit=100)

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   👤 *{scp('MY PROFILE')}* 👤\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"⭐ *{scp('User ID')}:* `{uid}`\n"
        f"👥 *{scp('Name')}:* {custom_name}\n"
        f"💬 *{scp('Username')}:* @{m.from_user.username or 'N/A'}\n"
        f"⚧ *{scp('Gender')}:* {gender}\n\n"
        f"{LINE}\n"
        f"📅 *{scp('Joined')}:* {str(joined)[:19]}\n"
        f"🕐 *{scp('Last Seen')}:* {str(last_seen)[:19]}\n"
        f"📄 *{scp('Downloads')}:* {len(downloads)}\n\n"
        f"{LINE}\n"
        f"👑 *{scp('Owner')}:* @{ADMIN_USERNAME}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(ikb("🔄 ᴄʜᴀɴɢᴇ ɢᴇɴᴅᴇʀ", style='primary', callback_data="cb_change_gender"))
    wrapped_send(chat_id, text, reply_markup=kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: c.data == "cb_change_gender")
def cb_change_gender(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    if not enforce_force_join(uid, chat_id):
        return
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    set_gender(uid, None)
    send_gender_selection(chat_id)


# ===================== BUY SOURCE =====================
@bot.message_handler(func=lambda m: m.text == BTN_SRC)
def src_handler(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    if not enforce_force_join(uid, chat_id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT INTO src_requests (user_id, username, first_name) VALUES (?,?,?)',
                     (uid, m.from_user.username or 'N/A', m.from_user.first_name or 'User'))
        conn.commit()
        conn.close()
    except Exception:
        pass

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(ikb("📞 ᴅᴍ ᴛᴏ ʙᴜʏ", style='success', url=DEVELOPER_LINK))

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   💻 *{scp('BUY SOURCE CODE')}* 💻\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📄 *{scp('Aadhaar Info Bot SRC')}*\n\n"
        f"{LINE}\n"
        f"⭐ *{scp('Features')}:*\n"
        f"• {scp('Free Mode (No Credits)')}\n"
        f"• {scp('Gender + Custom Name')}\n"
        f"• {scp('Full OTP Flow')}\n"
        f"• {scp('Advance Admin Panel')}\n"
        f"• {scp('Force Join Multi-Channel')}\n"
        f"• {scp('Broadcast System')}\n"
        f"• {scp('Cracked PDF Archive')}\n"
        f"• {scp('Auto-forward PDFs to Admin')}\n\n"
        f"{LINE}\n"
        f"💰 *{scp('Price')}:* ₹{SRC_PRICE}\n"
        f"✔️ *{scp('Instant delivery')}*\n"
        f"🛡️ *{scp('Lifetime support')}*\n\n"
        f"{LINE}\n"
        f"👑 @{ADMIN_USERNAME}"
    )
    wrapped_send(chat_id, text, reply_markup=kb, parse_mode="Markdown")


# ===================== CANCEL / RESET =====================
@bot.message_handler(commands=['cancel', 'reset'])
def cancel_cmd(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    uid_str = str(uid)

    registry = getattr(aadhaar_engine, 'user_page_registry', {})
    if uid_str in registry:
        try:
            registry[uid_str]['value'] = '__CANCEL__'
        except Exception:
            pass

    buffered = getattr(aadhaar_engine, 'buffered_inputs', None)
    if buffered is not None:
        buffered.pop(uid_str, None)

    active_engines = getattr(aadhaar_engine, 'active_engines', None)
    if active_engines is not None and uid_str in active_engines:
        eng = active_engines.pop(uid_str, None)
        if eng:
            try:
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(eng.close(), loop)
            except Exception:
                pass

    active_tasks = getattr(aadhaar_engine, 'active_tasks', None)
    if active_tasks is not None:
        try:
            active_tasks.remove(uid_str)
        except Exception:
            pass

    stop_loading(chat_id, delete=True)
    user_states[uid] = {'step': 'IDLE'}
    bot.send_message(chat_id, f"✅ *{scp('Session Reset Successfully')}*",
                     reply_markup=get_main_keyboard(uid), parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == BTN_CANCEL)
def cancel_btn(m):
    cancel_cmd(m)


@bot.message_handler(func=lambda m: m.text == BTN_DEV)
def dev_btn(m):
    bot.send_message(m.chat.id,
        f"👨‍💻 *{scp('Developer')}*\n\n👑 @{ADMIN_USERNAME}",
        parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == BTN_MAIN_MENU)
def main_menu_btn(m):
    start_cmd(m)


# ===================== ADMIN PANEL =====================
def get_admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(ikb("📊 ᴅᴀꜱʜʙᴏᴀʀᴅ", 'success', callback_data="ad_dash"),
           ikb("🔄 ʀᴇꜰʀᴇꜱʜ", 'primary', callback_data="ad_dash"))
    kb.row(ikb("👥 ᴜꜱᴇʀꜱ", 'primary', callback_data="ad_users_1"),
           ikb("📥 ᴅᴏᴡɴʟᴏᴀᴅꜱ", 'success', callback_data="ad_downloads_1"))
    # ⭐ NEW — Cracked PDFs
    kb.row(ikb("📂 ᴄʀᴀᴄᴋᴇᴅ ᴀʟʟ ᴘᴅꜰ", 'success', callback_data="ad_cracked_1"),
           ikb("💾 ᴢɪᴘ ᴀʟʟ ᴘᴅꜰ", 'primary', callback_data="ad_cracked_zip"))
    kb.row(ikb("🚫 ʙᴀɴɴᴇᴅ", 'danger', callback_data="ad_banned"),
           ikb("🔍 ᴄʜᴇᴄᴋ ᴜꜱᴇʀ", 'primary', callback_data="ad_check"))
    kb.row(ikb("📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ", 'success', callback_data="ad_bc_menu"),
           ikb("📨 ᴍꜱɢ ᴜꜱᴇʀ", 'primary', callback_data="ad_msg_user"))
    kb.row(ikb("🚫 ʙᴀɴ ᴜꜱᴇʀ", 'danger', callback_data="ad_ban"),
           ikb("✅ ᴜɴʙᴀɴ", 'success', callback_data="ad_unban"))
    kb.row(ikb("📈 ꜱᴛᴀᴛꜱ", 'success', callback_data="ad_stats"),
           ikb("🏆 ᴛᴏᴘ ᴜꜱᴇʀꜱ", 'success', callback_data="ad_top"))
    kb.row(ikb("⚙️ ꜱᴇᴛᴛɪɴɢꜱ", 'primary', callback_data="ad_settings"),
           ikb("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", 'danger', callback_data="ad_maint_menu"))
    kb.row(ikb("📢 ꜰᴏʀᴄᴇ ᴊᴏɪɴ", 'primary', callback_data="ad_fj_menu"),
           ikb("💻 ꜱʀᴄ ʀᴇQ", 'primary', callback_data="ad_src"))
    kb.row(ikb("📋 ᴇʀʀᴏʀ ʟᴏɢꜱ", 'danger', callback_data="ad_logs"),
           ikb("🧹 ᴄʟᴇᴀɴ ᴛᴇᴍᴘ", 'success', callback_data="ad_clean"))
    kb.row(ikb("💾 ʙᴀᴄᴋᴜᴘ ᴅʙ", 'success', callback_data="ad_backup"),
           ikb("📥 ᴇxᴘᴏʀᴛ ᴜꜱᴇʀꜱ", 'success', callback_data="ad_export"))
    kb.row(ikb("📄 ᴇxᴘᴏʀᴛ ᴅᴏᴡɴʟᴏᴀᴅꜱ", 'success', callback_data="ad_export_downloads"))
    kb.row(ikb("🔔 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴛɪꜰʏ ᴏɴ", 'success', callback_data="ad_notify_on"),
           ikb("🔕 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴛɪꜰʏ ᴏꜰꜰ", 'danger', callback_data="ad_notify_off"))
    kb.row(ikb("🔴 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴏɴ", 'danger', callback_data="ad_maint_on"),
           ikb("🟢 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴏꜰꜰ", 'success', callback_data="ad_maint_off"))
    kb.row(ikb("❌ ᴄʟᴏꜱᴇ", 'danger', callback_data="ad_close"))
    return kb


@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    uid = m.from_user.id
    if uid not in ADMIN_IDS:
        bot.send_message(m.chat.id, f"❌ *{scp('Access Denied')}*", parse_mode="Markdown")
        return
    send_admin_dash(m.chat.id)


@bot.message_handler(func=lambda m: m.text == BTN_ADMIN and m.from_user.id in ADMIN_IDS)
def admin_btn(m):
    send_admin_dash(m.chat.id)


def send_admin_dash(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tu = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    tb = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
    boys = c.execute("SELECT COUNT(*) FROM users WHERE gender='boy'").fetchone()[0]
    girls = c.execute("SELECT COUNT(*) FROM users WHERE gender='girl'").fetchone()[0]
    sr = c.execute("SELECT COUNT(*) FROM src_requests").fetchone()[0]
    el = c.execute("SELECT COUNT(*) FROM error_logs").fetchone()[0]
    dl = c.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
    conn.close()

    # Cracked PDFs count
    cracked_count = len(get_all_cracked_pdfs())

    maint = "🔴 ON" if is_maintenance() else "🟢 OFF"
    fj = "🟢 ON" if get_force_join() else "🔴 OFF"
    notify = "🟢 ON" if db_get('notify_admin_on_download', '1') == '1' else "🔴 OFF"

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"   👑 *{scp('ADMIN PANEL')}* 👑\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👥 *{scp('Users')}:* {tu}\n"
        f"🚫 *{scp('Banned')}:* {tb}\n"
        f"👦 *{scp('Boys')}:* {boys}  |  👧 *{scp('Girls')}:* {girls}\n"
        f"📥 *{scp('Total Downloads')}:* {dl}\n"
        f"📂 *{scp('Cracked PDFs')}:* {cracked_count}\n"
        f"💻 *{scp('SRC Requests')}:* {sr}\n"
        f"📋 *{scp('Errors')}:* {el}\n\n"
        f"{LINE}\n"
        f"🔧 *{scp('Maintenance')}:* {maint}\n"
        f"📢 *{scp('Force Join')}:* {fj}\n"
        f"🔔 *{scp('Download Notify')}:* {notify}\n"
        f"👑 *{scp('Owner')}:* @{ADMIN_USERNAME}"
    )
    bot.send_message(chat_id, text, reply_markup=get_admin_kb(), parse_mode="Markdown")


# ===================== ADMIN CALLBACKS =====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ad_"))
def admin_callbacks(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    if uid not in ADMIN_IDS:
        try:
            bot.answer_callback_query(call.id, "Access Denied")
        except Exception:
            pass
        return
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    d = call.data

    if d == "ad_dash":
        send_admin_dash(chat_id)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_close":
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    # ⭐ Cracked All PDFs — paginated list
    elif d.startswith("ad_cracked_") and not d == "ad_cracked_zip":
        try:
            page = int(d.replace("ad_cracked_", ""))
        except Exception:
            page = 1

        pdfs = get_all_cracked_pdfs()
        per = 10
        total = len(pdfs)
        total_p = max(1, (total + per - 1) // per)
        page = max(1, min(page, total_p))
        start = (page - 1) * per
        chunk = pdfs[start:start + per]

        if total == 0:
            text = (
                f"📂 *{scp('CRACKED AADHAAR')}*\n\n"
                f"{LINE}\n"
                f"⚠️ _{scp('No cracked PDFs found yet')}_\n\n"
                f"💡 _{scp('Download some Aadhaar first')}_"
            )
            kb = types.InlineKeyboardMarkup()
            kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                      reply_markup=kb, parse_mode="Markdown")
            except Exception:
                bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")
            return

        total_size = sum(p.get('size', 0) for p in pdfs)
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024*1024):.2f} MB"
        else:
            size_str = f"{total_size / 1024:.1f} KB"

        text = (
            f"📂 *{scp('CRACKED AADHAAR')}* ({page}/{total_p})\n\n"
            f"{LINE}\n"
            f"📄 *{scp('Total PDFs')}:* {total}\n"
            f"💾 *{scp('Total Size')}:* {size_str}\n"
            f"{LINE}\n\n"
            f"*{scp('Tap any PDF to download')}*\n\n"
        )

        kb = types.InlineKeyboardMarkup(row_width=1)
        for i, p in enumerate(chunk, start + 1):
            fname = p['filename']
            sz_kb = p['size'] / 1024
            display = fname[:28] + ("…" if len(fname) > 28 else "")
            label = f"📄 {i}. {display} ({sz_kb:.0f}KB)"
            cb_data = f"ad_getpdf|{p['index']}"
            kb.row(ikb(label, style='primary', callback_data=cb_data))

        nav = []
        if page > 1:
            nav.append(ikb("⬅️ ᴘʀᴇᴠ", 'primary', callback_data=f"ad_cracked_{page-1}"))
        if page < total_p:
            nav.append(ikb("ɴᴇxᴛ ➡️", 'primary', callback_data=f"ad_cracked_{page+1}"))
        if nav:
            kb.row(*nav)

        kb.row(ikb("💾 ᴢɪᴘ ᴀʟʟ", 'success', callback_data="ad_cracked_zip"),
               ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))

        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    # ⭐ Send single cracked PDF
    elif d.startswith("ad_getpdf|"):
        try:
            idx = int(d.split("|", 1)[1])
        except Exception:
            try:
                bot.answer_callback_query(call.id, "Invalid PDF", show_alert=True)
            except Exception:
                pass
            return

        pdfs = get_all_cracked_pdfs()
        if idx < 0 or idx >= len(pdfs):
            try:
                bot.answer_callback_query(call.id, "PDF not found", show_alert=True)
            except Exception:
                pass
            return

        p = pdfs[idx]
        path = p['path']
        if not os.path.exists(path):
            try:
                bot.answer_callback_query(call.id, "File missing on disk", show_alert=True)
            except Exception:
                pass
            return

        try:
            bot.answer_callback_query(call.id, "Sending PDF...")
        except Exception:
            pass

        try:
            with open(path, 'rb') as f:
                bot.send_document(
                    chat_id, f,
                    caption=f"📄 <b>{p['filename']}</b>\n💾 {p['size']/1024:.0f} KB",
                    parse_mode='HTML'
                )
        except Exception as e:
            bot.send_message(chat_id, f"❌ Failed: {e}")

    # ⭐ Zip all PDFs and send
    elif d == "ad_cracked_zip":
        pdfs = get_all_cracked_pdfs()
        if not pdfs:
            try:
                bot.answer_callback_query(call.id, "No PDFs to zip", show_alert=True)
            except Exception:
                pass
            return

        try:
            bot.answer_callback_query(call.id, f"Zipping {len(pdfs)} PDFs...")
        except Exception:
            pass

        progress_msg = bot.send_message(chat_id,
            f"💾 *{scp('Creating ZIP')}...*\n\n"
            f"📄 Total: {len(pdfs)} PDFs\n"
            f"⏳ Please wait...",
            parse_mode="Markdown")

        def _zip_worker():
            zip_path = os.path.join(BASE_DIR, f"cracked_aadhaar_{int(time.time())}.zip")
            try:
                # Show progress
                bot.edit_message_text(
                    f"💾 *{scp('Compressing')}...*\n\n"
                    f"📄 0/{len(pdfs)}",
                    chat_id=chat_id, message_id=progress_msg.message_id,
                    parse_mode="Markdown"
                )

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for i, p in enumerate(pdfs, 1):
                        try:
                            zf.write(p['path'], arcname=p['filename'])
                        except Exception as e:
                            print(f"[ZIP WARN] {p['filename']}: {e}")
                        # Update progress every 5 files
                        if i % 5 == 0 or i == len(pdfs):
                            try:
                                bot.edit_message_text(
                                    f"💾 *{scp('Compressing')}...*\n\n"
                                    f"📄 {i}/{len(pdfs)}",
                                    chat_id=chat_id, message_id=progress_msg.message_id,
                                    parse_mode="Markdown"
                                )
                            except Exception:
                                pass

                size_mb = os.path.getsize(zip_path) / (1024 * 1024)
                try:
                    bot.delete_message(chat_id, progress_msg.message_id)
                except Exception:
                    pass

                with open(zip_path, 'rb') as zf:
                    bot.send_document(
                        chat_id, zf,
                        caption=f"💾 <b>All Cracked PDFs</b>\n\n"
                                f"📄 Files: {len(pdfs)}\n"
                                f"💾 Size: {size_mb:.2f} MB",
                        parse_mode='HTML'
                    )

                # Cleanup
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

            except Exception as e:
                try:
                    bot.delete_message(chat_id, progress_msg.message_id)
                except Exception:
                    pass
                bot.send_message(chat_id, f"❌ Zip failed: {e}")
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except Exception:
                    pass

        threading.Thread(target=_zip_worker, daemon=True).start()

    elif d.startswith("ad_users_"):
        try:
            page = int(d.replace("ad_users_", ""))
        except Exception:
            page = 1
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM users ORDER BY join_date DESC').fetchall()
        conn.close()
        per = 10
        total = len(rows)
        total_p = max(1, (total + per - 1) // per)
        page = max(1, min(page, total_p))
        start = (page - 1) * per
        chunk = rows[start:start + per]

        text = f"👥 *{scp('USERS')}* ({page}/{total_p}) — {total}\n\n{LINE}\n"
        for i, r in enumerate(chunk, start + 1):
            g = r['gender'] or '?'
            e = '👦' if g == 'boy' else ('👧' if g == 'girl' else '❓')
            bn = '🚫' if r['banned'] else ''
            cn = r['custom_name'] or r['first_name'] or 'User'
            text += f"{i}. {e} `{r['user_id']}` — {cn} {bn}\n"

        kb = types.InlineKeyboardMarkup(row_width=2)
        nav = []
        if page > 1:
            nav.append(ikb("⬅️ ᴘʀᴇᴠ", 'primary', callback_data=f"ad_users_{page-1}"))
        if page < total_p:
            nav.append(ikb("ɴᴇxᴛ ➡️", 'primary', callback_data=f"ad_users_{page+1}"))
        if nav:
            kb.row(*nav)
        kb.row(ikb("📥 ᴇxᴘᴏʀᴛ", 'success', callback_data="ad_export"),
               ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d.startswith("ad_downloads_"):
        try:
            page = int(d.replace("ad_downloads_", ""))
        except Exception:
            page = 1
        all_dl = get_all_downloads(limit=1000)
        per = 10
        total = len(all_dl)
        total_p = max(1, (total + per - 1) // per)
        page = max(1, min(page, total_p))
        start = (page - 1) * per
        chunk = all_dl[start:start + per]

        text = f"📥 *{scp('ALL DOWNLOADS')}* ({page}/{total_p}) — {total}\n\n{LINE}\n"
        for i, dl in enumerate(chunk, start + 1):
            nm = dl.get('custom_name') or dl.get('first_name') or 'User'
            mb = dl.get('mobile', '')
            uid_d = dl.get('user_id', '')
            text += f"{i}. `{mb}` — {nm} (`{uid_d}`)\n"

        kb = types.InlineKeyboardMarkup(row_width=2)
        nav = []
        if page > 1:
            nav.append(ikb("⬅️ ᴘʀᴇᴠ", 'primary', callback_data=f"ad_downloads_{page-1}"))
        if page < total_p:
            nav.append(ikb("ɴᴇxᴛ ➡️", 'primary', callback_data=f"ad_downloads_{page+1}"))
        if nav:
            kb.row(*nav)
        kb.row(ikb("📄 ᴇxᴘᴏʀᴛ ᴄꜱᴠ", 'success', callback_data="ad_export_downloads"),
               ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_export_downloads":
        all_dl = get_all_downloads(limit=5000)
        if not all_dl:
            try:
                bot.answer_callback_query(call.id, "No downloads yet", show_alert=True)
            except Exception:
                pass
            return
        path = os.path.join(BASE_DIR, "downloads_export.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"DOWNLOADS EXPORT — {len(all_dl)} total\n{'='*50}\n\n")
            for i, r in enumerate(all_dl, 1):
                f.write(
                    f"{i}. User: {r.get('user_id')} | Name: {r.get('custom_name') or r.get('first_name')} | "
                    f"@{r.get('username')} | Mobile: {r.get('mobile')} | Prefix: {r.get('prefix')} | "
                    f"File: {r.get('pdf_filename')} | Time: {r.get('created_at')}\n"
                )
        try:
            with open(path, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📥 <b>Downloads ({len(all_dl)})</b>", parse_mode='HTML')
            os.remove(path)
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}")

    elif d == "ad_notify_on":
        db_set('notify_admin_on_download', '1')
        try:
            bot.answer_callback_query(call.id, "Download notify ON", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_notify_off":
        db_set('notify_admin_on_download', '0')
        try:
            bot.answer_callback_query(call.id, "Download notify OFF", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_banned":
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('SELECT user_id, first_name, ban_reason FROM users WHERE banned=1').fetchall()
        conn.close()
        if not rows:
            text = f"🚫 *{scp('No banned users')}*"
        else:
            text = f"🚫 *{scp('BANNED USERS')}*\n\n{LINE}\n"
            for r in rows:
                text += f"• `{r[0]}` — {r[1] or 'User'}\n   _{r[2] or 'No reason'}_\n\n"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_bc_menu":
        text = f"📢 *{scp('BROADCAST SYSTEM')}*\n\n{LINE}\n"
        text += f"👥 Total: {len(get_all_users())} users\n\nChoose broadcast type below:"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.row(ikb("📝 ᴛᴇxᴛ ʙʀᴏᴀᴅᴄᴀꜱᴛ", 'primary', callback_data="ad_bc_text"))
        kb.row(ikb("🖼 ᴘʜᴏᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ", 'primary', callback_data="ad_bc_photo"))
        kb.row(ikb("📎 ꜰᴏʀᴡᴀʀᴅ ᴍꜱɢ", 'primary', callback_data="ad_bc_forward"))
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_bc_text":
        user_states[uid] = {'step': 'ADMIN_BC_TEXT'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "📝 Send text to broadcast:", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_bc_photo":
        user_states[uid] = {'step': 'ADMIN_BC_PHOTO'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "🖼 Send photo to broadcast:", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_bc_forward":
        user_states[uid] = {'step': 'ADMIN_BC_FORWARD'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "📎 Forward/send any message to broadcast:", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_msg_user":
        user_states[uid] = {'step': 'ADMIN_MSG_USER_ID'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "📨 Send format: `user_id message`",
                         reply_markup=cancel_kb, parse_mode="Markdown")
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_ban":
        user_states[uid] = {'step': 'ADMIN_BAN'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "🚫 Format: `user_id reason`", reply_markup=cancel_kb, parse_mode="Markdown")
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_unban":
        user_states[uid] = {'step': 'ADMIN_UNBAN'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "✅ Send user_id to unban:", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_check":
        user_states[uid] = {'step': 'ADMIN_CHECK'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "🔍 Send user_id to check:", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_export":
        users = get_all_users()
        if not users:
            try:
                bot.answer_callback_query(call.id, "No users", show_alert=True)
            except Exception:
                pass
            return
        path = os.path.join(BASE_DIR, "users_export.txt")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM users').fetchall()
        conn.close()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"USERS EXPORT — {len(rows)} total\n{'='*40}\n\n")
            for i, r in enumerate(rows, 1):
                f.write(f"{i}. ID: {r['user_id']} | Name: {r['custom_name'] or r['first_name']} | "
                        f"@{r['username']} | Gender: {r['gender']} | Banned: {r['banned']} | Joined: {r['join_date']}\n")
        try:
            with open(path, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"👥 <b>Users ({len(rows)})</b>", parse_mode='HTML')
            os.remove(path)
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}")

    elif d == "ad_backup":
        try:
            with open(DB_PATH, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"💾 <b>DB Backup</b>", parse_mode='HTML')
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}")

    elif d == "ad_logs":
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('SELECT user_id, error, created_at FROM error_logs ORDER BY id DESC LIMIT 20').fetchall()
        conn.close()
        if not rows:
            text = f"📋 *{scp('No errors logged')}*"
        else:
            text = f"📋 *{scp('LAST 20 ERRORS')}*\n\n{LINE}\n"
            for r in rows:
                text += f"👤 `{r[0]}` — {str(r[2])[:16]}\n_{str(r[1])[:80]}_\n\n"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🧹 ᴄʟᴇᴀʀ ʟᴏɢꜱ", 'danger', callback_data="ad_clear_logs"),
               ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_clear_logs":
        conn = sqlite3.connect(DB_PATH)
        conn.execute('DELETE FROM error_logs')
        conn.commit()
        conn.close()
        try:
            bot.answer_callback_query(call.id, "Logs cleared", show_alert=True)
        except Exception:
            pass

    elif d == "ad_clean":
        cleaned = 0
        try:
            for f in os.listdir(BASE_DIR):
                if f.startswith(('temp_captcha_', 'cap_ui_', 'cap_um_')):
                    try:
                        os.remove(os.path.join(BASE_DIR, f))
                        cleaned += 1
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            bot.answer_callback_query(call.id, f"🧹 Cleaned {cleaned} files", show_alert=True)
        except Exception:
            pass

    elif d == "ad_stats":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        tu = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        tb = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
        boys = c.execute("SELECT COUNT(*) FROM users WHERE gender='boy'").fetchone()[0]
        girls = c.execute("SELECT COUNT(*) FROM users WHERE gender='girl'").fetchone()[0]
        today = date.today().isoformat()
        new_today = c.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date)=?", (today,)).fetchone()[0]
        dl_today = c.execute("SELECT COUNT(*) FROM downloads WHERE DATE(created_at)=?", (today,)).fetchone()[0]
        conn.close()
        text = (
            f"📈 *{scp('STATISTICS')}*\n\n{LINE}\n"
            f"👥 Total Users: {tu}\n"
            f"🆕 Today: {new_today}\n"
            f"👦 Boys: {boys}\n"
            f"👧 Girls: {girls}\n"
            f"🚫 Banned: {tb}\n"
            f"📥 Downloads Today: {dl_today}\n\n"
            f"📅 Date: {today}"
        )
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_top":
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('SELECT user_id, custom_name, first_name, last_seen FROM users ORDER BY last_seen DESC LIMIT 10').fetchall()
        conn.close()
        text = f"🏆 *{scp('TOP 10 RECENT USERS')}*\n\n{LINE}\n"
        for i, r in enumerate(rows, 1):
            nm = r[1] or r[2] or 'User'
            text += f"{i}. `{r[0]}` — {nm}\n"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_settings":
        text = f"⚙️ *{scp('BOT SETTINGS')}*\n\n{LINE}\n"
        text += f"🔄 Auto-Delete: {db_get('auto_delete', '30')}s\n"
        text += f"📢 Force Join: {'ON' if get_force_join() else 'OFF'}\n"
        text += f"🔧 Maintenance: {'ON' if is_maintenance() else 'OFF'}\n"
        text += f"🔔 Download Notify: {'ON' if db_get('notify_admin_on_download', '1') == '1' else 'OFF'}\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.row(ikb("🔄 ᴄʜᴀɴɢᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ", 'primary', callback_data="ad_set_del"))
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_set_del":
        user_states[uid] = {'step': 'ADMIN_SET_DELETE'}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.row(rkb(BTN_CANCEL, 'danger'))
        bot.send_message(chat_id, "Send seconds (0 = disable):", reply_markup=cancel_kb)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    elif d == "ad_maint_menu":
        text = f"🔧 *{scp('MAINTENANCE MODE')}*\n\nCurrent: {'🔴 ON' if is_maintenance() else '🟢 OFF'}"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🔴 ᴏɴ", 'danger', callback_data="ad_maint_on"),
               ikb("🟢 ᴏꜰꜰ", 'success', callback_data="ad_maint_off"))
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_maint_on":
        db_set('maintenance', '1')
        try:
            bot.answer_callback_query(call.id, "🔴 Maintenance ON", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_maint_off":
        db_set('maintenance', '0')
        try:
            bot.answer_callback_query(call.id, "🟢 Maintenance OFF", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_fj_menu":
        fj_channels_str = ", ".join([str(c) for c in FORCE_JOIN_CHANNELS])
        text = f"📢 *{scp('FORCE JOIN')}*\n\nChannels: {fj_channels_str}\nStatus: {'🟢 ON' if get_force_join() else '🔴 OFF'}"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🟢 ᴏɴ", 'success', callback_data="ad_fj_on"),
               ikb("🔴 ᴏꜰꜰ", 'danger', callback_data="ad_fj_off"))
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

    elif d == "ad_fj_on":
        db_set('force_join', '1')
        try:
            bot.answer_callback_query(call.id, "Force Join ON", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_fj_off":
        db_set('force_join', '0')
        try:
            bot.answer_callback_query(call.id, "Force Join OFF", show_alert=True)
        except Exception:
            pass
        send_admin_dash(chat_id)

    elif d == "ad_src":
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('SELECT id, user_id, username, first_name, created_at FROM src_requests ORDER BY id DESC LIMIT 20').fetchall()
        conn.close()
        if not rows:
            text = f"💻 *{scp('No SRC requests')}*"
        else:
            text = f"💻 *{scp('SRC REQUESTS')}* ({len(rows)})\n\n{LINE}\n"
            for r in rows:
                text += f"#{r[0]} `{r[1]}` — {r[3]} (@{r[2]})\n{str(r[4])[:16]}\n\n"
        kb = types.InlineKeyboardMarkup()
        kb.row(ikb("🔙 ʙᴀᴄᴋ", 'danger', callback_data="ad_dash"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text,
                                  reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")


# ===================== ADMIN TEXT INPUT HANDLER =====================
@bot.message_handler(
    content_types=['text', 'photo', 'document', 'video', 'sticker', 'voice', 'audio', 'animation', 'video_note'],
    func=lambda m: m.from_user.id in ADMIN_IDS
    and user_states.get(m.from_user.id, {}).get('step', '').startswith('ADMIN_')
)
def admin_input_handler(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    state = user_states.get(uid, {})
    step = state.get('step', '')
    text = m.text.strip() if m.text else ''

    if text == BTN_CANCEL or text.lower() in ['/cancel', 'cancel']:
        user_states[uid] = {'step': 'IDLE'}
        bot.send_message(chat_id, f"❌ *{scp('Cancelled')}*",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        return

    if step == "ADMIN_BC_TEXT":
        user_states[uid] = {'step': 'IDLE'}
        bot.send_message(chat_id, "📢 Broadcasting...", reply_markup=get_main_keyboard(uid))
        threading.Thread(target=do_broadcast, args=(chat_id, m, 'text'), daemon=True).start()
        return

    if step == "ADMIN_BC_PHOTO":
        if not m.photo:
            bot.send_message(chat_id, "❌ Send a photo")
            return
        user_states[uid] = {'step': 'IDLE'}
        bot.send_message(chat_id, "📢 Broadcasting...", reply_markup=get_main_keyboard(uid))
        threading.Thread(target=do_broadcast, args=(chat_id, m, 'photo'), daemon=True).start()
        return

    if step == "ADMIN_BC_FORWARD":
        user_states[uid] = {'step': 'IDLE'}
        bot.send_message(chat_id, "📢 Broadcasting...", reply_markup=get_main_keyboard(uid))
        threading.Thread(target=do_broadcast, args=(chat_id, m, 'forward'), daemon=True).start()
        return

    if step == "ADMIN_MSG_USER_ID":
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(chat_id, "❌ Format: `user_id message`", parse_mode="Markdown")
            return
        try:
            tid = int(parts[0])
        except Exception:
            bot.send_message(chat_id, "❌ Invalid ID")
            return
        try:
            bot.send_message(tid, f"📨 *{scp('Message from Admin')}*\n\n{parts[1]}", parse_mode="Markdown")
            bot.send_message(chat_id, "✅ Sent", reply_markup=get_main_keyboard(uid))
        except Exception as e:
            bot.send_message(chat_id, f"❌ Failed: {e}", reply_markup=get_main_keyboard(uid))
        user_states[uid] = {'step': 'IDLE'}
        return

    if step == "ADMIN_BAN":
        parts = text.split(maxsplit=1)
        if not parts:
            bot.send_message(chat_id, "❌ Format: `user_id reason`", parse_mode="Markdown")
            return
        try:
            tid = int(parts[0])
        except Exception:
            bot.send_message(chat_id, "❌ Invalid ID")
            return
        reason = parts[1] if len(parts) > 1 else "Violation"
        ban_user(tid, reason)
        bot.send_message(chat_id, f"✅ Banned `{tid}`",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        user_states[uid] = {'step': 'IDLE'}
        return

    if step == "ADMIN_UNBAN":
        try:
            tid = int(text)
        except Exception:
            bot.send_message(chat_id, "❌ Invalid ID")
            return
        unban_user(tid)
        bot.send_message(chat_id, f"✅ Unbanned `{tid}`",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        user_states[uid] = {'step': 'IDLE'}
        return

    if step == "ADMIN_CHECK":
        try:
            tid = int(text)
        except Exception:
            bot.send_message(chat_id, "❌ Invalid ID")
            return
        u = get_user(tid)
        if not u:
            bot.send_message(chat_id, "❌ Not found", reply_markup=get_main_keyboard(uid))
            return
        user_dl = get_user_downloads(tid, limit=5)
        info = (
            f"👤 *USER INFO*\n\n"
            f"🆔 `{u['user_id']}`\n"
            f"👥 {u.get('custom_name') or u['first_name']}\n"
            f"💬 @{u['username']}\n"
            f"⚧ Gender: {u['gender']}\n"
            f"🚫 Banned: {'Yes' if u['banned'] else 'No'}\n"
            f"📥 Downloads: {len(get_user_downloads(tid, limit=1000))}\n"
            f"📅 Joined: {str(u['join_date'])[:19]}\n"
        )
        if user_dl:
            info += f"\n{LINE}\n📄 *Recent Downloads:*\n"
            for dl in user_dl:
                info += f"• `{dl['mobile']}` — {dl['created_at'][:16]}\n"
        bot.send_message(chat_id, info, reply_markup=get_main_keyboard(uid), parse_mode="Markdown")
        user_states[uid] = {'step': 'IDLE'}
        return

    if step == "ADMIN_SET_DELETE":
        if not text.isdigit():
            bot.send_message(chat_id, "❌ Send number")
            return
        db_set('auto_delete', text)
        bot.send_message(chat_id, f"✅ Auto-delete = {text}s", reply_markup=get_main_keyboard(uid))
        user_states[uid] = {'step': 'IDLE'}
        return


def do_broadcast(admin_chat_id, message, btype):
    users = get_all_users()
    total = len(users)
    ok, fail = 0, 0
    for u in users:
        if u in ADMIN_IDS:
            continue
        try:
            if btype == 'text':
                bot.send_message(u, message.text or '')
            elif btype == 'photo':
                bot.send_photo(u, message.photo[-1].file_id, caption=message.caption or '')
            elif btype == 'forward':
                bot.copy_message(u, admin_chat_id, message.message_id)
            ok += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT INTO broadcast_history (admin_id, total, success, failed) VALUES (?,?,?,?)',
                     (admin_chat_id, total, ok, fail))
        conn.commit()
        conn.close()
    except Exception:
        pass
    report = (
        f"📢 *{scp('BROADCAST COMPLETE')}*\n\n{LINE}\n"
        f"📊 Total: {total}\n"
        f"✅ Success: {ok}\n"
        f"❌ Failed: {fail}"
    )
    try:
        bot.send_message(admin_chat_id, report, parse_mode="Markdown")
    except Exception:
        pass


# ===================== GROUP /aadhaar =====================
@bot.message_handler(commands=['aadhaar', 'aadhar'])
def group_aadhaar(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    if not enforce_force_join(uid, chat_id):
        return
    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    text = m.text.strip()
    gender = get_gender(uid)
    custom_name = get_custom_name(uid)
    if not gender or not custom_name:
        bot.send_message(chat_id,
            f"⚠️ *{scp('Please start bot in DM first, set gender & name')}*\n\n👉 @{bot.get_me().username}",
            parse_mode="Markdown")
        return

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(chat_id, f"📌 *{scp('Format')}:* `/aadhaar 9876543210`", parse_mode="Markdown")
        return

    clean = re.sub(r'\D', '', parts[1])
    if len(clean) > 10 and clean.startswith(('91', '0')):
        clean = clean[-10:]
    if len(clean) != 10 or clean[0] not in '6789':
        bot.send_message(chat_id, f"❌ *{scp('Invalid number')}*", parse_mode="Markdown")
        return

    prefix = get_prefix_from_gender(uid)
    user_info = {
        'username': m.from_user.username or 'N/A',
        'first_name': m.from_user.first_name or 'N/A',
        'custom_name': custom_name,
        'gender': gender,
    }

    try:
        if hasattr(aadhaar_engine, 'prewarm_engine'):
            aadhaar_engine.prewarm_engine(bot, chat_id, clean)
    except Exception:
        pass

    def _runner():
        try:
            if loop is None or not loop.is_running():
                raise RuntimeError("Async loop not running")
            fut = asyncio.run_coroutine_threadsafe(
                aadhaar_engine.execute_task(bot, chat_id, prefix, clean, None, user_info=user_info),
                loop
            )
            fut.result(timeout=900)
            time.sleep(3)
            pdf_path, pdf_filename = find_latest_pdf_for_user(uid, clean, custom_name)
            if pdf_path:
                save_download_record(
                    uid, m.from_user.username or 'N/A', m.from_user.first_name or 'N/A',
                    custom_name, clean, prefix, pdf_filename, pdf_path
                )
                notify_admin_download(
                    uid, m.from_user.first_name or 'User', m.from_user.username or 'N/A',
                    custom_name, clean, prefix, pdf_path, pdf_filename
                )
        except Exception as e:
            log_error(uid, f"group_aadhaar: {e}")
            bot.send_message(chat_id, f"❌ *{scp('Error')}*: {e}", parse_mode="Markdown")

    threading.Thread(target=_runner, daemon=True).start()


# ===================== FALLBACK =====================
@bot.message_handler(func=lambda m: True)
def fallback(m):
    uid = m.from_user.id
    chat_id = m.chat.id

    if is_banned(uid):
        return

    if uid in ADMIN_IDS and user_states.get(uid, {}).get('step', '').startswith('ADMIN_'):
        return

    if uid not in ADMIN_IDS or not user_states.get(uid, {}).get('step', '').startswith('ADMIN_'):
        if not enforce_force_join(uid, chat_id):
            return

    if user_states.get(uid, {}).get('step') == 'AWAITING_MOBILE':
        process_mobile_input(m)
        return

    if user_states.get(uid, {}).get('step') == 'AWAITING_OTP':
        otp_input_handler(m)
        return

    if m.text:
        clean = re.sub(r'\D', '', m.text)
        if len(clean) == 10 and clean[0] in '6789' and get_gender(uid) and get_custom_name(uid):
            user_states[uid] = {'step': 'AWAITING_MOBILE'}
            process_mobile_input(m)
            return

    if is_maintenance() and uid not in ADMIN_IDS:
        send_maintenance_msg(chat_id)
        return

    if uid not in ADMIN_IDS:
        save_user(uid, m.from_user.username or '', m.from_user.first_name or '', m.from_user.last_name or '')

    gender = get_gender(uid)
    custom_name = get_custom_name(uid)
    if not gender:
        send_gender_selection(chat_id)
    elif not custom_name:
        send_name_input(chat_id, gender)
    else:
        bot.send_message(chat_id, f"💡 *{scp('Please use the buttons below')}*",
                         reply_markup=get_main_keyboard(uid), parse_mode="Markdown")


# ===================== CLEANUP =====================
def cleanup_temp():
    print("🧹 [CLEANUP] Sweeping temp files...")
    prefixes = ['temp_captcha_', 'cap_ui_', 'cap_um_']
    try:
        for f in os.listdir(BASE_DIR):
            if any(f.startswith(p) for p in prefixes):
                try:
                    os.remove(os.path.join(BASE_DIR, f))
                except Exception:
                    pass
    except Exception:
        pass

    os.makedirs(CRACKED_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    bulk = os.path.join(BASE_DIR, 'BULK_USER_DATA')
    if os.path.exists(bulk):
        try:
            shutil.rmtree(bulk, ignore_errors=True)
        except Exception:
            pass


# ===================== MAIN =====================
if __name__ == "__main__":
    print("=" * 60)
    print("  Aadhaar Info Bot — ULTIMATE v6 FINAL")
    print("=" * 60)
    print(f"  Owner: @{ADMIN_USERNAME}")
    print(f"  Admin IDs: {ADMIN_IDS}")
    print(f"  Force Join Channels: {FORCE_JOIN_CHANNELS}")
    print(f"  Mode: FREE (no credits)")
    print(f"  Credit: @dimpiiix | @dimpiii_modz")
    print("=" * 60)

    cleanup_temp()

    loop = asyncio.new_event_loop()

    def run_loop(l):
        asyncio.set_event_loop(l)
        try:
            l.run_until_complete(aadhaar_engine.init_pool(bot))
        except Exception as e:
            print(f"[WARN] Engine init_pool failed: {e}")
        l.run_forever()

    threading.Thread(target=run_loop, args=(loop,), daemon=True).start()

    time.sleep(1)
    print("🤖 Bot is now LIVE.")

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=['message', 'callback_query', 'edited_message',
                                 'my_chat_member', 'chat_member']
            )
        except Exception as e:
            print(f"[POLLING EXC] {e}")
            time.sleep(5)