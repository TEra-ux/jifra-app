"""
Jifra 🗼 - AI Smart Translator & Prompt generator (Refactored Edition)
=====================================================================
Features: Translation, SNS mode, Prompt Generation (PRO)
Systems: Session-based History, Pinning, Security Hardened
"""

import streamlit as st
import google.generativeai as genai
import re
import time
import random
from datetime import datetime

# =============================================================================
# 1. セキュリティ設定 (Streamlit Secrets)
# =============================================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    PRO_PASSWORD = st.secrets["PRO_PASSWORD"]
except KeyError:
    try:
        # 互換性のためのフォールバック
        API_KEY = st.secrets["gemini_api_key"]
        PRO_PASSWORD = st.secrets["pro_password"]
    except KeyError:
        st.error("❌ Secretsに 'GEMINI_API_KEY' または 'PRO_PASSWORD' が設定されていません。")
        st.stop()

# =============================================================================
# 2. ページ基本設定 & Session State 初期化
# =============================================================================
st.set_page_config(
    page_title="Jifra 🗼",
    page_icon="🗼",
    layout="centered"
)

if 'history' not in st.session_state:
    st.session_state.history = []
if 'style' not in st.session_state:
    st.session_state.style = 'casual'

# =============================================================================
# 3. カスタムデザイン (CSS)
# =============================================================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
    }
    .main .block-container { padding-top: 2rem; max-width: 700px; }
    
    /* サイドバー */
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
    
    div.stButton > button { width: 100%; border-radius: 10px !important; font-weight: 600 !important; border: none !important; height: 3rem; transition: 0.2s; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important; color: white !important; }
    div.stButton > button[kind="secondary"] { background-color: #21262d !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    
    .stTextArea textarea { background-color: #0d1117 !important; border: 2px solid #30363d !important; border-radius: 12px !important; color: #ffffff !important; font-size: 1.1rem !important; }
    .stSelectbox > div > div { background-color: #161b22 !important; border: 1px solid #30363d !important; color: #ffffff !important; }

    /* 結果カード */
    .result-card { background-color: #161b22; border: 1px solid #30363d; border-left: 5px solid #ff6b6b; border-radius: 12px; padding: 1.2rem; margin-top: 1rem; }
    .result-header { color: #ff6b6b !important; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.4rem; text-transform: uppercase; }
    .result-text { color: #e6edf3 !important; font-size: 1.05rem; line-height: 1.5; white-space: pre-wrap; }
    .back-trans { color: #8b949e !important; font-size: 0.9rem; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid #30363d; }
    
    /* 履歴セクション */
    .history-item { 
        background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px; 
        padding: 0.8rem; margin-bottom: 0.5rem; font-size: 0.9rem;
    }
    .pinned { border-left: 4px solid #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. モデル & API制御
# =============================================================================
@st.cache_resource
def init_stable_model():
    try:
        genai.configure(api_key=API_KEY)
        priority = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        target = next((p for p in priority if p in available), available[0] if available else None)
        if not target: return None, "No models available"
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
    return None, "Timeout"

# =============================================================================
# 5. ヘルパー関数
# =============================================================================
def add_history(data, is_pro):
    # 履歴追加
    st.session_state.history.insert(0, {
        "id": time.time(),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "style": st.session_state.style,
        "input": data["input"],
        "result": data["result"],
        "pinned": False
    })
    
    # 制限適用
    if not is_pro:
        # Free: 最新1件のみ (ピン留め考慮なし)
        st.session_state.history = st.session_state.history[:1]
    else:
        # Pro: 最大20件。ピン留めされているものは保持。
        pinned = [item for item in st.session_state.history if item.get("pinned")]
        unpinned = [item for item in st.session_state.history if not item.get("pinned")]
        st.session_state.history = (pinned + unpinned)[:20]

def detect_lang(text):
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text): return 'ja'
    return 'en'

# =============================================================================
# 6. メインロジック
# =============================================================================
def main():
    model, model_name = init_stable_model()
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Settings")
        pwd = st.text_input("🔑 PRO Password", type="password")
        is_pro = (pwd == PRO_PASSWORD)
        if is_pro: st.success("✨ PRO Activated")
        
        st.divider()
        st.subheader("📜 翻訳履歴")
        if not st.session_state.history:
            st.caption("履歴はありません")
        else:
            pinned_count = sum(1 for item in st.session_state.history if item.get("pinned"))
            for i, item in enumerate(st.session_state.history):
                with st.expander(f"{item['timestamp']} | {item['input'][:15]}..."):
                    st.write(f"**Style:** {item['style']}")
                    st.write(item['result'])
                    if is_pro:
                        # ピン留め機能
                        val = st.checkbox("📌 ピン留め", value=item.get("pinned"), key=f"pin_{item['id']}")
                        if val != item.get("pinned"):
                            if val and pinned_count >= 5:
                                st.warning("ピン留めは5個までです")
                            else:
                                item["pinned"] = val
                                st.rerun()

    # --- Main UI ---
    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Smart AI Refined Translator</p>', unsafe_allow_html=True)

    # スタイル選択 (2行に分けるなどして対応)
    styles = ["Casual", "Formal", "SNS Casual", "🤖 プロンプト生成 (Pro)"]
    style_keys = ["casual", "formal", "sns", "prompt_gen"]
    
    cols = st.columns(4)
    for i, (name, key) in enumerate(zip(styles, style_keys)):
        with cols[i]:
            disabled = (key in ["sns", "prompt_gen"] and not is_pro)
            if st.button(name, key=f"btn_{key}", type="primary" if st.session_state.style == key else "secondary", disabled=disabled):
                st.session_state.style = key
                st.rerun()

    st.write("")
    
    # モード選択
    if st.session_state.style == "prompt_gen":
        st.info("🤖 入力したキーワードを画像生成AI向けの高度なプロンプトに変換します。")
        sel_mode = "prompt_gen"
    else:
        dirs = {"auto": "🔄 自動検知", "ja_fr": "🇯🇵 日 ➡ 🇫🇷 仏", "fr_ja": "🇫🇷 仏 ➡ 🇯🇵 日"}
        if is_pro:
            dirs.update({"ja_en": "🇯🇵 日 ➡ 🇺🇸 英", "en_ja": "🇺🇸 英 ➡ 🇯🇵 日"})
        sel_mode = st.selectbox("Direction", options=list(dirs.keys()), format_func=lambda x: dirs[x], label_visibility="collapsed")

    input_text = st.text_area("Input", height=150, placeholder="テキストを入力してください...", label_visibility="collapsed")
    
    if st.button("変換・翻訳する", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("テキストを入力してください")
            return
            
        with st.spinner("Processing..."):
            if st.session_state.style == "prompt_gen":
                prompt = f"""
以下のキーワードを元に、3種類の高品質なAIプロンプト（英語）を作成してください。
説明は不要です。
【入力】: {input_text}
【出力形式】
Midjourney風: /imagine prompt: [詳細な描写, スタイル, ライティング]
Stable Diffusion風: (masterpiece, best quality, ultra-detailed), [タグ形式の描写], [アーティスト名], --n [ネガティブ]
System Prompt風: You are a helpful assistant specialized in [分野]. Your task is to [詳細な役割]...
"""
            elif st.session_state.style == "sns":
                prompt = f"""SNS投稿(日・英・仏)を作成。絵文字・タグ付。空行必須。入力: {input_text}"""
            else:
                tone = "カジュアル" if st.session_state.style == "casual" else "フォーマル"
                prompt = f"""プロの翻訳者として、{sel_mode}に基づき{tone}な翻訳パターンを2つ、それぞれの戻し訳と共に提示してください。余計な説明は不要。形式:
パターン1: [翻訳]
戻し訳1: [訳]
パターン2: [翻訳]
戻し訳2: [訳]
入力: {input_text}"""
            
            res, err = call_api(model, prompt)
            if err:
                st.error(f"Error: {err}")
            else:
                add_history({"input": input_text, "result": res}, is_pro)
                st.rerun()

    # --- Results Display ---
    if st.session_state.history:
        latest = st.session_state.history[0]
        st.divider()
        st.subheader("✨ Latest Result")
        
        if latest["style"] == "prompt_gen":
            st.markdown(f'<div class="result-card"><div class="result-header">🤖 Generated Prompts</div><div class="result-text">{latest["result"]}</div></div>', unsafe_allow_html=True)
        elif latest["style"] == "sns":
            st.markdown(f'<div class="result-card"><div class="result-header">🌍 SNS Collection</div><div class="result-text">{latest["result"]}</div></div>', unsafe_allow_html=True)
        else:
            # 翻訳パターンの表示
            res_text = latest["result"]
            lines = res_text.split('\n')
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

            ca, cb = st.columns(2)
            with ca:
                st.markdown(f'<div class="result-card"><div class="result-header">💡 Pattern 1</div><div class="result-text">{p1_t if p1_t else res_text}</div><div class="back-trans">🔄 {p1_b}</div></div>', unsafe_allow_html=True)
            with cb:
                if p2_t:
                    st.markdown(f'<div class="result-card"><div class="result-header">💡 Pattern 2</div><div class="result-text">{p2_t}</div><div class="back-trans">🔄 {p2_b}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()