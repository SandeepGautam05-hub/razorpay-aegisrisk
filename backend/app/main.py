"""
Starlette REST API for AegisRisk AI Risk Manager
Razorpay Buildathon Track 02 (AI Risk Manager)
"""

import json
import os
import sys
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.ml.rto_model import RTORiskEngine
from backend.app.agents.chargeback_agent import ChargebackAutoResponderAgent
from backend.app.ring_detector.graph_sentinel import GraphSentinel

# Initialize engines
risk_engine = RTORiskEngine()
risk_engine.load_model("data/rto_model.joblib")

chargeback_agent = ChargebackAutoResponderAgent()
graph_sentinel = GraphSentinel()


async def health(request):
    return JSONResponse({
        "status": "healthy",
        "service": "Razorpay AegisRisk AI Risk Manager",
        "track": "Track 02: AI Risk Manager",
        "model_loaded": risk_engine.model is not None,
    })


async def get_heldout_metrics(request):
    """Returns exact precision, recall, ROC-AUC, and cost-matrix on held-out test set."""
    metrics_path = "data/heldout_metrics.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    else:
        # Run on the fly if not yet trained
        data = risk_engine.train_and_evaluate()
        return JSONResponse(data)


async def score_order(request):
    """Scores single order for RTO & return abuse with explainability."""
    try:
        payload = await request.json()
    except Exception:
        payload = {
            "order_id": "ord_live_demo",
            "order_amount": 3499.00,
            "category": "Smartphones & Laptops",
            "payment_method": "COD",
            "tier": "Tier-2/3",
            "city": "Patna",
            "state": "Bihar",
            "pincode": "800001",
            "pincode_base_rto": 0.38,
            "address": "Near Gandhi Maidan, call on reach",
            "address_completeness_score": 0.30,
            "has_house_number": 0,
            "account_age_days": 2,
            "previous_orders": 0,
            "previous_returns": 0,
            "historical_return_rate": 0.0,
            "orders_last_1hr": 2,
            "ip_reputation_score": 0.65,
            "phone_carrier_verified": 1,
            "delivery_attempt_history_score": 0.50,
        }

    res = risk_engine.score_single_order(payload)
    return JSONResponse(res)


async def list_disputes(request):
    """Returns active disputes awaiting merchant response."""
    disputes = chargeback_agent.list_disputes()
    return JSONResponse(disputes)


async def generate_chargeback_dossier(request):
    """Autonomous agent that generates a formal bank rebuttal and evidence package."""
    try:
        payload = await request.json()
        dispute_id = payload.get("dispute_id", "dp_9872145A")
    except Exception:
        dispute_id = "dp_9872145A"

    dossier = chargeback_agent.run_investigation(dispute_id)
    return JSONResponse(dossier)


async def get_abuse_rings(request):
    """Returns entity resolution graph nodes and clusters."""
    rings = graph_sentinel.get_abuse_rings()
    return JSONResponse(rings)


async def simulate_stream(request):
    """Simulates live incoming transactions with mixed risk signals."""
    import random
    from data.generate_dataset import generate_single_order
    samples = [generate_single_order(random.randint(1000, 99999)) for _ in range(8)]
    scored = [risk_engine.score_single_order(s) for s in samples]
    return JSONResponse(scored)


async def index(request):
    """Serves the Merchant Command Center browser application."""
    index_path = os.path.join(os.path.dirname(__file__), "../../static/index.html")
    if not os.path.exists(index_path):
        index_path = "static/index.html"
    return FileResponse(index_path)


routes = [
    Route("/", index, methods=["GET"]),
    Route("/dashboard", index, methods=["GET"]),
    Route("/api/health", health, methods=["GET"]),
    Route("/api/metrics/heldout-evaluation", get_heldout_metrics, methods=["GET"]),
    Route("/api/score-order", score_order, methods=["POST"]),
    Route("/api/chargeback/disputes", list_disputes, methods=["GET"]),
    Route("/api/chargeback/generate-dossier", generate_chargeback_dossier, methods=["POST"]),
    Route("/api/network/abuse-rings", get_abuse_rings, methods=["GET"]),
    Route("/api/stream/simulate", simulate_stream, methods=["GET", "POST"]),
    Mount("/static", StaticFiles(directory="static"), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
