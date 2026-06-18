import os
import json
import pandas as pd
import numpy as np
from sklearn.utils.class_weight import compute_class_weight

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed")
MERGED_DATASET_PATH = os.path.join(PROCESSED_DATA_DIR, "merged_dataset.csv")
WEIGHTS_PATH = os.path.join(PROCESSED_DATA_DIR, "class_weights.json")

def calculate_class_weights():
    """
    Loads the merged dataset and uses sklearn to compute balanced class weights,
    saving the result to a JSON file to be used during model training.
    """
    if not os.path.exists(MERGED_DATASET_PATH):
        print(f"Error: Merged dataset not found at {MERGED_DATASET_PATH}")
        print("Please run 'run_pipeline.py' first.")
        return

    print("Loading merged dataset to compute class weights...")
    df = pd.read_csv(MERGED_DATASET_PATH)
    
    if "label" not in df.columns:
        print("Error: 'label' column is missing from the dataset.")
        return
        
    # Extract label array and find unique classes
    labels = df["label"].values
    unique_classes = np.unique(labels)
    
    # Use sklearn to magically compute perfectly balanced weights
    # 'balanced' setting uses the formula: n_samples / (n_classes * np.bincount(y))
    weights = compute_class_weight(class_weight='balanced', classes=unique_classes, y=labels)
    
    # Generate dictionary mapping class label to weight (e.g. {"0": 1.5, "1": 0.8})
    class_weights_dict = {
        str(int(cls)): round(float(weight), 4) 
        for cls, weight in zip(unique_classes, weights)
    }
    
    print("\n" + "="*40)
    print("COMPUTED CLASS WEIGHTS")
    print("="*40)
    for cls, weight in class_weights_dict.items():
        print(f"Label {cls}: {weight}")
    print("="*40 + "\n")
    
    # Save the generated weights configuration
    try:
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        with open(WEIGHTS_PATH, "w") as f:
            json.dump(class_weights_dict, f, indent=4)
        print(f"Saved class weights to -> {WEIGHTS_PATH}")
    except Exception as e:
        print(f"Failed to save JSON weights: {e}")

if __name__ == "__main__":
    calculate_class_weights()
