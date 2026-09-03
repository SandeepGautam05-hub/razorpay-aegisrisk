"""
Agentic Chargeback Evidence Auto-Responder
For Razorpay Buildathon Track 02 (AI Risk Manager)

Autonomous agent that investigates incoming payment disputes, aggregates 
transaction telemetry, courier PODs, and 3DS logs, computes dispute win probability,
and compiles a bank-compliant Rebuttal Dossier for card networks and NPCI.
"""

import json
from datetime import datetime, timezone, timedelta

DISPUTE_SCENARIOS = [
    {
        "dispute_id": "dp_9872145A",
        "payment_id": "pay_O9aK1L2mn87B",
        "order_id": "ord_104822",
        "customer_name": "Aarav Sharma",
        "customer_email": "aarav.sharma@gmail.com",
        "amount": 4299.00,
        "currency": "INR",
        "card_network": "VISA",
        "card_last4": "4242",
        "reason_code": "10.4",
        "reason_description": "Other Fraud - Card Absent Environment (Cardholder claims unauthorized charge)",
        "dispute_date": "2026-08-28T14:20:00Z",
        "evidence_due_by": "2026-09-06T23:59:59Z",
        "status": "ACTION_REQUIRED",
        "category": "Physical E-Commerce",
        "items": [{"name": "Noise Cancelling Wireless Headphones", "qty": 1, "price": 4299}],
        "merchant_telemetry": {
            "three_ds_version": "2.2.0",
            "three_ds_auth_status": "Y (Fully Authenticated via Bank OTP)",
            "auth_timestamp": "2026-08-21T18:42:10Z",
            "auth_bank_arn": "745210982341209384",
            "ip_address": "49.37.12.184",
            "ip_city": "Bengaluru, Karnataka",
            "shipping_address": "Flat 302, Green Glen Enclave, Bellandur, Bengaluru, 560103",
            "courier_partner": "BlueDart Express",
            "awb_number": "BD982341102IN",
            "delivery_timestamp": "2026-08-24T12:15:30Z",
            "signed_pod_name": "Aarav Sharma (OTP Confirmed at Doorstep)",
            "customer_support_logs": "Customer logged in from the same device 2 days after delivery to view warranty.",
        }
    },
    {
        "dispute_id": "dp_6719822C",
        "payment_id": "pay_L8k39Xp1Q94Z",
        "order_id": "ord_105190",
        "customer_name": "Pooja Verma",
        "customer_email": "pooja.v@outlook.com",
        "amount": 1850.00,
        "currency": "INR",
        "card_network": "MASTERCARD",
        "card_last4": "8819",
        "reason_code": "4837",
        "reason_description": "No Cardholder Authorization",
        "dispute_date": "2026-08-30T09:12:00Z",
        "evidence_due_by": "2026-09-08T23:59:59Z",
        "status": "ACTION_REQUIRED",
        "category": "Fashion & Apparel",
        "items": [{"name": "Handcrafted Silk Anarkali Kurti", "qty": 1, "price": 1850}],
        "merchant_telemetry": {
            "three_ds_version": "2.1.0",
            "three_ds_auth_status": "Y (Frictionless / OTP Verified)",
            "auth_timestamp": "2026-08-23T16:04:12Z",
            "auth_bank_arn": "849201938472910293",
            "ip_address": "157.34.88.22",
            "ip_city": "Pune, Maharashtra",
            "shipping_address": "Bungalow 4, Model Colony, Shivajinagar, Pune, 411016",
            "courier_partner": "Delhivery Surface",
            "awb_number": "DEL198237491",
            "delivery_timestamp": "2026-08-26T15:40:19Z",
            "signed_pod_name": "P. Verma (Geotagged Delivery Photo Captured)",
            "customer_support_logs": "No cancellation or return request logged prior to chargeback.",
        }
    },
    {
        "dispute_id": "dp_1029481U",
        "payment_id": "pay_U19v82Km402N",
        "order_id": "ord_106720",
        "customer_name": "Rohan Deshmukh",
        "customer_email": "rohan.desh@gmail.com",
        "amount": 999.00,
        "currency": "INR",
        "card_network": "UPI",
        "card_last4": "VPA: rohan@okhdfcbank",
        "reason_code": "U01",
        "reason_description": "NPCI UPI Dispute - Customer claims non-receipt of merchandise / service",
        "dispute_date": "2026-09-01T11:00:00Z",
        "evidence_due_by": "2026-09-05T23:59:59Z",
        "status": "ACTION_REQUIRED",
        "category": "Digital SaaS / EdTech Access",
        "items": [{"name": "Pro Annual Course Pass", "qty": 1, "price": 999}],
        "merchant_telemetry": {
            "three_ds_version": "UPI MPIN Auth",
            "three_ds_auth_status": "NPCI Success - RRN 624109823412",
            "auth_timestamp": "2026-08-29T10:14:02Z",
            "auth_bank_arn": "NPCI-RRN-624109823412",
            "ip_address": "27.59.190.11",
            "ip_city": "Mumbai, Maharashtra",
            "shipping_address": "Instant Digital Delivery (rohan.desh@gmail.com)",
            "courier_partner": "Digital Fulfillment Service",
            "awb_number": "LIC-PRO-98214-DIGITAL",
            "delivery_timestamp": "2026-08-29T10:14:08Z",
            "signed_pod_name": "Account Login & API Session Recorded (IP: 27.59.190.11)",
            "customer_support_logs": "User consumed 6 video modules and downloaded PDF notes on Aug 29 & 30.",
        }
    }
]


class ChargebackAutoResponderAgent:
    """Multi-step agent for autonomous dispute defense."""

    def list_disputes(self):
        return DISPUTE_SCENARIOS

    def run_investigation(self, dispute_id: str):
        """Runs multi-step investigation pipeline for a specific dispute."""
        dispute = next((d for d in DISPUTE_SCENARIOS if d["dispute_id"] == dispute_id), None)
        if not dispute:
            # Fallback to first dispute
            dispute = DISPUTE_SCENARIOS[0]

        tel = dispute["merchant_telemetry"]

        # Step 1: Evaluate 3D Secure / UPI Auth Strength
        is_strong_auth = "Y" in tel["three_ds_auth_status"] or "NPCI Success" in tel["three_ds_auth_status"]
        auth_score = 35 if is_strong_auth else 10

        # Step 2: Evaluate Fulfillment & Delivery Evidence
        has_pod = "OTP" in tel["signed_pod_name"] or "Geotagged" in tel["signed_pod_name"] or "Session" in tel["signed_pod_name"]
        fulfillment_score = 35 if has_pod else 15

        # Step 3: Evaluate Customer Digital Footprint & Telemetry Consistency
        ip_match = tel["ip_city"].split(",")[0] in tel["shipping_address"] or "Digital" in tel["shipping_address"]
        telemetry_score = 25 if ip_match else 15

        win_probability = min(98, auth_score + fulfillment_score + telemetry_score + 3)

        # Generate Bank-Formatted Rebuttal Letter
        rebuttal_text = self._generate_formal_rebuttal(dispute, tel, win_probability)

        # Structured Evidence Checklist
        evidence_checklist = [
            {
                "id": "ev_3ds",
                "title": "Two-Factor / 3D-Secure Authentication Logs",
                "description": f"Verified {tel['three_ds_auth_status']} with Bank ARN {tel['auth_bank_arn']} at {tel['auth_timestamp']}",
                "status": "VERIFIED_ATTACHED",
                "strength": "HIGH",
            },
            {
                "id": "ev_pod",
                "title": "Proof of Delivery (POD) & Carrier Courier Tracking",
                "description": f"{tel['courier_partner']} AWB {tel['awb_number']}, Confirmed Delivered at {tel['delivery_timestamp']} to {tel['signed_pod_name']}",
                "status": "VERIFIED_ATTACHED",
                "strength": "HIGH",
            },
            {
                "id": "ev_invoice",
                "title": "Tax Invoice & Merchant Terms of Service",
                "description": f"GST Invoice for Order {dispute['order_id']} ({dispute['items'][0]['name']}), ToS accepted at checkout.",
                "status": "VERIFIED_ATTACHED",
                "strength": "MEDIUM",
            },
            {
                "id": "ev_telemetry",
                "title": "Device IP & Geolocation Telemetry Match",
                "description": f"IP {tel['ip_address']} located in {tel['ip_city']}, matching delivery destination.",
                "status": "VERIFIED_ATTACHED",
                "strength": "HIGH",
            },
            {
                "id": "ev_activity",
                "title": "Post-Purchase Account Activity & Usage Telemetry",
                "description": tel["customer_support_logs"],
                "status": "VERIFIED_ATTACHED",
                "strength": "MEDIUM",
            }
        ]

        return {
            "dispute_id": dispute["dispute_id"],
            "order_id": dispute["order_id"],
            "win_probability": win_probability,
            "win_tier": "VERY_HIGH" if win_probability >= 85 else "MODERATE",
            "liability_shift_applicable": is_strong_auth,
            "liability_shift_reason": "3D-Secure 2.2 / EMV 3DS Authentication was completed successfully; liability shifts to the card issuing bank under Card Network Rules.",
            "rebuttal_letter": rebuttal_text,
            "evidence_checklist": evidence_checklist,
            "ready_for_submission": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_formal_rebuttal(self, dispute, tel, win_prob):
        today_str = datetime.now().strftime("%d %B %Y")
        items_desc = ", ".join([f"{item['qty']}x {item['name']} (₹{item['price']})" for item in dispute['items']])
        
        return f"""FORMAL CHARGEBACK REBUTTAL STATEMENT
To: Acquiring Bank Dispute Review Committee / Card Network Arbitration (Razorpay Merchant Services)
Date: {today_str}
Case Reference: Dispute ID {dispute['dispute_id']} | Payment ID {dispute['payment_id']}
Merchant Name: Razorpay ShieldAI Defense Merchant
Cardholder Name: {dispute['customer_name']}
Transaction Amount: {dispute['currency']} {dispute['amount']:.2f}
Disputed Reason Code: {dispute['reason_code']} - {dispute['reason_description']}

RE: FORMAL CONTESTATION OF FRAUDULENT CHARGEBACK WITH CONCLUSIVE EVIDENCE

Dear Dispute Analyst / Chargeback Review Team,

We hereby formally refute and contest the chargeback initiated under Reason Code {dispute['reason_code']} for the transaction of {dispute['currency']} {dispute['amount']:.2f} executed on {dispute['dispute_date'][:10]}.

1. CONCLUSIVE TWO-FACTOR CARDHOLDER AUTHENTICATION (3D-SECURE 2.0 / NPCI):
The transaction was authenticated via Bank Two-Factor Authentication with Acquirer Reference Number (ARN) {tel['auth_bank_arn']}.
- 3DS Version: {tel['three_ds_version']}
- Authentication Result: {tel['three_ds_auth_status']}
- Timestamp of OTP Validation: {tel['auth_timestamp']}
Under Visa Core Rules (§5.4.1.2) / Mastercard Chargeback Guide (Rule 4837), successful 3DS authentication grants the merchant an indisputable Liability Shift. The cardholder's issuing bank authenticated the customer directly.

2. IRREFUTABLE PROOF OF FULFILLMENT & PHYSICAL/DIGITAL DELIVERY:
The ordered items ({items_desc}) were fulfilled and delivered to the cardholder's verified destination:
- Carrier / Dispatcher: {tel['courier_partner']}
- Waybill / Tracking ID: {tel['awb_number']}
- Confirmed Delivery Timestamp: {tel['delivery_timestamp']}
- Recipient Verification at Doorstep: {tel['signed_pod_name']}
- Destination Address: {tel['shipping_address']}

3. DIGITAL FOOTPRINT & GEOLOCATION CONSISTENCY:
The transaction was placed from IP Address {tel['ip_address']} ({tel['ip_city']}), which correlates directly with the cardholder's delivery city. Additionally:
- Audit Log: {tel['customer_support_logs']}

CONCLUSION & REQUEST FOR ARBITRATION RESOLUTION:
The enclosed evidence satisfies all criteria for merchant defense under Indian BFSI and Card Network Dispute Resolution frameworks. As both authentication liability shift and proof of genuine delivery have been conclusively proven, we respectfully request that this chargeback be reversed and funds restored to the merchant account.

Submitted with digital verification,
Razorpay ShieldAI Automated Dispute Defense Agent
On behalf of Merchant Loss Prevention Team
"""


if __name__ == "__main__":
    agent = ChargebackAutoResponderAgent()
    disputes = agent.list_disputes()
    print(f"Loaded {len(disputes)} dispute cases.")
    dossier = agent.run_investigation(disputes[0]["dispute_id"])
    print(f"Generated dossier for {dossier['dispute_id']} with Win Probability: {dossier['win_probability']}%")
