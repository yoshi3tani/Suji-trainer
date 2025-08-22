# main.py — Japanese/Thai number reader (toggle) + mobile-friendly + classic HTML audio (fixed)
import streamlit as st
from gtts import gTTS
from io import BytesIO
import re

# ------------------------------------------------------------
# UI languages (labels)
# ------------------------------------------------------------
LABELS = {
    "ja": {
        "app_title": "数字読み上げアプリ（日本語 / タイ語）",
        "ui_lang": "UI 言語",
        "target": "学習対象（読み言語）",
        "target_jp": "日本語",
        "target_th": "タイ語",
        "input_label": "数字を入力してください（0〜10^16）",
        "read_btn": "読み上げ",
        "invalid": "無効な数字です（半角数字のみ／0〜10^16）。",
        "layout_title": "表示設定（スマホで崩れる場合は列数を下げてください）",
        "cols_label": "ボタンの列数",
        "sec_basic": "0〜10",
        "sec_11_99": "11〜99（1刻み）",
        "sec_100s": "100〜900（100刻み）",
        "sec_1000s": "1000〜9000（1000刻み）",
        "sec_10k": "10000〜90000（1万刻み）",
        "sec_100k": "100000〜900000（10万刻み）",
        "sec_1m": "1000000〜9000000（100万刻み）",
        "sec_10m": "10000000〜90000000（1000万刻み）",
        "sec_big": "特別（1億・1兆・1京）",
        "romaji": "ローマ字",
        "hira": "ひらがな",
        "kata": "カタカナ",
        "kanji": "漢字",
        "rtgs": "ローマ字（RTGS）",
        "thai": "タイ語",
        "thai_digits": "タイ数字",
        "arabic": "アラビア数字",
    },
    "en": {
        "app_title": "Number Reader (Japanese / Thai)",
        "ui_lang": "UI Language",
        "target": "Target language",
        "target_jp": "Japanese",
        "target_th": "Thai",
        "input_label": "Enter a number (0–10^16)",
        "read_btn": "Speak",
        "invalid": "Invalid number (digits only / 0–10^16).",
        "layout_title": "Layout (reduce columns if layout breaks on phones)",
        "cols_label": "Buttons per row",
        "sec_basic": "0–10",
        "sec_11_99": "11–99 (step 1)",
        "sec_100s": "100–900 (by 100)",
        "sec_1000s": "1000–9000 (by 1000)",
        "sec_10k": "10,000–90,000 (by 10k)",
        "sec_100k": "100,000–900,000 (by 100k)",
        "sec_1m": "1,000,000–9,000,000 (by 1M)",
        "sec_10m": "10,000,000–90,000,000 (by 10M)",
        "sec_big": "Special (100M / 1T / 10^16)",
        "romaji": "Romaji",
        "hira": "Hiragana",
        "kata": "Katakana",
        "kanji": "Kanji",
        "rtgs": "RTGS",
        "thai": "Thai",
        "thai_digits": "Thai numerals",
        "arabic": "Arabic numerals",
    },
    "th": {
        "app_title": "แอปอ่านตัวเลข (ญี่ปุ่น / ไทย)",
        "ui_lang": "ภาษา UI",
        "target": "ภาษาเป้าหมาย",
        "target_jp": "ภาษาญี่ปุ่น",
        "target_th": "ภาษาไทย",
        "input_label": "ป้อนตัวเลข (0–10^16)",
        "read_btn": "อ่านออกเสียง",
        "invalid": "ไม่ถูกต้อง (กรอกเลขล้วน / 0–10^16).",
        "layout_title": "ตั้งค่าเค้าโครง (ถ้าเละบนมือถือให้ลดจำนวนคอลัมน์)",
        "cols_label": "จำนวนปุ่มต่อแถว",
        "sec_basic": "0–10",
        "sec_11_99": "11–99 (ทีละ 1)",
        "sec_100s": "100–900 (ทีละ 100)",
        "sec_1000s": "1000–9000 (ทีละ 1000)",
        "sec_10k": "10000–90000 (ทีละ 10000)",
        "sec_100k": "100000–900000 (ทีละ 100000)",
        "sec_1m": "1000000–9000000 (ทีละ 1000000)",
        "sec_10m": "10000000–90000000 (ทีละ 10000000)",
        "sec_big": "พิเศษ (ร้อยล้าน / ล้านล้าน / 10^16)",
        "romaji": "RTGS",
        "hira": "ฮิรางานะ",
        "kata": "คะตะกะนะ",
        "kanji": "คันจิ",
        "thai": "ภาษาไทย",
        "thai_digits": "เลขไทย",
        "arabic": "เลขอารบิก",
        "rtgs": "RTGS"
    },
}

# ------------------------------------------------------------
# Audio — 従来(HTML autoplay) 固定
# ------------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=256)
def tts_b64(text: str, lang_code: str) -> str:
    tts = gTTS(text=text, lang=lang_code)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    import base64
    return base64.b64encode(fp.read()).decode()

def play_audio(text: str, lang_code: str):
    """従来の base64 + <audio autoplay controls> を挿入"""
    if not text or not text.strip():
        return
    try:
        b64 = tts_b64(text, lang_code)
        st.markdown(
            f"<audio autoplay controls src='data:audio/mp3;base64,{b64}'></audio>",
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning("音声の生成に失敗しました。ネットワーク状況をご確認ください。")
        st.caption(f"details: {e}")

# ------------------------------------------------------------
# Japanese number reading (万進法)
# ------------------------------------------------------------
JP_DIG = {
    0: ("ぜろ","zero","ゼロ","零"),
    1: ("いち","ichi","イチ","一"),
    2: ("に","ni","ニ","二"),
    3: ("さん","san","サン","三"),
    4: ("よん","yon","ヨン","四"),
    5: ("ご","go","ゴ","五"),
    6: ("ろく","roku","ロク","六"),
    7: ("なな","nana","ナナ","七"),
    8: ("はち","hachi","ハチ","八"),
    9: ("きゅう","kyuu","キュウ","九"),
}
KANJI_DIG = ["","一","二","三","四","五","六","七","八","九"]

def hira_to_kata(s: str) -> str:
    out = []
    for ch in s:
        o = ord(ch)
        if 0x3041 <= o <= 0x3096:
            out.append(chr(o + 0x60))
        else:
            out.append(ch)
    return "".join(out)

def read_four_digits_jp(n: int):
    """0<=n<=9999 → (romaji, hira, kata, kanji)"""
    assert 0 <= n <= 9999
    if n == 0:
        return ("","","","")
    a = n // 1000
    b = (n // 100) % 10
    c = (n // 10) % 10
    d = n % 10
    hira, roma, kanj = [], [], []

    # 千
    if a:
        if a == 1:
            hira += ["せん"]; roma += ["sen"]; kanj += ["千"]
        elif a == 3:
            hira += ["さんぜん"]; roma += ["sanzen"]; kanj += ["三千"]
        elif a == 8:
            hira += ["はっせん"]; roma += ["hassen"]; kanj += ["八千"]
        else:
            hira += [JP_DIG[a][0] + "せん"]; roma += [JP_DIG[a][1] + "sen"]; kanj += [KANJI_DIG[a] + "千"]

    # 百
    if b:
        if b == 1:
            hira += ["ひゃく"]; roma += ["hyaku"]; kanj += ["百"]
        elif b == 3:
            hira += ["さんびゃく"]; roma += ["sanbyaku"]; kanj += ["三百"]
        elif b == 6:
            hira += ["ろっぴゃく"]; roma += ["roppyaku"]; kanj += ["六百"]
        elif b == 8:
            hira += ["はっぴゃく"]; roma += ["happyaku"]; kanj += ["八百"]
        else:
            hira += [JP_DIG[b][0] + "ひゃく"]; roma += [JP_DIG[b][1] + "hyaku"]; kanj += [KANJI_DIG[b] + "百"]

    # 十
    if c:
        if c == 1:
            hira += ["じゅう"]; roma += ["juu"]; kanj += ["十"]
        else:
            hira += [JP_DIG[c][0] + "じゅう"]; roma += [JP_DIG[c][1] + "juu"]; kanj += [KANJI_DIG[c] + "十"]

    # 一の位
    if d:
        hira += [JP_DIG[d][0]]; roma += [JP_DIG[d][1]]; kanj += [KANJI_DIG[d]]

    hira_s = "".join(hira)
    roma_s = "".join(roma)
    kata_s = hira_to_kata(hira_s)
    kanj_s = "".join(kanj)
    return (roma_s, hira_s, kata_s, kanj_s)

JP_UNITS = [
    ("",     "",      "",      ""),      # 10^0
    ("まん", "man",   "マン",  "万"),    # 10^4
    ("おく", "oku",   "オク",  "億"),    # 10^8
    ("ちょう","chou", "チョウ","兆"),   # 10^12
    ("けい", "kei",   "ケイ",  "京"),    # 10^16
]

def number_to_japanese(n: int):
    if n == 0:
        hira, roma, kata, kanj = JP_DIG[0]
        return (roma, hira, kata, kanj)
    if n < 0 or n > 10**16:
        raise ValueError("Out of supported range")

    groups = []
    x = n
    while x > 0:
        groups.append(x % 10000)  # 4桁ごと
        x //= 10000

    hira_parts, roma_parts, kata_parts, kanj_parts = [], [], [], []

    for idx in reversed(range(len(groups))):
        q = groups[idx]
        if q == 0:
            continue
        roma_g, hira_g, kata_g, kanj_g = read_four_digits_jp(q)

        # 1000万/1000億/1000兆/1000京 = 「いっせん◯◯」
        if q == 1000 and idx >= 1:
            hira_g, roma_g, kata_g, kanj_g = "いっせん", "issen", "イッセン", "一千"

        # 1兆/1京 = いっちょう / いっけい（促音）
        if q == 1 and idx == 3:   # 兆
            hira_g, roma_g, kata_g, kanj_g = "いっ", "ic", "イッ", "一"
        if q == 1 and idx == 4:   # 京
            hira_g, roma_g, kata_g, kanj_g = "いっ", "ik", "イッ", "一"

        unit_h, unit_r, unit_k, unit_c = JP_UNITS[idx]
        hira_parts.append(hira_g + unit_h)
        roma_parts.append(roma_g + unit_r)
        kata_parts.append(kata_g + unit_k)
        kanj_parts.append(kanj_g + unit_c)

    hira = "".join(hira_parts)
    roma = "".join(roma_parts)
    kata = "".join(kata_parts)
    kanj = "".join(kanj_parts)
    return (roma, hira, kata, kanj)

# ------------------------------------------------------------
# Thai number reading (million-based groups)
# ------------------------------------------------------------
TH_DIGIT = ["ศูนย์","หนึ่ง","สอง","สาม","สี่","ห้า","หก","เจ็ด","แปด","เก้า"]
RTGS = {
    "ศูนย์":"sun", "หนึ่ง":"nueng", "สอง":"song", "สาม":"sam", "สี่":"si",
    "ห้า":"ha", "หก":"hok", "เจ็ด":"chet", "แปด":"paet", "เก้า":"kao",
    "สิบ":"sip", "ยี่สิบ":"yi sip", "เอ็ด":"et",
    "ร้อย":"roi", "พัน":"phan", "หมื่น":"muen", "แสน":"saen", "ล้าน":"lan"
}
def to_thai_digits(n: int) -> str:
    m = {"0":"๐","1":"๑","2":"๒","3":"๓","4":"๔","5":"๕","6":"๖","7":"๗","8":"๘","9":"๙"}
    return "".join(m[ch] for ch in str(n))

def read_under_million_th(n: int) -> list[str]:
    assert 0 <= n <= 999_999
    if n == 0: return []
    tokens = []
    k = n // 100_000
    if k: tokens += [TH_DIGIT[k], "แสน"]; n %= 100_000
    k = n // 10_000
    if k: tokens += [TH_DIGIT[k], "หมื่น"]; n %= 10_000
    k = n // 1_000
    if k: tokens += [TH_DIGIT[k], "พัน"]; n %= 1_000
    k = n // 100
    if k: tokens += [TH_DIGIT[k], "ร้อย"]; n %= 100
    t = n // 10; u = n % 10
    if t:
        if t == 1: tokens += ["สิบ"]
        elif t == 2: tokens += ["ยี่สิบ"]
        else: tokens += [TH_DIGIT[t], "สิบ"]
    if u:
        if t >= 1 and u == 1: tokens += ["เอ็ด"]
        else: tokens += [TH_DIGIT[u]]
    return tokens

def thai_number_tokens(n: int) -> list[str]:
    if n == 0: return ["ศูนย์"]
    tokens, groups, x = [], [], n
    while x > 0:
        groups.append(x % 1_000_000)
        x //= 1_000_000
    for i in reversed(range(len(groups))):
        g = groups[i]
        if g == 0: continue
        tokens += read_under_million_th(g)
        tokens += ["ล้าน"] * i
    return tokens

def tokens_to_rtgs(tokens: list[str]) -> str:
    return " ".join(RTGS.get(tok, tok) for tok in tokens)
def tokens_to_thai(tokens: list[str]) -> str:
    return " ".join(tokens)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
ui_lang = st.selectbox("UI / 言語 / ภาษา", ["ja","en","th"], index=0,
                       format_func=lambda k: LABELS[k]["app_title"])
L = LABELS[ui_lang]
st.title(L["app_title"])

target = st.radio(L["target"], [("jp", L["target_jp"]), ("th", L["target_th"])],
                  horizontal=True, index=0, format_func=lambda x: x[1])[0]

with st.expander(L["layout_title"], expanded=False):
    cols_per_row = st.select_slider(L["cols_label"], options=[4,6,8,10], value=4)

# 任意入力（テキストで受け、JSの整数上限を回避）
s = st.text_input(L["input_label"], value="")
if st.button(L["read_btn"], key=f"read_{target}"):
    if re.fullmatch(r"\d+", s or "") and len(s) <= 17:
        n = int(s)
        if n <= 10**16:
            if target == "jp":
                roma, hira, kata, kanj = number_to_japanese(n)
                st.markdown(f"**{L['romaji']}**: `{roma}`")
                st.markdown(f"**{L['hira']}**: {hira}")
                st.markdown(f"**{L['kata']}**: {kata}")
                st.markdown(f"**{L['kanji']}**: {kanj}")
                play_audio(hira, "ja")
            else:
                toks = thai_number_tokens(n)
                thai_text = tokens_to_thai(toks)
                rtgs = tokens_to_rtgs(toks)
                st.markdown(f"**{L['rtgs']}**: `{rtgs}`")
                st.markdown(f"**{L['thai']}**: {thai_text}")
                st.markdown(f"**{L['thai_digits']}**: {to_thai_digits(n)}")
                st.markdown(f"**{L['arabic']}**: {n:,}")
                play_audio(thai_text, "th")
        else:
            st.warning(L["invalid"])
    else:
        st.warning(L["invalid"])

# ------------------------------------------------------------
# Buttons (sections) — responsive columns with unique keys
# ------------------------------------------------------------
rendered = set()

def grid_section(title: str, nums: list[int], key_prefix: str):
    st.subheader(title)
    cols = st.columns(cols_per_row)
    i = 0
    for num in nums:
        if num in rendered:
            continue
        rendered.add(num)
        if cols[i].button(str(num), key=f"{key_prefix}-{target}-{num}"):
            if target == "jp":
                roma, hira, kata, kanj = number_to_japanese(num)
                st.markdown(f"**{L['romaji']}**: `{roma}`")
                st.markdown(f"**{L['hira']}**: {hira}")
                st.markdown(f"**{L['kata']}**: {kata}")
                st.markdown(f"**{L['kanji']}**: {kanj}")
                play_audio(hira, "ja")
            else:
                toks = thai_number_tokens(num)
                thai_text = tokens_to_thai(toks)
                rtgs = tokens_to_rtgs(toks)
                st.markdown(f"**{L['rtgs']}**: `{rtgs}`")
                st.markdown(f"**{L['thai']}**: {thai_text}")
                st.markdown(f"**{L['thai_digits']}**: {to_thai_digits(num)}")
                st.markdown(f"**{L['arabic']}**: {num:,}")
                play_audio(thai_text, "th")
        i = (i + 1) % cols_per_row

# Sections
grid_section(L["sec_basic"], list(range(0, 11)), "b0-10")
grid_section(L["sec_11_99"], list(range(11, 100)), "b11-99")
grid_section(L["sec_100s"], list(range(100, 1000, 100)), "b100s")
grid_section(L["sec_1000s"], list(range(1000, 10000, 1000)), "b1000s")
grid_section(L["sec_10k"], [i*10000 for i in range(1,10)], "b10k")
grid_section(L["sec_100k"], [i*100000 for i in range(1,10)], "b100k")
grid_section(L["sec_1m"], [i*1000000 for i in range(1,10)], "b1m")
grid_section(L["sec_10m"], [i*10000000 for i in range(1,10)], "b10m")
grid_section(L["sec_big"], [100000000, 1000000000000, 10000000000000000], "bbig")
