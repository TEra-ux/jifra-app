"""
Jifra 🗼 - AI Smart Translator (Enhanced Edition v4)
====================================================
Features: Translation, SNS, Prompt Generation, History, Pin
Tech: Streamlit + Google GenerativeAI (Legacy SDK)
"""

import streamlit as st
import google.generativeai as genai
import re
import time
import random

# =============================================================================
# 1. 認証設定
# =============================================================================
try:
    API_KEY = st.secrets["gemini_api_key"]
    PRO_PASSWORD = st.secrets["pro_password"]
except KeyError:
    st.error("❌ Secrets not configured.")
    st.stop()

# =============================================================================
# 2. ページ基本設定 & Session State
# =============================================================================
st.set_page_config(page_title="Jifra 🗼", page_icon="🗼", layout="centered")

if 'style' not in st.session_state: st.session_state.style = 'casual'
if 'history' not in st.session_state: st.session_state.history = []
if 'current_result' not in st.session_state: st.session_state.current_result = None
if 'input_text' not in st.session_state: st.session_state.input_text = ""

# =============================================================================
# 3. カスタムデザイン (CSS)
# =============================================================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
    }
    .main .block-container { padding-top: 2rem; max-width: 700px; }
    
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #ffffff !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
    }

    .stApp p, .stApp span, .stApp label, .stApp div { color: #f0f6fc !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
    .main-title {
        text-align: center; font-size: 3.5rem; font-weight: 800;
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle { text-align: center; color: #8b949e !important; font-size: 1.1rem; margin-bottom: 2rem; }
    
    /* PRO表示バッジ */
    .pro-badge {
        text-align: center; padding: 0.5rem; margin-bottom: 1rem;
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
        border-radius: 8px; font-weight: 600; color: white !important;
    }
    .free-badge {
        text-align: center; padding: 0.5rem; margin-bottom: 1rem;
        background: #21262d; border: 1px solid #30363d;
        border-radius: 8px; font-weight: 600; color: #8b949e !important;
    }
    
    /* ボタン: 選択時=塗り、非選択=赤枠のみ */
    div.stButton > button { 
        width: 100%; border-radius: 10px !important; font-weight: 600 !important; 
        height: 3.5rem; cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"] { 
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important; 
        color: white !important; 
        border: none !important;
    }
    div.stButton > button[kind="secondary"] { 
        background-color: transparent !important; 
        color: #ff6b6b !important; 
        border: 2px solid #ff6b6b !important;
    }
    div.stButton > button:disabled { 
        opacity: 0.3 !important; 
        cursor: not-allowed !important; 
        border-color: #30363d !important;
        color: #484f58 !important;
    }
    
    /* 入力欄 */
    .stTextArea textarea { 
        background-color: #0d1117 !important; 
        border: 2px solid #30363d !important; 
        border-radius: 12px !important; 
        color: #ffffff !important; 
        font-size: 1.1rem !important;
        cursor: text !important;
        caret-color: #ff6b6b !important;
    }
    .stTextArea textarea:focus {
        border-color: #ff6b6b !important;
        outline: none !important;
    }
    
    .stSelectbox > div > div { background-color: #161b22 !important; border: 1px solid #30363d !important; color: #ffffff !important; cursor: pointer !important; }
    
    /* 結果表示: コードブロックをダークに */
    .stCode { 
        border-radius: 12px !important; 
        border: 1px solid #30363d !important; 
        margin-top: 1rem !important;
    }
    .stCode pre { 
        background-color: #161b22 !important; 
    }
    .stCode code { 
        background-color: #161b22 !important; 
        color: #e6edf3 !important; 
        font-size: 1rem !important;
        font-family: inherit !important;
    }
    
    /* 履歴 */
    .history-item {
        padding: 0.5rem; background: #0d1117; border: 1px solid #30363d;
        border-radius: 6px; margin-bottom: 0.4rem; font-size: 0.85rem; color: #8b949e;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .pinned { border-left: 3px solid #f1c40f !important; }
    
    /* スピナーの色 */
    .stSpinner > div { border-top-color: #ff6b6b !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. モデル初期化
# =============================================================================
@st.cache_resource
def init_model():
    try:
        genai.configure(api_key=API_KEY)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        target = next((p for p in priority if p in available), available[0] if available else "models/gemini-1.5-flash")
        return genai.GenerativeModel(target), target
    except Exception as e:
        return None, str(e)

def call_api(model, prompt):
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
    return None, "Error"

# =============================================================================
# 5. 履歴管理
# =============================================================================
def add_history(input_text, result, is_pro):
    st.session_state.history.insert(0, {"id": time.time(), "input": input_text[:30], "result": result, "pinned": False})
    if not is_pro:
        st.session_state.history = st.session_state.history[:1]
    else:
        pinned = [h for h in st.session_state.history if h.get("pinned")]
        unpinned = [h for h in st.session_state.history if not h.get("pinned")]
        st.session_state.history = (pinned + unpinned)[:20]

# =============================================================================
# 6. メインUI
# =============================================================================
def main():
    model, model_name = init_model()

    with st.sidebar:
        st.header("⚙️")
        pwd = st.text_input("🔑 PRO", type="password")
        is_pro = (pwd == PRO_PASSWORD)
        if is_pro: st.success("✨ PRO")
        
        st.divider()
        st.subheader("📜")
        if not st.session_state.history:
            st.caption("Empty")
        else:
            pinned_count = sum(1 for h in st.session_state.history if h.get("pinned"))
            for h in st.session_state.history:
                css = "history-item pinned" if h.get("pinned") else "history-item"
                st.markdown(f'<div class="{css}">{h["input"]}...</div>', unsafe_allow_html=True)
                if is_pro:
                    c1, c2 = st.columns([3, 1])
                    with c2:
                        if h.get("pinned"):
                            if st.button("📌", key=f"u_{h['id']}"): h["pinned"] = False; st.rerun()
                        elif pinned_count < 5:
                            if st.button("📍", key=f"p_{h['id']}"): h["pinned"] = True; st.rerun()
            if st.button("🗑️"):
                st.session_state.history = [h for h in st.session_state.history if h.get("pinned")]
                st.rerun()

    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Smart Translator</p>', unsafe_allow_html=True)
    
    # PRO/Free バッジ表示 (常時)
    if is_pro:
        st.markdown('<div class="pro-badge">✨ PRO Plan Active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="free-badge">Free Plan</div>', unsafe_allow_html=True)

    # モード選択 (絵文字+英語)
    c1, c2, c3, c4 = st.columns(4)
    def set_s(s): st.session_state.style = s
    with c1: st.button("👕 Casual", on_click=set_s, args=('casual',), type="primary" if st.session_state.style=='casual' else "secondary", use_container_width=True)
    with c2: st.button("👔 Formal", on_click=set_s, args=('formal',), type="primary" if st.session_state.style=='formal' else "secondary", use_container_width=True)
    with c3: st.button("📱 SNS", on_click=set_s, args=('sns',), type="primary" if st.session_state.style=='sns' else "secondary", use_container_width=True, disabled=not is_pro)
    with c4: st.button("🎨 Prompt", on_click=set_s, args=('prompt',), type="primary" if st.session_state.style=='prompt' else "secondary", use_container_width=True, disabled=not is_pro)

    st.write("")
    
    # 出力言語選択
    if st.session_state.style not in ['sns', 'prompt']:
        opts = {"🇯🇵 Japanese": "ja", "🇫🇷 French": "fr"}
        if is_pro: opts["🇺🇸 English"] = "en"
        target_lang = st.selectbox("Output", options=list(opts.keys()), label_visibility="collapsed")
        sel_lang = opts[target_lang]
    else:
        sel_lang = None

    input_text = st.text_area("", value=st.session_state.input_text, height=160, placeholder="Input text (auto-detect)...", label_visibility="collapsed")

    # アクションボタン
    col_run, col_clear = st.columns([5, 1])
    with col_run:
        run_btn = st.button("✈️ Translate", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️", use_container_width=True):
            st.session_state.input_text = ""
            st.session_state.current_result = None
            st.rerun()

    if run_btn:
        if not input_text.strip(): return
        
        with st.spinner("⏳ Generating..."):
            STRICT = "OUTPUT ONLY THE RESULT. NO INTRO. NO LABELS. NO EXPLANATION."
            
            if st.session_state.style == "prompt":
                prompt = f"""{STRICT}
Create 3 short prompts (English) from the keyword. Add Japanese translation after each.

MJ: [prompt]
[日本語]

SD: [prompt]
[日本語]

SYS: [prompt]
[日本語]

Keyword: {input_text}"""
            elif st.session_state.style == "sns":
                prompt = f"""{STRICT}
Translate to JP/EN/FR for SNS. No imaginary content. Add emoji and hashtags.

🇯🇵 [text]
#tags

🇺🇸 [text]
#tags

🇫🇷 [text]
#tags

Input: {input_text}"""
            else:
                tone = "casual friendly" if st.session_state.style == 'casual' else "formal polite"
                lang_name = {"ja": "Japanese", "fr": "French", "en": "English"}[sel_lang]
                prompt = f"""{STRICT}
Translate to {lang_name} in {tone} tone. Give 2 variations with Japanese back-translation.
Do NOT use labels. Output directly.

[translation 1]
[日本語]

[translation 2]
[日本語]

Input: {input_text}"""
            
            res, err = call_api(model, prompt)
        
        if err:
            st.error(f"❌ {err}")
        else:
            st.session_state.current_result = res
            st.session_state.input_text = input_text
            add_history(input_text, res, is_pro)
            st.rerun()

    # 結果表示: 直接コードブロック（コピー可能）
    if st.session_state.current_result:
        st.divider()
        st.code(st.session_state.current_result, language="text")

if __name__ == "__main__":
    main()