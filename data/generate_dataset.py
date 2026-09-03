"""
Synthetic Dataset Generator for Razorpay Buildathon: Track 02 (AI Risk Manager)
Generates realistic Indian e-commerce & BFSI transactions with:
- Strict Train (7,500) vs Held-Out Test (2,500) split
- Real Indian logistics patterns (Tier 1/2/3 pin codes, COD vs UPI vs Cards)
- Address entropy & verification signals
- Customer order history & velocity
"""

import json
import random
import os
import csv
import math

random.seed(42)

CITIES_TIER_1 = [
    ("Mumbai", "Maharashtra", ["400001", "400050", "400076", "400092"], 0.12),
    ("Bengaluru", "Karnataka", ["560001", "560034", "560068", "560102"], 0.10),
    ("Delhi NCR", "Delhi", ["110001", "110020", "110085", "122001"], 0.14),
    ("Hyderabad", "Telangana", ["500001", "500032", "500081", "500034"], 0.11),
    ("Pune", "Maharashtra", ["411001", "411014", "411038", "411057"], 0.12),
    ("Chennai", "Tamil Nadu", ["600001", "600028", "600096", "600040"], 0.11),
]

CITIES_TIER_2_3 = [
    ("Patna", "Bihar", ["800001", "800020", "800013"], 0.38),
    ("Meerut", "Uttar Pradesh", ["250001", "250002", "250103"], 0.36),
    ("Ranchi", "Jharkhand", ["834001", "834002", "834005"], 0.32),
    ("Guwahati", "Assam", ["781001", "781005", "781012"], 0.31),
    ("Indore", "Madhya Pradesh", ["452001", "452010", "452016"], 0.22),
    ("Surat", "Gujarat", ["395001", "395007", "395003"], 0.19),
    ("Aligarh", "Uttar Pradesh", ["202001", "202002"], 0.37),
    ("Muzaffarpur", "Bihar", ["842001", "842002"], 0.42),
]

CATEGORIES = [
    ("Smartphones & Laptops", 18000, 45000, 0.28),
    ("Fashion & Apparel", 1200, 3500, 0.35),
    ("Consumer Electronics & Audio", 1500, 5000, 0.22),
    ("Beauty & Personal Care", 600, 1800, 0.14),
    ("Home & Kitchen", 900, 2800, 0.18),
    ("Luxury Watches & Jewelry", 8000, 25000, 0.38),
]

ADDRESS_TEMPLATES_HIGH_QUALITY = [
    "Flat {flat}, {bldg}, {road}, Near {landmark}",
    "House No. {flat}, 2nd Floor, {bldg}, {road}",
    "Villa {flat}, Green Valley Enclave, {road}, Opp {landmark}",
    "Office #{flat}, Technopark Phase 1, {road}",
]

ADDRESS_TEMPLATES_LOW_QUALITY = [
    "Near banyan tree, post office road",
    "Gali no 3, pass me dukaan",
    "Behind primary school, village post",
    "Near railway station",
    "House behind mandir, call when reach",
    "Main market shop, call me on delivery",
]

ROAD_NAMES = ["MG Road", "Brigade Road", "Link Road", "Ring Road", "Station Road", "Gandhi Nagar 4th Cross", "Civil Lines"]
BUILDINGS = ["Galaxy Apartments", "Sai Residency", "Royal Palms", "Shanti Niketan", "Surya Towers", "Cyber Heights"]
LANDMARKS = ["Apollo Hospital", "Axis Bank ATM", "City Mall", "Metro Pillar 142", "Water Tank", "St. Mary School"]


def generate_single_order(order_idx):
    is_tier_1 = random.random() < 0.55
    if is_tier_1:
        city_info = random.choice(CITIES_TIER_1)
        tier = "Tier-1"
    else:
        city_info = random.choice(CITIES_TIER_2_3)
        tier = "Tier-2/3"

    city, state, pincodes, base_pincode_rto = city_info
    pincode = random.choice(pincodes)

    category, min_price, max_price, cat_risk_factor = random.choice(CATEGORIES)
    order_amount = round(random.uniform(min_price, max_price), 2)

    # Payment method distribution
    pm_roll = random.random()
    if pm_roll < 0.45:
        payment_method = "COD"  # Cash on Delivery
    elif pm_roll < 0.75:
        payment_method = "UPI"
    elif pm_roll < 0.92:
        payment_method = "Credit_Card"
    else:
        payment_method = "Netbanking"

    # Address quality
    addr_quality_roll = random.random()
    if addr_quality_roll < 0.75:
        address = random.choice(ADDRESS_TEMPLATES_HIGH_QUALITY).format(
            flat=random.randint(10, 999),
            bldg=random.choice(BUILDINGS),
            road=random.choice(ROAD_NAMES),
            landmark=random.choice(LANDMARKS),
        )
        address_completeness_score = round(random.uniform(0.70, 1.0), 2)
        has_house_number = 1
    else:
        address = random.choice(ADDRESS_TEMPLATES_LOW_QUALITY)
        address_completeness_score = round(random.uniform(0.15, 0.45), 2)
        has_house_number = 0

    # Customer profile
    is_new_customer = random.random() < 0.40
    if is_new_customer:
        account_age_days = random.randint(0, 7)
        previous_orders = 0
        previous_returns = 0
        historical_return_rate = 0.0
    else:
        account_age_days = random.randint(15, 750)
        previous_orders = random.randint(1, 35)
        # customer loyalty / history
        if random.random() < 0.20:
            # Serial returner
            previous_returns = random.randint(1, previous_orders)
            historical_return_rate = round(previous_returns / previous_orders, 2)
        else:
            previous_returns = 0 if random.random() < 0.7 else 1
            historical_return_rate = round(previous_returns / previous_orders, 2)

    # Device & telemetry signals
    is_device_reused = 1 if random.random() < 0.08 else 0
    orders_last_1hr = random.randint(1, 8) if is_device_reused else random.choices([1, 2, 3], weights=[0.85, 0.12, 0.03])[0]
    ip_reputation_score = round(random.uniform(0.1, 0.4) if is_device_reused else random.uniform(0.7, 0.99), 2)
    phone_carrier_verified = 0 if random.random() < 0.07 else 1
    delivery_attempt_history_score = round(random.uniform(0.3, 0.6) if tier == "Tier-2/3" and payment_method == "COD" else random.uniform(0.7, 1.0), 2)

    # Calculate actual ground-truth risk logit (defense-oriented loss probability)
    risk_score = 0.0
    
    # Base risk by payment method
    if payment_method == "COD":
        risk_score += 0.35
    elif payment_method == "Credit_Card":
        risk_score += 0.06
    elif payment_method == "UPI":
        risk_score += 0.03
    else:
        risk_score += 0.04

    # Geography
    risk_score += (base_pincode_rto * 0.45)

    # Address quality
    risk_score += (1.0 - address_completeness_score) * 0.28
    if not has_house_number:
        risk_score += 0.12

    # Customer profile
    if is_new_customer and payment_method == "COD":
        risk_score += 0.18
    elif historical_return_rate > 0.4:
        risk_score += (historical_return_rate * 0.35)
    elif previous_orders > 3 and historical_return_rate == 0.0:
        risk_score -= 0.15

    # Velocity and device
    if orders_last_1hr > 3:
        risk_score += 0.25
    if ip_reputation_score < 0.4:
        risk_score += 0.15
    if not phone_carrier_verified:
        risk_score += 0.15

    # Category and high amount COD
    if payment_method == "COD" and order_amount > 10000:
        risk_score += 0.22

    # Sigmoid to normalize to [0, 1] probability
    prob = 1.0 / (1.0 + math.exp(-3.5 * (risk_score - 0.48)))
    
    # Ground truth loss label (with slight natural noise)
    is_loss = 1 if (random.random() < prob) else 0

    return {
        "order_id": f"ord_{100000 + order_idx}",
        "customer_id": f"cust_{random.randint(1000, 9999)}",
        "order_amount": order_amount,
        "category": category,
        "payment_method": payment_method,
        "tier": tier,
        "city": city,
        "state": state,
        "pincode": pincode,
        "pincode_base_rto": base_pincode_rto,
        "address": address,
        "address_completeness_score": address_completeness_score,
        "has_house_number": has_house_number,
        "account_age_days": account_age_days,
        "previous_orders": previous_orders,
        "previous_returns": previous_returns,
        "historical_return_rate": historical_return_rate,
        "orders_last_1hr": orders_last_1hr,
        "ip_reputation_score": ip_reputation_score,
        "phone_carrier_verified": phone_carrier_verified,
        "delivery_attempt_history_score": delivery_attempt_history_score,
        "is_loss": is_loss,
        "ground_truth_prob": round(prob, 4),
    }


def generate_all():
    TOTAL_SAMPLES = 10000
    TRAIN_RATIO = 0.75
    
    orders = [generate_single_order(i) for i in range(TOTAL_SAMPLES)]
    
    train_count = int(TOTAL_SAMPLES * TRAIN_RATIO)
    train_orders = orders[:train_count]
    heldout_test_orders = orders[train_count:]
    
    os.makedirs("data", exist_ok=True)
    
    with open("data/train_set.json", "w", encoding="utf-8") as f:
        json.dump(train_orders, f, indent=2)
        
    with open("data/heldout_test_set.json", "w", encoding="utf-8") as f:
        json.dump(heldout_test_orders, f, indent=2)

    keys = list(heldout_test_orders[0].keys())
    with open("data/heldout_test_set.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(heldout_test_orders)

    print(f"Generated {TOTAL_SAMPLES} total records.")
    print(f"Train set: {len(train_orders)} samples -> data/train_set.json")
    print(f"Held-out test set: {len(heldout_test_orders)} samples -> data/heldout_test_set.json & data/heldout_test_set.csv")
    
    train_loss_rate = sum(x["is_loss"] for x in train_orders) / len(train_orders)
    test_loss_rate = sum(x["is_loss"] for x in heldout_test_orders) / len(heldout_test_orders)
    print(f"Train loss incidence: {train_loss_rate*100:.1f}%")
    print(f"Held-out test loss incidence: {test_loss_rate*100:.1f}%")

if __name__ == "__main__":
    generate_all()
