import threading
import logging
import joblib
import os

logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Singleton class to ensure ML models are loaded into memory only once.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(ModelLoader, cls).__new__(cls)
                cls._instance._classifier = None
                cls._instance._severity_model = None
                cls._instance._encoders = None
                cls._instance._is_loaded = False
        return cls._instance
        
    def load_models(self, models_dir: str = "app/ml/models"):
        """
        Loads the trained models and encoders into memory.
        """
        with self._lock:
            if self._is_loaded:
                return
                
            try:
                clf_path = os.path.join(models_dir, 'classifier.pkl')
                sev_path = os.path.join(models_dir, 'severity.pkl')
                enc_path = os.path.join(models_dir, 'encoders.pkl')
                
                if not os.path.exists(clf_path):
                    logger.warning(f"Models not found at {models_dir}. Ensure training has completed.")
                    return
                
                self._classifier = joblib.load(clf_path)
                self._severity_model = joblib.load(sev_path)
                self._encoders = joblib.load(enc_path)
                
                self._is_loaded = True
                logger.info("Fine-tuned models loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                raise e
            
    def get_classifier(self):
        if not self._is_loaded:
            self.load_models()
        return self._classifier
        
    def get_severity_model(self):
        if not self._is_loaded:
            self.load_models()
        return self._severity_model
        
    def get_encoders(self):
        if not self._is_loaded:
            self.load_models()
        return self._encoders
