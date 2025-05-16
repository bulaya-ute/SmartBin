import os
import cv2
import shutil
import numpy as np
from pathlib import Path
import torch
from segment_anything import sam_model_registry, SamPredictor
from tqdm import tqdm


# === CONFIGURATION ===
input_dataset = r"D:\Downloads\drinking_waste_dataset\Images_of_Waste\formatted"  # input YOLO-style dataset folder
output_dataset = r"D:\Downloads\drinking_waste_dataset\Images_of_Waste\segmented"  # where the new dataset will be saved
model_type = "vit_b"
checkpoint = "sam_vit_b_01ec64.pth"  # path to SAM .pth file
device = "cuda" if torch.cuda.is_available() else "cpu"
image_exts = [".jpg", ".jpeg", ".png"]

# === LOAD SAM MODEL ===
sam = sam_model_registry[model_type](checkpoint=checkpoint)
sam.to(device)
predictor = SamPredictor(sam)

# === HELPERS ===
def yolo_to_pixel_coords(box, img_w, img_h):
    x_center, y_center, w, h = box
    x1 = int((x_center - w / 2) * img_w)
    y1 = int((y_center - h / 2) * img_h)
    x2 = int((x_center + w / 2) * img_w)
    y2 = int((y_center + h / 2) * img_h)
    return [x1, y1, x2, y2]

# def process_split(split_name):
#     in_img_dir = Path(input_dataset) / "images" / split_name
#     in_lbl_dir = Path(input_dataset) / "labels" / split_name
#     out_img_dir = Path(output_dataset) / "images" / split_name
#     out_lbl_dir = Path(output_dataset) / "labels" / split_name
#
#     out_img_dir.mkdir(parents=True, exist_ok=True)
#     out_lbl_dir.mkdir(parents=True, exist_ok=True)
#
#     for img_path in in_img_dir.glob("*"):
#         if img_path.suffix.lower() not in image_exts:
#             continue
#
#         label_path = in_lbl_dir / (img_path.stem + ".txt")
#         if not label_path.exists():
#             print(f"⚠️ No label found for {img_path.name}, skipping.")
#             continue
#
#         # Copy image
#         shutil.copy(str(img_path), str(out_img_dir / img_path.name))
#
#         # Load image
#         image = cv2.imread(str(img_path))
#         image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#         h, w, _ = image.shape
#         predictor.set_image(image_rgb)
#
#         # Process labels
#         with open(label_path, 'r') as f:
#             lines = f.readlines()
#
#         seg_lines = []
#         for line in lines:
#             parts = line.strip().split()
#             if len(parts) < 5:
#                 continue
#             class_id = parts[0]
#             box = list(map(float, parts[1:5]))
#             x1, y1, x2, y2 = yolo_to_pixel_coords(box, w, h)
#             input_box = np.array([x1, y1, x2, y2])
#
#             masks, _, _ = predictor.predict(box=input_box[None, :], multimask_output=False)
#             mask = masks[0]
#
#             # Convert binary mask to contour
#             contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             if contours:
#                 polygon = contours[0].reshape(-1, 2)
#                 normalized = [(pt[0] / w, pt[1] / h) for pt in polygon]
#                 flat = [class_id] + [f"{x:.6f} {y:.6f}" for x, y in normalized]
#                 seg_lines.append(" ".join(flat))
#
#         # Save new label file
#         with open(out_lbl_dir / (img_path.stem + ".txt"), 'w') as f:
#             f.write("\n".join(seg_lines) + "\n")
#
#     print(f"✅ Processed split: {split_name}")

def process_split(split_name):
    in_img_dir = Path(input_dataset) / "images" / split_name
    in_lbl_dir = Path(input_dataset) / "labels" / split_name
    out_img_dir = Path(output_dataset) / "images" / split_name
    out_lbl_dir = Path(output_dataset) / "labels" / split_name

    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)

    img_paths = [p for p in in_img_dir.glob("*") if p.suffix.lower() in image_exts]

    for img_path in tqdm(img_paths, desc=f"Processing {split_name}", unit="img"):
        label_path = in_lbl_dir / (img_path.stem + ".txt")
        if not label_path.exists():
            print(f"⚠️ No label found for {img_path.name}, skipping.")
            continue

        # Copy image
        shutil.copy(str(img_path), str(out_img_dir / img_path.name))

        # Load image
        image = cv2.imread(str(img_path))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        predictor.set_image(image_rgb)

        with open(label_path, 'r') as f:
            lines = f.readlines()

        seg_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            class_id = parts[0]
            box = list(map(float, parts[1:5]))
            x1, y1, x2, y2 = yolo_to_pixel_coords(box, w, h)
            input_box = np.array([x1, y1, x2, y2])
            masks, _, _ = predictor.predict(box=input_box[None, :], multimask_output=False)
            mask = masks[0]

            contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                polygon = contours[0].reshape(-1, 2)
                normalized = [(pt[0] / w, pt[1] / h) for pt in polygon]
                flat = [class_id] + [f"{x:.6f} {y:.6f}" for x, y in normalized]
                seg_lines.append(" ".join(flat))

        with open(out_lbl_dir / (img_path.stem + ".txt"), 'w') as f:
            f.write("\n".join(seg_lines) + "\n")

    print(f"✅ Finished processing split: {split_name}")


# === MAIN LOOP ===
for split in ["train", "val"]:
    process_split(split)

print(f"\n🎉 Done! Segmented dataset saved to '{output_dataset}'")
