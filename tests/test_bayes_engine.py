"""
Unit tests for bayes_engine module (ML Unit 1 Project Phase 2)
"""
import unittest
from app.bayes_engine.engine import (
    prior,
    likelihood,
    posterior,
    expectation,
    variance,
    covariance,
    CONDITIONS,
    SYMPTOMS
)


class TestBayesEngine(unittest.TestCase):

    def test_prior_calculation(self):
        # Diabetes base prior = 0.10, age >50 factor = 1.8, family history yes factor = 2.0
        # Expected raw prior = 0.10 * 1.8 * 2.0 = 0.36
        res = prior("diabetes_t2", age_group=">50", family_history="yes")
        self.assertAlmostEqual(res["adjusted_prior_p_c"], 0.36, places=4)
        self.assertAlmostEqual(res["adjusted_prior_p_not_c"], 0.64, places=4)

    def test_likelihood_calculation(self):
        # Excessive thirst for diabetes_t2: P(S=1|C) = 0.75, P(S=1|not C) = 0.05
        lh_present = likelihood("excessive_thirst", "diabetes_t2", present=True)
        self.assertEqual(lh_present["p_s_given_c"], 0.75)
        self.assertEqual(lh_present["p_s_given_not_c"], 0.05)

        lh_absent = likelihood("excessive_thirst", "diabetes_t2", present=False)
        self.assertEqual(lh_absent["p_s_given_c"], 0.25)
        self.assertEqual(lh_absent["p_s_given_not_c"], 0.95)

    def test_posterior_bayes_rule_both_conditions(self):
        # Verify Bayesian inference works for both Type 2 Diabetes and Cardiovascular Disease
        for cond_id in ["diabetes_t2", "cardiovascular"]:
            res = posterior(
                selected_symptoms=["excessive_thirst", "frequent_urination"],
                condition_id=cond_id,
                age_group="30-50",
                family_history="no"
            )
            self.assertIn("posterior_probability", res)
            self.assertIn("math_formula_steps", res)
            self.assertIn("step_4_posterior", res["math_formula_steps"])

    def test_expectation_variance(self):
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        exp_res = expectation(data)
        # E[X] = (10+20+30+40+50)/5 = 30.0
        self.assertEqual(exp_res["mean"], 30.0)

        var_res = variance(data)
        # Var(X) = ((10-30)^2 + (20-30)^2 + (30-30)^2 + (40-30)^2 + (50-30)^2) / 5
        #        = (400 + 100 + 0 + 100 + 400) / 5 = 1000 / 5 = 200.0
        self.assertEqual(var_res["variance"], 200.0)

    def test_covariance(self):
        bmi = [20.0, 25.0, 30.0, 35.0]
        bp = [110.0, 120.0, 130.0, 140.0]
        cov_res = covariance(bmi, bp, name_x="BMI", name_y="Systolic BP")
        # mean(bmi) = 27.5, mean(bp) = 125.0
        # cov = ((-7.5*-15) + (-2.5*-5) + (2.5*5) + (7.5*15)) / 4 = (112.5 + 12.5 + 12.5 + 112.5)/4 = 250/4 = 62.5
        self.assertEqual(cov_res["covariance"], 62.5)
        self.assertIn("tends to increase", cov_res["interpretation"])


if __name__ == "__main__":
    unittest.main()
