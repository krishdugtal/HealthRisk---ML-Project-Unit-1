"""
FastAPI Main Server for HealthRisk Bayesian Health Risk Assessment Tool (Phase 3)
"""
from fastapi import FastAPI, HTTPException, Cookie, Response, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import secrets
import csv
import io

from app.bayes_engine import (
    posterior,
    expectation,
    variance,
    covariance,
    CONDITIONS,
    SYMPTOMS
)
from app.database import (
    init_db,
    save_assessment,
    get_all_assessments,
    get_assessment_by_id,
    create_user,
    authenticate_user,
    get_user_by_id
)

app = FastAPI(
    title="HealthRisk - Bayesian Health Risk Engine",
    description="ML Unit 1 Project: Multi-User Bayesian Health Risk & Population RV Engine",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Active Session Store: session_token -> user_dict
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Active Population Dataset (Defaults to bundled sample)
POPULATION_FILE = os.path.join(os.path.dirname(__file__), "data", "population_sample.json")
ACTIVE_DATASET: Dict[str, Any] = {
    "name": "Bundled Sample (N=25)",
    "records": []
}


def load_initial_population():
    global ACTIVE_DATASET
    if os.path.exists(POPULATION_FILE):
        with open(POPULATION_FILE, "r") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else data.get("records", [])
            ACTIVE_DATASET = {
                "name": f"Kaggle Framingham Dataset (N={len(records)})",
                "records": records
            }


@app.on_event("startup")
def on_startup():
    init_db()
    load_initial_population()


# Auth Helper
def get_current_user(session_id: Optional[str] = Cookie(None, alias="hr_session_id")) -> Dict[str, Any]:
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    # Default to demo_user if no active session
    return {"id": 1, "email": "demo@healthrisk.edu"}


# Pydantic Models
class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AssessmentRequest(BaseModel):
    patient_name: str = Field(default="Anonymous Patient", example="John Doe")
    age: int = Field(default=45, ge=1, le=120, example=45)
    age_group: str = Field(default="30-50", example="30-50")
    family_history: str = Field(default="no", example="yes")
    symptoms: List[str] = Field(default=[], example=["excessive_thirst", "frequent_urination"])
    condition_ids: Optional[List[str]] = Field(
        default=["diabetes_t2", "cardiovascular"],
        example=["diabetes_t2", "cardiovascular"]
    )


# 1. AUTHENTICATION ENDPOINTS (STEP 1)
@app.post("/api/register")
def register(req: RegisterRequest, response: Response):
    if not req.email or "@" not in req.email or len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Invalid email or password (min 4 characters).")

    try:
        user = create_user(req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session_id = secrets.token_hex(24)
    SESSIONS[session_id] = user
    response.set_cookie(key="hr_session_id", value=session_id, httponly=True, samesite="lax")
    return {"user": user, "message": "Registered successfully."}


@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    session_id = secrets.token_hex(24)
    SESSIONS[session_id] = user
    response.set_cookie(key="hr_session_id", value=session_id, httponly=True, samesite="lax")
    return {"user": user, "message": "Logged in successfully."}


@app.post("/api/logout")
def logout(response: Response, session_id: Optional[str] = Cookie(None, alias="hr_session_id")):
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    response.delete_cookie(key="hr_session_id")
    return {"message": "Logged out."}


@app.get("/api/me")
def get_me(session_id: Optional[str] = Cookie(None, alias="hr_session_id")):
    if session_id and session_id in SESSIONS:
        return {"authenticated": True, "user": SESSIONS[session_id]}
    return {"authenticated": False, "user": {"id": 1, "email": "demo@healthrisk.edu"}}


# 2. ASSESSMENT & CONDITIONS ENDPOINTS
@app.get("/api/conditions")
def get_conditions():
    symptoms_list = []
    for sym_id, sym_info in SYMPTOMS.items():
        symptoms_list.append({
            "id": sym_id,
            "name": sym_info["name"]
        })

    return {
        "conditions": CONDITIONS,
        "symptoms": symptoms_list
    }


@app.post("/api/assess")
def run_assessment(
    req: AssessmentRequest,
    session_id: Optional[str] = Cookie(None, alias="hr_session_id")
):
    current_user = get_current_user(session_id)
    target_conditions = req.condition_ids if req.condition_ids else ["diabetes_t2", "cardiovascular"]

    if req.age < 30:
        age_grp = "<30"
    elif req.age <= 50:
        age_grp = "30-50"
    else:
        age_grp = ">50"

    results_by_condition = {}
    for cond_id in target_conditions:
        if cond_id not in CONDITIONS:
            continue
        res = posterior(
            selected_symptoms=req.symptoms,
            condition_id=cond_id,
            age_group=age_grp,
            family_history=req.family_history
        )
        results_by_condition[cond_id] = res

    # Save to SQLite with current user_id
    assessment_id = save_assessment(
        patient_name=req.patient_name,
        age=req.age,
        age_group=age_grp,
        family_history=req.family_history,
        symptoms=req.symptoms,
        results=results_by_condition,
        user_id=current_user["id"]
    )

    return {
        "assessment_id": assessment_id,
        "user_id": current_user["id"],
        "patient": {
            "name": req.patient_name,
            "age": req.age,
            "age_group": age_grp,
            "family_history": req.family_history
        },
        "reported_symptoms": req.symptoms,
        "results": results_by_condition,
        "disclaimer": "This risk assessment tool is for educational and decision-support purposes only (ML Unit 1 Project). It does not provide medical diagnosis."
    }


@app.get("/api/assessments")
def list_assessments(session_id: Optional[str] = Cookie(None, alias="hr_session_id")):
    current_user = get_current_user(session_id)
    return {"assessments": get_all_assessments(user_id=current_user["id"])}


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: int, session_id: Optional[str] = Cookie(None, alias="hr_session_id")):
    current_user = get_current_user(session_id)
    data = get_assessment_by_id(assessment_id, user_id=current_user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="Assessment not found or access denied.")
    return data


# 3. PERSONAL TRENDS ENDPOINT (STEP 2)
@app.get("/api/user_trends")
def get_user_trends(session_id: Optional[str] = Cookie(None, alias="hr_session_id")):
    """
    Step 2 Endpoint: Computes Expectation and Variance over the logged-in user's
    personal time series of posterior risk scores (reusing Phase 2 expectation/variance).
    """
    current_user = get_current_user(session_id)
    assessments = get_all_assessments(user_id=current_user["id"], limit=100)

    if len(assessments) < 3:
        return {
            "has_trends": False,
            "count": len(assessments),
            "message": f"User has {len(assessments)} saved assessment(s). At least 3 assessments are required to calculate personal time-series risk trends."
        }

    # Extract risk scores per condition over user's history
    condition_scores: Dict[str, List[float]] = {}
    for item in assessments:
        res = item["results"]
        for cond_id, c_data in res.items():
            if cond_id not in condition_scores:
                condition_scores[cond_id] = []
            condition_scores[cond_id].append(c_data["posterior_percentage"])

    trends = {}
    for cond_id, scores in condition_scores.items():
        exp_res = expectation(scores)
        var_res = variance(scores)
        trends[cond_id] = {
            "condition_name": CONDITIONS[cond_id]["name"] if cond_id in CONDITIONS else cond_id,
            "mean": exp_res["mean"],
            "variance": var_res["variance"],
            "standard_deviation": var_res["standard_deviation"],
            "scores_history": scores
        }

    return {
        "has_trends": True,
        "count": len(assessments),
        "user_email": current_user["email"],
        "trends": trends,
        "formula_used": "E[X] = (1/n) ∑ x_i  |  Var(X) = (1/n) ∑ (x_i - E[X])²"
    }


# 4. POPULATION STATS & CSV IMPORT ENDPOINTS (STEP 3)
@app.post("/population_stats/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Step 3 Endpoint: Uploads a custom CSV dataset (columns: age, bmi, systolic_bp, risk_score)
    and switches active population dataset. Validates numerical ranges.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted.")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    fieldnames = [f.strip() for f in (reader.fieldnames or [])]
    field_map = {}

    for f in fieldnames:
        lower_f = f.lower()
        if lower_f in ["age"]:
            field_map["age"] = f
        elif lower_f in ["bmi", "body_mass_index"]:
            field_map["bmi"] = f
        elif lower_f in ["systolic_bp", "sysbp", "ap_hi", "trestbps", "systolic"]:
            field_map["systolic_bp"] = f
        elif lower_f in ["risk_score", "tenyearchd", "cardio", "target", "outcome", "risk"]:
            field_map["risk_score"] = f

    required_cols = {"age", "bmi", "systolic_bp", "risk_score"}
    missing = required_cols - set(field_map.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV validation failed. Could not find or map required columns: {list(missing)}. CSV must contain headers for age, bmi, systolic blood pressure (e.g., sysBP, systolic_bp, ap_hi), and risk score (e.g., TenYearCHD, risk_score, cardio)."
        )

    records = []
    row_num = 1
    for row in reader:
        row_num += 1
        try:
            val_age = row[field_map["age"]].strip()
            val_bmi = row[field_map["bmi"]].strip()
            val_bp = row[field_map["systolic_bp"]].strip()
            val_risk = row[field_map["risk_score"]].strip()

            if not val_age or not val_bmi or not val_bp or not val_risk:
                continue

            age = int(float(val_age))
            bmi = float(val_bmi)
            bp = float(val_bp)
            raw_risk = float(val_risk)

            # If risk column is binary (0/1) like TenYearCHD or cardio, scale to percentage or score
            if raw_risk in [0.0, 1.0] and set(r.get(field_map["risk_score"], "") for r in []).issubset({"0", "1", "0.0", "1.0", ""}):
                risk = round(min(99.0, max(5.0, (age * 0.7) + (bp * 0.25) + (bmi * 0.4) + (raw_risk * 25.0) - 35.0)), 1)
            else:
                risk = float(raw_risk)

            if age <= 0 or bmi <= 0 or bp <= 0 or risk < 0:
                continue

            records.append({
                "patient_id": f"CSV-{len(records)+1:04d}",
                "age": age,
                "bmi": round(bmi, 2),
                "systolic_bp": round(bp, 1),
                "risk_score": round(risk, 1)
            })
        except Exception:
            continue

    if len(records) < 2:
        raise HTTPException(status_code=400, detail="CSV must contain at least 2 valid data rows to compute statistics.")

    global ACTIVE_DATASET
    ACTIVE_DATASET = {
        "name": f"Uploaded CSV ({file.filename}) [N={len(records)}]",
        "records": records
    }

    return {
        "message": f"Successfully loaded uploaded CSV '{file.filename}' with {len(records)} valid records.",
        "dataset_name": ACTIVE_DATASET["name"],
        "row_count": len(records)
    }


@app.get("/population_stats/expectation_variance")
def get_expectation_variance():
    records = ACTIVE_DATASET["records"]
    if not records:
        load_initial_population()
        records = ACTIVE_DATASET["records"]

    risk_scores = [r["risk_score"] for r in records]
    exp_res = expectation(risk_scores)
    var_res = variance(risk_scores)

    return {
        "dataset_name": ACTIVE_DATASET["name"],
        "mean": exp_res["mean"],
        "variance": var_res["variance"],
        "standard_deviation": var_res["standard_deviation"],
        "formula_used": f"E[X] = (1/n) ∑ x_i  |  Var(X) = (1/n) ∑ (x_i - E[X])²",
        "n": len(risk_scores)
    }


@app.get("/population_stats/covariance")
def get_covariance_stat():
    records = ACTIVE_DATASET["records"]
    if not records:
        load_initial_population()
        records = ACTIVE_DATASET["records"]

    bmi_values = [r["bmi"] for r in records]
    bp_values = [r["systolic_bp"] for r in records]

    cov_res = covariance(bmi_values, bp_values, name_x="BMI", name_y="Systolic BP")

    return {
        "dataset_name": ACTIVE_DATASET["name"],
        "covariance": cov_res["covariance"],
        "mean_x": cov_res["mean_x"],
        "mean_y": cov_res["mean_y"],
        "formula_used": "Cov(X,Y) = (1/n) ∑ (x_i - E[X])(y_i - E[Y])",
        "interpretation": cov_res["interpretation"],
        "n": cov_res["n"]
    }


@app.get("/api/statistics")
def get_statistics():
    records = ACTIVE_DATASET["records"]
    if not records:
        load_initial_population()
        records = ACTIVE_DATASET["records"]

    bmi_values = [r["bmi"] for r in records]
    bp_values = [r["systolic_bp"] for r in records]
    risk_scores = [r["risk_score"] for r in records]

    bmi_exp = expectation(bmi_values)
    bmi_var = variance(bmi_values)

    bp_exp = expectation(bp_values)
    bp_var = variance(bp_values)

    risk_exp = expectation(risk_scores)
    risk_var = variance(risk_scores)

    cov_res = covariance(bmi_values, bp_values, name_x="BMI", name_y="Systolic BP")

    return {
        "dataset_name": ACTIVE_DATASET["name"],
        "sample_size": len(records),
        "records": records,
        "expectation": {
            "bmi": bmi_exp,
            "systolic_bp": bp_exp,
            "risk_score": risk_exp
        },
        "variance": {
            "bmi": bmi_var,
            "systolic_bp": bp_var,
            "risk_score": risk_var
        },
        "covariance": cov_res
    }


# Mount Static Files for Vanilla HTML/CSS/JS UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
