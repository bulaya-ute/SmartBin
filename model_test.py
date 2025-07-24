from ultralytics import YOLO

# model = YOLO("yolo11n-seg.pt")
model = YOLO("runs/train3/weights/best.pt")

model.predict(0, show=True)
