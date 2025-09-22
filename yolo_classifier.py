from ultralytics import YOLO

model = YOLO("runs/smartbin_9class/weights/best.pt")
model.predict(0, show=True)
