import os
import pandas as pd
from sklearn.utils import resample

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed")
MERGED_DATASET_PATH = os.path.join(PROCESSED_DATA_DIR, "merged_dataset.csv")
BALANCED_DATASET_PATH = os.path.join(PROCESSED_DATA_DIR, "merged_balanced.csv")

def balance_dataset():
    """
    Loads the merged dataset, separates majority and minority classes,
    oversamples the minority class until balanced, shuffles the result,
    and saves it to a new CSV file.
    """
    if not os.path.exists(MERGED_DATASET_PATH):
        print(f"Error: Merged dataset not found at {MERGED_DATASET_PATH}")
        print("Please run 'run_pipeline.py' first.")
        return

    print("Loading merged dataset to perform oversampling...")
    df = pd.read_csv(MERGED_DATASET_PATH)
    
    if "label" not in df.columns:
        print("Error: 'label' column is missing from the dataset.")
        return
        
    print(f"Original Dataset Size: {len(df)}")
    original_dist = df["label"].value_counts().to_dict()
    print("Original Distribution:")
    for cls, count in original_dist.items():
        print(f"  - Label {cls}: {count}")
        
    # 1. Separate minority and majority classes
    majority_class_label = max(original_dist, key=original_dist.get)
    minority_class_label = min(original_dist, key=original_dist.get)
    
    df_majority = df[df["label"] == majority_class_label]
    df_minority = df[df["label"] == minority_class_label]
    
    # 2. Duplicate minority samples until balanced
    print("\nOversampling minority class to match majority...")
    df_minority_oversampled = resample(
        df_minority, 
        replace=True,                  # Sample with replacement for oversampling
        n_samples=len(df_majority),    # Match the count of the majority class
        random_state=42                # Ensure reproducibility
    )
    
    # Combine the untouched majority class with the duplicated minority class
    df_balanced = pd.concat([df_majority, df_minority_oversampled])
    
    # 3. Shuffle dataset
    print("Shuffling balanced dataset...")
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # 4. Print new class distribution
    print("\n" + "="*40)
    print("NEW CLASS DISTRIBUTION")
    print("="*40)
    print(f"Total Size: {len(df_balanced)} records")
    new_dist = df_balanced["label"].value_counts().to_dict()
    for cls, count in new_dist.items():
        print(f"  - Label {cls}: {count}")
    print("="*40 + "\n")
    
    # 5. Save new dataset
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    df_balanced.to_csv(BALANCED_DATASET_PATH, index=False)
    print(f"Saved perfectly balanced dataset to -> {BALANCED_DATASET_PATH}")

if __name__ == "__main__":
    balance_dataset()
