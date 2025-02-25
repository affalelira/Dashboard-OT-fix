import streamlit as st
import requests
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Monitoring", page_icon="🛒", layout="wide")

# URL dari Google Apps Script
URL = "https://script.google.com/macros/s/AKfycbyiA9vhzPRBwNmsVWKY9Q0r0LwB2C0JWyaoYpzPuEVuntQcT7VSc6-phjxQz8CVLzSPRA/exec"

# Fungsi untuk mengambil data dari Google Apps Script
@st.cache_data(ttl=300)
def fetch_data():
    response = requests.get(URL)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Data Admin
admins = {
    "admin": {"password": "admin123", "role": "admin"},
}

# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.page = "Overview"


def sidebar_navigation():
    with st.sidebar:
        st.title("Navigation")
        options = ["Overview", "Add Data"]
        
        # Hanya tampilkan Update & Delete jika sudah login
        if st.session_state.logged_in:
            options.extend(["Update Data", "Delete Data"])
        
        page = st.selectbox("Pilih Halaman:", options, index=0)

        if not st.session_state.logged_in:
            if st.button("Login"):
                st.switch_page("pages/login.py")
        else:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.page = "Overview"
                st.rerun()

        st.session_state.page = page


hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)


# Fungsi Halaman Overview
def overview():
    st.title("Dashboard Overview")
    data = fetch_data()
    df = pd.DataFrame(data) if data else pd.DataFrame(columns=[
        "tanggal", "dies", "start_hour", "finish_hour", "total_pemakaian",
        "total_jam_ganti_dies", "keterangan", "aksi", "frekuensi_ganti_striper"
    ])
    
    if st.button("Muat Ulang Data"):
        fetch_data.clear()
        st.rerun()
    
    st.write("### Data Pemakaian")
    st.dataframe(df)

# Fungsi Halaman Tambah Data
def add_data():
    st.title("Add Data")
    st.switch_page("pages/add.py")

# Fungsi Halaman Update Data
def update_data():
    st.title("Update Data")
    st.switch_page("pages/update.py")

# Fungsi Halaman Hapus Data
def delete_data():
    st.title("Delete Data")
    st.switch_page("pages/delete.py")

# Menampilkan sidebar
sidebar_navigation()

# Menampilkan halaman berdasarkan pilihan di sidebar
if st.session_state.page == "Overview":
    overview()
elif st.session_state.page == "Add Data":
    add_data()
elif st.session_state.page == "Update Data" and st.session_state.logged_in:
    update_data()
elif st.session_state.page == "Delete Data" and st.session_state.logged_in:
    delete_data()
