import asyncio
import logging
import argparse
import sys
import json
from app.services.pipeline.pipeline_manager import PipelineManager
from app.ml.train import TrainPipeline

# Setup Global File Logging
os_makedirs = __import__("os").makedirs
os_makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("run_pipeline")

async def run_e2e_tests():
    logger.info("Initializing Pipeline Manager...")
    manager = PipelineManager()
    await manager.start_background_workers()
    
    logger.info("\n--- TEST CASE 1: NORMAL CASE ---")
    normal_text = "Garbage not collected in my area, it smells terrible."
    res1 = await manager.process_incident(normal_text)
    logger.info(f"Result (Normal): Routing -> {res1['final_decision']['assigned_team']}, Complaint -> {res1['final_decision']['complaint_categories']}")
    
    logger.info("\n--- TEST CASE 2: EDGE CASE (EMPTY/NOISY) ---")
    edge_text = "..... what is this ..... ?"
    res2 = await manager.process_incident(edge_text)
    logger.info(f"Result (Edge): Routing -> {res2['final_decision']['assigned_team']}, Complaint -> {res2['final_decision']['complaint_categories']}")
    
    logger.info("\n--- TEST CASE 3: UNSEEN MULTI-LABEL CASE ---")
    unseen_text = "Street light flickering and water leakage on 5th avenue."
    res3 = await manager.process_incident(unseen_text)
    logger.info(f"Result (Unseen): Routing -> {res3['final_decision']['assigned_team']}, Complaint -> {res3['final_decision']['complaint_categories']}")
    
    # Let async workers finish
    await asyncio.sleep(1)
    await manager.stop_background_workers()
    
    logger.info("\n✅ E2E Testing Completed. Output artifacts saved to logs/ and outputs/.")

def generate_report():
    logger.info("Generating Final System Report...")
    # Trigger model evaluation wrapper if we want to ensure metrics exist
    try:
        pipeline = TrainPipeline(data_path="app/ml/data/raw/train.csv")
        # We assume the models are already trained or we can trigger training
        # For validation, we just verify the metrics.json exists.
        with open("outputs/metrics.json", "r") as f:
            metrics = json.load(f)
            logger.info("Model Metrics Verified.")
            for model, m in metrics.items():
                logger.info(f"[{model}] Accuracy: {m.get('accuracy', 0):.2f} | F1: {m.get('f1_macro', 0):.2f}")
    except Exception as e:
        logger.warning("Could not read metrics.json. Please run the training pipeline once.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CM-Dashboard CLI")
    parser.add_argument("--test", action="store_true", help="Run End-to-End Pipeline Validation")
    parser.add_argument("--train", action="store_true", help="Run ML Training Pipeline")
    args = parser.parse_args()
    
    if args.train:
        pipeline = TrainPipeline(data_path="app/ml/data/raw/train.csv")
        pipeline.run()
        
    if args.test:
        asyncio.run(run_e2e_tests())
        generate_report()
        
    if not args.train and not args.test:
        parser.print_help()
