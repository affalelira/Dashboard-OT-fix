import streamlit as st
import requests
import pandas as pd
from itertools import product
import pytz
from datetime import datetime, time, timedelta
import time as tm  # Untuk mendapatkan timestamp unik

st.set_page_config(page_title="delete",)

# Sembunyikan sidebar di halaman ini
hide_sidebar_style = """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Tombol kembali ke dashboard overview
if st.button("Back to Dashboard"):
    st.switch_page("mainpage.py") 


# URL dari Google Apps Script
URL = "https://script.google.com/macros/s/AKfycbyiA9vhzPRBwNmsVWKY9Q0r0LwB2C0JWyaoYpzPuEVuntQcT7VSc6-phjxQz8CVLzSPRA/exec"

# Fungsi untuk mengambil data dari Google Apps Script dengan caching
@st.cache_data(ttl=300)  # Cache data selama 5 menit (300 detik)
def fetch_data():
    response = requests.get(URL)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Fungsi untuk mengubah timedelta menjadi string "H:mm"
# Zona waktu Indonesia (Jakarta)
def timedelta_to_str(td):
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}:{minutes:02d}"
    return str(td)


# Fungsi untuk menghapus data
def delete_data(tanggal, start_hour):
    response = requests.post(URL, json={
        "action": "delete",
        "tanggal": tanggal,
        "start_hour": start_hour
    })
    return response.text

# Mengambil data
data = fetch_data()

# Konversi ke DataFrame
if data:
    df = pd.DataFrame(data)
else:
    df = pd.DataFrame(columns=["tanggal", "dies", "start_hour", "finish_hour", "total_pemakaian", "total_jam_ganti_dies", "keterangan", "aksi", "frekuensi_ganti_striper"])

# Membuat rentang waktu dari 00:00 hingga 23:59 dengan interval 5 menit
time_options = [f"{h:02}:{m:02}" for h, m in product(range(24), range(0, 60, 5))]

# Membuat Dashboard dengan Streamlit
st.title("Dashboard Monitoring")

# Tombol untuk refresh data
if st.button("Muat Ulang Data"):
    st.cache_data.clear()  # Hapus cache
    data = fetch_data()  # Ambil data baru
    df = pd.DataFrame(data)
    st.rerun()  # Reload aplikasi

# Menampilkan DataFrame
st.write("### Data Pemakaian")
st.dataframe(df)

# Form untuk menghapus data
st.write("### Hapus Data")

# Cek dan set default di session_state jika belum ada
defaults_delete = {
    "form_delete_date": "",  # Default kosong
}

for key, value in defaults_delete.items():
    st.session_state.setdefault(key, value)

# Pastikan form_delete_reset ada di session_state
st.session_state.setdefault("form_delete_reset", False)

# Reset nilai form jika `form_delete_reset` bernilai True
if st.session_state.form_delete_reset:
    st.session_state.update(defaults_delete)
    st.session_state.form_delete_reset = False  # Kembalikan ke False setelah reset

if not df.empty:
    df["tanggal"] = pd.to_datetime(df["tanggal"], errors='coerce')
    tanggal_list = [""] + df["tanggal"].dt.strftime("%d-%b-%Y").unique().tolist()
    
    delete_tanggal = st.selectbox(
        "Pilih Tanggal", 
        tanggal_list, 
        index=tanggal_list.index(st.session_state["form_delete_date"]) if st.session_state["form_delete_date"] in tanggal_list else 0, 
        key="form_delete_date"
    )
    
    if delete_tanggal:  # Hanya lanjutkan jika tanggal dipilih
        df_filtered = df[df["tanggal"].dt.strftime("%d-%b-%Y") == delete_tanggal]
        
        if not df_filtered.empty:
            delete_start_hour = st.selectbox("Pilih Jam Mulai", df_filtered["start_hour"].unique(), key="delete_start_hour")
            with st.form("delete_form"):
                delete_submitted = st.form_submit_button("Hapus")
                if delete_submitted:
                    result = delete_data(delete_tanggal, delete_start_hour)
                    if "Deleted" in result:
                        # Tampilkan toast
                        st.toast("Data berhasil dihapus!", icon="✅")

                        # Tunggu sebentar agar toast terlihat
                        tm.sleep(2)  

                        # Set flag untuk reset form
                        st.session_state.form_delete_reset = True

                        # Refresh halaman agar form benar-benar kosong
                        st.rerun()
                    else:
                        st.error(f"Terjadi kesalahan: {result}")
        else:
            st.warning("Tidak ada data untuk tanggal yang dipilih.")
    else:
        st.warning("Silakan pilih tanggal terlebih dahulu.")
else:
    st.warning("Data tidak tersedia.")