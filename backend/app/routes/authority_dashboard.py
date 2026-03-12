from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.authority_model import Authority
from app.models.farmer_model import Farmer
from app.models.vet_model import Vet
from app.models.animal_model import Animal
from app.models.treatment_model import Treatment
from app.utils.responses import success_response, error_response

authority_dashboard_bp = Blueprint("authority_dashboard", __name__)


# -----------------------------------------------------------
# ROLE CHECK HELPER
# -----------------------------------------------------------
def authority_required(roles=None):
    def wrapper(fn):
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity()
            authority = Authority.objects(id=user_id).first()

            if not authority:
                return error_response("Unauthorized: not an authority user", 403)

            if roles and authority.role not in roles:
                return error_response("Access denied: insufficient permissions", 403)

            return fn(*args, **kwargs)
        return decorated
    return wrapper


# -----------------------------------------------------------
# 1) DASHBOARD OVERVIEW COUNTS
# -----------------------------------------------------------
@authority_dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
# @authority_required(roles=["admin", "dashboard_viewer", "verifier"])
def dashboard_overview():
    return success_response({
        "total_farmers": Farmer.objects.count(),
        "total_veterinarians": Vet.objects.count(),
        "total_animals": Animal.objects.count(),
        "total_treatments": Treatment.objects.count(),
        "pending_verifications": Farmer.objects(is_verified=False).count()
    }, 200)


# -----------------------------------------------------------
# 2) LIST ALL FARMERS (Admin / Verifier)
# -----------------------------------------------------------
@authority_dashboard_bp.route('/farmers', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "verifier", "dashboard_viewer"])
def list_farmers():
    farmers = Farmer.objects.all()
    resp = []

    for f in farmers:
        x = f.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 3) LIST ALL VETS
# -----------------------------------------------------------
@authority_dashboard_bp.route('/vets', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "verifier", "dashboard_viewer"])
def list_vets():
    vets = Vet.objects.all()
    resp = []

    for v in vets:
        x = v.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 4) LIST ALL ANIMALS
# -----------------------------------------------------------
@authority_dashboard_bp.route('/animals', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "dashboard_viewer"])
def list_animals():
    animals = Animal.objects.all()
    resp = []

    for a in animals:
        x = a.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        x["farmer"] = str(a.farmer.id)
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 5) ALL TREATMENTS (with filters)
# -----------------------------------------------------------
@authority_dashboard_bp.route('/treatments', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "dashboard_viewer", "verifier"])
def list_treatments():
    status = request.args.get("status")
    farmer_id = request.args.get("farmer_id")
    vet_id = request.args.get("vet_id")

    query = {}

    if status:
        query["status"] = status
    if farmer_id:
        query["farmer"] = farmer_id
    if vet_id:
        query["vet"] = vet_id

    treatments = Treatment.objects(**query)
    resp = []

    for t in treatments:
        x = t.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        x["farmer"] = str(t.farmer.id)
        x["animal"] = str(t.animal.id)
        x["vet"] = str(t.vet.id) if t.vet else None
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 6) PENDING FARMER VERIFICATIONS
# -----------------------------------------------------------
@authority_dashboard_bp.route('/pending-verifications', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "verifier"])
def pending_verifications():
    pending = Farmer.objects(is_verified=False)
    resp = []

    for f in pending:
        x = f.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 7) VERIFY A FARMER
# -----------------------------------------------------------
@authority_dashboard_bp.route('/verify-farmer/<farmer_id>', methods=['PUT'])
@jwt_required()
# @authority_required(roles=["admin", "verifier"])
def verify_farmer(farmer_id):
    farmer = Farmer.objects(id=farmer_id).first()
    if not farmer:
        return error_response("Farmer not found", 404)

    farmer.is_verified = True
    farmer.save()

    return success_response({"message": "Farmer verified successfully"}, 200)


# -----------------------------------------------------------
# 8) WITHDRAWAL VIOLATION CHECKER
# -----------------------------------------------------------
@authority_dashboard_bp.route('/violations', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "dashboard_viewer", "verifier"])
def withdrawal_violations():
    violations = Treatment.objects(is_flagged_violation=True)

    resp = []
    for v in violations:
        x = v.to_mongo().to_dict()
        x["_id"] = str(x["_id"])
        resp.append(x)

    return success_response(resp, 200)


# -----------------------------------------------------------
# 9) MEDICINE USAGE STATS (Top medicines used)
# -----------------------------------------------------------
@authority_dashboard_bp.route('/stats/medicine-usage', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "dashboard_viewer"])
def medicine_usage_stats():
    pipeline = [
        {"$unwind": "$medicines"},
        {"$group": {"_id": "$medicines.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    results = Treatment.objects.aggregate(pipeline)
    stats = [{"medicine": r["_id"], "count": r["count"]} for r in results]

    return success_response(stats, 200)


# -----------------------------------------------------------
# 10) DAILY TREATMENT COUNT
# -----------------------------------------------------------
from datetime import datetime, timedelta

@authority_dashboard_bp.route('/stats/daily-treatments', methods=['GET'])
@jwt_required()
@authority_required(roles=["admin", "dashboard_viewer"])
def daily_treatments():
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    count = Treatment.objects(
        treatment_start_date__gte=today,
        treatment_start_date__lt=tomorrow
    ).count()

    return success_response({"today_treatments": count}, 200)
