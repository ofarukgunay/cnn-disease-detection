import os
import shutil
import threading
import random
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from sklearn.model_selection import train_test_split

# Dizin Yapısı Ayarları
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))          # Proje ana dizini
DATA_DIR = os.path.join(ROOT_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "kvasir-dataset-v2")
PREPARED_DATA_DIR = os.path.join(DATA_DIR, "prepared-data")

# Main Window
root = Tk()
root.title("Gastroenterology Dataset Preparation Tool")
root.geometry("560x650")
root.resizable(False, False)

# Fonctions
def select_folder():
    folder = filedialog.askdirectory(initialdir=DATA_DIR)
    dataset_path.set(folder)

# İşlem sırasında UI öğelerini devre dışı bırakma
def set_ui_state(state):
    widgets = [
        train_entry, val_entry, test_entry,
        width_entry, height_entry,
        output_entry,
        normalize_check, grayscale_check, augment_check,
        browse_button, prepare_button
    ]
    for w in widgets:
        w.config(state=state)

def start_preprocessing_thread():
    thread = threading.Thread(target=start_preprocessing)
    thread.start()

def start_preprocessing():
    set_ui_state("disabled")

    folder = dataset_path.get()
    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Please select a valid dataset folder.")
        set_ui_state("normal")
        return

    try:
        train_ratio = int(train_var.get()) / 100
        val_ratio = int(val_var.get()) / 100
        test_ratio = int(test_var.get()) / 100
        width = int(width_var.get())
        height = int(height_var.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid ratio or image size values.")
        set_ui_state("normal")
        return
    
    # Kullanıcının belirttiği çıktı klasör adı
    folder_name = output_folder_var.get().strip()
    if not folder_name:
        messagebox.showerror("Error", "Please enter a name for the output folder.")
        set_ui_state("normal")
        return

    output_dir = os.path.join(PREPARED_DATA_DIR, folder_name)

    # Eğer klasör zaten varsa, kullanıcıya sor
    if os.path.exists(output_dir):
        confirm = messagebox.askyesno(
            "Overwrite Confirmation",
            f"The folder '{folder_name}' already exists.\nDo you want to overwrite it?"
        )
        if not confirm:
            set_ui_state("normal")
            return
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    classes = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
    total_images = sum(
        len([f for f in os.listdir(os.path.join(folder, c)) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        for c in classes
    )
    processed = 0

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

                    # Görsel işleme seçenekleri
                    if grayscale_var.get():
                        img = img.convert("L").convert("RGB")

                    if normalize_var.get():
                        arr = np.asarray(img).astype(np.float32) / 255.0
                        img = Image.fromarray((arr * 255).astype(np.uint8))

                    if augment_var.get():
                        if random.random() > 0.5:
                            img = img.transpose(Image.FLIP_LEFT_RIGHT)
                        if random.random() > 0.5:
                            img = img.transpose(Image.FLIP_TOP_BOTTOM)
                        if random.random() > 0.5:
                            angle = random.randint(-15, 15)
                            img = img.rotate(angle)

                    img.save(os.path.join(split_dir, os.path.basename(fpath)))
                    processed += 1
                    progress_bar["value"] = processed
                    progress_label.config(text=f"Processing {processed}/{total_images} images...")
                    root.update_idletasks()

                except Exception as e:
                    print(f"Error: {fpath} could not be processed ({e})")

    progress_label.config(text="Completed ✅")
    messagebox.showinfo("Done", f"Dataset prepared successfully!\nSaved in:\n{output_dir}")
    set_ui_state("normal")

# UI Elements
dataset_path = StringVar(value=RAW_DATA_DIR)
train_var = StringVar(value="80")
val_var = StringVar(value="100")
test_var = StringVar(value="10")
width_var = StringVar(value="224")
height_var = StringVar(value="224")
output_folder_var = StringVar(value="prepared_" + str(random.randint(100, 999)))  # varsayılan isim

Label(root, text="Dataset Folder:", font=("Arial", 11)).pack(pady=5)
Entry(root, textvariable=dataset_path, width=45).pack()
browse_button = Button(root, text="📂 Browse", command=select_folder)
browse_button.pack(pady=5)

Label(root, text="Data Split Ratios (%)", font=("Arial", 11, "bold")).pack(pady=10)
frame_ratio = Frame(root)
frame_ratio.pack()
Label(frame_ratio, text="Train").grid(row=0, column=0)
train_entry = Entry(frame_ratio, textvariable=train_var, width=5)
train_entry.grid(row=0, column=1)
Label(frame_ratio, text="Val").grid(row=0, column=2)
val_entry = Entry(frame_ratio, textvariable=val_var, width=5)
val_entry.grid(row=0, column=3)
Label(frame_ratio, text="Test").grid(row=0, column=4)
test_entry = Entry(frame_ratio, textvariable=test_var, width=5)
test_entry.grid(row=0, column=5)

Label(root, text="Image Size (px)", font=("Arial", 11, "bold")).pack(pady=10)
frame_size = Frame(root)
frame_size.pack()
Label(frame_size, text="Width").grid(row=0, column=0)
width_entry = Entry(frame_size, textvariable=width_var, width=5)
width_entry.grid(row=0, column=1)
Label(frame_size, text="Height").grid(row=0, column=2)
height_entry = Entry(frame_size, textvariable=height_var, width=5)
height_entry.grid(row=0, column=3)

Label(root, text="Output Folder Name:", font=("Arial", 11, "bold")).pack(pady=10)
output_entry = Entry(root, textvariable=output_folder_var, width=25)
output_entry.pack(pady=(0, 10))

Label(root, text="Image Processing Options", font=("Arial", 11, "bold")).pack(pady=10)
frame_opts = Frame(root)
frame_opts.pack()

normalize_var = BooleanVar(value=False)
grayscale_var = BooleanVar(value=False)
augment_var = BooleanVar(value=False)

normalize_check = Checkbutton(frame_opts, text="Normalize (0–1)", variable=normalize_var)
grayscale_check = Checkbutton(frame_opts, text="Grayscale", variable=grayscale_var)
augment_check = Checkbutton(frame_opts, text="Augmentation (Flip/Rotate)", variable=augment_var)

normalize_check.grid(row=0, column=0, padx=10)
grayscale_check.grid(row=0, column=1, padx=10)
augment_check.grid(row=0, column=2, padx=10)

prepare_button = Button(
    root, text="Prepare Dataset", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
    command=start_preprocessing_thread
)
prepare_button.pack(pady=25)

progress_label = Label(root, text="Progress: Waiting...", fg="gray")
progress_label.pack(pady=5)
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

Label(root, text="Output will be saved in 'data/prepared-data/<folder_name>'", wraplength=460, fg="gray").pack()

root.mainloop()
