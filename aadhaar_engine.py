import asyncio
import os
import re
import subprocess
import base64
import ddddocr
import random
import uuid
import sys
from dotenv import load_dotenv
import time
import stats_manager

# Load environmental variables from .env file
load_dotenv()

# Force all spawned python subprocesses to use UTF-8 output encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

DEVELOPER_USERNAME = os.getenv('DEVELOPER_USERNAME', 'dimpiiix')
CREDIT_LINE = "@dimpiiix | @dimpiii_modz"

def escape_html(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_ui_card(step_num, title, description, target=None, show_tip=True):
    body = ""
    if step_num:
        body += f"📱 <b>STEP {step_num}/4: {title}</b>\n\n"
    else:
        body += f"⭐ <b>{title}</b>\n\n"
    body += f"{description}\n"
    if target:
        body += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        body += f"📱 <b>Target Mobile:</b> <code>{target}</code>\n"
    if show_tip:
        body += (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <i>Tip: Send <b>/cancel</b> to abort.</i>"
        )
    else:
        body += "━━━━━━━━━━━━━━━━━━━━━━"
    return body


# ===================== GLOBAL REGISTRY =====================
user_page_registry = {}
buffered_inputs = {}
_engine_instance = None
_running_loop = None
active_engines = {}
active_tasks = set()
VISIBLE_MODE = {}
CRACKED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cracked_aadhar")

os.makedirs(CRACKED_DIR, exist_ok=True)

STICKERS = {
    "SUCCESS": "CAACAgIAAxkBAAEL6V9mAe7q-Q1R-O_0v57_5y7X-Q5_QAACSwADr8ZRGm_F-G7M7_9kNAQ"
}


def escape_html(text):
    return str(text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def parse_dob(date_str):
    if not date_str:
        return date_str

    months_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    clean = date_str.replace(',', '').strip()
    parts = re.split(r'[ /\-.]', clean)
    if len(parts) < 3:
        return date_str

    day, month, year = None, None, None
    if len(parts[0]) == 4:
        year, month, day = parts[0], parts[1], parts[2]
    elif len(parts[2]) == 4:
        day, month, year = parts[0], parts[1], parts[2]
    else:
        day, month, year = parts[0], parts[1], parts[2]

    m_lower = str(month).lower()[:3]
    if m_lower in months_map:
        month = months_map[m_lower]

    try:
        return f"{str(day).zfill(2)}-{str(month).zfill(2)}-{year}"
    except Exception:
        return date_str


async def init_pool(bot_instance):
    global _running_loop
    _running_loop = asyncio.get_running_loop()


# ===================== ENGINE =====================
class AadhaarEngine:
    def __init__(self, bot, chat_id=None, stage_callback=None):
        self.bot = bot
        self.chat_id = str(chat_id) if chat_id else None
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.status_msg_id = None
        self._preloader_active = False
        self._preloader_task = None
        self.temp_msg_ids = []
        self.stage_callback = stage_callback
        self._last_stage = None

    # ⭐ Emit stage to bot.py — bot.py handles ALL UI
    def _emit_stage(self, stage, extra=None):
        if self._last_stage == stage:
            return
        self._last_stage = stage
        if self.stage_callback:
            try:
                self.stage_callback(stage, extra or {})
            except Exception as e:
                print(f"⚠️ [STAGE CALLBACK] {stage}: {e}")

    # ⭐ ALL MESSAGING DISABLED — bot.py handles UI
    def update_status(self, text):
        return

    def refresh_status_card(self, text):
        return

    def start_preloader(self, base_text):
        return

    def stop_preloader(self):
        return

    async def _preloader_loop(self):
        return

    async def close(self):
        if self.chat_id == 'master':
            for uid, eng in list(active_engines.items()):
                try:
                    await eng.close()
                except Exception:
                    pass
            active_engines.clear()
            active_tasks.clear()

        try:
            if hasattr(self, 'phase1_process') and self.phase1_process:
                try:
                    self.phase1_process.terminate()
                    print(f"🛑 [ENGINE] Terminated Phase 1 for {self.chat_id}.")
                except Exception:
                    pass
                self.phase1_process = None
            if hasattr(self, 'phase1_task') and self.phase1_task:
                try:
                    self.phase1_task.cancel()
                except Exception:
                    pass
                self.phase1_task = None
        except Exception as e:
            print(f"⚠️ [ENGINE] Shutdown error: {e}")

    async def delete_temp_messages(self):
        if not self.chat_id:
            return
        try:
            chat_id_int = int(self.chat_id)
        except ValueError:
            return
        if chat_id_int < 0:
            for msg_id in list(self.temp_msg_ids):
                try:
                    self.bot.delete_message(chat_id=chat_id_int, message_id=msg_id)
                except Exception:
                    pass
            self.temp_msg_ids.clear()

    def start_early_phase1(self, mobile):
        if hasattr(self, 'phase1_process') and self.phase1_process:
            return
        self.phase1_ready = asyncio.Event()
        self.phase1_mobile = mobile
        global _running_loop
        if _running_loop:
            self.phase1_task = _running_loop.create_task(self._early_phase1_loop(mobile))
        else:
            print("⚠️ [PRE-WARM] Global loop not set.")

    async def _early_phase1_loop(self, mobile):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            get_eid_script = os.path.join(script_dir, 'retrive-eid.py')
            self.phase1_process = await asyncio.create_subprocess_exec(
                sys.executable, '-u', get_eid_script, "WAIT_INPUT", "WAIT_INPUT", mobile,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            while True:
                line_bytes = await self.phase1_process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if "🔑 WAITING_FOR_NAME_DOB" in line:
                    self.phase1_ready.set()
                    break
        except Exception as e:
            print(f"⚠️ [PRE-WARM] Error: {e}")
            if hasattr(self, 'phase1_process') and self.phase1_process:
                try:
                    self.phase1_process.terminate()
                except Exception:
                    pass
                self.phase1_process = None

    async def wait_for_input(self, chat_id, prompt_type, timeout=300):
        str_chat_id = str(chat_id)
        if str_chat_id in buffered_inputs:
            val = buffered_inputs.pop(str_chat_id)
            if val == '__CANCEL__':
                raise Exception("Process cancelled by user.")
            return val

        user_page_registry[str_chat_id] = {'type': prompt_type, 'value': None}
        try:
            for _ in range(timeout):
                if str_chat_id in buffered_inputs:
                    val = buffered_inputs.pop(str_chat_id)
                    if val == '__CANCEL__':
                        raise Exception("Process cancelled by user.")
                    return val
                if user_page_registry.get(str_chat_id) and user_page_registry[str_chat_id]['value'] is not None:
                    val = user_page_registry[str_chat_id]['value']
                    user_page_registry.pop(str_chat_id, None)
                    if val == '__CANCEL__':
                        raise Exception("Process cancelled by user.")
                    return val
                await asyncio.sleep(1)
            raise Exception(f"Timeout waiting for {prompt_type}")
        finally:
            user_page_registry.pop(str_chat_id, None)

    # ===================== MAIN FLOW =====================
    async def run_flow(self, chat_id, name, mobile, dob, user_info=None):
        self.start_time = time.time()

        self._emit_stage('finding', {'mobile': mobile})

        script_dir = os.path.dirname(os.path.abspath(__file__))
        get_eid_script = os.path.join(script_dir, 'retrive-eid.py')
        formatted_dob_iso = dob

        found_id = None
        process = None
        use_prewarmed = False
        if hasattr(self, 'phase1_process') and self.phase1_process:
            if getattr(self, 'phase1_mobile', None) == mobile and self.phase1_process.returncode is None:
                use_prewarmed = True

        captured_real_name = name
        try:
            if use_prewarmed:
                try:
                    await asyncio.wait_for(self.phase1_ready.wait(), timeout=15.0)
                except asyncio.TimeoutError:
                    use_prewarmed = False

            if use_prewarmed and self.phase1_process and self.phase1_process.returncode is None:
                process = self.phase1_process
                process.stdin.write(f"{name}|{formatted_dob_iso}\n".encode('utf-8'))
                await process.stdin.drain()
            else:
                if hasattr(self, 'phase1_process') and self.phase1_process:
                    try:
                        self.phase1_process.terminate()
                    except Exception:
                        pass
                    self.phase1_process = None

                process = await asyncio.create_subprocess_exec(
                    sys.executable, '-u', get_eid_script, name, str(formatted_dob_iso), mobile,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                print(f"[get_eid] {line}")

                if "LIMIT CROSSED" in line:
                    raise Exception("Technical difficulties / Rate limit reached. Limit crossed, try again later.")

                if "NETWORK ERROR" in line:
                    raise Exception("Network issue / slow portal response.")

                # ⭐ Aadhaar Number Found
                if "CAPTURED ID SUCCESSFULLY:" in line:
                    found_id = line.split("CAPTURED ID SUCCESSFULLY:")[1].strip()
                    found_id = re.sub(r'[^a-zA-Z0-9]', '', found_id)
                    self._emit_stage('aadhaar_found', {'mobile': mobile, 'eid': found_id})

                if "CAPTURED NAME SUCCESSFULLY:" in line:
                    captured_real_name = line.split("CAPTURED NAME SUCCESSFULLY:")[1].strip()

                # ⭐ OTP sent
                if "OTP Sent Successfully" in line:
                    self._emit_stage('otp_sent', {'mobile': mobile})

                # Manual Captcha
                if line.startswith("🔑 MANUAL CAPTCHA REQUIRED |"):
                    b64_img = line.split("🔑 MANUAL CAPTCHA REQUIRED |")[1].strip()
                    temp_captcha_path = os.path.join(script_dir, f"temp_captcha_p1_{chat_id}.png")
                    with open(temp_captcha_path, "wb") as f_cap:
                        f_cap.write(base64.b64decode(b64_img.encode()))
                    with open(temp_captcha_path, "rb") as f_photo:
                        photo_msg = self.bot.send_photo(
                            chat_id, f_photo,
                            caption="⚠️ <b>Auto-Captcha solve failed!</b>\n👇 Kripya image me dikh raha captcha code manually type karein:",
                            parse_mode='HTML'
                        )
                        try:
                            if photo_msg and int(chat_id) < 0:
                                self.temp_msg_ids.append(photo_msg.message_id)
                        except Exception:
                            pass
                    user_captcha_val = await self.wait_for_input(chat_id, 'CAPTCHA')
                    try:
                        os.remove(temp_captcha_path)
                    except Exception:
                        pass
                    process.stdin.write(f"{user_captcha_val}\n".encode())
                    await process.stdin.drain()

                # OTP wait
                if "ENTER THE OTP RECEIVED ON YOUR REGISTERED MOBILE" in line:
                    self._emit_stage('otp_waiting', {'mobile': mobile})
                    res_otp = await self.wait_for_input(chat_id, 'OTP')
                    self._emit_stage('otp_verified', {'mobile': mobile})
                    process.stdin.write(f"{res_otp}\n".encode())
                    await process.stdin.drain()

            await process.wait()

            if not found_id:
                stderr_bytes = await process.stderr.read()
                stderr_str = stderr_bytes.decode('utf-8', errors='ignore').strip()
                if stderr_str:
                    if "An error occurred:" in stderr_str:
                        err_msg = stderr_str.split("An error occurred:")[1].strip()
                        raise Exception(err_msg)
                    if "You have entered an invalid Captcha" in stderr_str:
                        raise Exception("Invalid Captcha! Please try again.")
                    if "experiencing technical difficulties" in stderr_str.lower():
                        raise Exception("Technical difficulties / Rate limit reached.")
                    last_err = [l for l in stderr_str.splitlines() if l.strip()][-1]
                    raise Exception(last_err)
                raise Exception("Aadhaar details galat hain ya portal response match nahi ho raha.")

        except Exception as e:
            if process:
                try:
                    process.terminate()
                except Exception:
                    pass
            raise e

        if found_id:
            await self.run_uidai_phase(chat_id, found_id, captured_real_name, mobile, user_info=user_info)

    # ===================== PHASE 2: DOWNLOAD =====================
    async def run_uidai_phase(self, chat_id, eid, name, mobile, user_info=None):
        self._emit_stage('downloading', {'mobile': mobile})

        script_dir = os.path.dirname(os.path.abspath(__file__))
        download_script = os.path.join(script_dir, 'aadhar-downlaod.py')

        max_retries = 3
        current_retry = 0
        while current_retry < max_retries:
            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, '-u', download_script, str(eid), str(chat_id),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                while True:
                    line_bytes = await process.stdout.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    print(f"[aadhar-downlaod] {line}")

                    if "✅ OTP Sent Successfully!" in line:
                        self._emit_stage('otp2_sent', {'mobile': mobile})

                    if line.startswith("🔑 MANUAL CAPTCHA REQUIRED |"):
                        b64_img = line.split("🔑 MANUAL CAPTCHA REQUIRED |")[1].strip()
                        temp_captcha_path = os.path.join(script_dir, f"temp_captcha_p2_{chat_id}.png")
                        with open(temp_captcha_path, "wb") as f_cap:
                            f_cap.write(base64.b64decode(b64_img.encode()))
                        with open(temp_captcha_path, "rb") as f_photo:
                            photo_msg = self.bot.send_photo(
                                chat_id, f_photo,
                                caption="⚠️ <b>Auto-Captcha solve failed!</b>\n👇 Kripya image me dikh raha captcha code manually type karein:",
                                parse_mode='HTML'
                            )
                            try:
                                if photo_msg and int(chat_id) < 0:
                                    self.temp_msg_ids.append(photo_msg.message_id)
                            except Exception:
                                pass
                        user_captcha_val = await self.wait_for_input(chat_id, 'CAPTCHA')
                        try:
                            os.remove(temp_captcha_path)
                        except Exception:
                            pass
                        process.stdin.write(f"{user_captcha_val}\n".encode())
                        await process.stdin.drain()

                    if "ENTER THE OTP RECEIVED ON YOUR REGISTERED MOBILE" in line:
                        self._emit_stage('otp2_waiting', {'mobile': mobile})
                        res_otp = await self.wait_for_input(chat_id, 'OTP')
                        self._emit_stage('otp2_verified', {'mobile': mobile})
                        process.stdin.write(f"{res_otp}\n".encode())
                        await process.stdin.drain()

                await process.wait()

                file_path = os.path.join(CRACKED_DIR, f"Aadhaar_{chat_id}.pdf")
                if os.path.exists(file_path):
                    self._emit_stage('downloaded', {'mobile': mobile})
                    await self.process_cracked_pdf(chat_id, file_path, name, mobile, eid=eid, user_info=user_info)
                    return
                else:
                    stderr_bytes = await process.stderr.read()
                    stderr_str = stderr_bytes.decode('utf-8', errors='ignore').strip()
                    if stderr_str:
                        if "An error occurred:" in stderr_str:
                            err_msg = stderr_str.split("An error occurred:")[1].strip()
                            raise Exception(err_msg)
                        else:
                            last_err = [l for l in stderr_str.splitlines() if l.strip()][-1]
                            raise Exception(last_err)
                    raise Exception("Aadhaar download failed.")
            except Exception as e:
                if process:
                    try:
                        process.terminate()
                    except Exception:
                        pass
                err_msg = str(e)
                if "technical difficulties" in err_msg.lower():
                    raise e
                is_otp_error = "invalid otp" in err_msg.lower() or "incorrect otp" in err_msg.lower()
                current_retry += 1
                if current_retry < max_retries:
                    await asyncio.sleep(2)
                else:
                    if is_otp_error:
                        raise Exception("❌ Invalid OTP. Max retries exceeded.")
                    else:
                        raise Exception(f"Registry Phase Failed: {e}")

    # ===================== PHASE 3: CRACK PDF =====================
    async def process_cracked_pdf(self, chat_id, file_path, name, mobile, eid=None, user_info=None):
        self._emit_stage('cracking', {'mobile': mobile})

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            proc_script = os.path.join(script_dir, 'pdf_processor.py')
            os.makedirs(CRACKED_DIR, exist_ok=True)
            process = await asyncio.create_subprocess_exec(
                sys.executable, proc_script, file_path, name, CRACKED_DIR, str(chat_id), 'True',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore').strip()

            if stdout_str.strip():
                print(f"[pdf_processor stdout] {stdout_str.strip()}")
            if stderr_str:
                print(f"[pdf_processor stderr] {stderr_str}")

            success_line = None
            uncracked_line = None
            error_line = None

            for line in stdout_str.split('\n'):
                line = line.strip()
                if line.startswith('SUCCESS|'):
                    success_line = line
                    break
                if line.startswith('UNCRACKED|'):
                    uncracked_line = line
                    break
                if line.startswith('ERROR|'):
                    error_line = line[6:]

            if success_line:
                parts = success_line.split('|', 5)
                if len(parts) < 6:
                    raise Exception("PDF processor returned malformed SUCCESS line.")
                _, uid, pdf_out, front, back, password = parts

                time_str = "N/A"
                if hasattr(self, 'start_time') and self.start_time:
                    elapsed_sec = int(time.time() - self.start_time)
                    m = elapsed_sec // 60
                    s = elapsed_sec % 60
                    time_str = f"{m}m {s}s" if m > 0 else f"{s}s"

                self._emit_stage('ready', {
                    'mobile': mobile, 'eid': eid, 'uid': uid,
                    'pdf_out': pdf_out, 'front': front, 'back': back,
                    'password': password, 'time_str': time_str,
                    'uncracked': False,
                })

                try:
                    stats_manager.record_success(chat_id, user_info, name, mobile, uid, password, eid=eid)
                except Exception as se:
                    print(f"⚠️ [STATS] {se}")

                # Save permanent copy
                try:
                    import shutil
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                    safe_uid = uid.replace(' ', '')
                    permanent_pdf_name = f"{safe_name}_{safe_uid}.pdf"
                    permanent_pdf_path = os.path.join(CRACKED_DIR, permanent_pdf_name)
                    shutil.copy(pdf_out, permanent_pdf_path)
                    print(f"💾 [SAVED] {permanent_pdf_path}")
                except Exception as e_copy:
                    print(f"⚠️ [SAVED PDF] {e_copy}")

                # Send files
                try:
                    if os.path.exists(front):
                        with open(front, 'rb') as f:
                            self.bot.send_photo(chat_id, f, caption="🖼️ <b>Aadhaar Front</b>", parse_mode='HTML')
                except Exception as e_front:
                    print(f"⚠️ Front: {e_front}")

                try:
                    if os.path.exists(back):
                        with open(back, 'rb') as f:
                            self.bot.send_photo(chat_id, f, caption="🖼️ <b>Aadhaar Back</b>", parse_mode='HTML')
                except Exception as e_back:
                    print(f"⚠️ Back: {e_back}")

                try:
                    if os.path.exists(pdf_out):
                        with open(pdf_out, 'rb') as f:
                            self.bot.send_document(chat_id, f, caption="📄 <b>Aadhaar PDF (Unlocked)</b>")
                except Exception as e_pdf:
                    print(f"⚠️ PDF: {e_pdf}")

                # Cleanup
                for temp_f in [front, back, pdf_out, file_path]:
                    if temp_f and os.path.exists(temp_f):
                        try:
                            os.remove(temp_f)
                        except Exception:
                            pass
                return

            if uncracked_line:
                parts = uncracked_line.split('|', 1)
                locked_pdf_path = parts[1] if len(parts) > 1 else file_path

                time_str = "N/A"
                if hasattr(self, 'start_time') and self.start_time:
                    elapsed_sec = int(time.time() - self.start_time)
                    m = elapsed_sec // 60
                    s = elapsed_sec % 60
                    time_str = f"{m}m {s}s" if m > 0 else f"{s}s"

                self._emit_stage('ready', {
                    'mobile': mobile, 'eid': eid, 'uid': None,
                    'pdf_out': locked_pdf_path, 'password': None,
                    'time_str': time_str, 'uncracked': True,
                })

                try:
                    stats_manager.record_failure()
                except Exception as se:
                    print(f"⚠️ [STATS] {se}")

                try:
                    if os.path.exists(locked_pdf_path):
                        with open(locked_pdf_path, 'rb') as f:
                            self.bot.send_document(chat_id, f, caption="📄 <b>Aadhaar PDF (Locked)</b>")
                except Exception as e_pdf:
                    print(f"⚠️ PDF: {e_pdf}")

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                return

            if error_line:
                raise Exception(f"PDF Error: {error_line}")
            elif stderr_str:
                last_err = [l for l in stderr_str.splitlines() if l.strip()][-1] if stderr_str else "Unknown error"
                raise Exception(f"PDF Processor crashed: {last_err}")
            else:
                raise Exception("PDF Cracking failed.")

        except Exception as e:
            raise Exception(f"PDF Crack Error: {e}")


# ===================== ENTRY POINT =====================
async def execute_task(bot, chat_id, name, mobile, dob, user_info=None, stage_callback=None):
    str_chat_id = str(chat_id)

    if str_chat_id in active_tasks:
        bot.send_message(chat_id, "⏳ <b>Aapka task pehle se process ho raha hai.</b>", parse_mode='HTML')
        return False

    max_concurrent = stats_manager.get_max_concurrent_tasks()
    if len(active_tasks) >= max_concurrent:
        bot.send_message(chat_id, f"⚠️ <b>Bot is overloaded!</b>", parse_mode='HTML')
        return False

    active_tasks.add(str_chat_id)

    if str_chat_id in active_engines:
        engine = active_engines[str_chat_id]
        engine.stage_callback = stage_callback
    else:
        engine = AadhaarEngine(bot, chat_id=str_chat_id, stage_callback=stage_callback)
        active_engines[str_chat_id] = engine

    try:
        await engine.run_flow(chat_id, name, mobile, dob, user_info=user_info)
    except Exception as e:
        err_str = str(e)
        user_msg = err_str
        real_msg = err_str
        try:
            if stage_callback:
                stage_callback('error', {'message': user_msg})
        except Exception:
            pass
        try:
            is_user_error = any(x in user_msg.lower() for x in [
                "no record", "not found", "mismatch", "validation failed",
                "invalid captcha", "incorrect otp", "invalid otp",
                "incorrect details", "wrong captcha", "galat hain",
                "match nahi", "incorrect", "invalid"
            ])
            if not is_user_error:
                stats_manager.record_failure()
            stats_manager.log_error(chat_id, user_info, f"Task Failed: {real_msg}")
        except Exception as se:
            print(f"⚠️ [STATS] {se}")
    finally:
        if str_chat_id in active_engines:
            del active_engines[str_chat_id]
        if str_chat_id in active_tasks:
            active_tasks.remove(str_chat_id)
        try:
            await engine.delete_temp_messages()
        except Exception as e:
            print(f"⚠️ [CLEANUP] {e}")
        await engine.close()
    return True


def prewarm_engine(bot, chat_id, mobile=None):
    str_chat_id = str(chat_id)
    if str_chat_id in active_engines:
        engine = active_engines[str_chat_id]
        if mobile and (not hasattr(engine, 'phase1_process') or engine.phase1_process is None):
            engine.start_early_phase1(mobile)
        return

    engine = AadhaarEngine(bot, chat_id=str_chat_id)
    active_engines[str_chat_id] = engine

    global _running_loop
    if _running_loop and _running_loop.is_running():
        if mobile:
            engine.start_early_phase1(mobile)
    else:
        try:
            loop = asyncio.get_event_loop()
        except Exception:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if mobile:
            loop.create_task(engine._early_phase1_loop(mobile))