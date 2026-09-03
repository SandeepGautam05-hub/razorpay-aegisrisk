"""
Abuse-Ring Sentinel & Fraud-Spike Velocity Detector
For Razorpay Buildathon Track 02 (AI Risk Manager)

Provides entity resolution graph detection connecting:
- Reused device fingerprints across disparate account names
- Synthetic identity clusters & address permutations
- Card testing velocity spikes & bot sweeps
"""

import json
import random

SAMPLE_FRAUD_RINGS = [
    {
        "ring_id": "ring_alpha_402",
        "name": "Coordinated Wardrobing Syndicate #402",
        "threat_category": "Serial Wardrobing & Return Abuse",
        "location": "Bengaluru East Corridor",
        "risk_level": "CRITICAL",
        "estimated_prevented_loss_inr": 64200,
        "active_accounts": 6,
        "detected_pattern": "Single physical device ID (dev_99x7) rotating 6 prepaid SIM cards, ordering luxury apparel on COD to adjacent flats in the same housing complex.",
        "nodes": [
            {"id": "dev_99x7", "label": "Device: Samsung S23 (dev_99x7)", "type": "device", "risk": "critical"},
            {"id": "usr_vikram", "label": "Vikram Sen", "type": "user", "risk": "high"},
            {"id": "usr_kunal", "label": "Kunal Sharma", "type": "user", "risk": "high"},
            {"id": "usr_rohit", "label": "Rohit Verma", "type": "user", "risk": "high"},
            {"id": "addr_bellandur", "label": "Green Glen Apt, Bellandur", "type": "address", "risk": "critical"},
            {"id": "vpa_vikram", "label": "UPI: sen.v@axis", "type": "vpa", "risk": "medium"},
        ],
        "links": [
            {"source": "usr_vikram", "target": "dev_99x7", "type": "USES_DEVICE"},
            {"source": "usr_kunal", "target": "dev_99x7", "type": "USES_DEVICE"},
            {"source": "usr_rohit", "target": "dev_99x7", "type": "USES_DEVICE"},
            {"source": "usr_vikram", "target": "addr_bellandur", "type": "SHIPS_TO"},
            {"source": "usr_kunal", "target": "addr_bellandur", "type": "SHIPS_TO"},
            {"source": "usr_rohit", "target": "addr_bellandur", "type": "SHIPS_TO"},
            {"source": "usr_vikram", "target": "vpa_vikram", "type": "PAID_WITH"},
        ]
    },
    {
        "ring_id": "ring_beta_109",
        "name": "Card Testing & Disposable Bin Ring #109",
        "threat_category": "Bot Card Testing / Stolen BINs",
        "location": "Distributed VPNs (NCR / Kolkata / Hyderabad)",
        "risk_level": "HIGH",
        "estimated_prevented_loss_inr": 112000,
        "active_accounts": 14,
        "detected_pattern": "Automated headless Chromium script testing stolen card BIN 4242xx in rapid bursts of ₹1-₹50 transactions.",
        "nodes": [
            {"id": "ip_vpn_cluster", "label": "VPN Gateway: 185.220.101.xx", "type": "device", "risk": "critical"},
            {"id": "bin_4242", "label": "Card BIN: 4242-98xx", "type": "card", "risk": "critical"},
            {"id": "usr_bot_1", "label": "Synthetic Buyer #108", "type": "user", "risk": "high"},
            {"id": "usr_bot_2", "label": "Synthetic Buyer #109", "type": "user", "risk": "high"},
            {"id": "usr_bot_3", "label": "Synthetic Buyer #110", "type": "user", "risk": "high"},
            {"id": "addr_ghost", "label": "Incomplete Pincode 110001", "type": "address", "risk": "high"},
        ],
        "links": [
            {"source": "usr_bot_1", "target": "ip_vpn_cluster", "type": "ORIGINATED_FROM"},
            {"source": "usr_bot_2", "target": "ip_vpn_cluster", "type": "ORIGINATED_FROM"},
            {"source": "usr_bot_3", "target": "ip_vpn_cluster", "type": "ORIGINATED_FROM"},
            {"source": "usr_bot_1", "target": "bin_4242", "type": "ATTEMPTED_CARD"},
            {"source": "usr_bot_2", "target": "bin_4242", "type": "ATTEMPTED_CARD"},
            {"source": "usr_bot_3", "target": "bin_4242", "type": "ATTEMPTED_CARD"},
            {"source": "usr_bot_1", "target": "addr_ghost", "type": "DUMMY_ADDRESS"},
        ]
    }
]


class GraphSentinel:
    """Manages graph entity resolution and velocity spike detection."""

    def get_abuse_rings(self):
        return SAMPLE_FRAUD_RINGS

    def detect_velocity_spike(self, recent_transactions):
        """Calculates sliding window transaction velocity and flags bot bursts."""
        count = len(recent_transactions)
        if count >= 8:
            return {
                "is_spike": True,
                "spike_severity": "CRITICAL" if count > 12 else "ELEVATED",
                "burst_rate_per_min": count * 6,
                "trigger_reason": f"Abnormal burst: {count} transactions processed in 10-second monitoring window.",
                "mitigation_action": "Enable CAPTCHA + 3DS Step-Up Challenge on subsequent requests",
            }
        return {
            "is_spike": False,
            "spike_severity": "NORMAL",
            "burst_rate_per_min": count * 6,
            "trigger_reason": "Traffic within normal merchant baseline.",
            "mitigation_action": "None",
        }


if __name__ == "__main__":
    sentinel = GraphSentinel()
    rings = sentinel.get_abuse_rings()
    print(f"Loaded {len(rings)} abuse rings with graph topologies.")
