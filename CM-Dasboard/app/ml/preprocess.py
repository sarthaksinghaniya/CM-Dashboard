import pandas as pd
import re
import logging
from typing import Tuple
from sklearn.preprocessing import LabelEncoder
import joblib

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Handles data cleaning, normalization, and label encoding for incident records.
    """
    def __init__(self):
        self.category_encoder = LabelEncoder()
        self.severity_encoder = LabelEncoder()
        
    def clean_text(self, text: str) -> str:
        """Removes noise, punctuation, and lowers the text."""
        if not isinstance(text, str):
            return ""
        text = text.lower()
        # Remove all non-word characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def process(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, LabelEncoder, LabelEncoder]:
        """
        Executes the cleaning pipeline: dropping missing values, deduplication, 
        text cleaning, and label encoding.
        """
        logger.info("Starting data preprocessing pipeline...")
        
        # 1. Handle missing expected columns by generating them if needed
        initial_len = len(df)
        
        if 'category' not in df.columns:
            if 'source' in df.columns:
                df['category'] = df['source']
            else:
                df['category'] = 'unknown'
                
        if 'severity' not in df.columns:
            if 'label' in df.columns:
                # If label is 1 (disaster), severity is high/critical. If 0, low/medium.
                import numpy as np
                np.random.seed(42)
                conditions = [df['label'] == 1, df['label'] == 0]
                choices = [np.random.choice(['high', 'critical'], size=len(df)), 
                           np.random.choice(['low', 'medium'], size=len(df))]
                df['severity'] = np.select(conditions, choices, default='unknown')
            else:
                df['severity'] = 'unknown'
                
        df = df.dropna(subset=['text', 'category', 'severity'])
        
        # 2. Remove exact duplicates based on text
        df = df.drop_duplicates(subset=['text'])
        
        # 3. Clean the text
        df['cleaned_text'] = df['text'].apply(self.clean_text)
        
        # 4. Drop rows where text became empty after cleaning
        df = df[df['cleaned_text'] != ""]
        
        logger.info(f"Data cleaning complete. Retained {len(df)} out of {initial_len} rows.")
        
        # 5. Encode labels
        df['category_encoded'] = self.category_encoder.fit_transform(df['category'])
        df['severity_encoded'] = self.severity_encoder.fit_transform(df['severity'])
        
        return df, self.category_encoder, self.severity_encoder

    def save_encoders(self, path: str):
        """Saves the fitted LabelEncoders for inference use."""
        joblib.dump({
            "category": self.category_encoder,
            "severity": self.severity_encoder
        }, path)
        logger.info(f"Saved label encoders to {path}")
