from ultralytics import YOLO

# model = YOLO("yolo11n-seg.pt")
# model = YOLO("runs/train3/weights/best.pt")
# model = YOLO("/home/bulaya/Downloads/Programs/runs-20250730T233253Z-1-001/runs/segment/train/weights/best.pt")
model = YOLO("best.pt")

model.predict(0, show=True)
