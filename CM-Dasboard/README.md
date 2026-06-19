# CM-Dashboard (Complaint Intelligence System)

## Project Overview
CM-Dashboard is an advanced, production-ready AI system designed to intelligently process, classify, and route civic complaints. By leveraging a multi-agent negotiation pipeline, dynamic RAG (Retrieval-Augmented Generation) via FAISS, and a continuous Reinforcement Learning loop, the system can autonomously handle complex, multi-label municipal issues with high precision.

## Problem Statement
Municipalities struggle to efficiently route public complaints, especially when issues span multiple departments (e.g., a burst water pipe flooding a street and causing a power outage). Human operators are easily overwhelmed, and simple AI classifiers cannot handle nuanced, multi-departmental failures or spatial clustering.

## Key Features
- **Multi-Label Classification**: Simultaneously detects overlapping issues (e.g., `WATER_SUPPLY`, `ELECTRICITY`).
- **Geo-Tagging & Clustering**: Automatically extracts spatial locations and runs DBSCAN algorithms to detect neighborhood hotspots.
- **RAG (FAISS)**: Uses `sentence-transformers` and a high-performance vector database to retrieve historical incident contexts.
- **Multi-Agent Negotiation**: A hierarchy of specialized agents (Classification, Severity, Routing, Complaint) cross-check each other's outputs and negotiate conflicts before yielding a final decision.
- **Memory-Based Reasoning**: Past incidents heavily influence current decisions.
- **Reinforcement Learning Loop**: User feedback automatically sculpts the vector space, boosting positive memories and deprecating bad ones.
- **Async Task Queue**: Handles post-processing actions (dispatching alerts) asynchronously via Celery (Mocked with `asyncio` natively for ease of use).

## Architecture Diagram
```text
[User Complaint] 
       |
       v
[Multi-Label Classifier & Geo-Tagger]
       |
       v
[RAG Context Retrieval (FAISS)]
       |
       v
[Multi-Agent Decision Engine] <---> [Negotiation Loop]
       |
       v
[Async Task Queue (Execution)]
       |
       v
[Memory Store (RL Learning)] <---> [Dashboard Analytics]
```

## Installation & Setup
1. Clone the repository and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize FAISS and outputs:
   ```bash
   mkdir -p outputs logs
   ```
3. Run the automated testing suite and pipeline:
   ```bash
   python run_pipeline.py --test
   ```

## Usage Example (Python API)
```python
import asyncio
from app.services.pipeline.pipeline_manager import PipelineManager

async def run():
    manager = PipelineManager()
    
    # Process a complex incident
    incident = "The main water pipe burst downtown, causing a massive power outage."
    result = await manager.process_incident(incident)
    
    print(result["final_decision"])

if __name__ == "__main__":
    asyncio.run(run())
```
