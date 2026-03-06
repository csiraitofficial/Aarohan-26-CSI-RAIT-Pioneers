from datetime import datetime, timedelta
from app.db import DB
from app.models.withdrawal_alert import WithdrawalAlert

class WithdrawalService:

    @staticmethod
    def create_withdrawal_alert(treatment_id, animal_id, withdrawal_days):
        print("\n[WITHDRAWAL] create_withdrawal_alert() CALLED")
        print(f"[WITHDRAWAL] treatment_id = {treatment_id}")
        print(f"[WITHDRAWAL] animal_id    = {animal_id}")
        print(f"[WITHDRAWAL] days         = {withdrawal_days}")

        safe_from = datetime.utcnow() + timedelta(days=withdrawal_days)
        print(f"[WITHDRAWAL] safe_from    = {safe_from}")

        alert = WithdrawalAlert(
            treatment_id=str(treatment_id),
            animal_id=str(animal_id),
            safe_from=safe_from
        )
        alert.save()

        print(f"[WITHDRAWAL] ALERT SAVED with id = {alert.id}")
        return safe_from

    @staticmethod
    def check_animal_safety(animal_id):
        print("\n[WITHDRAWAL] check_animal_safety()")
        print(f"[WITHDRAWAL] animal_id = {animal_id}")
        print("[WITHDRAWAL] USING PyMongo path")

        active_alert = DB.withdrawal_alerts.find_one({
            'animal_id': str(animal_id),
            'safe_from': {'$gt': datetime.utcnow().isoformat()}
        })

        print(f"[WITHDRAWAL] active_alert FOUND? {bool(active_alert)}")
        return active_alert is None

    @staticmethod
    def get_active_withdrawal_alerts_for_farmer(farmer_id):
        print("\n[WITHDRAWAL] get_active_withdrawal_alerts_for_farmer()")
        print(f"[WITHDRAWAL] farmer_id = {farmer_id}")
        print("[WITHDRAWAL] USING PyMongo path")

        animals = list(DB.animals.find({'farmer_id': farmer_id}))
        print(f"[WITHDRAWAL] animals found = {len(animals)}")

        animal_ids = []
        for a in animals:
            aid = str(a.get('_id'))
            animal_ids.append(aid)

        print(f"[WITHDRAWAL] animal_ids = {animal_ids}")

        if not animal_ids:
            print("[WITHDRAWAL] No animals → returning []")
            return []

        active_alerts = list(DB.withdrawal_alerts.find({
            'animal_id': {'$in': animal_ids},
            'safe_from': {'$gt': datetime.utcnow().isoformat()}
        }))

        print(f"[WITHDRAWAL] active alerts found = {len(active_alerts)}")

        for alert in active_alerts:
            alert['_id'] = str(alert['_id'])

        return active_alerts

    @staticmethod
    def get_active_alerts_for_animals(animal_ids):
        print("\n[WITHDRAWAL] get_active_alerts_for_animals()")
        print("[WITHDRAWAL] USING MongoEngine path")
        print(f"[WITHDRAWAL] animal_ids = {animal_ids}")
        print(f"[WITHDRAWAL] now        = {datetime.utcnow()}")

        alerts = WithdrawalAlert.objects(
            animal_id__in=animal_ids,
            safe_from__gt=datetime.utcnow()
        )

        print(f"[WITHDRAWAL] alerts found = {alerts.count()}")
        for a in alerts:
            print(
                f"[WITHDRAWAL] alert → id={a.id}, "
                f"animal_id={a.animal_id}, safe_from={a.safe_from}"
            )

        return alerts
