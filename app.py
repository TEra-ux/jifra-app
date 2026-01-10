import streamlit as st
import google.generativeai as genai

# デザイン設定（ログイン後に反映）
st.set_page_config(page_title="Jifra 🗼", page_icon="🗼", layout="centered")

# CSSでデザインをプロ仕様に
st.markdown("""
<style>
    .stApp { background-color: #0d1117 !important; color: #f0f6fc !important; }
    h1 { background: linear-gradient(90deg, #ff6b6b, #ff8e53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    div.stButton > button { width: 100%; background: linear-gradient(135deg, #ff6b6b, #ee5253) !important; color: white !important; border: none !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# APIキーとパスワードの読み込み
API_KEY = st.secrets["gemini_api_key"]
PRO_PASSWORD = st.secrets["pro_password"]

# ログイン機能
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("Jifra 🗼")
    pw = st.text_input("パスワードを入力", type="password")
    if st.button("ログイン"):
        if pw == PRO_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else: st.error("パスワードが違います")
    st.stop()

# メイン機能
st.title("Jifra 🗼 日英仏・SNS生成")
text = st.text_area("内容を入力してください", placeholder="例：今日はエッフェル塔に行きました！")

if st.button("生成する"):
    if text:
        with st.spinner("AIが考え中..."):
            try:
                # 最新の呼び出し方に修正
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"以下の内容を、自然な日本語、洗練された英語、おしゃれなフランス語、そしてSNS投稿文（ハッシュタグ付）にしてください：\n{text}"
                response = model.generate_content(prompt)
                st.markdown("### ✨ 生成結果")
                st.write(response.text)
            except Exception as e:
                st.error(f"エラー: {e}")
    else:
        st.warning("内容を入力してください")
