"""
Unit & Integration Test Suite for AegisRisk AI Risk Manager
Razorpay Buildathon Track 02 (AI Risk Manager)
"""

import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.ml.rto_model import RTORiskEngine
from backend.app.agents.chargeback_agent import ChargebackAutoResponderAgent
from backend.app.ring_detector.graph_sentinel import GraphSentinel


class TestAegisRiskEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = RTORiskEngine()
        cls.engine.load_model("data/rto_model.joblib")
        cls.agent = ChargebackAutoResponderAgent()
        cls.sentinel = GraphSentinel()

    def test_heldout_split_strict_separation(self):
        """Verifies zero data leakage between train and held-out test splits."""
        with open("data/train_set.json", "r", encoding="utf-8") as f:
            train_data = json.load(f)
        with open("data/heldout_test_set.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)

        self.assertEqual(len(train_data), 7500)
        self.assertEqual(len(test_data), 2500)

        train_ids = set(x["order_id"] for x in train_data)
        test_ids = set(x["order_id"] for x in test_data)

        # Ensure complete mutual exclusivity
        intersection = train_ids.intersection(test_ids)
        self.assertEqual(len(intersection), 0, "Test set must have strictly 0 overlap with training data")

    def test_heldout_metrics_validity(self):
        """Validates that held-out test evaluation has genuine metrics and cost curves."""
        with open("data/heldout_metrics.json", "r", encoding="utf-8") as f:
            metrics = json.load(f)

        summary = metrics["summary"]
        self.assertGreater(summary["roc_auc"], 0.70)
        self.assertGreater(summary["pr_auc"], 0.65)
        self.assertGreater(summary["optimal_max_net_savings_inr"], 0)
        self.assertIn("threshold_sweep", metrics)
        self.assertGreater(len(metrics["threshold_sweep"]), 10)

    def test_risk_scoring_behavior(self):
        """Verifies model appropriately ranks high-risk COD vs trusted prepaid order."""
        high_risk_order = {
            "order_id": "ord_test_high_risk",
            "order_amount": 25000.00,
            "category": "Smartphones & Laptops",
            "payment_method": "COD",
            "tier": "Tier-2/3",
            "city": "Patna",
            "state": "Bihar",
            "pincode": "800001",
            "pincode_base_rto": 0.38,
            "address": "Near station, call on reach",
            "address_completeness_score": 0.20,
            "has_house_number": 0,
            "account_age_days": 1,
            "previous_orders": 0,
            "previous_returns": 0,
            "historical_return_rate": 0.0,
            "orders_last_1hr": 4,
            "ip_reputation_score": 0.30,
            "phone_carrier_verified": 0,
            "delivery_attempt_history_score": 0.30,
        }

        trusted_order = {
            "order_id": "ord_test_trusted",
            "order_amount": 1200.00,
            "category": "Beauty & Personal Care",
            "payment_method": "UPI",
            "tier": "Tier-1",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
            "pincode_base_rto": 0.10,
            "address": "Flat 402, Sai Residency, MG Road",
            "address_completeness_score": 0.95,
            "has_house_number": 1,
            "account_age_days": 340,
            "previous_orders": 12,
            "previous_returns": 0,
            "historical_return_rate": 0.0,
            "orders_last_1hr": 1,
            "ip_reputation_score": 0.95,
            "phone_carrier_verified": 1,
            "delivery_attempt_history_score": 0.95,
        }

        res_high = self.engine.score_single_order(high_risk_order)
        res_trusted = self.engine.score_single_order(trusted_order)

        self.assertGreater(res_high["risk_score"], res_trusted["risk_score"])
        self.assertIn(res_high["risk_tier"], ["HIGH", "CRITICAL"])
        self.assertEqual(res_trusted["risk_tier"], "LOW")
        self.assertGreater(len(res_high["drivers"]), 0)

    def test_chargeback_agent_dossier(self):
        """Verifies autonomous chargeback rebuttal generation and evidence assembly."""
        disputes = self.agent.list_disputes()
        self.assertGreaterEqual(len(disputes), 3)

        dossier = self.agent.run_investigation(disputes[0]["dispute_id"])
        self.assertIn("rebuttal_letter", dossier)
        self.assertIn("evidence_checklist", dossier)
        self.assertGreaterEqual(len(dossier["evidence_checklist"]), 4)
        self.assertGreaterEqual(dossier["win_probability"], 80)
        self.assertTrue(dossier["liability_shift_applicable"])

    def test_abuse_ring_sentinel(self):
        """Verifies entity resolution graph detection."""
        rings = self.sentinel.get_abuse_rings()
        self.assertGreaterEqual(len(rings), 2)
        first_ring = rings[0]
        self.assertIn("nodes", first_ring)
        self.assertIn("links", first_ring)
        self.assertGreater(first_ring["estimated_prevented_loss_inr"], 10000)


if __name__ == "__main__":
    unittest.main()
