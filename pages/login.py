import streamlit as st

# Sembunyikan sidebar di halaman ini
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Data Admin
admins = {
    "admin": {"password": "admin123", "role": "admin"},
}

# Inisialisasi session state jika belum ada
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

st.title("Login")

# Form Login
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_submit = st.form_submit_button("Log in")

    if login_submit:
        if username in admins and admins[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = admins[username]["role"]
            st.success("Login berhasil! Mengalihkan...")
            st.switch_page("mainpage.py")  # Kembali ke halaman utama
        else:
            st.error("Username atau password salah!")
