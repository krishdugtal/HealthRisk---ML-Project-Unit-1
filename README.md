# HealthRisk — Bayesian Health Risk Assessment System

> **Course Project**: 3rd Year B.Tech CSE — Machine Learning (Unit 1: Probability & Bayesian Inference)  
> **Core Objective**: Fully transparent, inspectable Bayesian calculations and Discrete Random Variable statistics for college viva examination.  
> **UI Aesthetic**: Apple.com official Light Mode design system (`#F5F5F7` canvas, `#FFFFFF` cards, `-apple-system` SF Pro typography, `#0071E3` pill CTAs, fixed frosted-glass sticky nav).  
> **Dataset**: Real Kaggle Framingham Heart Study Dataset ($N=4,221$ clinical records).

---

## 📌 Project Overview

**HealthRisk** is an educational decision-support web application demonstrating core ML Unit 1 probability concepts with pure Python implementations (no external ML/statistics packages like numpy or scipy hiding the formulas):

1. **Prior Probability $P(C)$**: Dynamic base rate adjustment based on age group and family history.
2. **Bernoulli Conditional Likelihood $P(S_i \mid C)$**: Discrete Bernoulli random variable likelihood matrix for present and absent symptoms (with complement rule derivation $1 - P(S_i = 1 \mid C)$ for absent symptoms).
3. **Bayes' Theorem & Naive Bayes Chaining**: Manual calculation of joint likelihoods, marginal evidence $P(\mathbf{S})$, and normalizing constants.
4. **Posterior Probability $P(C \mid \mathbf{S})$**: Multi-condition posterior risk estimation (Type 2 Diabetes & Cardiovascular Disease Risk) with Viva Math Inspector breakdown.
5. **Expectation $E[X]$**: Manual mean over population datasets ($N=4,221$) and personal time-series risk scores.
   $$E[X] = \frac{1}{n} \sum_{i=1}^n x_i$$
6. **Variance $\text{Var}(X)$ & Standard Deviation**: Manual spread and uncertainty calculation.
   $$\text{Var}(X) = \frac{1}{n} \sum_{i=1}^n (x_i - E[X])^2$$
7. **Covariance $\text{Cov}(X, Y)$**: Manual joint variability calculation between Body Mass Index (BMI) and Systolic Blood Pressure with dynamic plain-English interpretation.
   $$\text{Cov}(X, Y) = \frac{1}{n} \sum_{i=1}^n (x_i - E[X])(y_i - E[Y])$$

---

## 🛠️ Codebase Structure

```
ML-Unit1/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI server & Auth / Trend / CSV endpoints
│   ├── database.py                 # SQLite database layer with Auth tables & User Isolation
│   ├── bayes_engine/               # Pure Python Math Module
│   │   ├── __init__.py
│   │   ├── conditions_config.py    # Conditions & Symptoms configuration catalog
│   │   └── engine.py               # prior(), likelihood(), posterior(), expectation(), variance(), covariance()
│   ├── static/
│   │   ├── index.html              # Apple Light Mode SPA UI with Auth Modal, Personal Trends & CSV Upload
│   │   ├── styles.css              # Apple Design System Styling (#F5F5F7 canvas, #0071E3 CTAs, frosted glass)
│   │   └── app.js                  # Frontend SPA logic & Bivariate Scatter Plot Canvas Renderer
├── tests/
│   └── test_bayes_engine.py        # 5/5 Passing Unit Tests
├── framingham_kaggle_real.csv      # Real Kaggle Framingham Heart Study Dataset (N=4,221 records)
├── requirements.txt                # Dependencies (fastapi, uvicorn, pydantic, pytest)
├── .gitignore                      # Git exclusion rules
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Installation & Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/ML-Unit1.git
cd ML-Unit1

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Web Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to: **`http://127.0.0.1:8000/`**

### 3. Run Automated Tests
```bash
pytest
```

---

## 🔬 API Endpoints

- `POST /api/register` & `POST /api/login` & `POST /api/logout`: Self-contained account authentication with PBKDF2-HMAC-SHA256 salted password hashing and HTTP-only session cookies.
- `GET /api/me`: Returns current user session details.
- `POST /api/assess`: Computes Bayesian posteriors across selected conditions with step-by-step formula trace, attached to user ID.
- `GET /api/assessments`: Retrieves audit log of historical runs for current logged-in user.
- `GET /api/user_trends`: Computes personal time-series $E[\text{Risk}]$ and $\text{Var}(\text{Risk})$ across user's past runs (requires 3+ runs).
- `POST /population_stats/upload_csv`: Uploads custom CSV dataset (`age,bmi,systolic_bp,risk_score`), validates row ranges, and sets active dataset.
- `GET /population_stats/expectation_variance`: Returns manual $E[X]$, $\text{Var}(X)$, $\text{SD}(X)$ on active dataset.
- `GET /population_stats/covariance`: Returns manual $\text{Cov}(\text{BMI}, \text{Systolic BP})$ and interpretation on active dataset.

---

## 📊 Verification & Reference Case (Rahul Sharma, 45, FamHist YES)

- **Reference Test Case**: Rahul Sharma (45, Family History YES, Symptoms: `unexplained_fatigue`, `chest_tightness`, `dizziness_headaches`):
  - **Cardiovascular Disease Risk**: **88.96%** (Verified reproducible across all phases).
- **Unit Test Suite**: 5/5 unit tests passing cleanly.
- **Population Dataset**: Real Kaggle Framingham Heart Study Dataset ($N=4,221$ records) yielding $E[\text{Risk}] = 46.85\%$, $\text{Var}(\text{Risk}) = 228.56$, and $\text{Cov}(\text{BMI}, \text{Systolic BP}) = +29.29$.
