from ultralytics import YOLO

model = YOLO("yolo11n.pt")
results = model.train(data="dataset.yaml", epochs=10, imgsz=640)