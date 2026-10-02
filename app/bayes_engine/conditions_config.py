"""
Conditions & Symptoms Configuration Module for HealthRisk Engine

This file defines condition base rates, age/family history multipliers,
and Bernoulli conditional likelihood tables for all supported health conditions.
Editing this configuration updates the Bayesian inference engine dynamically.
"""

CONDITIONS = {
    "diabetes_t2": {
        "name": "Type 2 Diabetes Risk",
        "description": "Metabolic risk characterized by insulin resistance and hyperglycemia.",
        "base_prior": 0.10,
        "age_multipliers": {
            "<30": 0.5,
            "30-50": 1.0,
            ">50": 1.8
        },
        "family_history_multipliers": {
            "yes": 2.0,
            "no": 1.0
        }
    },
    "cardiovascular": {
        "name": "Cardiovascular Disease Risk",
        "description": "Risk of coronary heart disease, arterial blockage, and heart events.",
        "base_prior": 0.08,
        "age_multipliers": {
            "<30": 0.4,
            "30-50": 1.0,
            ">50": 2.2
        },
        "family_history_multipliers": {
            "yes": 1.8,
            "no": 1.0
        }
    },
    "hypertension": {
        "name": "Hypertension Risk",
        "description": "Chronic high blood pressure causing vascular stress and cardiac workload.",
        "base_prior": 0.15,
        "age_multipliers": {
            "<30": 0.6,
            "30-50": 1.0,
            ">50": 1.9
        },
        "family_history_multipliers": {
            "yes": 1.7,
            "no": 1.0
        }
    }
}

SYMPTOMS = {
    "excessive_thirst": {
        "name": "Excessive Thirst (Polydipsia)",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.75, "p_s_given_not_c": 0.05},
            "cardiovascular": {"p_s_given_c": 0.10, "p_s_given_not_c": 0.05},
            "hypertension": {"p_s_given_c": 0.08, "p_s_given_not_c": 0.05}
        }
    },
    "frequent_urination": {
        "name": "Frequent Urination (Polyuria)",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.80, "p_s_given_not_c": 0.08},
            "cardiovascular": {"p_s_given_c": 0.12, "p_s_given_not_c": 0.08},
            "hypertension": {"p_s_given_c": 0.15, "p_s_given_not_c": 0.08}
        }
    },
    "unexplained_fatigue": {
        "name": "Unexplained Fatigue & Lethargy",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.65, "p_s_given_not_c": 0.20},
            "cardiovascular": {"p_s_given_c": 0.70, "p_s_given_not_c": 0.20},
            "hypertension": {"p_s_given_c": 0.50, "p_s_given_not_c": 0.20}
        }
    },
    "blurred_vision": {
        "name": "Blurred or Altered Vision",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.55, "p_s_given_not_c": 0.08},
            "cardiovascular": {"p_s_given_c": 0.20, "p_s_given_not_c": 0.08},
            "hypertension": {"p_s_given_c": 0.35, "p_s_given_not_c": 0.08}
        }
    },
    "chest_tightness": {
        "name": "Chest Tightness / Pressure",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.15, "p_s_given_not_c": 0.05},
            "cardiovascular": {"p_s_given_c": 0.82, "p_s_given_not_c": 0.04},
            "hypertension": {"p_s_given_c": 0.40, "p_s_given_not_c": 0.04}
        }
    },
    "shortness_of_breath": {
        "name": "Shortness of Breath on Exertion",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.20, "p_s_given_not_c": 0.10},
            "cardiovascular": {"p_s_given_c": 0.78, "p_s_given_not_c": 0.08},
            "hypertension": {"p_s_given_c": 0.45, "p_s_given_not_c": 0.08}
        }
    },
    "dizziness_headaches": {
        "name": "Dizziness & Morning Headaches",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.30, "p_s_given_not_c": 0.15},
            "cardiovascular": {"p_s_given_c": 0.60, "p_s_given_not_c": 0.15},
            "hypertension": {"p_s_given_c": 0.75, "p_s_given_not_c": 0.12}
        }
    },
    "slow_healing_wounds": {
        "name": "Slow-Healing Cuts or Sores",
        "likelihoods": {
            "diabetes_t2": {"p_s_given_c": 0.60, "p_s_given_not_c": 0.04},
            "cardiovascular": {"p_s_given_c": 0.15, "p_s_given_not_c": 0.04},
            "hypertension": {"p_s_given_c": 0.10, "p_s_given_not_c": 0.04}
        }
    }
}
