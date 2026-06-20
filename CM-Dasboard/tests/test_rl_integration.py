import os
import json
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor

from app.services.rl.feedback_manager import FeedbackManager
from app.services.rl.policy import DynamicPolicyEngine

# Use a separate test ledger path
TEST_LEDGER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "outputs",
    "test_feedback_ledger.json"
)

@pytest.fixture(autouse=True)
def clean_test_ledger():
    # Remove test ledger if exists
    if os.path.exists(TEST_LEDGER_PATH):
        try:
            os.remove(TEST_LEDGER_PATH)
        except Exception:
            pass
    yield
    # Cleanup after test
    if os.path.exists(TEST_LEDGER_PATH):
        try:
            os.remove(TEST_LEDGER_PATH)
        except Exception:
            pass

def test_citizen_rating_rewards():
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)
    
    # Test rating mapping
    assert fm.record_citizen_rating("DL-2026-T1", 5) == 1.0
    assert fm.record_citizen_rating("DL-2026-T2", 4) == 0.5
    assert fm.record_citizen_rating("DL-2026-T3", 3) == 0.0
    assert fm.record_citizen_rating("DL-2026-T4", 2) == -1.0
    assert fm.record_citizen_rating("DL-2026-T5", 1) == -2.0

    # Verify storage on disk
    with open(TEST_LEDGER_PATH, 'r') as f:
        data = json.load(f)
        assert len(data) == 5
        assert data[0]["reward"] == 1.0
        assert data[4]["reward"] == -2.0

def test_officer_correction_rewards():
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)

    # 1. Correct prediction (match)
    reward_match = fm.calculate_reward(
        predicted={"category": "ROAD", "severity": "HIGH", "confidence": 0.9},
        actual={"category": "ROAD", "severity": "HIGH"}
    )
    assert reward_match == 1.0

    # 2. Incorrect prediction, low confidence (no correction bonus)
    reward_mismatch = fm.calculate_reward(
        predicted={"category": "ROAD", "severity": "HIGH", "confidence": 0.5},
        actual={"category": "WATER", "severity": "HIGH"},
        is_corrected=False
    )
    assert reward_mismatch == -1.0

    # 3. Incorrect prediction, low confidence (WITH correction bonus +0.5)
    reward_corrected_low = fm.calculate_reward(
        predicted={"category": "ROAD", "severity": "HIGH", "confidence": 0.5},
        actual={"category": "WATER", "severity": "HIGH"},
        is_corrected=True
    )
    assert reward_corrected_low == -0.5  # -1.0 + 0.5

    # 4. Incorrect prediction, high confidence (WITH correction bonus +0.5)
    reward_corrected_high = fm.calculate_reward(
        predicted={"category": "ROAD", "severity": "HIGH", "confidence": 0.95},
        actual={"category": "WATER", "severity": "HIGH"},
        is_corrected=True
    )
    assert reward_corrected_high == -1.5  # -2.0 + 0.5

def test_corrupted_ledger_recovery():
    # Create corrupted file
    os.makedirs(os.path.dirname(TEST_LEDGER_PATH), exist_ok=True)
    with open(TEST_LEDGER_PATH, 'w') as f:
        f.write("invalid json { corrupted ledger")

    # Re-instantiating feedback manager should not crash
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)
    assert fm.ledger == []  # should fall back to empty list

    # Operations should still work fine
    assert fm.record_citizen_rating("DL-2026-OK", 5) == 1.0
    assert len(fm.ledger) == 1

def test_rolling_average_rolling_20():
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)

    # Add 25 ratings of 5 stars (reward +1.0) and 5 ratings of 1 star (reward -2.0)
    # Total 30 items
    for i in range(25):
        fm.record_citizen_rating(f"DL-2026-P{i}", 5)
    for i in range(5):
        fm.record_citizen_rating(f"DL-2026-N{i}", 1)

    # get_average_reward(last_n=20) should calculate the average of the last 20 items only.
    # The last 20 items consist of: 15 items of 5 stars (+1.0) + 5 items of 1 star (-2.0).
    # Expected sum = 15*(1.0) + 5*(-2.0) = 15 - 10 = 5.0
    # Expected average = 5.0 / 20 = 0.25
    assert fm.get_average_reward(last_n=20) == 0.25

def test_policy_thresholds():
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)
    policy_engine = DynamicPolicyEngine()
    # Override policy's internal feedback manager to use test ledger path
    policy_engine.feedback_manager = fm

    # State A: Empty ledger -> safe neutral baseline -> returns base threshold 0.75
    assert policy_engine.get_current_policy()["confidence_storage_threshold"] == 0.75

    # State B: Highly accurate trend (> 0.5) -> relax threshold to 0.65
    for _ in range(5):
        fm.record_citizen_rating("DL-2026-GOOD", 5) # reward +1.0
    assert fm.get_average_reward(last_n=20) == 1.0
    assert policy_engine.get_current_policy()["confidence_storage_threshold"] == 0.65

    # State C: Negative trend (< 0.0) -> tighten threshold to 0.85
    # Clear ledger and write negative records
    fm.ledger = []
    fm._save_ledger()
    for _ in range(5):
        fm.record_citizen_rating("DL-2026-BAD", 1) # reward -2.0
    assert fm.get_average_reward(last_n=20) == -2.0
    assert policy_engine.get_current_policy()["confidence_storage_threshold"] == 0.85

def test_concurrent_writes():
    fm = FeedbackManager(ledger_path=TEST_LEDGER_PATH)

    def write_feedback(i):
        fm.record_citizen_rating(f"DL-2026-C{i}", 5)

    num_threads = 20
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(write_feedback, range(num_threads))

    # Verify count on disk matches thread submissions without corruption or dropouts
    with open(TEST_LEDGER_PATH, 'r') as f:
        data = json.load(f)
        assert len(data) == num_threads
        for item in data:
            assert item["reward"] == 1.0
