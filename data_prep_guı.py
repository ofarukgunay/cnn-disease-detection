import os
import shutil
import threading
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from sklearn.model_selection import train_test_split

# =======================
# DİZİN YAPISI AYARLARI
# =======================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))          # proje ana dizini
DATA_DIR = os.path.join(ROOT_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "kvasir-dataset-v2")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared-data")

# Ana pencere
root = Tk()
root.title("Gastroenterology Dataset Preparation Tool")
root.geometry("520x520")
root.resizable(False, False)

# --- Fonksiyonlar ---
def select_folder():
    folder = filedialog.askdirectory(initialdir=DATA_DIR)
    dataset_path.set(folder)

def start_preprocessing_thread():
    thread = threading.Thread(target=start_preprocessing)
    thread.start()

def start_preprocessing():
    folder = dataset_path.get()
    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Please select a valid dataset folder.")
        return

    try:
        train_ratio = int(train_var.get()) / 100
        val_ratio = int(val_var.get()) / 100
        test_ratio = int(test_var.get()) / 100
        width = int(width_var.get())
        height = int(height_var.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid ratio or image size values.")
        return

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
        messagebox.showerror("Error", "Ratios must sum to 100%.")
        return

    # hedef klasör -> prepared-data
    output_dir = PREPARED_DATA_DIR
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    classes = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
    total_images = 0
    processed = 0

    # toplam resim sayısını hesapla
    for c in classes:
        class_path = os.path.join(folder, c)
        total_images += len([f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])

    # progress bar sıfırla
    progress_bar["maximum"] = total_images
    progress_bar["value"] = 0
    progress_label.config(text="Processing started...")

    for c in classes:
        imgs = [os.path.join(folder, c, f) for f in os.listdir(os.path.join(folder, c)) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        train_files, temp = train_test_split(imgs, test_size=(1 - train_ratio), random_state=42)
        val_files, test_files = train_test_split(temp, test_size=(test_ratio / (val_ratio + test_ratio)), random_state=42)

        for split_name, file_list in zip(["train", "val", "test"], [train_files, val_files, test_files]):
            split_dir = os.path.join(output_dir, split_name, c)
            os.makedirs(split_dir, exist_ok=True)
            for fpath in file_list:
                try:
                    img = Image.open(fpath).convert("RGB")
                    img = img.resize((width, height))
                    img.save(os.path.join(split_dir, os.path.basename(fpath)))
                    processed += 1
                    progress_bar["value"] = processed
                    progress_label.config(text=f"Processing {processed}/{total_images} images...")
                    root.update_idletasks()
                except Exception as e:
                    print(f"Error: {fpath} could not be processed ({e})")

    progress_label.config(text="Completed ✅")
    messagebox.showinfo("Done", f"Dataset prepared successfully!\nSaved in:\n{output_dir}")

# --- UI Elements ---
dataset_path = StringVar(value=RAW_DATA_DIR)
train_var = StringVar(value="70")
val_var = StringVar(value="20")
test_var = StringVar(value="10")
width_var = StringVar(value="224")
height_var = StringVar(value="224")

Label(root, text="Dataset Folder:", font=("Arial", 11)).pack(pady=5)
Entry(root, textvariable=dataset_path, width=45).pack()
Button(root, text="📂 Browse", command=select_folder).pack(pady=5)

Label(root, text="Data Split Ratios (%)", font=("Arial", 11, "bold")).pack(pady=10)
frame_ratio = Frame(root)
frame_ratio.pack()
Label(frame_ratio, text="Train").grid(row=0, column=0)
Entry(frame_ratio, textvariable=train_var, width=5).grid(row=0, column=1)
Label(frame_ratio, text="Val").grid(row=0, column=2)
Entry(frame_ratio, textvariable=val_var, width=5).grid(row=0, column=3)
Label(frame_ratio, text="Test").grid(row=0, column=4)
Entry(frame_ratio, textvariable=test_var, width=5).grid(row=0, column=5)

Label(root, text="Image Size (px)", font=("Arial", 11, "bold")).pack(pady=10)
frame_size = Frame(root)
frame_size.pack()
Label(frame_size, text="Width").grid(row=0, column=0)
Entry(frame_size, textvariable=width_var, width=5).grid(row=0, column=1)
Label(frame_size, text="Height").grid(row=0, column=2)
Entry(frame_size, textvariable=height_var, width=5).grid(row=0, column=3)

Button(root, text="🚀 Prepare Dataset", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), command=start_preprocessing_thread).pack(pady=25)

# --- Progress Bar ---
progress_label = Label(root, text="Progress: Waiting...", fg="gray")
progress_label.pack(pady=5)
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

Label(root, text="Output will be saved in 'data/prepared-data/'", wraplength=460, fg="gray").pack()

root.mainloop()
