import streamlit as st
import requests
import pandas as pd
from itertools import product
import pytz
from datetime import datetime, time, timedelta
import time as tm  # Untuk mendapatkan timestamp unik

st.set_page_config(page_title="add",)
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

# Fungsi untuk menambahkan data
def add_data(tanggal, dies, start_hour, finish_hour, total_pemakaian, total_jam_ganti_dies, keterangan, aksi, frekuensi_ganti_striper):
    start_hour_str = start_hour.strftime("%H:%M") if hasattr(start_hour, "strftime") else str(start_hour)
    finish_hour_str = finish_hour.strftime("%H:%M") if hasattr(finish_hour, "strftime") else str(finish_hour)
    total_pemakaian_str = total_pemakaian.strftime("%H:%M") if hasattr(total_pemakaian, "strftime") else str(total_pemakaian)
    total_jam_ganti_dies_str = total_jam_ganti_dies.strftime("%H:%M") if hasattr(total_jam_ganti_dies, "strftime") else str(total_jam_ganti_dies)

    response = requests.post(URL, json={
        "action": "add",
        "tanggal": tanggal,
        "dies": dies,
        "start_hour": start_hour_str,
        "finish_hour": finish_hour_str,
        "total_pemakaian": total_pemakaian_str,
        "total_jam_ganti_dies": total_jam_ganti_dies_str,
        "keterangan": keterangan,
        "aksi" : aksi,
        "frekuensi_ganti_striper": frekuensi_ganti_striper
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

# Form untuk menambahkan data
st.write("### Tambah Data")

# Cek dan set default di session_state jika belum ada
defaults = {
    "form_date": datetime.today().date(),
    "form_dies": df["dies"].unique()[0] if len(df["dies"].unique()) > 0 else "",
    "form_start_hour": datetime.now().time(),
    "form_finish_hour": datetime.now().time(),
    "form_total_ganti_dies": time(0, 0),
    "form_keterangan": "",
    "form_aksi": "",
    "form_frekuensi_ganti_striper": 0,
}

# Pastikan semua nilai default ada di session state tanpa overwrite jika sudah ada
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# Pastikan form_add_reset ada di session_state
st.session_state.setdefault("form_add_reset", False)

# Reset nilai form jika `form_add_reset` bernilai True
if st.session_state.form_add_reset:
    st.session_state.update(defaults)
    st.session_state.form_add_reset = False  # Kembalikan ke False setelah reset

# Form input
with st.form("add_form"):
    new_date = st.date_input("Tanggal", value=st.session_state.get("form_date"), key="form_date")
    formatted_date = new_date.strftime('%d-%b-%Y')

    new_dies_options = df["dies"].unique().tolist()  # Ambil daftar opsi dies

    # Pastikan nilai default ada dalam daftar, jika tidak, gunakan indeks 0
    if st.session_state.form_dies in new_dies_options:
        dies_index = new_dies_options.index(st.session_state.form_dies)
    else:
        dies_index = 0  # Gunakan indeks 0 jika nilai default tidak ditemukan

    new_dies = st.selectbox(
        "Pilih Dies",
        new_dies_options,
        index=dies_index,
        key="form_dies"
    )

    new_start_hour = st.time_input("Jam Mulai (HH:mm)", value=st.session_state.get("form_start_hour"), key="form_start_hour")
    new_finish_hour = st.time_input("Jam Selesai (HH:mm)", value=st.session_state.get("form_finish_hour"), key="form_finish_hour")

    start_datetime = datetime.combine(datetime.today(), new_start_hour)
    finish_datetime = datetime.combine(datetime.today(), new_finish_hour)

    if finish_datetime < start_datetime:
        finish_datetime += timedelta(days=1)
    new_total_pemakaian = finish_datetime - start_datetime
    base_time = datetime(1900, 1, 1)
    new_total_pemakaian_time = (base_time + new_total_pemakaian).time()

    new_total_ganti_dies = st.time_input("Total Jam Ganti Dies (HH:mm)", value=st.session_state.get("form_total_ganti_dies"), key="form_total_ganti_dies")
    new_keterangan = st.text_area("Keterangan", value=st.session_state.get("form_keterangan"), key="form_keterangan")
    new_aksi = st.text_input("Aksi", value=st.session_state.get("form_aksi"), key="form_aksi")
    new_frekuensi_ganti_striper = st.number_input(
        "Frekuensi Ganti Striper", 
        min_value=0, step=1, value=st.session_state.get("form_frekuensi_ganti_striper"), key="form_frekuensi_ganti_striper"
    )

    submitted = st.form_submit_button("Tambah")

    if submitted:
        # Pastikan data yang dikirim benar
        result = add_data(
            formatted_date,
            new_dies,
            new_start_hour,
            new_finish_hour,
            new_total_pemakaian_time,
            new_total_ganti_dies,
            new_keterangan,
            new_aksi,
            new_frekuensi_ganti_striper
        )

        if "Success" in result:
             # Tampilkan toast
            st.toast("Data berhasil ditambahkan!", icon="✅")

            # Tunggu sebentar agar toast terlihat
            tm.sleep(3)  # Gunakan modul time yang diimpor sebagai tmst.toast("Data berhasil ditambahkan!")

            # Set flag untuk reset form
            st.session_state.form_add_reset = True

            st.rerun()  # Refresh halaman agar form benar-benar kosong
