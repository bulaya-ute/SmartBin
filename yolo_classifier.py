from ultralytics import YOLO

model = YOLO("runs/smartbin_classify2/weights/best.pt")
model.predict(0, show=True)
