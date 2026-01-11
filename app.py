"""
Jifra 🗼 - AI Smart Translator (Enhanced Edition v11)
=====================================================
Features: Translation, SNS, Visual Prompt Generation (3-tier), History, Pin
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
if 'prompt_level' not in st.session_state: st.session_state.prompt_level = 1
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
        opacity: 0.4 !important; 
        cursor: not-allowed !important; 
        border-color: #484f58 !important;
        color: #6e7681 !important;
        background-color: #21262d !important;
    }
    
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
    
    .stSelectbox > div > div { background-color: #161b22 !important; border: 1px solid #30363d !important; color: #ffffff !important; }
    
    .stCode { 
        border-radius: 10px !important; 
        border: 1px solid #30363d !important; 
        margin-bottom: 0.3rem !important;
        max-height: none !important;
    }
    .stCode pre { 
        background-color: #161b22 !important; 
        max-height: none !important;
        white-space: pre-wrap !important;
    }
    .stCode code { 
        background-color: #161b22 !important; 
        color: #e6edf3 !important; 
        font-size: 1rem !important;
        white-space: pre-wrap !important;
    }
    
    .lang-flag {
        display: inline-block;
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
        color: white !important;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .back-trans { color: #8b949e !important; font-size: 0.9rem; margin-bottom: 1rem; padding-left: 0.5rem; }
    
    /* 履歴アイテム */
    .history-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.4rem;
    }
    .history-text {
        flex: 1;
        padding: 0.4rem 0.6rem;
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #8b949e;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .history-pinned { border-left: 3px solid #f1c40f !important; }
    .pin-icon {
        font-size: 1.2rem;
        cursor: pointer;
        user-select: none;
    }
    
    .stCode button {
        background-color: #ff6b6b !important;
        color: white !important;
    }
    
    .star-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #ffffff !important;
        text-align: center;
        margin-top: 0.3rem;
    }
    .star-desc {
        font-size: 0.7rem;
        color: #8b949e !important;
        text-align: center;
        line-height: 1.3;
        margin-top: 0.2rem;
    }
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
def add_history(result, is_pro):
    lines = result.strip().split('\n')
    summary = ""
    for line in lines:
        line = line.strip()
        if line and not line.startswith('(') and not line.endswith(':') and len(line) > 5:
            summary = line[:35]
            break
    if not summary:
        summary = result[:35]
    
    st.session_state.history.insert(0, {"id": time.time(), "text": summary, "result": result, "pinned": False})
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
        st.subheader("📜 History")
        if not st.session_state.history:
            st.caption("Empty")
        else:
            pinned_count = sum(1 for h in st.session_state.history if h.get("pinned"))
            for h in st.session_state.history:
                is_pinned = h.get("pinned", False)
                css = "history-text history-pinned" if is_pinned else "history-text"
                
                # アイコンでピン表示
                if is_pro:
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.markdown(f'<div class="{css}">{h["text"]}...</div>', unsafe_allow_html=True)
                    with col2:
                        if is_pinned:
                            if st.button("📌", key=f"u_{h['id']}", help="Unpin"):
                                h["pinned"] = False
                                st.rerun()
                        elif pinned_count < 5:
                            if st.button("☆", key=f"p_{h['id']}", help="Pin"):
                                h["pinned"] = True
                                st.rerun()
                else:
                    st.markdown(f'<div class="{css}">{h["text"]}...</div>', unsafe_allow_html=True)
            
            if st.button("🗑️ Clear"):
                st.session_state.history = [h for h in st.session_state.history if h.get("pinned")]
                st.rerun()

    st.markdown('<h1 class="main-title">Jifra 🗼</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Smart Translator</p>', unsafe_allow_html=True)
    
    if is_pro:
        st.markdown('<div class="pro-badge">✨ PRO Plan Active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="free-badge">Free Plan</div>', unsafe_allow_html=True)

    # モード選択
    c1, c2, c3, c4 = st.columns(4)
    def set_s(s): st.session_state.style = s
    with c1: st.button("👕 Casual", on_click=set_s, args=('casual',), type="primary" if st.session_state.style=='casual' else "secondary", use_container_width=True)
    with c2: st.button("👔 Formal", on_click=set_s, args=('formal',), type="primary" if st.session_state.style=='formal' else "secondary", use_container_width=True)
    with c3: st.button("📱 SNS", on_click=set_s, args=('sns',), type="primary" if st.session_state.style=='sns' else "secondary", use_container_width=True, disabled=not is_pro)
    with c4: st.button("🎨 Prompt", on_click=set_s, args=('prompt',), type="primary" if st.session_state.style=='prompt' else "secondary", use_container_width=True)

    st.write("")
    
    # 画像生成プロンプトモード: 3段階システム
    if st.session_state.style == 'prompt':
        st.caption("🎨 Visual Prompt")
        
        p1, p2, p3 = st.columns(3)
        
        def set_level(lv): st.session_state.prompt_level = lv
        
        with p1:
            st.button("★", on_click=set_level, args=(1,), type="primary" if st.session_state.prompt_level==1 else "secondary", use_container_width=True)
            st.markdown('<p class="star-label">Literal</p>', unsafe_allow_html=True)
            st.markdown('<p class="star-desc">言葉を忠実に<br>Simple English</p>', unsafe_allow_html=True)
        with p2:
            st.button("★★", on_click=set_level, args=(2,), type="primary" if st.session_state.prompt_level==2 else "secondary", use_container_width=True, disabled=not is_pro)
            st.markdown('<p class="star-label">Creative</p>', unsafe_allow_html=True)
            st.markdown('<p class="star-desc">表現を豊かに<br>Rich Narrative</p>', unsafe_allow_html=True)
        with p3:
            st.button("★★★", on_click=set_level, args=(3,), type="primary" if st.session_state.prompt_level==3 else "secondary", use_container_width=True, disabled=not is_pro)
            st.markdown('<p class="star-label">Masterpiece</p>', unsafe_allow_html=True)
            st.markdown('<p class="star-desc">写実を極める<br>Tech Specs</p>', unsafe_allow_html=True)

    # 入力欄
    input_text = st.text_area("", value=st.session_state.input_text, height=160, placeholder="Input text...", label_visibility="collapsed")
    
    # 言語選択（翻訳モード時のみ）- ラジオボタン
    if st.session_state.style not in ['sns', 'prompt']:
        opts = ["ja", "fr"]
        if is_pro: opts.append("en")
        
        format_map = {"ja": "➡JP", "fr": "➡FR", "en": "➡EN"}
        
        # デフォルト設定
        if 'sel_lang' not in st.session_state: st.session_state.sel_lang = 'fr'
        if st.session_state.sel_lang not in opts: st.session_state.sel_lang = opts[0]
            
        sel_lang = st.radio(
            "Output", 
            options=opts, 
            format_func=lambda x: format_map[x], 
            horizontal=True, 
            label_visibility="collapsed",
            index=opts.index(st.session_state.sel_lang)
        )
        st.session_state.sel_lang = sel_lang
    else:
        sel_lang = None

    col_run, col_clear = st.columns([5, 1])
    with col_run:
        # 条件分岐: 翻訳系はTranslate、SNS/★★以上はMetamorph
        if st.session_state.style in ['casual', 'formal']:
            btn_label = "✈️ Translate"
        elif st.session_state.style == 'prompt' and st.session_state.prompt_level == 1:
            btn_label = "✈️ Translate"
        else:
            btn_label = "🦋 Metamorph"
        run_btn = st.button(btn_label, type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️", use_container_width=True):
            st.session_state.input_text = ""
            st.session_state.current_result = None
            st.rerun()

    if run_btn and input_text.strip():
        with st.spinner("⏳ Generating..."):
            STRICT = "OUTPUT ONLY THE RESULT. NO INTRO. NO CHAT. NO EXPLANATION. SEPARATE EACH OUTPUT WITH A BLANK LINE."
            
            if st.session_state.style == "prompt":
                level = st.session_state.prompt_level
                
                if level == 1:
                    # ★ Literal: 画像生成視点の忠実な翻訳
                    prompt = f"""{STRICT}
Convert this to a simple English image generation prompt.
Keep the original meaning but phrase it for visual AI (describe what to see, not actions).
Output the English prompt first, then the Japanese back-translation in parentheses on a NEW LINE.

{input_text}"""
                elif level == 2:
                    # ★★ Creative: 豊かな表現（短め）
                    prompt = f"""{STRICT}
Create a concise image prompt with atmosphere and mood. Keep it under 30 words.
Output English first, then Japanese translation in parentheses on a NEW LINE.

{input_text}"""
                else:
                    # ★★★ Masterpiece: プロ仕様タグ
                    prompt = f"""{STRICT}
Create a professional-level image generation prompt with:
- Camera settings (lens, aperture, etc.)
- Lighting (natural, studio, golden hour, etc.)
- Art style (photorealistic, anime, oil painting, etc.)
Use comma-separated format.
Output the English prompt first, then the Japanese back-translation in parentheses on a NEW LINE.

{input_text}"""
                    
            elif st.session_state.style == "sns":
                prompt = f"""{STRICT}
Translate to JP/EN/FR for SNS. No imaginary content. Add emoji and hashtags.
Use [JP] [EN] [FR] as labels.

[JP] [text]
#tags

[EN] [text]
#tags

[FR] [text]
#tags

Input: {input_text}"""
            else:
                tone = "casual friendly" if st.session_state.style == 'casual' else "formal polite"
                lang_name = {"ja": "Japanese", "fr": "French", "en": "English"}[sel_lang]
                prompt = f"""{STRICT}
Translate to {lang_name} in {tone} tone. 
Give 2 variations. Each variation should be on its own line.
After each variation, add the Japanese back-translation in parentheses on a NEW LINE.
Do NOT combine them on the same line.

Input: {input_text}"""
            
            res, err = call_api(model, prompt)
        
        if err:
            st.error(f"❌ {err}")
        else:
            st.session_state.current_result = {"raw": res, "style": st.session_state.style}
            st.session_state.input_text = input_text
            add_history(res, is_pro)
            st.rerun()

    # 結果表示
    if st.session_state.current_result:
        st.divider()
        res_data = st.session_state.current_result
        raw = res_data["raw"]
        
        lines = raw.strip().split('\n')
        blocks = []
        current_block = {"text": "", "back": "", "label": ""}
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # SNSラベル
            if line.startswith('[JP]') or line.startswith('[EN]') or line.startswith('[FR]'):
                if current_block["text"]:
                    blocks.append(current_block)
                    current_block = {"text": "", "back": "", "label": ""}
                label = line[:4]
                current_block["label"] = {"[JP]": "JP", "[EN]": "EN", "[FR]": "FR"}.get(label, label)
                current_block["text"] = line[4:].strip()
                continue
            
            # 戻し訳（括弧で始まり括弧で終わる）
            if line.startswith('(') and line.endswith(')'):
                current_block["back"] = line
                if current_block["text"]:
                    blocks.append(current_block)
                    current_block = {"text": "", "back": "", "label": ""}
            # ラベル行をスキップ
            elif line.startswith('[') and line.endswith(']'):
                if current_block["text"]:
                    blocks.append(current_block)
                current_block = {"text": "", "back": "", "label": ""}
            else:
                # 通常テキスト
                if current_block["text"]:
                    # 同じブロックに追加しない、新しいブロックとして追加
                    if current_block["back"]:
                        # 既に戻し訳がある場合は新しいブロック
                        blocks.append(current_block)
                        current_block = {"text": line, "back": "", "label": ""}
                    else:
                        # まだ戻し訳がない場合は改行で追加
                        current_block["text"] += "\n" + line
                else:
                    current_block["text"] = line
        
        if current_block["text"]:
            blocks.append(current_block)
        
        if blocks:
            for b in blocks:
                if b["label"]:
                    st.markdown(f'<span class="lang-flag">{b["label"]}</span>', unsafe_allow_html=True)
                if b["text"]:
                    st.code(b["text"], language="text")
                    if b["back"]:
                        st.markdown(f'<p class="back-trans">{b["back"]}</p>', unsafe_allow_html=True)
        else:
            st.code(raw, language="text")

if __name__ == "__main__":
    main()