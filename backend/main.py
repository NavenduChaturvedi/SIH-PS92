import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

try:
    import models
    from database import engine, get_db, SessionLocal
    from schemas import LoanApplicationRequest, FinancialSimulationResult, FullApplicationResponse, RawVoiceRequest, ApplyRequest, TranslationRequest, TranslationResponse
    from services.simulator import simulate_loan_terms
    from services.router import find_optimal_partners
    from services.nlp import parse_vernacular_intent
    from services.bhashini import translate_to_english
    from services.translation import translate_dict
    from services.scheme_catalogue import SCHEME_CATALOGUE, get_scheme
    from migrate import migrate
    from cors_utils import normalize_cors_origins
    from seed_db import seed_data
except ModuleNotFoundError:
    from . import models
    from .database import engine, get_db, SessionLocal
    from .schemas import LoanApplicationRequest, FinancialSimulationResult, FullApplicationResponse, RawVoiceRequest, ApplyRequest, TranslationRequest, TranslationResponse
    from .services.simulator import simulate_loan_terms
    from .services.router import find_optimal_partners
    from .services.nlp import parse_vernacular_intent
    from .services.bhashini import translate_to_english
    from .services.translation import translate_dict
    from .services.scheme_catalogue import SCHEME_CATALOGUE, get_scheme
    from .migrate import migrate
    from .cors_utils import normalize_cors_origins
    from .seed_db import seed_data

cors_origins = normalize_cors_origins(os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175,http://localhost:5177,http://127.0.0.1:5177,https://sih-2026-26092-t2.vercel.app"
))

# Create tables in the database
models.Base.metadata.create_all(bind=engine)
migrate()

# Render's free tier has no persistent disk and no build/start hook that runs
# seed_db.py, so without this the channel_partners table is silently empty on
# every deploy/restart. Only seed when empty so this never clobbers real data
# on an environment that does have a persistent Postgres database.
with SessionLocal() as _db:
    if _db.query(models.ChannelPartner).count() == 0:
        seed_data()

app = FastAPI(title="SIH Health-Aware Router API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "operational", "service": "health-aware-router"}

@app.get("/partners/count")
def get_partners_count(db: Session = Depends(get_db)):
    count = db.query(models.ChannelPartner).count()
    return {"total_registered_partners": count}

@app.get("/schemes")
def list_schemes():
    return {"schemes": SCHEME_CATALOGUE}

@app.get("/schemes/{scheme_id}")
def get_scheme_detail(scheme_id: str):
    scheme = get_scheme(scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail=f"Unknown scheme id '{scheme_id}'.")
    return scheme

@app.post("/translate", response_model=TranslationResponse)
def batch_translate(request: TranslationRequest):
    return TranslationResponse(
        translations=translate_dict(request.texts, request.target_language, request.source_language),
        target_language=request.target_language,
    )

@app.get("/translate/languages")
def get_translation_languages():
    return {"languages": ["en", "bn", "hi", "mr", "ta", "te"]}


@app.post("/simulate", response_model=FinancialSimulationResult)
def run_financial_simulation(application: LoanApplicationRequest):
    return simulate_loan_terms(application)

@app.post("/process-application", response_model=FullApplicationResponse)
def process_full_application(application: LoanApplicationRequest, db: Session = Depends(get_db)):
    # 1. Run the financial simulation[cite: 1]
    sim_result = simulate_loan_terms(application)
    
    # 2. Find the optimal channel partners[cite: 1]
    partners = []
    if sim_result.is_eligible:
        partners = find_optimal_partners(db, application)
        
    return FullApplicationResponse(
        simulation=sim_result,
        recommended_partners=partners
    )

@app.post("/apply", response_model=FullApplicationResponse)
def process_apply(request: ApplyRequest, db: Session = Depends(get_db)):
    if request.input_mode == "form":
        structured_data = LoanApplicationRequest(
            business_type=request.loan_type or "General",
            loan_type=request.loan_type,
            capital_required=request.capital_required or 0.0,
            annual_income=request.annual_income or 0.0,
            latitude=request.latitude,
            longitude=request.longitude,
            education_status="student" if (request.loan_type or "").lower() == "education" else None,
            preferred_language=request.preferred_language,
        )
    else:
        normalized_text, _provider = translate_to_english(
            request.translated_text or "", request.preferred_language
        )
        structured_data = parse_vernacular_intent(
            normalized_text,
            request.latitude,
            request.longitude,
        )
        structured_data.preferred_language = request.preferred_language
        if request.loan_type:
            structured_data.loan_type = request.loan_type
            structured_data.business_type = request.loan_type
            if request.loan_type.lower() == "education":
                structured_data.education_status = "student"

    sim_result = simulate_loan_terms(structured_data)
    partners = []
    if sim_result.is_eligible:
        partners = find_optimal_partners(db, structured_data)

    return FullApplicationResponse(
        simulation=sim_result,
        recommended_partners=partners
    )


@app.post("/voice-apply", response_model=FullApplicationResponse)
def process_voice_application(request: RawVoiceRequest, db: Session = Depends(get_db)):
    apply_request = ApplyRequest(
        input_mode="voice",
        translated_text=request.translated_text,
        latitude=request.latitude,
        longitude=request.longitude,
    )
    return process_apply(apply_request, db)
