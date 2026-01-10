"""
Jifra 🗼 - AI Smart Translator (Production Edition)
=================================================
Tech: Streamlit + Google GenAI SDK (v1)
Features: Casual, Formal, SNS PRO, Auto-Discovery, High Contrast Dark Theme
"""

import streamlit as st
from google import genai
import re
import time
import random

# =============================================================================
# 1. 認証設定 (Streamlit Secrets / Environment Variables)
# =============================================================================
# Streamlit CloudのSecrets設定欄には以下のキー名で保存してください:
# gemini_api_key = "..."
# pro_password = "..."

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
# 3. カスタムデザインシステム (高級感のあるダークモード)
# =============================================================================
st.markdown("""
<style>
    /* 全体背景 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 700px;
    }

    /* テキストカラー */
    .stApp p, .stApp span, .stApp label, .stApp div {
        color: #f0f6fc !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* タイトルロゴ */
    .main-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #8b949e !important;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
    }

    /* セレクトボックス */
    .stSelectbox > div > div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #ffffff !important;
    }

    /* ボタン共通 */
    div.stButton > button {
        width: 100%;
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 3rem;
    }
    /* プライマリボタン (赤系グラデーション) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255, 107, 107, 0.4) !important;
    }
    /* セカンダリボタン (ダークグレー) */
    div.stButton > button[kind="secondary"] {
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #ff6b6b !important;
        color: white !important;
    }

    /* 入力エリア */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 2px solid #30363d !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        padding: 1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #ff6b6b !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.2) !important;
    }

    /* 結果ボックス */
    .result-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 5px solid #ff6b6b;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .result-header {
        color: #ff6b6b !important;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .result-text {
        color: #e6edf3 !important;
        font-size: 1.2rem;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    
    /* リトライ通知 (Toast風) */
    .status-toast {
        position: fixed; bottom: 2rem; right: 2rem;
        background-color: #161b22;
        border: 1px solid #ff6b6b;
        color: #ff6b6b;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        z-index: 9999;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. API制御ロジック (New SDK: google-genai)
# =============================================================================
@st.cache_resource
def get_client():
    # 接続を安定させるため api_version='v1' を明示
    return genai.Client(api_key=API_KEY, http_options={'api_version': 'v1'})

def call_gemini(prompt, status_box):
    client = get_client()
    # モデル選択 (1.5-flashが最も高速で安定)
    model_id = "gemini-1.5-flash"
    
    max_retries = 3
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            return response.text, None
        except Exception as e:
            err = str(e)
            if "429" in err or "ResourceExhausted" in err:
                if i < max_retries - 1:
                    wait = (2 ** i) + random.random()
                    status_box.markdown(f'<div class="status-toast">⏳ Traffic High. Retrying in {wait:.1f}s...</div>', unsafe_allow_html=True)
                    time.sleep(wait)
                    status_box.empty()
                    continue
            return None, err
    return None, "Connection Timeout"

# =============================================================================
# 5. 翻訳・SNS処理
# =============================================================================
def simple_detect(text):
    sample = text[:300]
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', sample): return 'ja'
    if re.search(r'[àâäéèêëïîôùûüçœæ]', sample): return 'fr'
    if len(re.findall(r'\b(the|is|and|of|to|in|it|that)\b', sample, re.I)) >= 2: return 'en'
    return 'ja'

def run_translation(text, mode, style, status_box):
    # 言語方向の判定
    if mode == "auto":
        det = simple_detect(text)
        src, tgt = ('日本語', 'フランス語') if det == 'ja' else (('フランス語', '日本語') if det == 'fr' else ('英語', '日本語'))
    else:
        dirs = {"ja_fr": ('日本語', 'フランス語'), "fr_ja": ('フランス語', '日本語'), "ja_en": ('日本語', '英語'), "en_ja": ('英語', '日本語'), "en_fr": ('英語', 'フランス語'), "fr_en": ('フランス語', '英語')}
        src, tgt = dirs.get(mode, ('日本語', 'フランス語'))

    if style == "sns":
        prompt = f"""
あなたがSNSマーケティングのプロです。以下のテキストを元に、日・英・仏の3言語でSNS投稿を作成してください。
【要件】
- 絵文字(Emojis)を各言語3つ以上使う
- ハッシュタグ(Hashtags)を各言語3つ以上つける
- 各言語、本文とハッシュタグの間に必ず「空行（改行）」を1行入れてください。
【入力】
{text}
【出力形式】
🇯🇵 日本語:
[本文]
(空行)
#タグ

🇺🇸 English:
...
"""
    else:
        tone = "親しみやすいカジュアル" if style == 'casual' else "ビジネス向けのフォーマル"
        prompt = f"""
あなたはプロの翻訳者です。{src}から{tgt}へ「{tone}」な口調で翻訳してください。
その後、翻訳結果から{src}への「戻し訳」も作成してください。
【入力】
{text}
【出力形式】
翻訳:
...
戻し訳:
...
"""
    return call_gemini(prompt, status_box)

# =============================================================================
# 6. メインUI
# =============================================================================
def main():
    if 'style' not in st.session_state: st.session_state.style = 'casual'

    # --- サイドバー ---
    with st.sidebar:
        st.header("⚙️ Settings")
        p_input = st.text_input("🔑 PRO Password", type="password", help="Enter JIFRA PRO Secret")
        is_pro = (p_input == PRO_PASSWORD)
        if is_pro: st.success("✨ PRO Activated")
        st.divider()
        st.caption(f"Powered by Gemini 1.5 Flash")

    # --- ヘッダー ---
    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Premium AI Smart Translator</p>', unsafe_allow_html=True)

    # --- スタイル選択 ---
    c1, c2, c3 = st.columns(3)
    def update_style(s): st.session_state.style = s
    with c1: st.button("💬 Casual", on_click=update_style, args=('casual',), type="primary" if st.session_state.style=='casual' else "secondary", use_container_width=True)
    with c2: st.button("👔 Formal", on_click=update_style, args=('formal',), type="primary" if st.session_state.style=='formal' else "secondary", use_container_width=True)
    with c3: st.button("📱 SNS [PRO]", on_click=update_style, args=('sns',), type="primary" if st.session_state.style=='sns' else "secondary", use_container_width=True, disabled=not is_pro)

    st.write("")

    # --- 言語選択 ---
    opts = {"auto": "🔄 自動検知 / Auto Detect", "ja_fr": "🇯🇵 日 ➡ 🇫🇷 仏", "fr_ja": "🇫🇷 仏 ➡ 🇯🇵 日"}
    if is_pro: opts.update({"ja_en": "🇯🇵 日 ➡ 🇺🇸 英", "en_ja": "🇺🇸 英 ➡ 🇯🇵 日", "en_fr": "🇺🇸 英 ➡ 🇫🇷 仏", "fr_en": "🇫🇷 仏 ➡ 🇺🇸 英"})
    
    sel_mode = st.selectbox("Direction", options=list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")

    # --- テキスト入力 ---
    input_text = st.text_area("Input", height=180, placeholder="翻訳したいテキストを入力してください...", label_visibility="collapsed")
    
    st_box = st.empty()

    # --- 実行ボタン ---
    if st.button("翻訳する / Translate", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("⚠️ テキストを入力してください。")
            return
        
        # PRO権限チェック (Autoモード時の英語判定)
        if not is_pro and sel_mode == "auto" and simple_detect(input_text) == 'en':
            st.error("🔒 英語の翻訳機能は PRO ユーザー限定です。")
            return

        with st.spinner("🚀 AI処理中..."):
            res, err = run_translation(input_text, sel_mode, st.session_state.style, st_box)
        
        st_box.empty()

        if err:
            st.error(f"❌ エラーが発生しました: {err}")
        else:
            if st.session_state.style == "sns":
                st.markdown(f'<div class="result-card"><div class="result-header">🌍 SNS Collection</div><div class="result-text">{res}</div></div>', unsafe_allow_html=True)
            else:
                # パース処理
                trans, back = "", ""
                parts = res.split("戻し訳:")
                trans = parts[0].replace("翻訳:", "").strip()
                if len(parts) > 1: back = parts[1].strip()
                
                if not trans: trans = res
                
                sc1, sc2 = st.columns(2)
                with sc1: st.markdown(f'<div class="result-card"><div class="result-header">📝 Translation</div><div class="result-text">{trans}</div></div>', unsafe_allow_html=True)
                with sc2: st.markdown(f'<div class="result-card"><div class="result-header">🔄 Back Translation</div><div class="result-text">{back}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()