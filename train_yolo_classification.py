#!/usr/bin/env python3
"""
Simple YOLO Classification Training Script
Trains YOLO11 classification model on waste dataset
"""

from ultralytics import YOLO

def main():
    print("🚀 Starting YOLO Classification Training")
    print("📁 Dataset: ./larger_dataset")
    print("🎯 Classes: aluminium, carton, e_waste, glass, organic_waste, paper_and_cardboard, plastic, textile, wood")
    print("♻️ Target: Binary classification (recyclable vs non-recyclable)")
    print("=" * 50)
    
    # Load pretrained YOLO11 classification model
    model = YOLO('yolo11n-cls.pt')  # nano model for faster training
    
    # Train the model
    results = model.train(
        data='./larger_dataset',  # path to new dataset
        epochs=10,                # increased epochs for more classes
        imgsz=224,               # image size
        batch=16,                # batch size
        device='cpu',            # use CPU (change to 'cuda' if you have GPU)
        project='runs',          # save results to runs/
        name='smartbin_9class'   # experiment name
    )
    
    print("✅ Training completed!")
    print(f"📊 Best model saved to: runs/smartbin_9class/weights/best.pt")
    
    # Validate the model
    print("\n🧪 Validating model...")
    metrics = model.val()
    print(f"🎯 Top-1 Accuracy: {metrics.top1:.3f}")
    print(f"🎯 Top-5 Accuracy: {metrics.top5:.3f}")
    
    # Export for deployment
    print("\n📦 Exporting model...")
    model.export(format='onnx')  # Export to ONNX for deployment
    
    print("\n✅ All done! Model ready for integration.")
    print("💡 Remember: GUI will show specific class, ESP32 gets recyclable/non-recyclable")

if __name__ == "__main__":
    main()
