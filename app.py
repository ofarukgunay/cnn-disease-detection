import streamlit as st
import os
import shutil
import random
from PIL import Image

# --- Uygulama Başlığı ve Konfigürasyon ---
st.set_page_config(page_title="Dataset Preparator", layout="wide")
st.title("🚀 Interactive Dataset Preparation Tool")
st.markdown("Bu araç, bir kaynak klasördeki görüntüleri `train` ve `validation` olarak fiziksel olarak ayırır ve yeni bir hedef klasöre kaydeder.")

# --- Klasör Yolları için Girdi Alanları ---
st.header("1. Klasör Yollarını Belirleyin")
col1, col2 = st.columns(2)
with col1:
    source_dir = st.text_input("Kaynak Veri Klasörü (Source)", "data/kvasir-dataset-v2")
with col2:
    dest_dir = st.text_input("Hedef Klasör (Destination)", "data/prepared_data")

# --- Yan Menü (Sidebar) Ayarları ---
st.sidebar.header("⚙️ Preparation Settings")
val_split = st.sidebar.slider("Validation Split Oranı (%)", 10, 50, 20, 5) / 100.0
seed = st.sidebar.number_input("Random Seed (Tekrarlanabilirlik için)", value=42)
st.sidebar.info("Ayarları değiştirdikten sonra aşağıdaki butona basarak işlemi başlatın.")

# --- Başlatma Butonu ---
st.header("2. Hazırlama İşlemini Başlatın")
if st.button("Veri Setini Hazırla", type="primary", use_container_width=True):
    
    # 1. Kontroller
    if not os.path.isdir(source_dir):
        st.error(f"HATA: Kaynak klasör bulunamadı! -> '{source_dir}'")
    else:
        st.info(f"Kaynak: '{source_dir}' | Hedef: '{dest_dir}' | Ayırma Oranı: {int(val_split*100)}%")
        
        progress_bar = st.progress(0, text="Hazırlık yapılıyor...")

        try:
            # 2. Eski hedef klasörü temizle ve yenisini oluştur
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            
            train_path = os.path.join(dest_dir, "train")
            val_path = os.path.join(dest_dir, "validation")
            os.makedirs(train_path, exist_ok=True)
            os.makedirs(val_path, exist_ok=True)
            progress_bar.progress(10, text=f"'{dest_dir}' klasörü oluşturuldu.")

            # 3. Sınıfları bul ve kopyalama işlemini yap
            class_names = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
            total_classes = len(class_names)
            total_files_copied = 0

            for i, class_name in enumerate(class_names):
                progress_text = f"Sınıf işleniyor: {class_name} ({i+1}/{total_classes})"
                progress_bar.progress(10 + int((i/total_classes)*80), text=progress_text)

                # Hedef klasörleri oluştur (train/polyps, validation/polyps vb.)
                os.makedirs(os.path.join(train_path, class_name), exist_ok=True)
                os.makedirs(os.path.join(val_path, class_name), exist_ok=True)

                # Görüntüleri listele ve karıştır
                source_class_path = os.path.join(source_dir, class_name)
                images = os.listdir(source_class_path)
                random.seed(seed)
                random.shuffle(images)

                # Ayırma noktasını hesapla
                split_point = int(len(images) * val_split)
                val_images = images[:split_point]
                train_images = images[split_point:]

                # Dosyaları kopyala
                for img in train_images:
                    shutil.copy(os.path.join(source_class_path, img), os.path.join(train_path, class_name, img))
                for img in val_images:
                    shutil.copy(os.path.join(source_class_path, img), os.path.join(val_path, class_name, img))
                
                total_files_copied += len(images)
            
            progress_bar.progress(100, text="İşlem başarıyla tamamlandı!")
            
            # 4. Sonuç Raporu
            st.header("✅ İşlem Tamamlandı!")
            st.success(f"Toplam {total_files_copied} görüntü {len(class_names)} sınıftan başarıyla ayrıldı.")
            
            st.subheader("Oluşturulan Klasör Yapısı:")
            st.code(f"""
{dest_dir}/
├── train/
│   ├── {class_names[0]}/
│   ├── {class_names[1]}/
│   └── ...
└── validation/
    ├── {class_names[0]}/
    ├── {class_names[1]}/
    └── ...
            """)

        except Exception as e:
            st.error(f"İşlem sırasında bir hata oluştu: {e}")