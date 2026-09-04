import math

from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    import models
    from schemas import LoanApplicationRequest
except ModuleNotFoundError:
    from .. import models
    from ..schemas import LoanApplicationRequest

# Channel partners are now real State Channelizing Agencies (one per
# state/UT, headquartered in the state capital — see seed_db.py), not a dense
# local branch network, so a tight urban radius would only ever match
# applicants literally inside a capital city. 300km comfortably covers most
# states end-to-end. This is still a simplification: in reality an applicant
# is routed to their own state's SCA, not simply the nearest one by straight-
# line distance, which matters near state borders. A future improvement
# would resolve the applicant's state (e.g. via reverse geocoding) and match
# on that instead of radius.
def find_optimal_partners(db: Session, request: LoanApplicationRequest, radius_km: float = 300.0):
    if db.bind.dialect.name == "sqlite":
        def distance_km(location):
            try:
                point = location.split("POINT(", 1)[1].rstrip(")")
                longitude, latitude = map(float, point.split())
                latitude_delta = math.radians(latitude - request.latitude)
                longitude_delta = math.radians(longitude - request.longitude)
                value = math.sin(latitude_delta / 2) ** 2 + math.cos(math.radians(request.latitude)) * math.cos(math.radians(latitude)) * math.sin(longitude_delta / 2) ** 2
                return 6371 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))
            except (AttributeError, IndexError, ValueError):
                return float("inf")

        matches = []
        for partner in db.query(models.ChannelPartner).filter(models.ChannelPartner.is_active == True).all():
            distance = distance_km(partner.location)
            scheme = "Education Loan" if request.education_status or request.business_type == "Education" else ("Microfinance" if request.capital_required <= 140000 else "Term Loan")
            supported = [item.strip() for item in partner.supported_schemes.split(",") if item.strip()]
            if distance <= radius_km and partner.active_quota >= request.capital_required * 0.90 and partner.npa_ratio < 5.0 and partner.overdue_ratio < 5.0 and scheme in supported:
                matches.append((partner, distance, supported))
        matches.sort(key=lambda item: (-(item[0].active_quota / (item[0].npa_ratio + item[0].overdue_ratio + 1)), item[1]))
        return [{"partner_id": partner.id, "name": partner.name, "type": partner.partner_type, "distance_km": round(distance, 2), "health_status": "Healthy", "remaining_capacity": partner.active_quota, "supported_schemes": supported, "latitude": float(partner.location.split("POINT(", 1)[1].rstrip(")").split()[1]), "longitude": float(partner.location.split("POINT(", 1)[1].rstrip(")").split()[0])} for partner, distance, supported in matches[:3]]

    # Convert user lat/lon into a PostGIS Point (SRID 4326 for GPS coordinates)
    user_point = f"POINT({request.longitude} {request.latitude})"
    
    # Calculate a simple health score: (Active Quota / (NPA Ratio + 1))
    # Higher active quota and lower NPA yields a better score
    health_score = models.ChannelPartner.active_quota / (models.ChannelPartner.npa_ratio + models.ChannelPartner.overdue_ratio + 1)
    requested_scheme = "Education Loan" if request.education_status or request.business_type == "Education" else ("Microfinance" if request.capital_required <= 140000 else "Term Loan")
    
    # Query for active partners within the radius (in meters), ordered by health score then distance
    optimal_partners = db.query(
        models.ChannelPartner,
        func.ST_DistanceSphere(models.ChannelPartner.location, func.ST_GeomFromText(user_point, 4326)).label("distance_meters"),
        func.ST_Y(models.ChannelPartner.location).label("latitude"),
        func.ST_X(models.ChannelPartner.location).label("longitude"),
    ).filter(
        models.ChannelPartner.is_active == True,
        models.ChannelPartner.active_quota >= request.capital_required * 0.90,
        models.ChannelPartner.npa_ratio < 5.0,
        models.ChannelPartner.overdue_ratio < 5.0,
        models.ChannelPartner.supported_schemes.ilike(f"%{requested_scheme}%"),
        func.ST_DWithin(
            func.ST_Transform(models.ChannelPartner.location, 3857), 
            func.ST_Transform(func.ST_GeomFromText(user_point, 4326), 3857), 
            radius_km * 1000
        )
    ).order_by(
        health_score.desc(),
        func.ST_DistanceSphere(models.ChannelPartner.location, func.ST_GeomFromText(user_point, 4326))
    ).limit(3).all()
    
    # Format the results
    results = []
    for partner, distance, latitude, longitude in optimal_partners:
        results.append({
            "partner_id": partner.id,
            "name": partner.name,
            "type": partner.partner_type,
            "distance_km": round(distance / 1000, 2),
            "health_status": "Healthy",
            "remaining_capacity": partner.active_quota,
            "supported_schemes": [item.strip() for item in partner.supported_schemes.split(",") if item.strip()],
            "latitude": latitude,
            "longitude": longitude,
        })
        
    return results
