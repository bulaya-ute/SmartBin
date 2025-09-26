from ultralytics import YOLO

model = YOLO("classifier_model_yolo.pt")
results = model.predict("bus.jpg", task="classify", verbose=False)
print([round(float(i), 2) for i in list(results[0].probs.data)])
print(results[0].names)