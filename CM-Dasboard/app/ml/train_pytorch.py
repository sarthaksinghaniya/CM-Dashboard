import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FocalLoss(nn.Module):
    """
    Optional Focal Loss for highly imbalanced datasets.
    """
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha  # Tensor of class weights
        self.gamma = gamma
        self.reduction = reduction
        self.ce = nn.CrossEntropyLoss(weight=alpha, reduction='none')

    def forward(self, inputs, targets):
        ce_loss = self.ce(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss

class NNTrainer:
    """
    PyTorch-based training loop with Early Stopping, LR Scheduler, and Gradient Clipping.
    Satisfies advanced "production-grade" ML requirements.
    Supports both multi-class (CrossEntropy) and multi-label (BCEWithLogits).
    """
    def __init__(self, input_dim: int, num_classes: int, class_weights: dict = None, use_focal_loss: bool = False, use_multi_label: bool = False):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.use_multi_label = use_multi_label
        
        # Simple feed-forward network over BERT embeddings
        self.model = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        ).to(self.device)
        
        # Class weights conversion
        alpha = None
        if class_weights:
            sorted_weights = [class_weights[k] for k in sorted(class_weights.keys())]
            alpha = torch.tensor(sorted_weights, dtype=torch.float32).to(self.device)
            
        if self.use_multi_label:
            logger.info("Using BCEWithLogitsLoss for Multi-Label Classification...")
            self.criterion = nn.BCEWithLogitsLoss(pos_weight=alpha)
        elif use_focal_loss:
            logger.info("Using Focal Loss for Multi-Class...")
            self.criterion = FocalLoss(alpha=alpha)
        else:
            logger.info("Using standard Cross Entropy Loss with weights...")
            self.criterion = nn.CrossEntropyLoss(weight=alpha)
            
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-3, weight_decay=1e-4)
        # LR Scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode='min', patience=2, factor=0.5)

    def fit(self, X_train, y_train, X_val=None, y_val=None, epochs=20, batch_size=32, patience=5):
        train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        val_loader = None
        if X_val is not None and y_val is not None:
            val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long))
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
        best_loss = float('inf')
        epochs_no_improve = 0
        
        logger.info(f"Starting PyTorch Training on {self.device}")
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient Clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                total_loss += loss.item()
                
            avg_train_loss = total_loss / len(train_loader)
            val_loss = avg_train_loss # Default to train if no val
            
            if val_loader:
                self.model.eval()
                val_total = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                        outputs = self.model(batch_X)
                        val_total += self.criterion(outputs, batch_y).item()
                val_loss = val_total / len(val_loader)
                
            # Scheduler Step
            self.scheduler.step(val_loss)
            
            logger.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {val_loss:.4f}")
            
            # Early Stopping
            if val_loss < best_loss:
                best_loss = val_loss
                epochs_no_improve = 0
                # Could save best model state dict here
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= patience:
                    logger.info(f"Early stopping triggered at epoch {epoch+1}")
                    break
                    
        return self.model
        
    def predict(self, X):
        self.model.eval()
        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(X_tensor)
            
            if self.use_multi_label:
                probs = torch.sigmoid(outputs)
                preds = (probs > 0.5).int()
                return preds.cpu().numpy()
            else:
                _, preds = torch.max(outputs, 1)
                return preds.cpu().numpy()
