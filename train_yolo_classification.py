#!/usr/bin/env python3
"""
Simple YOLO Classification Training Script
Trains YOLO11 classification model on waste dataset
"""

from ultralytics import YOLO

def main():
    print("🚀 Starting YOLO Classification Training")
    print("📁 Dataset: ./dataset")
    print("🎯 Classes: metal, misc, paper, plastic")
    print("=" * 50)
    
    # Load pretrained YOLO11 classification model
    model = YOLO('yolo11n-cls.pt')  # nano model for faster training
    
    # Train the model
    results = model.train(
        data='./dataset',     # path to dataset
        epochs=5,           # number of epochs
        # imgsz=224,           # image size
        # batch=8,             # smaller batch for CPU
        device='cpu',        # use CPU
        # project='runs',      # save results to runs/
        # name='smartbin_classify'  # experiment name
    )
    
    print("✅ Training completed!")
    print(f"📊 Best model saved to: runs/smartbin_classify/weights/best.pt")
    
    # Validate the model
    print("\n🧪 Validating model...")
    metrics = model.val()
    print(f"🎯 Top-1 Accuracy: {metrics.top1:.3f}")
    print(f"🎯 Top-5 Accuracy: {metrics.top5:.3f}")
    
    # Export for deployment
    print("\n📦 Exporting model...")
    model.export(format='onnx')  # Export to ONNX for deployment
    
    print("\n✅ All done! Model ready for integration.")

if __name__ == "__main__":
    main()
