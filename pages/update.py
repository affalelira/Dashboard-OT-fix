import streamlit as st
import requests
import pandas as pd
from itertools import product
import pytz
from datetime import datetime, time, timedelta
import time as tm  # Untuk mendapatkan timestamp unik

st.set_page_config(page_title="update",)

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

# Fungsi untuk mengupdate data
def update_data(tanggal, start_hour, dies, finish_hour, total_pemakaian, total_jam_ganti_dies, keterangan, aksi, frekuensi_ganti_striper):
    update_start_hour_str = start_hour.strftime("%H:%M") if hasattr(start_hour, "strftime") else str(start_hour)
    update_finish_hour_str =finish_hour.strftime("%H:%M") if hasattr(finish_hour, "strftime") else str(finish_hour)
    update_total_pemakaian_str = total_pemakaian.strftime("%H:%M") if hasattr(total_pemakaian, "strftime") else str(total_pemakaian)
    update_total_jam_ganti_dies_str = total_jam_ganti_dies.strftime("%H:%M") if hasattr(total_jam_ganti_dies, "strftime") else str(total_jam_ganti_dies)
    
    response = requests.post(URL, json={
        "action": "update",
        "tanggal": tanggal,
        "start_hour": update_start_hour_str,
        "dies": dies,
        "finish_hour": update_finish_hour_str,
        "total_pemakaian": update_total_pemakaian_str,
        "total_jam_ganti_dies": update_total_jam_ganti_dies_str,
        "keterangan": keterangan,
        "aksi": aksi,
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

# Form untuk mengupdate data
st.write("### Update Data")

# Cek dan set default di session_state jika belum ada
defaults_update = {
    "form_update_date": "",  # Format yang sesuai dengan tampilan
}

for key, value in defaults_update.items():
    st.session_state.setdefault(key, value)

# Pastikan form_update_reset ada di session_state
st.session_state.setdefault("form_update_reset", False)

# Ambil nilai yang sudah tersimpan
selected_date_str = st.session_state["form_update_date"]

# Reset nilai form jika `form_update_reset` bernilai True
if st.session_state.form_update_reset:
    st.session_state.update(defaults_update)
    st.session_state.form_update_reset = False  # Kembalikan ke False setelah reset
    
if not df.empty:
    df["tanggal"] = pd.to_datetime(df["tanggal"], errors='coerce')
    tanggal_list = [""] + df["tanggal"].dt.strftime("%d-%b-%Y").unique().tolist()
    
    update_tanggal = st.selectbox(
        "Pilih Tanggal", 
        tanggal_list, 
        index=tanggal_list.index(selected_date_str) if selected_date_str in tanggal_list else "", 
        key="form_update_date"
    )
    
    df_filtered = df[df["tanggal"].dt.strftime("%d-%b-%Y") == update_tanggal]
    
    if not df_filtered.empty:
        update_start_hour_str = st.selectbox("Pilih Jam Mulai", df_filtered["start_hour"].unique())
        selected_row = df_filtered[df_filtered["start_hour"] == update_start_hour_str].iloc[0]
        
        with st.form("update_form"):
            update_dies = st.selectbox("Pilih Dies", df["dies"].unique(), 
                                       index=list(df_filtered["dies"].unique()).index(selected_row["dies"]))

            # UNTUK FINISH HOUR
            finish_hour_str = selected_row["finish_hour"]
            try:
                if "T" in finish_hour_str:
                    finish_hour_time = datetime.fromisoformat(finish_hour_str.replace("Z", "")).time()
                else:
                    finish_hour_time = datetime.strptime(finish_hour_str, "%H:%M").time()
            except ValueError:
                finish_hour_time = datetime.strptime("00:00", "%H:%M").time()

            update_finish_hour = st.time_input("Jam Selesai (HH:mm)", value=finish_hour_time)

            # UNTUK START HOUR
            try:
                if "T" in update_start_hour_str:
                    update_start_hour = datetime.fromisoformat(update_start_hour_str.replace("Z", "")).time()
                else:
                    update_start_hour = datetime.strptime(update_start_hour_str, "%H:%M").time()
            except ValueError:
                update_start_hour = datetime.strptime("00:00", "%H:%M").time()

            start_datetime = datetime.combine(datetime.today(), update_start_hour)
            finish_datetime = datetime.combine(datetime.today(), update_finish_hour)

            if finish_datetime < start_datetime:
                finish_datetime += timedelta(days=1)
                
            new_total_pemakaian = finish_datetime - start_datetime
            base_time = datetime(1900, 1, 1)
            new_total_pemakaian_time = (base_time + new_total_pemakaian).time()

            # UNTUK TOTAL GANTI DIES
            total_ganti_dies_str = selected_row["total_jam_ganti_dies"]
            try:
                if "T" in total_ganti_dies_str:
                    total_ganti_dies_time = datetime.fromisoformat(total_ganti_dies_str.replace("Z", "")).time()
                else:
                    total_ganti_dies_time = datetime.strptime(total_ganti_dies_str, "%H:%M").time()
            except ValueError:
                total_ganti_dies_time = datetime.strptime("00:00", "%H:%M").time()

            update_total_ganti_dies = st.time_input("Total Jam Ganti Dies (HH:mm)", value=total_ganti_dies_time)

            update_keterangan = st.text_area("Keterangan", value=selected_row["keterangan"])
            update_aksi = st.text_input("Aksi", value=selected_row["aksi"])
            update_frekuensi_ganti_striper = st.number_input("Frekuensi Ganti Striper", min_value=0, step=1, 
                                                             value=int(selected_row["frekuensi_ganti_striper"]))
            
            update_submitted = st.form_submit_button("Update")
            
            if update_submitted:
                result = update_data(update_tanggal, update_start_hour_str, update_dies, 
                                     update_finish_hour, new_total_pemakaian_time, 
                                     update_total_ganti_dies, update_keterangan, 
                                     update_aksi, update_frekuensi_ganti_striper)
                
                if "Updated" in result:
                     # Tampilkan toast
                    st.toast("Data berhasil diperbarui!", icon="✅")

                    # Tunggu sebentar agar toast terlihat
                    tm.sleep(3)  # Gunakan modul time yang diimpor sebagai tmst.toast("Data berhasil ditambahkan!")

                    st.session_state.form_update_reset = True
                    st.rerun()
                else:
                    st.error(f"Terjadi kesalahan: {result}")
    else:
        st.warning("Tidak ada data untuk tanggal yang dipilih.")
else:
    st.warning("Data tidak tersedia.")
