from app.services.rl.feedback_manager import FeedbackManager

class DynamicPolicyEngine:
    """
    Adjusts the pipeline manager's thresholds based on RL reward trends.
    """
    def __init__(self):
        self.feedback_manager = FeedbackManager()
        
    def get_current_policy(self):
        """
        Calculates dynamic thresholds.
        If avg_reward is high (> 0.5), we relax thresholds.
        If avg_reward is low (< 0.0), we tighten thresholds.
        """
        avg_reward = self.feedback_manager.get_average_reward(last_n=20)
        
        policy = {
            "confidence_storage_threshold": 0.75, # base
            "rag_override_agreement": 0.7,        # base
            "rag_override_similarity": 0.8        # base
        }
        
        if avg_reward < 0.0:
            # System is making mistakes, be more conservative
            policy["confidence_storage_threshold"] = 0.85
            policy["rag_override_agreement"] = 0.8
            policy["rag_override_similarity"] = 0.85
        elif avg_reward > 0.5:
            # System is highly accurate, trust predictions more
            policy["confidence_storage_threshold"] = 0.65
            policy["rag_override_agreement"] = 0.6
            policy["rag_override_similarity"] = 0.75
            
        return policy
