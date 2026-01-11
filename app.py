"""
Jifra 🗼 - The Definitive Edition
================================
Refined UI/UX with Flag-only Labels & One-click Copy
Tech: Streamlit + Google GenerativeAI (Legacy SDK)
"""

import streamlit as st
import google.generativeai as genai
import time
import random

# =============================================================================
# 1. 認証 & ページ設定
# =============================================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    PRO_PASSWORD = st.secrets["PRO_PASSWORD"]
except KeyError:
    # 互換性フォールバック
    API_KEY = st.secrets.get("gemini_api_key", "YOUR_DEFAULT_API_KEY")
    PRO_PASSWORD = st.secrets.get("pro_password", "JIFRA2026")

st.set_page_config(page_title="Jifra 🗼", page_icon="🗼", layout="centered")

# Session State 初期化
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'results' not in st.session_state: st.session_state.results = None
if 'history' not in st.session_state: st.session_state.history = []

# =============================================================================
# 2. カスタムデザイン (CSS)
# =============================================================================
st.markdown("""
<style>
    /* ベースカラー */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
    }
    .main .block-container { padding-top: 1.5rem; max-width: 700px; }
    
    /* フォント・テキスト */
    .stApp p, .stApp span, .stApp label, .stApp div { color: #f0f6fc !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; }

    /* タイトル */
    .main-title {
        text-align: center; font-size: 3.2rem; font-weight: 800;
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }

    /* サイドバー */
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }

    /* 入力エリア */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 2px solid #30363d !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }

    /* ボタン */
    div.stButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
        transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important;
        border: none !important; color: white !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #21262d !important; border: 1px solid #30363d !important;
    }

    /* タブ */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important; color: #8b949e !important;
        background-color: transparent !important; border: none !important;
    }
    .stTabs [aria-selected="true"] { color: #ff6b6b !important; border-bottom: 2px solid #ff6b6b !important; }

    /* コードブロック (コピー用) */
    code { background-color: #161b22 !important; color: #e6edf3 !important; }
    
    /* 履歴 */
    .history-card {
        background-color: #0d1117; border: 1px solid #30363d;
        border-radius: 8px; padding: 0.6rem; margin-bottom: 0.4rem; font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. AIロジック (Gemini)
# =============================================================================
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=API_KEY)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        target = next((m for m in models if "1.5-flash" in m), models[0] if models else "models/gemini-1.5-flash")
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
            if i < max_retries - 1:
                time.sleep((2 ** i) + random.random())
                continue
            return None, str(e)
    return None, "Connection failed."

# =============================================================================
# 4. メインアプリケーション
# =============================================================================
def main():
    model, model_name = get_model()

    # --- Sidebar (Settings & History) ---
    with st.sidebar:
        st.title("⚙️ Settings")
        pwd = st.text_input("🔑 PRO Key", type="password")
        is_pro = (pwd == PRO_PASSWORD)
        if is_pro: st.success("✨ PRO Mode")
        
        st.divider()
        st.subheader("📜 History")
        if not st.session_state.history:
            st.caption("No history yet.")
        else:
            for h in st.session_state.history:
                st.markdown(f'<div class="history-card">{h}</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()

    # --- Header ---
    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)

    # --- Input Mode (Flag Icons Only) ---
    st.markdown('<p style="font-weight:600; margin-bottom:0.5rem; color:#8b949e;">Select Mode</p>', unsafe_allow_html=True)
    mode_options = ["🇯🇵 ➡ 🇫🇷🇺🇸", "🇫🇷 ➡ 🇯🇵🇺🇸", "🇺🇸 ➡ 🇯🇵", "🎨 AI Prompts"]
    sel_mode = st.radio("Mode", options=mode_options, horizontal=True, label_visibility="collapsed")
    
    # --- Text Area ---
    input_text = st.text_area(
        "Input", 
        value=st.session_state.input_text,
        placeholder="Enter text to translate or prompt keyword...",
        height=150,
        label_visibility="collapsed"
    )

    # --- Action Buttons ---
    col_run, col_clear = st.columns([4, 1])
    with col_run:
        run_btn = st.button("翻訳 / Generate", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️", use_container_width=True, help="Clear input and results"):
            st.session_state.input_text = ""
            st.session_state.results = None
            st.rerun()

    # =============================================================================
    # 5. AI Execution & Formatting
    # =============================================================================
    if run_btn:
        if not input_text.strip():
            st.warning("⚠️ Please enter some text.")
            return

        with st.spinner("🚀 Working..."):
            if "🎨" in sel_mode:
                # Prompt Mode
                sys_prompt = f"""
Convert the following keyword into 3 types of high-quality AI prompts in English.
Provide ONLY the requested content. No chit-chat.
Format strictly:
[MJ]
/imagine prompt: ...
(Translation in JP)

[SD]
(masterpiece, best quality), ...
(Translation in JP)

[SYS]
You are ...
(Translation in JP)

Input: {input_text}
"""
            else:
                # Translation & SNS Mode (Combined)
                style_guide = "Casual (friendly) and Formal (business)"
                sys_prompt = f"""
As a linguistic expert, translate the following input based on the direction: {sel_mode}.
Generate results for Casual, Formal, and SNS.

【CRITICAL RULES】
1. NO IMAGINARY FACTS. Do not create experiences or facts not present in the input. Just rewrite/translate the input.
2. SNS: One post each for 🇺🇸, 🇫🇷, 🇯🇵 with emoji and hashtags. Keep it sleek. Single empty line between text and tags.
3. Casual/Formal: Provide two distinct natural patterns with simple back-translations in JP.
4. Output format MUST be parsable.

Input: {input_text}
"""
            
            res, err = call_ai(model, sys_prompt)
            if err:
                st.error(f"❌ Error: {err}")
            else:
                st.session_state.results = res
                st.session_state.input_text = input_text
                # Update history (keep unique text only)
                if input_text not in st.session_state.history:
                    st.session_state.history.insert(0, input_text[:50])
                    st.session_state.history = st.session_state.history[:10]

    # =============================================================================
    # 6. Display Results (Tabs)
    # =============================================================================
    if st.session_state.results:
        raw_res = st.session_state.results
        
        if "🎨" in sel_mode:
            st.divider()
            st.subheader("🎨 AI Prompts")
            # Simple code display for prompts
            parts = raw_res.split("[")
            for p in parts:
                if "]" in p:
                    label, content = p.split("]", 1)
                    st.caption(f"**{label}**")
                    st.code(content.strip(), language="text")
        else:
            # Tabs for Casual, Formal, SNS
            t1, t2, t3 = st.tabs(["Casual", "Formal", "for SNS *PRO"])
            
            with t1:
                st.markdown("**ニュアンス違いの2パターン**")
                st.code(raw_res, language="text") # Simplified for robustness
            with t2:
                st.markdown("**ビジネス・丁寧な表現**")
                st.code(raw_res, language="text")
            with t3:
                if is_pro:
                    st.markdown("**コピーしてそのまま投稿**")
                    st.code(raw_res, language="text")
                else:
                    st.warning("🔒 SNS Mode is PRO Only.")

if __name__ == "__main__":
    main()