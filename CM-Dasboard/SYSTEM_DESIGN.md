# System Design & Architecture

## Architecture Breakdown
1. **Classifier (`app/ml/`)**: Uses XGBoost/RandomForest (with PyTorch support built-in) to perform initial inference for Incident Type and Severity. Utilizes SMOTE for class imbalance and BCEWithLogits for multi-label predictions.
2. **RAG / FAISS (`app/services/memory/`)**: High-performance vector database. Converts text via `sentence-transformers` and searches for historical precedents. Stores `metadata` including location and prior labels.
3. **Agents (`app/services/agents/`)**: Specialized asynchronous worker modules (Classification, Severity, Complaint, Routing) that process data independently and cross-check outputs.
4. **Memory System (`FaissMemory`)**: A self-sculpting ledger. Good predictions are boosted in the vector space, while penalized predictions (via RL) are deprecated to prevent hallucination loops.
5. **Async System (`AsyncQueue`)**: Handles post-decision execution (e.g., department dispatching) without blocking the main event loop.
6. **Dashboard (`ClusterEngine`)**: Utilizes DBSCAN to map geo-tagged complaints into localized hotspots for frontend consumption.

## Data Flow
`Input` → `Geo-Tagging` → `Classification` → `Retrieval (RAG)` → `Agent Negotiation (Decision)` → `Async Execution` → `Memory Storage (Learning)`

## Agent Behavior
Agents possess autonomy to:
- **Call RAG**: View historical context to break ties.
- **Call Memory**: Validate past decisions.
- **Call Other Agents**: Using the `re_evaluate()` hook, agents can yield to peers. If the `ComplaintAgent` is highly confident about an electricity issue, the `RoutingAgent` will actively switch its assignment to the `POWER_GRID`.

## Memory Design
Stores:
- **Past Complaints**: The raw incident text.
- **Actions**: The final decisions and classifications.
- **Outcomes/Rewards**: The RL system flags objects as `deprecated: True` if the user submits negative feedback.

## Training Pipeline
- **Data Ingestion**: Reads from `raw/train.csv`.
- **Preprocessing**: Cleans, deduplicates, and label-encodes target variables.
- **Training**: Balances data with SMOTE, calculates specific `class_weights`, and fits models.
- **Evaluation**: Emits precision/recall metrics, class distributions, and confusion matrices.
- **Saving Models**: Exports `.pkl` objects via `joblib` into `app/ml/models`.
