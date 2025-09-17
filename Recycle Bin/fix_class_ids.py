import os
from pathlib import Path

# === CONFIGURATION ===
dataset_root = "/mnt/Data/Downloads/drinking_waste_dataset/Images_of_Waste/formatted"  # Replace with your actual dataset root
old_class_id = "3"
new_class_id = "2"

# Expected label folders
label_paths = [
    Path(dataset_root) / "labels/train",
    Path(dataset_root) / "labels/val"
]

for label_dir in label_paths:
    if not label_dir.exists():
        print(f"⚠️ Directory not found: {label_dir}")
        continue

    txt_files = label_dir.glob("*.txt")
    for file in txt_files:
        with open(file, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == old_class_id:
                parts[0] = new_class_id
            updated_lines.append(" ".join(parts))

        with open(file, 'w') as f:
            f.write("\n".join(updated_lines) + "\n")

print(f"✅ Completed: Replaced class ID '{old_class_id}' with '{new_class_id}' in all label files under {dataset_root}/labels/train and /val.")
