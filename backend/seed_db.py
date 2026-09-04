from database import SessionLocal, Base, engine
from models import ChannelPartner
from migrate import migrate

# Real State Channelizing Agencies (SCAs) for NSFDC/NSKFDC schemes, one per
# state/UT, sourced from the Ministry of Social Justice & Empowerment's
# official list of State Scheduled Castes Development Corporations:
# https://socialjustice.gov.in/writereaddata/UploadFile/List%20of%2027%20SCDCs%20with%20addresses.pdf
#
# Names and headquarters cities are real; a couple of names that don't
# mention their state (e.g. "Dr. B.R. Ambedkar Development Corporation Ltd.")
# have the state appended in parentheses for clarity in the UI. Obvious
# source typos ("Gujrat", "Pondicherri") are corrected.
#
# npa_ratio / active_quota / overdue_ratio are NOT published by NSFDC/NSKFDC
# for individual channelizing agencies anywhere public — they are simulated
# placeholders (cycled across a few illustrative profiles) purely so the
# health-aware routing logic has something to filter on. Replace with real
# MIS figures if/when NSFDC or the respective SCAs make them available.
STATE_CHANNELIZING_AGENCIES = [
    ("A.P. Scheduled Castes Co-operative Finance Corporation Ltd.", 17.3850, 78.4867),
    ("Assam State Development Corporation for Scheduled Castes Ltd.", 26.1445, 91.7362),
    ("Bihar State Scheduled Castes Co-operative Development Corporation Ltd.", 25.5941, 85.1376),
    ("Chandigarh Scheduled Castes Financial and Development Corporation Ltd.", 30.7333, 76.7794),
    ("Delhi Scheduled Castes Financial and Development Corporation", 28.7041, 77.1025),
    ("Goa State SCs & Backward Class Finance and Development Corporation", 15.4909, 73.8278),
    ("Gujarat Scheduled Castes Development Corporation", 23.2156, 72.6369),
    ("Haryana SCs Finance & Dev. Corporation Ltd.", 30.7333, 76.7794),
    ("Himachal Pradesh Scheduled Castes and Scheduled Tribes Development Corporation", 30.9045, 77.0967),
    ("J & K Scheduled Castes, STs & OBC Development Corporation", 32.7266, 74.8570),
    ("Dr. B.R. Ambedkar Development Corporation Ltd. (Karnataka)", 12.9716, 77.5946),
    ("Kerala State Development Corporation for SCs & STs Ltd.", 10.5276, 76.2144),
    ("M.P. State Co-operative Scheduled Castes Finance & Development Corporation", 23.2599, 77.4126),
    ("Mahatma Phule Backward Classes Development Corporation Ltd. (Maharashtra)", 19.1075, 72.8263),
    ("Orissa Scheduled Castes & Scheduled Tribes Development Finance Co-op Corporation Ltd.", 20.2961, 85.8245),
    ("Pondicherry Adi Dravidar Development Corporation Ltd.", 11.9416, 79.8083),
    ("Punjab Scheduled Castes Land Development & Finance Corporation Ltd.", 30.7333, 76.7794),
    ("Rajasthan Scheduled Castes & Scheduled Tribes Development Corporation Ltd.", 26.9124, 75.7873),
    ("Sikkim SC/ST and other Backward Classes Development Corporation Ltd.", 27.3389, 88.6065),
    ("Tamil Nadu Adi Dravidar Housing & Development Corporation Ltd.", 13.0827, 80.2707),
    ("Tripura Scheduled Castes Co-op. Development Corporation Ltd.", 23.8315, 91.2868),
    ("U.P. Scheduled Castes Finance & Development Corporation Ltd.", 26.8467, 80.9462),
    ("West Bengal Scheduled Castes & Scheduled Tribes Development & Finance Corporation", 22.5726, 88.3639),
    ("Dadra & Nagar Haveli, Daman & Diu SC/ST/OBC & Minorities Financial and Development Corporation Ltd.", 20.2738, 73.0165),
    ("Chhattisgarh State Antavayasayee Co-op. Scheduled Castes Finance & Development Corporation Ltd.", 21.2514, 81.6296),
    ("Bahu Udasay Vitta Avam Vikas Nigam (Uttarakhand)", 30.3165, 78.0322),
    ("Jharkhand State Scheduled Caste Co-op. Dev. Corporation", 23.3441, 85.3096),
]

# Cycled, clearly-simulated health/capacity profiles (see note above).
ILLUSTRATIVE_PROFILES = [
    {"npa_ratio": 2.1, "active_quota": 8000000.0, "overdue_ratio": 1.5},
    {"npa_ratio": 3.4, "active_quota": 6000000.0, "overdue_ratio": 2.8},
    {"npa_ratio": 1.8, "active_quota": 10000000.0, "overdue_ratio": 1.0},
    {"npa_ratio": 4.2, "active_quota": 4500000.0, "overdue_ratio": 3.5},
]


def seed_data():
    # Render's build command seeds data directly, before the API process starts.
    # Ensure both fresh and existing databases have the current table shape first.
    Base.metadata.create_all(bind=engine)
    migrate()
    db = SessionLocal()

    # Clear existing data for a clean test environment
    db.query(ChannelPartner).delete()

    partners = [
        ChannelPartner(
            name=name,
            partner_type="SCA",
            supported_schemes="Microfinance,Term Loan,Education Loan,Green Business",
            is_active=True,
            # Note: PostGIS expects Longitude first, then Latitude
            location=f"SRID=4326;POINT({longitude} {latitude})",
            **ILLUSTRATIVE_PROFILES[index % len(ILLUSTRATIVE_PROFILES)],
        )
        for index, (name, latitude, longitude) in enumerate(STATE_CHANNELIZING_AGENCIES)
    ]

    db.add_all(partners)
    db.commit()
    print(f"Database seeded with {len(partners)} state channelizing agencies.")
    db.close()

if __name__ == "__main__":
    seed_data()
