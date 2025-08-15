# main.py
import streamlit as st
from gtts import gTTS
from io import BytesIO
import base64
import re

# -----------------------------
# UI ラベル（日本語/英語/タイ語）※初期は日本語
# -----------------------------
LANG = {
    "ja": {
        "title": "日本語の数字読み上げアプリ",
        "input_label": "数字を入力してください（0〜10^16）",
        "read_btn": "読み上げ",
        "invalid": "無効な数字です（半角数字のみ／0〜10^16）",
        "sec_basic": "0〜10",
        "sec_11_99": "11〜99（1刻み）",
        "sec_100s": "100〜900（100刻み）",
        "sec_1000s": "1000〜9000（1000刻み）",
        "sec_10k": "10000〜90000（1万刻み）",
        "sec_100k": "100000〜900000（10万刻み）",
        "sec_1m": "1000000〜9000000（100万刻み）",
        "sec_10m": "10000000〜90000000（1000万刻み）",
        "sec_big": "特別（1億・1兆・1京）"
    },
    "en": {
        "title": "Japanese Number Reader",
        "input_label": "Enter a number (0–10^16)",
        "read_btn": "Speak",
        "invalid": "Invalid number (digits only / 0–10^16).",
        "sec_basic": "0–10",
        "sec_11_99": "11–99 (step 1)",
        "sec_100s": "100–900 (by 100)",
        "sec_1000s": "1000–9000 (by 1000)",
        "sec_10k": "10,000–90,000 (by 10k)",
        "sec_100k": "100,000–900,000 (by 100k)",
        "sec_1m": "1,000,000–9,000,000 (by 1M)",
        "sec_10m": "10,000,000–90,000,000 (by 10M)",
        "sec_big": "Special (100M / 1T / 10^16)"
    },
    "th": {
        "title": "แอปอ่านตัวเลขภาษาญี่ปุ่น",
        "input_label": "ป้อนตัวเลข (0–10^16)",
        "read_btn": "อ่านออกเสียง",
        "invalid": "ไม่ถูกต้อง (ใส่เลขล้วน / 0–10^16).",
        "sec_basic": "0–10",
        "sec_11_99": "11–99 (ทีละ 1)",
        "sec_100s": "100–900 (ทีละ 100)",
        "sec_1000s": "1000–9000 (ทีละ 1000)",
        "sec_10k": "10000–90000 (ทีละ 10000)",
        "sec_100k": "100000–900000 (ทีละ 100000)",
        "sec_1m": "1000000–9000000 (ทีละ 1000000)",
        "sec_10m": "10000000–90000000 (ทีละ 10000000)",
        "sec_big": "พิเศษ (หนึ่งร้อยล้าน / หนึ่งล้านล้าน / หนึ่งหมื่นล้านล้าน)"
    },
}

# -----------------------------
# 数詞データ
# -----------------------------
DIGITS = {
    0: ("ぜろ", "zero", "ゼロ", "零"),
    1: ("いち", "ichi", "イチ", "一"),
    2: ("に", "ni", "ニ", "二"),
    3: ("さん", "san", "サン", "三"),
    4: ("よん", "yon", "ヨン", "四"),
    5: ("ご", "go", "ゴ", "五"),
    6: ("ろく", "roku", "ロク", "六"),
    7: ("なな", "nana", "ナナ", "七"),
    8: ("はち", "hachi", "ハチ", "八"),
    9: ("きゅう", "kyuu", "キュウ", "九"),
}

KANJI_DIG = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]

# 大きい位（4桁ごと）
LARGE_UNITS = [
    ("",    "",     "",      ""),     # 10^0 〜 10^3
    ("まん", "man",  "マン",  "万"),  # 10^4
    ("おく", "oku",  "オク",  "億"),  # 10^8
    ("ちょう","chou","チョウ","兆"), # 10^12
    ("けい", "kei",  "ケイ",  "京"),  # 10^16
]

# -----------------------------
# 4桁（〜9999）を読む：音便・省略対応
# -----------------------------
def read_four_digits(n: int):
    """
    0<=n<=9999 の読みを (hira, roma, kata, kanji) で返す
    """
    assert 0 <= n <= 9999
    if n == 0:
        return ("", "", "", "")
    a = n // 1000
    b = (n // 100) % 10
    c = (n // 10) % 10
    d = n % 10

    hira = []
    roma = []
    kanj = []

    # 千
    if a:
        if a == 1:
            hira.append("せん"); roma.append("sen"); kanj.append("千")
        elif a == 3:
            hira.append("さんぜん"); roma.append("sanzen"); kanj.append("三千")
        elif a == 8:
            hira.append("はっせん"); roma.append("hassen"); kanj.append("八千")
        else:
            hira.append(DIGITS[a][0] + "せん")
            roma.append(DIGITS[a][1] + "sen")
            kanj.append(KANJI_DIG[a] + "千")

    # 百
    if b:
        if b == 1:
            hira.append("ひゃく"); roma.append("hyaku"); kanj.append("百")
        elif b == 3:
            hira.append("さんびゃく"); roma.append("sanbyaku"); kanj.append("三百")
        elif b == 6:
            hira.append("ろっぴゃく"); roma.append("roppyaku"); kanj.append("六百")
        elif b == 8:
            hira.append("はっぴゃく"); roma.append("happyaku"); kanj.append("八百")
        else:
            hira.append(DIGITS[b][0] + "ひゃく")
            roma.append(DIGITS[b][1] + "hyaku")
            kanj.append(KANJI_DIG[b] + "百")

    # 十
    if c:
        if c == 1:
            hira.append("じゅう"); roma.append("juu"); kanj.append("十")
        else:
            hira.append(DIGITS[c][0] + "じゅう")
            roma.append(DIGITS[c][1] + "juu")
            kanj.append(KANJI_DIG[c] + "十")

    # 一の位
    if d:
        hira.append(DIGITS[d][0]); roma.append(DIGITS[d][1]); kanj.append(KANJI_DIG[d])

    hira_s = "".join(hira)
    roma_s = "".join(roma)
    kanj_s = "".join(kanj)
    kata_s = hira_to_kata(hira_s)
    return (roma_s, hira_s, kata_s, kanj_s)

# ひらがな→カタカナ
def hira_to_kata(s: str) -> str:
    res = []
    for ch in s:
        code = ord(ch)
        if 0x3041 <= code <= 0x3096:  # ぁ〜ゖ
            res.append(chr(code + 0x60))
        elif ch == "ー":
            res.append("ー")
        else:
            res.append(ch)
    return "".join(res)

# -----------------------------
# 全体の数（0〜一京）を読む
# -----------------------------
def number_to_japanese(n: int):
    if n == 0:
        return DIGITS[0]

    if n < 0 or n > 10**16:
        raise ValueError("Out of supported range")

    groups = []
    x = n
    while x > 0:
        groups.append(x % 10000)  # 4桁ずつ
        x //= 10000

    # 高位から結合
    hira_parts = []
    roma_parts = []
    kata_parts = []
    kanj_parts = []

    for idx in reversed(range(len(groups))):
        q = groups[idx]
        if q == 0:
            continue

        roma_g, hira_g, kata_g, kanj_g = read_four_digits(q)

        # 特別処理: 1000万 / 1000億 / 1000兆 / 1000京 = 「いっせん◯◯」
        if q == 1000 and idx >= 1:
            hira_g = "いっせん"
            roma_g = "issen"
            kata_g = "イッセン"
            kanj_g = "一千"

        # 特別処理: 1兆 / 1京 の「いっ◯◯」
        # （万・億は「いち◯◯」のまま）
        if q == 1 and idx == 3:  # 兆
            hira_g = "いっ"
            roma_g = "ic"
            kata_g = "イッ"
            kanj_g = "一"
        if q == 1 and idx == 4:  # 京
            hira_g = "いっ"
            roma_g = "ik"
            kata_g = "イッ"
            kanj_g = "一"

        unit_h, unit_r, unit_k, unit_c = LARGE_UNITS[idx]
        hira_parts.append(hira_g + unit_h)
        roma_parts.append(roma_g + unit_r)
        kata_parts.append(kata_g + unit_k)
        kanj_parts.append(kanj_g + unit_c)

    hira = "".join(hira_parts)
    roma = "".join(roma_parts)
    kata = "".join(kata_parts)
    kanj = "".join(kanj_parts)

    return (roma, hira, kata, kanj)

# -----------------------------
# 音声生成（gTTS）
# -----------------------------
def generate_audio(hira_text: str) -> str:
    if not hira_text.strip():
        return ""
    tts = gTTS(text=hira_text, lang='ja')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    return f"<audio autoplay controls src='data:audio/mp3;base64,{b64}'></audio>"

# -----------------------------
# UI
# -----------------------------
lang = st.selectbox("Language / 言語 / ภาษา", ["ja", "en", "th"], index=0,
                    format_func=lambda k: LANG[k]["title"])
L = LANG[lang]
st.title(L["title"])

# 任意入力（テキストで受け、JSの整数上限に縛られない）
s = st.text_input(L["input_label"], value="")
if st.button(L["read_btn"]):
    if re.fullmatch(r"\d+", s or "") and len(s) <= 17:  # 10^16 は 17桁（1 + 16個の0）
        n = int(s)
        if n <= 10**16:
            roma, hira, kata, kanj = number_to_japanese(n)
            st.markdown(f"**ローマ字**: `{roma}`")
            st.markdown(f"**ひらがな**: {hira}")
            st.markdown(f"**カタカナ**: {kata}")
            st.markdown(f"**漢字**: {kanj}")
            st.markdown(generate_audio(hira), unsafe_allow_html=True)
        else:
            st.warning(L["invalid"])
    else:
        st.warning(L["invalid"])

# -----------------------------
# ボタン群（重複は自動スキップ）
# -----------------------------
rendered = set()

def button_grid(title: str, nums: list[int], cols_per_row: int = 10, key_prefix: str = ""):
    st.subheader(title)
    cols = st.columns(cols_per_row)
    col_idx = 0
    for num in nums:
        if num in rendered:
            continue
        rendered.add(num)
        if cols[col_idx].button(str(num), key=f"{key_prefix}{num}"):
            roma, hira, kata, kanj = number_to_japanese(num)
            st.markdown(f"**ローマ字**: `{roma}`")
            st.markdown(f"**ひらがな**: {hira}")
            st.markdown(f"**カタカナ**: {kata}")
            st.markdown(f"**漢字**: {kanj}")
            st.markdown(generate_audio(hira), unsafe_allow_html=True)
        col_idx = (col_idx + 1) % cols_per_row

# 0–10, 11–99（分割して重複回避）
button_grid(L["sec_basic"], list(range(0, 11)), key_prefix="b0-10-")
button_grid(L["sec_11_99"], list(range(11, 100)), key_prefix="b11-99-")

# 100–900（100刻み）
button_grid(L["sec_100s"], list(range(100, 1000, 100)), key_prefix="b100s-")

# 1000–9000（1000刻み）
button_grid(L["sec_1000s"], list(range(1000, 10000, 1000)), key_prefix="b1000s-")

# 1万〜9万（1万刻み）
button_grid(L["sec_10k"], [i * 10000 for i in range(1, 10)], key_prefix="b10k-")

# 10万〜90万（10万刻み）
button_grid(L["sec_100k"], [i * 100000 for i in range(1, 10)], key_prefix="b100k-")

# 100万〜900万（100万刻み）
button_grid(L["sec_1m"], [i * 1000000 for i in range(1, 10)], key_prefix="b1m-")

# 1000万〜9000万（1000万刻み）
button_grid(L["sec_10m"], [i * 10000000 for i in range(1, 10)], key_prefix="b10m-")

# 特別：一億・一兆・一京
button_grid(L["sec_big"], [100000000, 1000000000000, 10000000000000000], key_prefix="bbig-")
