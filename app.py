"""
Jifra 🗼 - Definitive Smart Edition (v4.0)
=========================================
Simple. Intuitive. No nonsense.
Tech: Streamlit + Google GenerativeAI (Legacy SDK)
"""

import streamlit as st
import google.generativeai as genai
import re
import time
import random

# =============================================================================
# 1. セキュリティ & 認証
# =============================================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    PRO_PASSWORD = st.secrets["PRO_PASSWORD"]
except KeyError:
    try:
        API_KEY = st.secrets["gemini_api_key"]
        PRO_PASSWORD = st.secrets["pro_password"]
    except KeyError:
        st.error("❌ KEY Error: 'GEMINI_API_KEY' or 'PRO_PASSWORD' not found in Secrets.")
        st.stop()

# =============================================================================
# 2. ページ基本設定 & Session State
# =============================================================================
st.set_page_config(page_title="Jifra 🗼", page_icon="🗼", layout="centered")

if 'history' not in st.session_state: st.session_state.history = []
if 'style' not in st.session_state: st.session_state.style = 'casual'
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'current_result' not in st.session_state: st.session_state.current_result = None

# =============================================================================
# 3. 究極の洗練デザイン (CSS)
# =============================================================================
st.markdown(f"""
<style>
    /* ベースカラー */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: #0d1117 !important;
    }}
    .main .block-container {{ padding-top: 1.5rem; max-width: 700px; }}
    
    /* サイドバー */
    [data-testid="stSidebar"] {{
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }}
    [data-testid="stSidebar"] * {{ color: #e6edf3 !important; }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{ color: #ffffff !important; }}
    [data-testid="stSidebar"] .stTextInput input {{
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
    }}

    /* テキストスタイル */
    .stApp p, .stApp span, .stApp label, .stApp div {{ color: #f0f6fc !important; }}
    h1, h2, h3, h4, h5, h6 {{ color: #ffffff !important; font-weight: 700 !important; }}
    .main-title {{
        text-align: center; font-size: 3.2rem; font-weight: 800;
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }}
    
    /* インタラクティブ要素: カーソル形状 */
    div.stButton > button {{
        cursor: pointer !important;
    }}
    .stTextArea textarea {{
        cursor: text !important; /* I-beam for typing intuition */
    }}
    
    /* ボタンデザイン */
    div.stButton > button {{
        width: 100%; border-radius: 12px !important; font-weight: 600 !important;
        height: 3.2rem; transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        border: none !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important;
        color: white !important;
    }}
    div.stButton > button[kind="secondary"] {{
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }}
    /* 無効ボタンの視覚的表現: より暗く目立たなく */
    div.stButton > button:disabled {{
        opacity: 0.15 !important;
        background: #0d1117 !important;
        color: #30363d !important;
        cursor: not-allowed !important;
    }}

    /* 入力欄 */
    .stTextArea textarea {{
        background-color: #0d1117 !important;
        border: 2px solid #30363d !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        padding: 1rem !important;
    }}
    .stTextArea textarea:focus {{ border-color: #ff6b6b !important; }}

    /* ワンタップコピー (st.code) の洗練 */
    .stCode {{ border-radius: 10px !important; border: 1px solid #30363d !important; }}
    code {{ background-color: #161b22 !important; color: #e6edf3 !important; font-size: 1rem !important; }}
    
    /* 履歴リスト: シンプル化 */
    .history-item {{
        padding: 0.4rem 0.6rem; background: #0d1117; border: 1px solid #30363d;
        border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.85rem; color: #8b949e;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. AI ロジック
# =============================================================================
@st.cache_resource
def get_ai_model():
    try:
        genai.configure(api_key=API_KEY)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        target = next((m for m in models if "1.5-flash" in m), models[0] if models else None)
        return genai.GenerativeModel(target), target
    except Exception as e:
        return None, str(e)

def call_ai(model, prompt):
    max_retries = 3
    for i in range(max_retries):
        try:
            # 物理的に余計な文章を封印するためのグローバルな制約
            strict_prompt = f"ANSWER ONLY WITH THE RESULT. NO CHAT, NO INTRODUCTION, NO EXPLANATION.\n\n{prompt}"
            response = model.generate_content(strict_prompt)
            return response.text, None
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                time.sleep((2 ** i) + random.random())
                continue
            return None, str(e)
    return None, "Failed."

def detect_lang(text):
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text): return 'JP'
    return 'EN/FR'

# =============================================================================
# 5. アプリケーション本体
# =============================================================================
def main():
    model, model_name = get_ai_model()
    
    with st.sidebar:
        st.header("⚙️ Settings")
        pwd = st.text_input("🔑 PRO Password", type="password")
        is_pro = (pwd == PRO_PASSWORD)
        if is_pro: st.success("PRO Active")
        
        st.divider()
        st.subheader("📜 History")
        if not st.session_state.history:
            st.caption("Empty.")
        else:
            for h in st.session_state.history:
                st.markdown(f'<div class="history-item">{h}</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear", help="Clear history"):
                st.session_state.history = []
                st.rerun()

    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)

    # --- Mode Selection ---
    # 日本語名から洗練されたシンボル/表記へ。SNSボタンはPROに復元。
    modes = ["💬 Casual", "👔 Formal", "✨ PRO", "🎨 Prompt"]
    style_keys = ["casual", "formal", "sns", "prompt_gen"]
    
    cols = st.columns(4)
    for i, (label, key) in enumerate(zip(modes, style_keys)):
        with cols[i]:
            is_locked = (key in ["sns", "prompt_gen"] and not is_pro)
            if st.button(label, key=f"btn_{key}", type="primary" if st.session_state.style == key else "secondary", disabled=is_locked):
                st.session_state.style = key
                st.rerun()

    st.write("")
    
    # --- UI Logic based on Mode ---
    lang = detect_lang(st.session_state.input_text)
    
    if st.session_state.style == "prompt_gen":
        guide = "🤖 Keyword ➡ Image Prompt (ENG) + JP Translation" if lang == 'EN/FR' else "🤖 キーワード ➡ 画像プロンプト (英語) + 日本語訳"
        st.info(guide)
        sel_mode = "prompt_gen"
    elif st.session_state.style == "sns":
        sel_mode = "sns"
    else:
        # PROボタン以外では出力言語選択を表示
        dirs = {"auto": "🔄 Auto Detect", "ja_fr": "🇯🇵 日 ➡ 🇫🇷 仏", "fr_ja": "🇫🇷 仏 ➡ 🇯🇵 日"}
        if is_pro:
            dirs.update({"ja_en": "🇯🇵 日 ➡ 🇺🇸 英", "en_ja": "🇺🇸 英 ➡ 🇯🇵 日"})
        sel_mode = st.selectbox("Dir", options=list(dirs.keys()), format_func=lambda x: dirs[x], label_visibility="collapsed")

    # --- Input ---
    input_text = st.text_area(
        "Input",
        value=st.session_state.input_text,
        placeholder="Input text here...",
        height=140,
        label_visibility="collapsed"
    )

    # --- Actions: Paper Plane Icon ---
    c_run, c_clear = st.columns([5, 1])
    with c_run:
        # 紙飛行機アイコンを含むスマートなラベル
        btn_txt = "✈️ Send" if lang == 'EN/FR' else "✈️ 送信する"
        run_btn = st.button(btn_txt, type="primary", use_container_width=True)
    with c_clear:
        if st.button("🗑️", use_container_width=True, help="Reset everything"):
            st.session_state.input_text = ""
            st.session_state.current_result = None
            st.rerun()

    # --- Execution ---
    if run_btn:
        if not input_text.strip(): return
        
        with st.spinner("Processing..."):
            if sel_mode == "prompt_gen":
                prompt = f"""
                Convert onto 3 short version PROMPTS in English.
                Provide Japanese translation (back-translation) for each.
                [MJ] MJ v6 prompt
                [SD] Stable Diffusion tag format
                [SYS] Role-based prompt
                Input: {input_text}
                """
            elif sel_mode == "sns":
                prompt = f"""
                Convert input into 3 SNS posts: 🇯🇵, 🇺🇸, 🇫🇷.
                - PURE TRANSLATION/CONVERSION. DO NOT IMAGINE OR ADD FACTS.
                - Keep it simple: [Icon] [Language Code]
                - Compact spacing. Tag on new line with single empty line.
                Input: {input_text}
                """
            else:
                tone = "Casual" if st.session_state.style == 'casual' else "Formal"
                prompt = f"""
                Translate into {tone} natural phrases ({sel_mode}).
                Provide 2 variations with simple back-translations in JP.
                Input: {input_text}
                """
            
            res, err = call_ai(model, prompt)
            if err:
                st.error(f"❌ Error: {err}")
            else:
                st.session_state.current_result = res
                st.session_state.input_text = input_text
                # Clean History (latest content only)
                h_text = input_text.replace('\n', ' ')[:30]
                if h_text and (not st.session_state.history or h_text != st.session_state.history[0]):
                    st.session_state.history.insert(0, h_text)
                    st.session_state.history = st.session_state.history[:10]
                st.rerun()

    # --- Display Result: One-tap Copy ONLY ---
    if st.session_state.current_result:
        st.divider()
        # 装飾（✨Latest Result等）を一切排除し、ダイレクトに st.code を表示
        st.code(st.session_state.current_result, language="text")

if __name__ == "__main__":
    main()