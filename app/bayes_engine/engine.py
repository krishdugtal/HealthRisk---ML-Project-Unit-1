"""
HealthRisk - Pure Python Bayesian Risk Engine & Statistics Engine (ML Unit 1 Project)

This module implements probability and Bayesian concepts explicitly without external ML libraries.
Every function contains a detailed docstring explaining the exact mathematical formula implemented.
"""

from typing import Dict, List, Any, Tuple
import math

from app.bayes_engine.conditions_config import CONDITIONS, SYMPTOMS



def prior(condition_id: str, age_group: str, family_history: str) -> Dict[str, Any]:
    """
    Computes the prior probability P(Condition) adjusted for age group and family history.

    Formula implemented:
    P(C) = clip( P_base(C) * Factor_age * Factor_fam_history, 0.001, 0.999 )

    Parameters:
    - condition_id: Key identifying the target condition (e.g. 'diabetes_t2')
    - age_group: Age bracket ('<30', '30-50', '>50')
    - family_history: Family history status ('yes', 'no')

    Returns:
    Dict containing base prior, multipliers, adjusted prior P(C), and P(not C) = 1 - P(C).
    """
    if condition_id not in CONDITIONS:
        raise ValueError(f"Unknown condition ID: {condition_id}")

    cond_meta = CONDITIONS[condition_id]
    base_prior = cond_meta["base_prior"]

    age_factor = cond_meta["age_multipliers"].get(age_group.lower(), 1.0)
    fam_factor = cond_meta["family_history_multipliers"].get(family_history.lower(), 1.0)

    raw_prior = base_prior * age_factor * fam_factor
    # Bound within [0.001, 0.999] for numerical stability
    adj_prior = max(0.001, min(0.999, raw_prior))
    p_not_c = 1.0 - adj_prior

    return {
        "condition_id": condition_id,
        "condition_name": cond_meta["name"],
        "base_prior": base_prior,
        "age_factor": age_factor,
        "family_history_factor": fam_factor,
        "adjusted_prior_p_c": round(adj_prior, 6),
        "adjusted_prior_p_not_c": round(p_not_c, 6),
        "formula": "P(C) = P_base(C) * Factor_age * Factor_family_history"
    }


def likelihood(symptom_id: str, condition_id: str, present: bool = True) -> Dict[str, float]:
    """
    Retrieves the conditional likelihood P(S_i | C) or P(S_i | not C) modeled as a discrete Bernoulli RV.

    Formula implemented (Bernoulli Random Variable):
    If present = True:
        P(S_i = 1 | C) = L_i
        P(S_i = 1 | not C) = L'_i
    If present = False:
        P(S_i = 0 | C) = 1 - L_i
        P(S_i = 0 | not C) = 1 - L'_i

    Parameters:
    - symptom_id: Key identifying the symptom
    - condition_id: Key identifying the condition
    - present: True if patient reports symptom, False if absent

    Returns:
    Dict containing P(S_i | C) and P(S_i | not C).
    """
    if symptom_id not in SYMPTOMS:
        raise ValueError(f"Unknown symptom ID: {symptom_id}")
    if condition_id not in CONDITIONS:
        raise ValueError(f"Unknown condition ID: {condition_id}")

    sym_data = SYMPTOMS[symptom_id]["likelihoods"][condition_id]
    p_s_given_c_raw = sym_data["p_s_given_c"]
    p_s_given_not_c_raw = sym_data["p_s_given_not_c"]

    if present:
        p_c = p_s_given_c_raw
        p_not_c = p_s_given_not_c_raw
    else:
        p_c = 1.0 - p_s_given_c_raw
        p_not_c = 1.0 - p_s_given_not_c_raw

    return {
        "symptom_id": symptom_id,
        "symptom_name": SYMPTOMS[symptom_id]["name"],
        "present": present,
        "p_s_given_c": round(p_c, 6),
        "p_s_given_not_c": round(p_not_c, 6)
    }


def posterior(
    selected_symptoms: List[str],
    condition_id: str,
    age_group: str,
    family_history: str,
    all_symptom_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Calculates the posterior probability P(Condition | Symptoms) using Bayes' Theorem with Naive Bayes chaining.

    Formula implemented (Bayes' Theorem for Naive Bayes):
    P(C | S_1...S_n) = [ P(C) * Prod_{i=1}^n P(S_i | C) ] / P(S_1...S_n)

    Where Marginal Evidence P(S_1...S_n) is:
    P(S_1...S_n) = P(C) * Prod P(S_i | C) + P(not C) * Prod P(S_i | not C)

    Parameters:
    - selected_symptoms: List of symptom IDs reported as present
    - condition_id: Key of target condition
    - age_group: Age bracket ('<30', '30-50', '>50')
    - family_history: Family history status ('yes', 'no')
    - all_symptom_ids: List of symptom IDs evaluated (if None, defaults to all known symptoms in SYMPTOMS)

    Returns:
    Dict containing detailed step-by-step mathematical breakdown for Viva inspection.
    """
    if all_symptom_ids is None:
        all_symptom_ids = list(SYMPTOMS.keys())

    prior_info = prior(condition_id, age_group, family_history)
    p_c = prior_info["adjusted_prior_p_c"]
    p_not_c = prior_info["adjusted_prior_p_not_c"]

    symptom_breakdown = []
    joint_likelihood_c = 1.0
    joint_likelihood_not_c = 1.0

    for sym_id in all_symptom_ids:
        is_present = sym_id in selected_symptoms
        lh = likelihood(sym_id, condition_id, present=is_present)
        
        joint_likelihood_c *= lh["p_s_given_c"]
        joint_likelihood_not_c *= lh["p_s_given_not_c"]

        symptom_breakdown.append({
            "symptom_id": sym_id,
            "symptom_name": lh["symptom_name"],
            "present": is_present,
            "p_s_given_c": lh["p_s_given_c"],
            "p_s_given_not_c": lh["p_s_given_not_c"]
        })

    # Unnormalized joint probabilities P(S, C) and P(S, not C)
    joint_prob_c = joint_likelihood_c * p_c
    joint_prob_not_c = joint_likelihood_not_c * p_not_c

    # Marginal Likelihood / Normalizing Constant Evidence P(S)
    evidence_p_s = joint_prob_c + joint_prob_not_c

    if evidence_p_s == 0:
        posterior_p_c = p_c
    else:
        posterior_p_c = joint_prob_c / evidence_p_s

    # Qualitative risk category
    if posterior_p_c < 0.25:
        risk_level = "Low Risk"
    elif posterior_p_c < 0.60:
        risk_level = "Moderate Risk"
    elif posterior_p_c < 0.85:
        risk_level = "Elevated Risk"
    else:
        risk_level = "High Risk"

    return {
        "condition_id": condition_id,
        "condition_name": CONDITIONS[condition_id]["name"],
        "prior_step": prior_info,
        "symptoms_evaluated": symptom_breakdown,
        "joint_likelihood_given_c": round(joint_likelihood_c, 8),
        "joint_likelihood_given_not_c": round(joint_likelihood_not_c, 8),
        "joint_probability_c": round(joint_prob_c, 8),
        "joint_probability_not_c": round(joint_prob_not_c, 8),
        "evidence_marginal_p_s": round(evidence_p_s, 8),
        "posterior_probability": round(posterior_p_c, 6),
        "posterior_percentage": round(posterior_p_c * 100, 2),
        "risk_level": risk_level,
        "math_formula_steps": {
            "step_1_prior": f"P(C) = {p_c:.4f}, P(¬C) = {p_not_c:.4f}",
            "step_2_likelihood": f"P(S|C) = {joint_likelihood_c:.6e}, P(S|¬C) = {joint_likelihood_not_c:.6e}",
            "step_3_evidence": f"P(S) = P(S|C)·P(C) + P(S|¬C)·P(¬C) = {joint_prob_c:.6e} + {joint_prob_not_c:.6e} = {evidence_p_s:.6e}",
            "step_4_posterior": f"P(C|S) = P(S|C)·P(C) / P(S) = {joint_prob_c:.6e} / {evidence_p_s:.6e} = {posterior_p_c:.4f} ({posterior_p_c*100:.1f}%)"
        }
    }


def expectation(values: List[float]) -> Dict[str, Any]:
    """
    Computes Expected Value E[X] (Mean) for a population sample.

    Formula implemented:
    E[X] = (1 / n) * Sum_{i=1}^n x_i

    Parameters:
    - values: List of quantitative metric values or risk scores

    Returns:
    Dict containing expected_value (mean), n (sample size), formula_used.
    """
    if not values:
        raise ValueError("Cannot calculate expectation of an empty list.")

    n = len(values)
    exp_val = sum(values) / n

    return {
        "expected_value": round(exp_val, 4),
        "mean": round(exp_val, 4),
        "n": n,
        "formula_used": "E[X] = (1/n) * ∑ x_i"
    }


def variance(values: List[float]) -> Dict[str, Any]:
    """
    Computes Variance Var(X) and Standard Deviation SD(X) measuring population spread/uncertainty.

    Formula implemented:
    Var(X) = (1 / n) * Sum_{i=1}^n (x_i - E[X])^2

    Parameters:
    - values: List of quantitative metric values or risk scores

    Returns:
    Dict containing mean, variance, standard_deviation, n, formula_used.
    """
    if not values:
        raise ValueError("Cannot calculate variance of an empty list.")

    n = len(values)
    exp_res = expectation(values)
    e_x = exp_res["expected_value"]

    var_val = sum((x - e_x) ** 2 for x in values) / n
    std_dev = math.sqrt(var_val)

    return {
        "mean": e_x,
        "variance": round(var_val, 4),
        "standard_deviation": round(std_dev, 4),
        "n": n,
        "formula_used": "Var(X) = (1/n) * ∑ (x_i - E[X])²"
    }


def covariance(
    series_x: List[float],
    series_y: List[float],
    name_x: str = "BMI",
    name_y: str = "Systolic BP"
) -> Dict[str, Any]:
    """
    Computes Covariance Cov(X, Y) measuring joint linear variability between two health variables.

    Formula implemented:
    Cov(X, Y) = (1 / n) * Sum_{i=1}^n (x_i - E[X]) * (y_i - E[Y])

    Parameters:
    - series_x: First series of values (e.g. BMI)
    - series_y: Second series of values (e.g. Systolic Blood Pressure)
    - name_x: Plain text label for metric X
    - name_y: Plain text label for metric Y

    Returns:
    Dict containing covariance, formula_used, interpretation, n, mean_x, mean_y.
    """
    if len(series_x) != len(series_y):
        raise ValueError("Series X and Series Y must be of equal length.")
    if len(series_x) == 0:
        raise ValueError("Cannot calculate covariance of empty series.")

    n = len(series_x)
    mean_x = sum(series_x) / n
    mean_y = sum(series_y) / n

    cov_val = sum((x - mean_x) * (y - mean_y) for x, y in zip(series_x, series_y)) / n

    # Plain-English Interpretation based on sign and threshold
    if cov_val > 0.1:
        interp = f"As {name_x} increases, {name_y} tends to increase in this sample."
    elif cov_val < -0.1:
        interp = f"As {name_x} increases, {name_y} tends to decrease in this sample."
    else:
        interp = f"Little linear relationship between {name_x} and {name_y} in this sample."

    return {
        "covariance": round(cov_val, 4),
        "mean_x": round(mean_x, 4),
        "mean_y": round(mean_y, 4),
        "n": n,
        "formula_used": "Cov(X,Y) = (1/n) * ∑ (x_i - E[X])(y_i - E[Y])",
        "interpretation": interp,
        "name_x": name_x,
        "name_y": name_y
    }
