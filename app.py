import streamlit as st
import google.generativeai as genai

# セキュリティ設定
st.set_page_config(page_title="Jifra 🗼", layout="centered")

# Secretsから設定を読み込む
try:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    PRO_PASSWORD = st.secrets["pro_password"]
except:
    st.error("Secretsが設定されていません。")
    st.stop()

# パスワード認証
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Jifra 🗼")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == PRO_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    st.stop()

# メイン機能
st.title("Jifra 🗼 日英仏・SNS生成")
input_text = st.text_area("翻訳・投稿にしたい内容を入力してください", placeholder="例：今日はエッフェル塔に行きました！")

if st.button("生成する"):
    if input_text:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        以下の内容について、以下の3点を作成してください。
        1. 自然な日本語の文章
        2. 洗練された英語の文章
        3. おしゃれなフランス語の文章
        4. SNS（Instagram/X）向けのハッシュタグ付き投稿文
        
        内容：{input_text}
        """
        with st.spinner("作成中..."):
            response = model.generate_content(prompt)
            st.markdown(response.text)
    else:
        st.warning("内容を入力してください")
