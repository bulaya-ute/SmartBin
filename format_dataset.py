import os
import shutil
import random

# === CONFIGURATION ===
dataset_dir = "/mnt/Data/Downloads/drinking_waste_dataset/Images_of_Waste/YOLO_imgs"  # Path to your folder with images and labels
output_dir = "/mnt/Data/Downloads/drinking_waste_dataset/Images_of_Waste/formatted"            # Output folder for reorganized structure
image_exts = [".jpg", ".jpeg", ".png"]  # Add any other extensions you use
split_ratio = 0.8                 # 80% train, 20% val

# === DISCOVER IMAGE-LABEL PAIRS ===
files = os.listdir(dataset_dir)
images = []
for f in files:
    if f.lower().startswith("hdpem"):
        continue
    if os.path.splitext(f)[1].lower() in image_exts:
        images.append(f)
random.shuffle(images)

split_index = int(len(images) * split_ratio)
train_images = images[:split_index]
val_images = images[split_index:]

# === CREATE NEW DIRECTORY STRUCTURE ===
for subdir in ["images/train", "images/val", "labels/train", "labels/val"]:
    os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

# === MOVE FILES ===
def move_pair(img_list, split):
    for img_name in img_list:
        base, ext = os.path.splitext(img_name)
        label_name = base + ".txt"

        # Paths
        src_img = os.path.join(dataset_dir, img_name)
        src_label = os.path.join(dataset_dir, label_name)
        dst_img = os.path.join(output_dir, f"images/{split}", img_name)
        dst_label = os.path.join(output_dir, f"labels/{split}", label_name)

        # Move only if both image and label exist
        if os.path.exists(src_label):
            shutil.copy(src_img, dst_img)
            shutil.copy(src_label, dst_label)
        else:
            print(f"Warning: No label for {img_name}, skipping.")

move_pair(train_images, "train")
move_pair(val_images, "val")

print("✅ Dataset split complete!")
