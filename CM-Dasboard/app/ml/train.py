import pandas as pd
import logging
import os
import joblib
from typing import Optional

# To handle class imbalance
from imblearn.over_sampling import SMOTE

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

from app.ml.preprocess import DataPreprocessor
from app.ml.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainPipeline:
    """
    End-to-End training pipeline for Incident Classification and Severity Prediction.
    Handles data loading, preprocessing, embedding generation, SMOTE resampling, 
    model training, evaluation, and exporting.
    """
    def __init__(self, data_path: str, output_dir: str = 'app/ml/models'):
        self.data_path = data_path
        self.output_dir = output_dir
        self.preprocessor = DataPreprocessor()
        self.embedder = EmbeddingService()
        
        # Ensure the models directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_data(self) -> pd.DataFrame:
        """Loads dataset from CSV."""
        logger.info(f"Loading data from {self.data_path}...")
        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df)} records.")
        return df
        
    def train_model(self, X_train, y_train, model_type: str = "xgb"):
        """Trains either XGBoost or RandomForest based on the target task."""
        if model_type == "xgb":
            logger.info("Initializing XGBoost Classifier...")
            model = XGBClassifier(
                use_label_encoder=False, 
                eval_metric='mlogloss',
                random_state=42,
                n_estimators=100,
                max_depth=6
            )
        else:
            logger.info("Initializing Random Forest Classifier...")
            model = RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                class_weight="balanced"
            )
            
        logger.info("Fitting model...")
        model.fit(X_train, y_train)
        return model
        
    def evaluate(self, model, X_test, y_test, name: str = "Model", label_encoder=None):
        """Runs predictions and prints evaluation metrics including accuracy, F1, and confusion matrix."""
        preds = model.predict(X_test)
        
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average='weighted')
        
        logger.info(f"\n{'='*40}\n{name.upper()} EVALUATION\n{'='*40}")
        logger.info(f"Accuracy: {acc:.4f}")
        logger.info(f"F1 Score (Weighted): {f1:.4f}\n")
        
        # Determine target names if encoder is provided
        target_names = label_encoder.classes_ if label_encoder else None
        
        logger.info("Classification Report:")
        logger.info("\n" + classification_report(y_test, preds, target_names=target_names))
        
        logger.info("Confusion Matrix:")
        logger.info("\n" + str(confusion_matrix(y_test, preds)))
        logger.info("="*40)
        
    def run(self):
        """Executes the full pipeline sequentially."""
        logger.info("Starting CM-Dashboard ML Training Pipeline...")
        
        # 1. Load Data
        df = self.load_data()
        
        # 2. Preprocess Data (Clean, Dedup, Encode)
        df, cat_enc, sev_enc = self.preprocessor.process(df)
        
        # 3. Generate Embeddings (Feature Engineering)
        X = self.embedder.generate_embeddings(df['cleaned_text'].tolist())
        
        # 4. Prepare SMOTE
        smote = SMOTE(random_state=42)
        
        # ---------------------------------------------------------------------
        # 5. Train Classification Model (Incident Type)
        # ---------------------------------------------------------------------
        logger.info("\n>>> Phase 1: Classification Model Training <<<")
        y_cat = df['category_encoded'].values
        
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
            X, y_cat, test_size=0.2, random_state=42, stratify=y_cat
        )
        
        logger.info("Applying SMOTE to balance classification training classes...")
        X_train_c_sm, y_train_c_sm = smote.fit_resample(X_train_c, y_train_c)
        
        clf_model = self.train_model(X_train_c_sm, y_train_c_sm, model_type="xgb")
        self.evaluate(clf_model, X_test_c, y_test_c, name="Classification", label_encoder=cat_enc)
        
        # ---------------------------------------------------------------------
        # 6. Train Severity Model
        # ---------------------------------------------------------------------
        logger.info("\n>>> Phase 2: Severity Model Training <<<")
        y_sev = df['severity_encoded'].values
        
        X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(
            X, y_sev, test_size=0.2, random_state=42, stratify=y_sev
        )
        
        logger.info("Applying SMOTE to balance severity training classes...")
        X_train_s_sm, y_train_s_sm = smote.fit_resample(X_train_s, y_train_s)
        
        sev_model = self.train_model(X_train_s_sm, y_train_s_sm, model_type="rf") # Random Forest for Severity
        self.evaluate(sev_model, X_test_s, y_test_s, name="Severity", label_encoder=sev_enc)
        
        # ---------------------------------------------------------------------
        # 7. Export Models
        # ---------------------------------------------------------------------
        logger.info("\n>>> Phase 3: Exporting Models <<<")
        clf_path = os.path.join(self.output_dir, 'classifier.pkl')
        sev_path = os.path.join(self.output_dir, 'severity.pkl')
        enc_path = os.path.join(self.output_dir, 'encoders.pkl')
        
        joblib.dump(clf_model, clf_path)
        logger.info(f"Saved Classification Model to {clf_path}")
        
        joblib.dump(sev_model, sev_path)
        logger.info(f"Saved Severity Model to {sev_path}")
        
        self.preprocessor.save_encoders(enc_path)
        
        logger.info("🎉 CM-Dashboard ML Pipeline completed successfully!")

if __name__ == "__main__":
    # Assuming dataset is located in the data directory
    # User can easily retrain by running `python -m app.ml.train`
    pipeline = TrainPipeline(data_path="app/ml/data/raw/train.csv")
    try:
        pipeline.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
