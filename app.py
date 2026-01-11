"""
Jifra 🗼 - The Definitive Edition (v3.0)
=======================================
Masterpiece of Simplicity, Intelligence, and Intuition.
Tech: Streamlit + Google GenerativeAI (Legacy SDK)
"""

import streamlit as st
import google.generativeai as genai
import re
import time
import random
from datetime import datetime

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
    
    /* サイドバー: 洗練された暗色と高コントラスト */
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
    .subtitle {{ text-align: center; color: #8b949e !important; font-size: 1.1rem; margin-bottom: 2.5rem; }}
    
    /* インタラクティブ要素: カーソル形状変更 */
    div.stButton > button, .stTextArea textarea, .stSelectbox > div > div {{
        cursor: pointer !important;
    }}
    
    /* ボタンデザイン */
    div.stButton > button {{
        width: 100%; border-radius: 12px !important; font-weight: 600 !important;
        height: 3.2rem; transition: 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: none !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }}
    div.stButton > button[kind="secondary"] {{
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }}
    /* 無効ボタンの視覚的表現 */
    div.stButton > button:disabled {{
        opacity: 0.3 !important;
        background: #161b22 !important;
        color: #484f58 !important;
        cursor: not-allowed !important;
    }}

    /* 入力欄 */
    .stTextArea textarea {{
        background-color: #0d1117 !important;
        border: 2px solid #30363d !important;
        border-radius: 14px !important;
        color: #ffffff !important;
        font-size: 1.15rem !important;
        padding: 1rem !important;
    }}
    .stTextArea textarea:focus {{ border-color: #ff6b6b !important; }}

    /* セレクトボックス */
    .stSelectbox > div > div {{
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }}

    /* 結果表示 (ワンタップコピー機能 st.code 向けの調整) */
    .stCode {{ border-radius: 12px !important; border: 1px solid #30363d !important; overflow: hidden; }}
    code {{ background-color: #161b22 !important; font-family: 'Inter', sans-serif !important; }}
    
    /* 結果カード */
    .res-card {{
        background: #161b22; border-radius: 14px; border: 1px solid #30363d;
        padding: 1rem; margin-top: 1rem;
    }}
    .res-label {{
        font-size: 0.75rem; font-weight: 700; color: #8b949e !important;
        margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;
    }}
    
    /* 履歴リスト */
    .history-item {{
        padding: 0.5rem 0.8rem; background: #0d1117; border: 1px solid #30363d;
        border-radius: 8px; margin-bottom: 0.5rem; font-size: 0.9rem; color: #8b949e;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. インテリジェント AI ロジック
# =============================================================================
@st.cache_resource
def get_ai_model():
    try:
        genai.configure(api_key=API_KEY)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        target = next((m for m in models if "1.5-flash" in m), models[0] if models else None)
        if not target: return None, "No available models found."
        return genai.GenerativeModel(target), target
    except Exception as e:
        return None, str(e)

def call_ai(model, prompt):
    max_retries = 3
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text, None
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                time.sleep((2 ** i) + random.random())
                continue
            return None, str(e)
    return None, "Connection failed."

def detect_lang(text):
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text): return 'JP'
    return 'EN/FR'

# =============================================================================
# 5. アプリケーション本体
# =============================================================================
def main():
    model, model_name = get_ai_model()
    
    # --- Sidebar: Settings & Simplified History ---
    with st.sidebar:
        st.header("⚙️ Settings")
        pwd = st.text_input("🔑 PRO Key", type="password")
        is_pro = (pwd == PRO_PASSWORD)
        if is_pro: st.success("PRO Mode Active")
        
        st.divider()
        st.subheader("📜 History")
        if not st.session_state.history:
            st.caption("No history yet.")
        else:
            for h in st.session_state.history:
                st.markdown(f'<div class="history-item">{h}</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()

    # --- Header ---
    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)

    # --- Mode Selection (Visual Icons Only) ---
    tabs_labels = ["💬 Casual", "👔 Formal", "✨ PRO", "🎨 Prompt"]
    style_keys = ["casual", "formal", "sns", "prompt_gen"]
    
    cols = st.columns(4)
    for i, (label, key) in enumerate(zip(tabs_labels, style_keys)):
        with cols[i]:
            # SNSとPromptはPRO専用。無効時は視覚的に判別可能
            disabled_style = (key in ["sns", "prompt_gen"] and not is_pro)
            if st.button(label, key=f"btn_{key}", type="primary" if st.session_state.style == key else "secondary", disabled=disabled_style):
                st.session_state.style = key
                st.rerun()

    st.write("")
    
    # --- Intelligent Direction Control ---
    if st.session_state.style == "prompt_gen":
        guide_txt = "🤖 [Prompt Generator] Keywords to AI Prompt (English)" if detect_lang(st.session_state.input_text) == 'JP' else "🤖 [プロンプト生成] キーワードをAI用プロンプトに変換"
        st.info(guide_txt)
        sel_mode = "prompt_gen"
    elif st.session_state.style == "sns":
        sel_mode = "sns"
    else:
        dirs = {"auto": "🔄 Auto Detect", "ja_fr": "🇯🇵 日 ➡ 🇫🇷 仏", "fr_ja": "🇫🇷 仏 ➡ 🇯🇵 日"}
        if is_pro:
            dirs.update({"ja_en": "🇯🇵 日 ➡ 🇺🇸 英", "en_ja": "🇺🇸 英 ➡ 🇯🇵 日"})
        sel_mode = st.selectbox("Direction", options=list(dirs.keys()), format_func=lambda x: dirs[x], label_visibility="collapsed")

    # --- Input Area ---
    input_text = st.text_area(
        "Input",
        value=st.session_state.input_text,
        placeholder="Type here to translate or generate...",
        height=160,
        label_visibility="collapsed"
    )

    # --- Main Actions ---
    # 多言語対応のアクションボタン
    lang = detect_lang(input_text)
    btn_label = "翻訳・変換する" if lang == 'JP' else "Translate / Generate"
    
    c_run, c_clear = st.columns([5, 1])
    with c_run:
        run_btn = st.button(btn_label, type="primary", use_container_width=True)
    with c_clear:
        if st.button("🗑️", use_container_width=True, help="Clear input and results"):
            st.session_state.input_text = ""
            st.session_state.current_result = None
            st.rerun()

    # --- Execution Logic ---
    if run_btn:
        if not input_text.strip(): return
        
        with st.spinner("Processing..."):
            if sel_mode == "prompt_gen":
                prompt = f"""
                Convert the following keyword into 3 short, intelligent AI prompts in English.
                Provide ONLY the code and a simple JP translation for each.
                [MJ] (MJ version)
                [SD] (SD version)
                [SYS] (System prompt version)
                Input: {input_text}
                """
            elif sel_mode == "sns":
                prompt = f"""
                Convert the input into SLEEK SNS posts for 🇯🇵, 🇺🇸, and 🇫🇷.
                - NO hallucinations or imaginary facts. 
                - Emoji + Hashtags included.
                - Single line language tag (e.g., 🇯🇵 JP).
                - Proper spacing.
                Input: {input_text}
                """
            else:
                tone = "Casual and friendly" if st.session_state.style == 'casual' else "Formal and professional"
                prompt = f"""
                Translate the input into {tone} natural phrases ({sel_mode}).
                Provide 2 variations with simple back-translations in JP.
                Input: {input_text}
                """
            
            res, err = call_ai(model, prompt)
            if err:
                st.error(f"❌ Error: {err}")
            else:
                st.session_state.current_result = res
                st.session_state.input_text = input_text
                # Update history (content only)
                h_text = input_text.replace('\n', ' ')[:40]
                if h_text and (not st.session_state.history or h_text != st.session_state.history[0]):
                    st.session_state.history.insert(0, h_text)
                    st.session_state.history = st.session_state.history[:15]
                st.rerun()

    # --- Visual Results (One-tap Copy Enabled via st.code) ---
    if st.session_state.current_result:
        st.divider()
        res = st.session_state.current_result
        
        if st.session_state.style == "prompt_gen":
            st.markdown('<p class="res-label">🤖 AI Prompts (Tap code to copy)</p>', unsafe_allow_html=True)
            st.code(res, language="text")
        elif st.session_state.style == "sns":
            st.markdown('<p class="res-label">🌍 SNS Collection (Tap to copy)</p>', unsafe_allow_html=True)
            st.code(res, language="text")
        else:
            # 翻訳結果のスマートな表示
            st.markdown(f'<p class="res-label">💡 {st.session_state.style.upper()} Result (Tap to copy)</p>', unsafe_allow_html=True)
            st.code(res, language="text")

if __name__ == "__main__":
    main()