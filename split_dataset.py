#!/usr/bin/env python3
"""
Simple Dataset Splitter
Splits a dataset into train/val/test splits while maintaining class structure
"""

import os
import shutil
import random
import argparse
from pathlib import Path

def split_dataset(input_folder, output_folder, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """
    Split dataset into train/val/test splits
    
    Args:
        input_folder: Path to input dataset (class folders with images)
        output_folder: Path to output dataset structure
        train_ratio: Proportion for training (default 0.7)
        val_ratio: Proportion for validation (default 0.2) 
        test_ratio: Proportion for testing (default 0.1)
    """
    
    # Validate ratios
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        raise ValueError("Train, val, and test ratios must sum to 1.0")
    
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Create output directory structure
    splits = ['train', 'val', 'test']
    for split in splits:
        (output_path / split).mkdir(parents=True, exist_ok=True)
    
    # Get all class folders
    class_folders = [f for f in input_path.iterdir() if f.is_dir()]
    
    print(f"Found {len(class_folders)} classes: {[f.name for f in class_folders]}")
    
    total_images = 0
    split_counts = {'train': 0, 'val': 0, 'test': 0}
    
    # Process each class
    for class_folder in class_folders:
        class_name = class_folder.name
        print(f"\nProcessing class: {class_name}")
        
        # Create class folders in each split
        for split in splits:
            (output_path / split / class_name).mkdir(exist_ok=True)
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        images = [f for f in class_folder.iterdir() 
                 if f.is_file() and f.suffix.lower() in image_extensions]
        
        print(f"  Found {len(images)} images")
        
        # Shuffle images randomly
        random.shuffle(images)
        
        # Calculate split indices
        n_images = len(images)
        n_train = int(n_images * train_ratio)
        n_val = int(n_images * val_ratio)
        n_test = n_images - n_train - n_val  # Remaining goes to test
        
        # Split images
        train_images = images[:n_train]
        val_images = images[n_train:n_train + n_val]
        test_images = images[n_train + n_val:]
        
        # Copy images to respective splits
        for split_name, split_images in [('train', train_images), ('val', val_images), ('test', test_images)]:
            for image in split_images:
                src = image
                dst = output_path / split_name / class_name / image.name
                shutil.copy2(src, dst)
            
            print(f"  {split_name}: {len(split_images)} images")
            split_counts[split_name] += len(split_images)
        
        total_images += n_images
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Dataset split completed!")
    print(f"Total images: {total_images}")
    print(f"Train: {split_counts['train']} ({split_counts['train']/total_images:.1%})")
    print(f"Val: {split_counts['val']} ({split_counts['val']/total_images:.1%})")
    print(f"Test: {split_counts['test']} ({split_counts['test']/total_images:.1%})")
    print(f"Output folder: {output_folder}")

def main():
    parser = argparse.ArgumentParser(description='Split dataset into train/val/test')
    parser.add_argument('input_folder', help='Input dataset folder')
    parser.add_argument('output_folder', help='Output dataset folder')
    parser.add_argument('--train', type=float, default=0.7, help='Train ratio (default: 0.7)')
    parser.add_argument('--val', type=float, default=0.2, help='Validation ratio (default: 0.2)')
    parser.add_argument('--test', type=float, default=0.1, help='Test ratio (default: 0.1)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    
    # Validate input
    if not os.path.exists(args.input_folder):
        print(f"Error: Input folder '{args.input_folder}' does not exist")
        return
    
    try:
        split_dataset(args.input_folder, args.output_folder, args.train, args.val, args.test)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
