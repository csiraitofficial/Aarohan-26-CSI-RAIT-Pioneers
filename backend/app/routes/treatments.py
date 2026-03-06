from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from mongoengine.queryset.visitor import Q

from app.utils.responses import success_response, error_response
from app.models.treatments import Treatment, MedicineDetail
from app.models.farmers import Farmer
from app.models.vets import Vet
from app.models.animals import Animal
from app.services.withdrawal_service import WithdrawalService
from app.models.authorized_medicine import AuthorizedMedicine
from app.models.prescribed_medicine import PrescribedMedicine
from app.models.authorized_medicine import AuthorizedMedicine
from app.models.prescribed_medicine import PrescribedMedicine
from app.services.withdrawal_service import WithdrawalService
from datetime import datetime

treatments_bp = Blueprint("treatments", __name__)

# ------------------------------------------------------------
# 1) FARMER CREATES TREATMENT REQUEST
# ------------------------------------------------------------
@treatments_bp.route('/request', methods=['POST'])
@jwt_required()
def create_treatment_request():
    print("\n[TREATMENT] create_treatment_request CALLED")

    data = request.get_json() or {}
    farmer_id = get_jwt_identity()
    print(f"[TREATMENT] farmer_id = {farmer_id}")

    farmer = Farmer.objects(id=farmer_id).first()
    if not farmer:
        print("[TREATMENT] ERROR: Not a farmer")
        return error_response("Only farmers can create treatment requests", 403)

    required_fields = ["animal_id", "symptoms"]
    if not all(data.get(f) for f in required_fields):
        print("[TREATMENT] ERROR: Missing fields")
        return error_response("Missing fields", 400)

    animal = Animal.objects(id=data["animal_id"], farmer=farmer).first()
    if not animal:
        print("[TREATMENT] ERROR: Animal not found or not owned by farmer")
        return error_response("Animal not found", 403)

    treatment = Treatment(
        farmer=farmer,
        animal=animal,
        #diagnosis=data["diagnosis"],
        symptoms=data.get("symptoms", []),
        notes=data.get("notes"),
        medicines=[],
        status="pending"
    ).save()

    animal.treatment_ids.append(str(treatment.id))
    animal.save()

    print(f"[TREATMENT] Treatment request created: {treatment.id}")
    return success_response(treatment.to_json(), 201)

# ------------------------------------------------------------
# 2) GET A SINGLE TREATMENT
# ------------------------------------------------------------

@treatments_bp.route('/<treatment_id>', methods=['GET'])
@jwt_required()
def get_treatment(treatment_id):
    print(f"\n[TREATMENT] get_treatment CALLED: {treatment_id}")

    user_id = get_jwt_identity()
    treatment = Treatment.objects(id=treatment_id).first()

    if not treatment:
        return error_response("Treatment not found", 404)

    farmer = Farmer.objects(id=user_id).first()
    vet = Vet.objects(id=user_id).first()

    if farmer and str(treatment.farmer.id) != str(farmer.id):
        return error_response("Not allowed", 403)

    if vet:
        if treatment.vet and str(treatment.vet.id) != str(vet.id):
            return error_response("Not allowed", 403)
        if not treatment.vet and treatment.status != "pending":
            return error_response("Not allowed", 403)

    # ✅ BUILD MEDICINES WITH NAMES
    medicines_response = []
    for pm in treatment.medicines:
        medicines_response.append({
            "medicine_id": str(pm.medicine.id),
            "medicine_name": pm.medicine.name,   # ✅ FIX
            "dosage": pm.dosage,
            "frequency": pm.frequency,
            "duration_days": pm.duration_days,
            "withdrawal_period_days": pm.withdrawal_period_days
        })

    response = {
        "treatment_id": str(treatment.id),
        "status": treatment.status,
        "symptoms": treatment.symptoms,
        "notes": treatment.notes,
        "animal_id": str(treatment.animal.id),
        "vet_id": str(treatment.vet.id) if treatment.vet else None,
        "medicines": medicines_response,
        "is_withdrawal_completed": treatment.is_withdrawal_completed,
        "is_flagged_violation": treatment.is_flagged_violation,
        "created_at": treatment.created_at,
        "updated_at": treatment.updated_at,
    }

    return success_response(response, 200)




# ------------------------------------------------------------
# 3) VET DIAGNOSES TREATMENT (CRITICAL LOGIC)
# ------------------------------------------------------------


@treatments_bp.route('/<treatment_id>/diagnose', methods=['PUT'])
@jwt_required()
def diagnose_treatment(treatment_id):
    print(f"\n[TREATMENT] diagnose_treatment CALLED: {treatment_id}")

    data = request.get_json() or {}
    vet_id = get_jwt_identity()

    # -----------------------------
    # AUTH CHECK
    # -----------------------------
    vet = Vet.objects(id=vet_id).first()
    if not vet:
        return error_response("Only vets can diagnose", 403)

    treatment = Treatment.objects(id=treatment_id).first()
    if not treatment:
        return error_response("Treatment not found", 404)

    if treatment.status != "pending":
        return error_response("Already diagnosed", 400)

    medicines_input = data.get("medicines")
    if not medicines_input or not isinstance(medicines_input, list):
        return error_response("Medicines list required", 400)

    prescribed = []
    max_withdrawal_days = 0  # 🔴 STRICTEST RULE (IMPORTANT)

    # -----------------------------
    # PROCESS MEDICINES
    # -----------------------------
    for m in medicines_input:
        medicine_id = m.get("medicine_id")
        if not medicine_id:
            return error_response("medicine_id is required", 400)

        authorized = AuthorizedMedicine.objects(id=medicine_id).first()
        if not authorized:
            return error_response("Unauthorized medicine selected", 400)

        vet_days = m.get("vet_withdrawal_days")

        # -----------------------------
        # SAFETY WITHDRAWAL FORMULA
        # -----------------------------
        final_withdrawal_days = authorized.withdrawal_period_days

        if vet_days is not None:
            if vet_days < authorized.withdrawal_period_days:
                print(
                    f"[SAFETY] Vet tried to reduce withdrawal "
                    f"({vet_days} < {authorized.withdrawal_period_days}) → BLOCKED"
                )
                final_withdrawal_days = authorized.withdrawal_period_days
            else:
                final_withdrawal_days = vet_days

        print(
            f"[MEDICINE] {authorized.name}: "
            f"authorized={authorized.withdrawal_period_days}, "
            f"vet={vet_days}, "
            f"final={final_withdrawal_days}"
        )

        prescribed.append(
            PrescribedMedicine(
                medicine=authorized,               
                dosage=authorized.dosage,
                frequency=authorized.frequency,
                duration_days=authorized.duration_days,
                withdrawal_period_days=final_withdrawal_days
            )
        )

        max_withdrawal_days = max(max_withdrawal_days, final_withdrawal_days)

    # -----------------------------
    # SAVE TREATMENT
    # -----------------------------
    treatment.vet = vet
    treatment.medicines = prescribed
    treatment.notes = data.get("notes")
    treatment.status = "diagnosed"
    treatment.treatment_start_date = datetime.utcnow()
    treatment.save()

    # -----------------------------
    # CREATE WITHDRAWAL ALERT
    # -----------------------------
    WithdrawalService.create_withdrawal_alert(
        treatment_id=str(treatment.id),
        animal_id=str(treatment.animal.id),
        withdrawal_days=max_withdrawal_days
    )

    print(
        f"[WITHDRAWAL] Final withdrawal applied = {max_withdrawal_days} days "
        f"(strictest medicine rule)"
    )

    # -----------------------------
    # RESPONSE WITH MEDICINE NAMES
    # -----------------------------
    medicines_response = []
    for pm in treatment.medicines:
        medicines_response.append({
            "medicine_id": str(pm.medicine.id),
            "medicine_name": pm.medicine.name,
            "dosage": pm.dosage,
            "frequency": pm.frequency,
            "duration_days": pm.duration_days,
            "withdrawal_period_days": pm.withdrawal_period_days
        })
    print(medicines_response)

    response = {
        "treatment_id": str(treatment.id),
        "status": treatment.status,
        "diagnosis": treatment.diagnosis,
        "animal_id": str(treatment.animal.id),
        "vet_id": str(vet.id),
        "treatment_start_date": treatment.treatment_start_date,
        "notes": treatment.notes,
        "medicines": medicines_response,
        "final_withdrawal_days": max_withdrawal_days
    }

    return success_response(response, 200)

# ------------------------------------------------------------
# 4) GET ALL TREATMENTS FOR AN ANIMAL
# ------------------------------------------------------------
@treatments_bp.route('/animal/<animal_id>', methods=['GET'])
@jwt_required()
def get_treatments_by_animal(animal_id):
    print(f"\n[TREATMENT] get_treatments_by_animal CALLED: {animal_id}")

    user_id = get_jwt_identity()
    farmer = Farmer.objects(id=user_id).first()
    vet = Vet.objects(id=user_id).first()

    animal = Animal.objects(id=animal_id).first()
    if not animal:
        return error_response("Animal not found", 404)

    if farmer and str(animal.farmer.id) != str(farmer.id):
        return error_response("Not allowed", 403)

    query = Q(animal=animal)
    if vet:
        query &= (Q(vet=vet) | Q(status="pending"))

    treatments = Treatment.objects(query)
    print(f"[TREATMENT] treatments found = {treatments.count()}")

    return success_response([t.to_json() for t in treatments], 200)


# ------------------------------------------------------------
# 5) GET ALL TREATMENTS FOR A FARMER (VET ONLY)
# ------------------------------------------------------------
@treatments_bp.route('/farmer/<farmer_id>', methods=['GET'])
@jwt_required()
def get_treatments_by_farmer(farmer_id):
    print(f"\n[TREATMENT] get_treatments_by_farmer CALLED: {farmer_id}")

    user_id = get_jwt_identity()

    # ✅ Only vets allowed
    vet = Vet.objects(id=user_id).first()
    if not vet:
        return error_response("Only veterinarians can access this", 403)

    farmer = Farmer.objects(id=farmer_id).first()
    if not farmer:
        return error_response("Farmer not found", 404)

    query = Q(farmer=farmer) & (Q(status="pending") | Q(vet=vet))
    treatments = Treatment.objects(query).order_by("-created_at")

    print(f"[TREATMENT] treatments found = {treatments.count()}")

    data = []
    for t in treatments:
        data.append({
            "treatment_id": str(t.id),
            "status": t.status,

            # ✅ SAFE ONLY
            "animal_id": str(t.animal.id) if t.animal else None,

            "symptoms": t.symptoms,
            "notes": t.notes,
            "created_at": t.created_at,
            "diagnosed_by_vet": bool(t.vet),
        })

    return success_response(data, 200)
