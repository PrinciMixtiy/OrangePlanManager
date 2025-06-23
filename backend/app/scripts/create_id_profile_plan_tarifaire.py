from app.db.session import engine
from sqlmodel import Session, select
from app.models.id_profile_models import IDProfile
from app.models.plan_tarifaire_id_profile_model import PlanTarifaireIDProfile
from app.models.plan_tarifaire_models import PlanTarifaire

id_profiles = [
    "Postpaid",
    "Postpaid Controlled",
    "Postpaid Corporate",
    "Postpaid Corporate Admin",
    "Postpaid Corporate Zero",
    "Postpaid Corporate Gold",
    "Prepaid",
    "Prepaid Pro1",
    "Prepaid Pro2",
    "Prepaid Pro3",
    "Prepaid Korana",
    "Prepaid Freefiber",
    "Prepaid Aona",
    "Hybrid",
    "Homenet Postpaid",
    "Homenet Prepaid",
    "Ambatovy",
    "Allowa",
    "Allowa Plus",
]

plan_tarifaires = [
    "Orange 60 mode à la seconde",
    "Orange 60 mode classique",
    "Orange Max",
    "Orange Mitsitsy",
    "Orange 3G",
    "Orange Net Confort",
    "Intense (Orange Net)",
    "Corporate Admin",
    "Corporate Premium",
    "Corporate VIP",
    "Corporate Gold",
    "Corporate 250SMS",
    "Corporate BASSAN",
    "Corporate +",
    "Corporate 100",
    "Corporate Equilibre",
    "Corporate Intense",
    "Corporate Initial",
    "Corporate Ultra",
    "Corporate IN",
    "Corporate IN+",
    "Corporate Star",
    "Corporate Start",
    "Corporate SNU IN+",
    "Corporate Zero",
    "Corporate SMM New",
    "Forfait Smartphone",
    "Forfait iPhone",
    "Forfait Corporate SMS",
    "Forfait Corporate Voix",
    "Wifiber",
    "Wifiber Pro",
    "Smart",
    "Smart +",
    "Smart Pro2",
    "Smart Pro6",
    "Smart Pro12",
    "Smart Pro25", 
    "Smart Pro Ultra",
    "Smart Pro Prodigy",
    "Smart SSE",
    "So Smart",
    "Homenet",
    "Homenet Postpaid",
    "Homenet Prepaid",
    "Hong",
    "IZY",
    "Mitsitsy +",
    "Premium",
    "OPEN",
    "Pack Touriste",
    "Freefiber",
    "Aôonnaaa",
    "Sera Pro",
    "Allowa",
    "Allowa +",
    "Pro V1",
    "Pro V2",
    "Pro V3",
    "CMO Smartphone",
    "CMO Data",
    "CMO SMM Nex",
    "Tandem 0",
]

# Define the relationships between profiles and plans
profile_plan_mapping = {
    "Postpaid Controlled": [
        "Hong", "Corporate Star", "Forfait Smartphone", "Orange 60 mode classique",
        "Orange Max", "Corporate Admin", "Corporate Premium", "Corporate VIP",
        "Corporate 250SMS", "Corporate +", "Corporate BASSAN", "Corporate SMM New",
        "Corporate 100", "Mitsitsy +"
    ],
    "Postpaid": [
        "Hong", "Forfait Smartphone", "Orange 60 mode à la seconde", "Orange 60 mode classique",
        "Orange Mitsitsy", "Corporate Admin", "Corporate Premium", "Corporate VIP", "Corporate Gold", "Corporate 250SMS",
        "Forfait iPhone", "Corporate +", "Corporate BASSAN", "Corporate SMM New", "Corporate 100",
        "Intense (Orange Net)", "Orange Net Confort", "Orange 3G", "Premium", "Mitsitsy +"
    ],
    "Hybrid": [
        "Tandem 0", "CMO Smartphone", "CMO Data", "CMO SMM Nex", "Smart", "Smart +", "Smart SSE", "So Smart"
    ],
    "Postpaid Corporate Admin": [
        "Corporate Admin"
    ],
    "Postpaid Corporate Gold": [
        "Corporate Gold"
    ],
    "Postpaid Corporate Zero": [
        "Corporate Zero"
    ],
    "Postpaid Corporate": [
        "Corporate Equilibre", "Corporate Intense", "Corporate Initial",
        "Corporate Start", "Corporate IN", "Corporate IN+",
        "Smart Pro2", "Smart Pro6", "Smart Pro12", "Smart Pro25", "Smart Pro Ultra",
        "Smart Pro Prodigy", "Corporate SNU IN+", "Wifiber",
    ],
    "Homenet Postpaid": [
        "Homenet Postpaid"
    ],
    "Homenet Prepaid": ["Homenet Prepaid"],
    "Ambatovy": [
        "Corporate Ultra"
    ],
    "Prepaid": [
        "IZY", "OPEN", "Pack Touriste",
    ],
    "Allowa": [
        "Allowa"
    ],
    "Allowa Plus": [
        "Allowa +"
    ],
    "Prepaid Pro1": [
        "Pro V1"
    ], 
    "Prepaid Pro2": [
        "Pro V2"
    ], 
    "Prepaid Pro3": [
        "Pro V3"
    ],
    "Homenet Prepaid": [
        "Homenet"
    ],
    "Prepaid Korana": [
        "Sera Pro"
    ],
    "Prepaid Freefiber": [
        "Freefiber"
    ],
    "Prepaid Aona": [
        "Aôonnaaa"
    ],
}

def create_id_profiles_and_plans():
    with Session(engine) as session:
        # First create all profiles and plans
        profile_dict = {}
        plan_dict = {}
        
        # Create ID Profiles
        for profile_name in id_profiles:
            profile = session.exec(select(IDProfile).where(
                IDProfile.name == profile_name)).first()
            if not profile:
                profile = IDProfile(name=profile_name)
                session.add(profile)
                session.commit()
                session.refresh(profile)
                print(f"ID Profile '{profile_name}' created successfully.")
            profile_dict[profile_name] = profile

        # Create Plan Tarifaires
        for plan_name in plan_tarifaires:
            plan = session.exec(select(PlanTarifaire).where(
                PlanTarifaire.name == plan_name)).first()
            if not plan:
                plan = PlanTarifaire(name=plan_name)
                session.add(plan)
                session.commit()
                session.refresh(plan)
                print(f"Plan Tarifaire '{plan_name}' created successfully.")
            plan_dict[plan_name] = plan

        # Create relationships
        for profile_name, plan_names in profile_plan_mapping.items():
            profile = profile_dict.get(profile_name)
            if not profile:
                print(f"Warning: Profile {profile_name} not found")
                continue

            for plan_name in plan_names:
                plan = plan_dict.get(plan_name)
                if not plan:
                    print(f"Warning: Plan {plan_name} not found")
                    continue

                stmt = select(PlanTarifaireIDProfile).where(
                    PlanTarifaireIDProfile.id_profile_id == profile.id,
                    PlanTarifaireIDProfile.plan_tarifaire_id == plan.id
                )
                existing_relation = session.exec(stmt).first()

                if not existing_relation:
                    profile.plans.append(plan)  # Ajout direct
                    print(f"Added relationship: {profile_name} -> {plan_name}")
                else:
                    print(f"Relationship between {profile_name} and {plan_name} already exists.")

        session.commit()
        print("All relationships created successfully.")

# Run the function
if __name__ == "__main__":
    create_id_profiles_and_plans()
