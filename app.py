# app.py
import streamlit as st
import numpy as np
import wave, io, math, random, uuid
from typing import List

# ---------- تنظیمات صوت ----------
SAMPLE_RATE = 44100
FREQ = 800
DOT_MS = 120
DASH_MS = 360
INTRA_SYMBOL_MS = 100
LETTER_GAP_MS = 300
WORD_GAP_MS = 600

# جدول مورس (حروف و اعداد)
MORSE = {
 'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.',
 'G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..',
 'M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.',
 'S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-',
 'Y':'-.--','Z':'--..',
 '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
 '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'
}

# ---------- توابع ایجاد ویو (آرایه numpy) ----------
def tone_array(duration_ms: int) -> np.ndarray:
    n = int(SAMPLE_RATE * duration_ms / 1000)
    if n <= 0:
        return np.zeros(0, dtype=np.int16)
    t = np.linspace(0, duration_ms/1000, n, False)
    data = 0.5 * np.sin(2 * math.pi * FREQ * t)
    return (data * 32767).astype(np.int16)

def silence_array(duration_ms: int) -> np.ndarray:
    n = int(SAMPLE_RATE * duration_ms / 1000)
    return np.zeros(n, dtype=np.int16)

# ---------- تبدیل پیام به WAV (برگشت بایت‌ها) ----------
@st.cache_data(show_spinner=False)
def message_to_wav_bytes(message: str) -> bytes:
    frames = []
    message = message.upper()
    for ch in message:
        if ch == ' ':
            frames.append(silence_array(WORD_GAP_MS))
            continue
        code = MORSE.get(ch)
        if not code:
            # نویسه‌ای که مورس ندارد را نادیده می‌گیریم
            continue
        for symbol in code:
            if symbol == '.':
                frames.append(tone_array(DOT_MS))
            else:
                frames.append(tone_array(DASH_MS))
            frames.append(silence_array(INTRA_SYMBOL_MS))
        frames.append(silence_array(LETTER_GAP_MS))
    if not frames:
        audio = np.zeros(1, dtype=np.int16)
    else:
        audio = np.concatenate(frames)
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    bio.seek(0)
    return bio.read()

# ---------- کمک: دریافت لیست کلمات از st.secrets یا fallback ----------
def get_word_list() -> List[str]:

    return ["AE04"]

# ---------- UI و منطق بازی ----------
st.set_page_config(page_title="AeroGame — Morse", layout="centered")
st.title("🎧 AeroGame — Morse Challenge")
st.write("دکمهٔ «شروع» را بزن تا یک سیگنال مورس پخش شود؛ سپس حدس بزن و ارسال کن.")

# آماده‌سازی session
if "secret_word" not in st.session_state:
    st.session_state.secret_word = None
if "wav_bytes" not in st.session_state:
    st.session_state.wav_bytes = None
if "played_id" not in st.session_state:
    st.session_state.played_id = None  # شناسهٔ هر چالش برای جلوگیری از کش/تقلب

col1, col2 = st.columns([1,1])

with col1:
    if st.button("▶️ شروع چالش جدید"):
        words = get_word_list()
        chosen = random.choice(words).strip().upper()
        st.session_state.secret_word = chosen
        st.session_state.wav_bytes = message_to_wav_bytes(chosen)
        st.session_state.played_id = uuid.uuid4().hex[:8]

with col2:
    if st.button("🔁 چالش بعدی (رِفرش)"):
        words = get_word_list()
        chosen = random.choice(words).strip().upper()
        st.session_state.secret_word = chosen
        st.session_state.wav_bytes = message_to_wav_bytes(chosen)
        st.session_state.played_id = uuid.uuid4().hex[:8]

# اگر wav موجود است، نمایش و پخش کن (کاربر اجازهٔ دانلود هم دارد)
if st.session_state.wav_bytes:
    st.audio(st.session_state.wav_bytes, format="audio/wav")
    st.write(f"شناسهٔ این چالش: `{st.session_state.played_id}` (برای ثبت در گزارش‌ها قابل استفاده است)")

# ورودی جواب
answer = st.text_input("جواب را وارد کن (حروف انگلیسی/اعداد):")
if st.button("ارسال"):
    if not st.session_state.secret_word:
        st.warning("ابتدا یک چالش شروع کن.")
    else:
        if answer.strip().upper() == st.session_state.secret_word:
            st.success("🏆 تبریک! جواب درست است — کد جایزه: **1234**")
            # اگر خواستی اینجا می‌تونی لاگ شدن برنده را به گوگل شیت/وبهوک ارسال کنی
        else:
            st.error("❌ اشتباه — دوباره تلاش کن!")

st.write("---")
st.caption("نکته: کلمات چالش در Streamlit Secrets ذخیره شده‌اند؛ کد منبع ریپو شامل جواب‌ها نیست.")


