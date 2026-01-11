"""
Jifra 🗼 - AI Smart Translator (Original Stable Edition)
========================================================
Tech: Streamlit + Google GenerativeAI (Legacy SDK)
Features: Translation Only (No Prompt Generation Mode)
"""

import streamlit as st
import google.generativeai as genai
import re
import time
import random

# =============================================================================
# 1. 認証設定 (Streamlit Secrets)
# =============================================================================
try:
    API_KEY = st.secrets["gemini_api_key"]
    PRO_PASSWORD = st.secrets["pro_password"]
except KeyError:
    st.error("❌ Streamlit Secrets 'gemini_api_key' or 'pro_password' not found.")
    st.stop()

# =============================================================================
# 2. ページ基本設定
# =============================================================================
st.set_page_config(
    page_title="Jifra 🗼",
    page_icon="🗼",
    layout="centered"
)

# =============================================================================
# 3. カスタムデザイン (黒背景・高級感)
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
    .subtitle { text-align: center; color: #8b949e !important; font-size: 1.1rem; margin-bottom: 2.5rem; }
    .stSelectbox > div > div { background-color: #161b22 !important; border: 1px solid #30363d !important; color: #ffffff !important; }
    div.stButton > button { width: 100%; border-radius: 10px !important; font-weight: 600 !important; border: none !important; height: 3rem; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #21262d !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    .stTextArea textarea { background-color: #0d1117 !important; border: 2px solid #30363d !important; border-radius: 12px !important; color: #ffffff !important; font-size: 1.1rem !important; }
    
    .result-card { background-color: #161b22; border: 1px solid #30363d; border-left: 5px solid #ff6b6b; border-radius: 12px; padding: 1.2rem; margin-top: 1rem; }
    .result-header { color: #ff6b6b !important; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.4rem; text-transform: uppercase; }
    .result-text { color: #e6edf3 !important; font-size: 1.05rem; line-height: 1.5; white-space: pre-wrap; }
    .pattern-label { color: #8b949e !important; font-size: 0.8rem; margin-top: 0.8rem; border-top: 1px solid #30363d; padding-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. モデル初期化
# =============================================================================
@st.cache_resource
def init_stable_model():
    try:
        genai.configure(api_key=API_KEY)
        
        available = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available.append(m.name)
        except:
            pass

        priority = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        target = None
        for p in priority:
            if p in available:
                target = p
                break
        if not target:
            target = available[0] if available else "models/gemini-1.5-flash"
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
            err = str(e)
            if "429" in err or "ResourceExhausted" in err:
                if i < max_retries - 1:
                    time.sleep((2 ** i) + random.random())
                    continue
            return None, err
    return None, "Error"

def simple_detect(text):
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text): return 'ja'
    if re.search(r'[àâäéèêëïîôùûüçœæ]', text): return 'fr'
    return 'en'

# =============================================================================
# 5. メインUI
# =============================================================================
def main():
    if 'style' not in st.session_state: st.session_state.style = 'casual'
    
    model, model_name = init_stable_model()

    with st.sidebar:
        st.header("⚙️ Settings")
        p_input = st.text_input("🔑 PRO Password", type="password")
        is_pro = (p_input == PRO_PASSWORD)
        if is_pro: st.success("✨ PRO Activated")
        st.divider()
        st.caption(f"Connected: {model_name}")

    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Premium AI Smart Translator</p>', unsafe_allow_html=True)

    # スタイル選択ボタン (3つのみ: Casual, Formal, SNS)
    c1, c2, c3 = st.columns(3)
    def set_s(s): st.session_state.style = s
    with c1: st.button("💬 Casual", on_click=set_s, args=('casual',), type="primary" if st.session_state.style=='casual' else "secondary", use_container_width=True)
    with c2: st.button("👔 Formal", on_click=set_s, args=('formal',), type="primary" if st.session_state.style=='formal' else "secondary", use_container_width=True)
    with c3: st.button("📱 SNS [PRO]", on_click=set_s, args=('sns',), type="primary" if st.session_state.style=='sns' else "secondary", use_container_width=True, disabled=not is_pro)

    st.write("")
    
    # 言語選択
    opts = {"auto": "🔄 自動検知 / Auto Detect", "ja_fr": "🇯🇵 日 ➡ 🇫🇷 仏", "fr_ja": "🇫🇷 仏 ➡ 🇯🇵 日"}
    if is_pro: opts.update({"ja_en": "🇯🇵 日 ➡ 🇺🇸 英", "en_ja": "🇺🇸 英 ➡ 🇯🇵 日"})
    sel_mode = st.selectbox("Dir", options=list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    
    input_text = st.text_area("Input", height=180, placeholder="テキストを入力...", label_visibility="collapsed")

    if st.button("翻訳する / Translate", type="primary", use_container_width=True):
        if not input_text.strip(): return
        if not is_pro and sel_mode == "auto" and simple_detect(input_text) == 'en':
            st.error("🔒 PRO機能です。")
            return

        with st.spinner("AI処理中..."):
            if st.session_state.style == "sns":
                prompt = f"""以下のテキストを元に、日・英・仏の3言語でSNS投稿を作成してください。
- 各言語に絵文字とハッシュタグを入れる
- 本文とハッシュタグの間に空行を入れる
- 説明は不要

🇯🇵 日本語:
[本文]

#タグ

🇺🇸 English:
[Body]

#Hashtags

🇫🇷 Français:
[Corps]

#Hashtags

入力: {input_text}"""
            else:
                tone = "カジュアル" if st.session_state.style == 'casual' else "フォーマル"
                prompt = f"""プロの翻訳者として、{tone}なトーンで翻訳してください。
- 2つのパターンを提示
- 各パターンに戻し訳を添える
- 説明は不要

パターン1: [翻訳]
戻し訳1: [日本語]

パターン2: [翻訳]
戻し訳2: [日本語]

入力: {input_text}"""
            
            res, err = call_api(model, prompt)
        
        if err: st.error(f"❌ {err}")
        else:
            if st.session_state.style == "sns":
                st.markdown(f'<div class="result-card"><div class="result-header">🌍 SNS Collection</div><div class="result-text">{res}</div></div>', unsafe_allow_html=True)
            else:
                lines = res.strip().split('\n')
                p1_t, p1_b, p2_t, p2_b = "", "", "", ""
                curr = None
                for line in lines:
                    if "パターン1" in line: curr = "p1_t"; p1_t = line.split(":", 1)[-1].strip()
                    elif "戻し訳1" in line: curr = "p1_b"; p1_b = line.split(":", 1)[-1].strip()
                    elif "パターン2" in line: curr = "p2_t"; p2_t = line.split(":", 1)[-1].strip()
                    elif "戻し訳2" in line: curr = "p2_b"; p2_b = line.split(":", 1)[-1].strip()
                    elif curr == "p1_t" and line.strip(): p1_t += "\n" + line
                    elif curr == "p1_b" and line.strip(): p1_b += "\n" + line
                    elif curr == "p2_t" and line.strip(): p2_t += "\n" + line
                    elif curr == "p2_b" and line.strip(): p2_b += "\n" + line

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f'<div class="result-card"><div class="result-header">💡 Pattern 1</div><div class="result-text">{p1_t if p1_t else res}</div><div class="pattern-label">🔄 Back Translation</div><div class="result-text" style="font-size:0.9rem; color:#8b949e !important;">{p1_b}</div></div>', unsafe_allow_html=True)
                with col_b:
                    if p2_t:
                        st.markdown(f'<div class="result-card"><div class="result-header">💡 Pattern 2</div><div class="result-text">{p2_t}</div><div class="pattern-label">🔄 Back Translation</div><div class="result-text" style="font-size:0.9rem; color:#8b949e !important;">{p2_b}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()