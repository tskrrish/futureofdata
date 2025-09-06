"""
Statistical Analysis Module for A/B Test Framework
Provides robust statistical calculations for measuring campaign message impact
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class StatisticalResult:
    metric_name: str
    control_value: float
    variant_value: float
    sample_size_control: int
    sample_size_variant: int
    effect_size: float
    lift_percentage: float
    p_value: float
    confidence_level: float
    confidence_interval: Tuple[float, float]
    is_statistically_significant: bool
    power: float
    required_sample_size: int
    test_type: str
    interpretation: str

@dataclass
class BayesianResult:
    metric_name: str
    probability_variant_better: float
    credible_interval: Tuple[float, float]
    expected_lift: float
    risk_of_loss: float
    potential_gain: float

class StatisticalAnalyzer:
    """Advanced statistical analysis for A/B test results"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        self.z_score = stats.norm.ppf(1 - self.alpha / 2)
    
    def analyze_conversion_rate(self, control_conversions: int, control_total: int,
                              variant_conversions: int, variant_total: int) -> StatisticalResult:
        """Analyze conversion rate difference between control and variant"""
        
        if control_total == 0 or variant_total == 0:
            return self._create_empty_result("Conversion Rate", "Insufficient data")
        
        control_rate = control_conversions / control_total
        variant_rate = variant_conversions / variant_total
        
        # Chi-square test for proportion differences
        contingency_table = np.array([
            [control_conversions, control_total - control_conversions],
            [variant_conversions, variant_total - variant_conversions]
        ])
        
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Calculate effect size (Cohen's h for proportions)
        effect_size = self._cohens_h(control_rate, variant_rate)
        
        # Calculate confidence interval for difference in proportions
        diff = variant_rate - control_rate
        se_diff = math.sqrt(
            (control_rate * (1 - control_rate) / control_total) +
            (variant_rate * (1 - variant_rate) / variant_total)
        )
        
        ci_lower = diff - self.z_score * se_diff
        ci_upper = diff + self.z_score * se_diff
        
        lift_percentage = ((variant_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0
        
        # Statistical power calculation
        power = self._calculate_power_proportions(
            control_rate, variant_rate, control_total, variant_total
        )
        
        # Required sample size for desired power
        required_n = self._required_sample_size_proportions(
            control_rate, variant_rate, power=0.8
        )
        
        return StatisticalResult(
            metric_name="Conversion Rate",
            control_value=control_rate,
            variant_value=variant_rate,
            sample_size_control=control_total,
            sample_size_variant=variant_total,
            effect_size=effect_size,
            lift_percentage=lift_percentage,
            p_value=p_value,
            confidence_level=self.confidence_level,
            confidence_interval=(ci_lower, ci_upper),
            is_statistically_significant=p_value < self.alpha,
            power=power,
            required_sample_size=required_n,
            test_type="Chi-square test",
            interpretation=self._interpret_result(p_value, lift_percentage, power)
        )
    
    def analyze_continuous_metric(self, control_values: List[float], 
                                variant_values: List[float],
                                metric_name: str = "Continuous Metric") -> StatisticalResult:
        """Analyze continuous metrics (e.g., time spent, satisfaction scores)"""
        
        if not control_values or not variant_values:
            return self._create_empty_result(metric_name, "Insufficient data")
        
        control_array = np.array(control_values)
        variant_array = np.array(variant_values)
        
        control_mean = np.mean(control_array)
        variant_mean = np.mean(variant_array)
        
        # Check for normality (Shapiro-Wilk test for small samples)
        if len(control_values) < 50 and len(variant_values) < 50:
            _, control_normal_p = stats.shapiro(control_array)
            _, variant_normal_p = stats.shapiro(variant_array)
            is_normal = control_normal_p > 0.05 and variant_normal_p > 0.05
        else:
            is_normal = True  # Assume normality for large samples (CLT)
        
        if is_normal:
            # Use t-test for normal distributions
            t_stat, p_value = ttest_ind(variant_array, control_array, equal_var=False)
            test_type = "Welch's t-test"
            
            # Effect size (Cohen's d)
            pooled_std = math.sqrt(
                ((len(control_array) - 1) * np.var(control_array, ddof=1) +
                 (len(variant_array) - 1) * np.var(variant_array, ddof=1)) /
                (len(control_array) + len(variant_array) - 2)
            )
            effect_size = (variant_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        else:
            # Use Mann-Whitney U test for non-normal distributions
            u_stat, p_value = mannwhitneyu(variant_array, control_array, alternative='two-sided')
            test_type = "Mann-Whitney U test"
            
            # Effect size (rank-biserial correlation)
            n1, n2 = len(control_array), len(variant_array)
            effect_size = 1 - (2 * u_stat) / (n1 * n2)
        
        # Calculate confidence interval for the difference in means
        se_diff = math.sqrt(
            np.var(control_array, ddof=1) / len(control_array) +
            np.var(variant_array, ddof=1) / len(variant_array)
        )
        
        diff = variant_mean - control_mean
        ci_lower = diff - self.z_score * se_diff
        ci_upper = diff + self.z_score * se_diff
        
        lift_percentage = ((variant_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0
        
        # Statistical power (approximate)
        power = self._calculate_power_ttest(control_array, variant_array, effect_size)
        
        return StatisticalResult(
            metric_name=metric_name,
            control_value=control_mean,
            variant_value=variant_mean,
            sample_size_control=len(control_values),
            sample_size_variant=len(variant_values),
            effect_size=effect_size,
            lift_percentage=lift_percentage,
            p_value=p_value,
            confidence_level=self.confidence_level,
            confidence_interval=(ci_lower, ci_upper),
            is_statistically_significant=p_value < self.alpha,
            power=power,
            required_sample_size=self._required_sample_size_ttest(effect_size),
            test_type=test_type,
            interpretation=self._interpret_result(p_value, lift_percentage, power)
        )
    
    def bayesian_analysis(self, control_conversions: int, control_total: int,
                         variant_conversions: int, variant_total: int,
                         prior_alpha: float = 1, prior_beta: float = 1) -> BayesianResult:
        """Bayesian analysis for conversion rates using Beta-Binomial model"""
        
        # Posterior distributions
        control_alpha = prior_alpha + control_conversions
        control_beta = prior_beta + control_total - control_conversions
        
        variant_alpha = prior_alpha + variant_conversions
        variant_beta = prior_beta + variant_total - variant_conversions
        
        # Monte Carlo simulation
        n_simulations = 100000
        control_samples = np.random.beta(control_alpha, control_beta, n_simulations)
        variant_samples = np.random.beta(variant_alpha, variant_beta, n_simulations)
        
        # Probability that variant is better
        prob_variant_better = np.mean(variant_samples > control_samples)
        
        # Expected lift
        lift_samples = (variant_samples - control_samples) / control_samples
        expected_lift = np.mean(lift_samples) * 100
        
        # Credible interval for lift
        ci_lower, ci_upper = np.percentile(lift_samples * 100, [2.5, 97.5])
        
        # Risk calculations
        negative_lifts = lift_samples[lift_samples < 0]
        risk_of_loss = len(negative_lifts) / len(lift_samples)
        
        positive_lifts = lift_samples[lift_samples > 0]
        potential_gain = np.mean(positive_lifts) * 100 if len(positive_lifts) > 0 else 0
        
        return BayesianResult(
            metric_name="Conversion Rate",
            probability_variant_better=prob_variant_better,
            credible_interval=(ci_lower, ci_upper),
            expected_lift=expected_lift,
            risk_of_loss=risk_of_loss,
            potential_gain=potential_gain
        )
    
    def sequential_analysis(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sequential analysis to monitor test progress and recommend early stopping"""
        
        if not data_points:
            return {"recommendation": "continue", "reason": "Insufficient data"}
        
        df = pd.DataFrame(data_points)
        df['cumulative_control_conv'] = df['control_conversions'].cumsum()
        df['cumulative_control_total'] = df['control_total'].cumsum()
        df['cumulative_variant_conv'] = df['variant_conversions'].cumsum()
        df['cumulative_variant_total'] = df['variant_total'].cumsum()
        
        # Calculate p-values over time
        p_values = []
        for i, row in df.iterrows():
            if row['cumulative_control_total'] > 0 and row['cumulative_variant_total'] > 0:
                result = self.analyze_conversion_rate(
                    int(row['cumulative_control_conv']),
                    int(row['cumulative_control_total']),
                    int(row['cumulative_variant_conv']),
                    int(row['cumulative_variant_total'])
                )
                p_values.append(result.p_value)
            else:
                p_values.append(1.0)
        
        df['p_value'] = p_values
        
        # Check for early stopping conditions
        latest_p = p_values[-1] if p_values else 1.0
        
        if latest_p < 0.01:  # Very strong evidence
            return {
                "recommendation": "stop_early",
                "reason": "Strong statistical significance achieved",
                "confidence": "high"
            }
        elif latest_p < self.alpha and len(data_points) >= 100:  # Minimum sample size
            return {
                "recommendation": "stop_early", 
                "reason": "Statistical significance achieved with adequate sample",
                "confidence": "medium"
            }
        elif len(data_points) >= 1000 and latest_p > 0.5:  # Large sample, no effect
            return {
                "recommendation": "stop_early",
                "reason": "Large sample with no detectable effect",
                "confidence": "medium"
            }
        else:
            return {
                "recommendation": "continue",
                "reason": "Insufficient evidence for early stopping",
                "sample_size": len(data_points),
                "current_p_value": latest_p
            }
    
    def multi_variant_analysis(self, variants_data: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Analyze multiple variants using ANOVA and post-hoc tests"""
        
        if len(variants_data) < 3:
            return {"error": "Multi-variant analysis requires at least 3 variants"}
        
        # Prepare data for ANOVA
        conversion_rates = []
        variant_labels = []
        
        for variant_name, data in variants_data.items():
            rate = data['conversions'] / data['total'] if data['total'] > 0 else 0
            conversion_rates.append(rate)
            variant_labels.append(variant_name)
        
        # One-way ANOVA (simplified - in practice, use proper proportion tests)
        f_stat, p_value = stats.f_oneway(*[
            [data['conversions'] / data['total']] * data['total'] 
            for data in variants_data.values() if data['total'] > 0
        ])
        
        # Pairwise comparisons (Bonferroni correction)
        pairwise_results = {}
        variant_names = list(variants_data.keys())
        
        for i in range(len(variant_names)):
            for j in range(i + 1, len(variant_names)):
                var1, var2 = variant_names[i], variant_names[j]
                data1, data2 = variants_data[var1], variants_data[var2]
                
                result = self.analyze_conversion_rate(
                    data1['conversions'], data1['total'],
                    data2['conversions'], data2['total']
                )
                
                # Apply Bonferroni correction
                n_comparisons = len(variant_names) * (len(variant_names) - 1) / 2
                adjusted_p = min(1.0, result.p_value * n_comparisons)
                
                pairwise_results[f"{var1}_vs_{var2}"] = {
                    "p_value": result.p_value,
                    "adjusted_p_value": adjusted_p,
                    "is_significant": adjusted_p < self.alpha,
                    "lift_percentage": result.lift_percentage
                }
        
        return {
            "overall_test": {
                "f_statistic": f_stat,
                "p_value": p_value,
                "is_significant": p_value < self.alpha
            },
            "pairwise_comparisons": pairwise_results,
            "best_variant": max(variants_data.items(), 
                              key=lambda x: x[1]['conversions'] / x[1]['total'] if x[1]['total'] > 0 else 0)[0]
        }
    
    def sample_size_calculator(self, baseline_rate: float, minimum_detectable_effect: float,
                             power: float = 0.8, alpha: float = 0.05) -> Dict[str, int]:
        """Calculate required sample sizes for different scenarios"""
        
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # Effect size
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        
        # Two-proportion z-test sample size
        p_pooled = (p1 + p2) / 2
        
        n = (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) + 
             z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2 / (p2 - p1)**2
        
        return {
            "per_variant": math.ceil(n),
            "total": math.ceil(n * 2),
            "baseline_rate": baseline_rate,
            "target_rate": p2,
            "minimum_detectable_effect": minimum_detectable_effect,
            "power": power,
            "alpha": alpha
        }
    
    def _cohens_h(self, p1: float, p2: float) -> float:
        """Calculate Cohen's h for effect size between two proportions"""
        return 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
    
    def _calculate_power_proportions(self, p1: float, p2: float, n1: int, n2: int) -> float:
        """Calculate statistical power for two-proportion test"""
        if p1 == p2 or n1 == 0 or n2 == 0:
            return 0.0
        
        p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
        se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        se_separate = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        z_beta = (abs(p2 - p1) - z_alpha * se_pooled) / se_separate
        
        power = stats.norm.cdf(z_beta)
        return max(0.0, min(1.0, power))
    
    def _calculate_power_ttest(self, control: np.ndarray, variant: np.ndarray, 
                              effect_size: float) -> float:
        """Calculate statistical power for t-test"""
        n1, n2 = len(control), len(variant)
        
        if n1 == 0 or n2 == 0 or effect_size == 0:
            return 0.0
        
        # Approximate power calculation
        ncp = effect_size * math.sqrt((n1 * n2) / (n1 + n2))
        critical_t = stats.t.ppf(1 - self.alpha / 2, n1 + n2 - 2)
        
        power = 1 - stats.t.cdf(critical_t, n1 + n2 - 2, ncp)
        return max(0.0, min(1.0, power))
    
    def _required_sample_size_proportions(self, p1: float, p2: float, 
                                        power: float = 0.8) -> int:
        """Calculate required sample size for proportion test"""
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        p_avg = (p1 + p2) / 2
        
        n = ((z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + 
              z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) / (p2 - p1))**2
        
        return math.ceil(n)
    
    def _required_sample_size_ttest(self, effect_size: float, power: float = 0.8) -> int:
        """Calculate required sample size for t-test"""
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        n = 2 * ((z_alpha + z_beta) / effect_size)**2
        return math.ceil(n)
    
    def _create_empty_result(self, metric_name: str, interpretation: str) -> StatisticalResult:
        """Create empty result for insufficient data cases"""
        return StatisticalResult(
            metric_name=metric_name,
            control_value=0.0,
            variant_value=0.0,
            sample_size_control=0,
            sample_size_variant=0,
            effect_size=0.0,
            lift_percentage=0.0,
            p_value=1.0,
            confidence_level=self.confidence_level,
            confidence_interval=(0.0, 0.0),
            is_statistically_significant=False,
            power=0.0,
            required_sample_size=0,
            test_type="None",
            interpretation=interpretation
        )
    
    def _interpret_result(self, p_value: float, lift_percentage: float, power: float) -> str:
        """Generate interpretation of statistical results"""
        
        if power < 0.5:
            return f"Low statistical power ({power:.2f}). Consider increasing sample size."
        
        if p_value < 0.001:
            significance = "very strong"
        elif p_value < 0.01:
            significance = "strong"
        elif p_value < 0.05:
            significance = "significant"
        else:
            significance = "not significant"
        
        direction = "positive" if lift_percentage > 0 else "negative"
        
        return f"Result is {significance} with a {direction} lift of {abs(lift_percentage):.1f}%"

# Helper class for comprehensive A/B test analysis
class ABTestAnalyzer:
    """High-level analyzer that combines all statistical methods"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.analyzer = StatisticalAnalyzer(confidence_level)
        self.confidence_level = confidence_level
    
    def comprehensive_analysis(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive analysis on A/B test data"""
        
        results = {}
        
        # Conversion rate analysis
        if all(key in test_data for key in ['control_conversions', 'control_total', 
                                           'variant_conversions', 'variant_total']):
            
            conv_result = self.analyzer.analyze_conversion_rate(
                test_data['control_conversions'],
                test_data['control_total'],
                test_data['variant_conversions'],
                test_data['variant_total']
            )
            results['conversion_analysis'] = conv_result
            
            # Bayesian analysis
            bayesian_result = self.analyzer.bayesian_analysis(
                test_data['control_conversions'],
                test_data['control_total'],
                test_data['variant_conversions'],
                test_data['variant_total']
            )
            results['bayesian_analysis'] = bayesian_result
        
        # Continuous metrics analysis
        if 'control_values' in test_data and 'variant_values' in test_data:
            continuous_result = self.analyzer.analyze_continuous_metric(
                test_data['control_values'],
                test_data['variant_values'],
                test_data.get('metric_name', 'Engagement Score')
            )
            results['continuous_analysis'] = continuous_result
        
        # Multi-variant analysis
        if 'variants_data' in test_data and len(test_data['variants_data']) > 2:
            multivariant_result = self.analyzer.multi_variant_analysis(
                test_data['variants_data']
            )
            results['multivariant_analysis'] = multivariant_result
        
        # Sequential analysis
        if 'time_series_data' in test_data:
            sequential_result = self.analyzer.sequential_analysis(
                test_data['time_series_data']
            )
            results['sequential_analysis'] = sequential_result
        
        # Overall recommendation
        results['recommendation'] = self._generate_recommendation(results)
        
        return results
    
    def _generate_recommendation(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate overall recommendation based on all analyses"""
        
        recommendations = []
        
        # Check conversion analysis
        if 'conversion_analysis' in results:
            conv = results['conversion_analysis']
            if conv.is_statistically_significant and conv.lift_percentage > 0:
                recommendations.append("Implement variant - statistically significant improvement")
            elif conv.power < 0.8:
                recommendations.append("Continue test - insufficient statistical power")
            elif not conv.is_statistically_significant:
                recommendations.append("No significant difference detected")
        
        # Check Bayesian analysis
        if 'bayesian_analysis' in results:
            bayes = results['bayesian_analysis']
            if bayes.probability_variant_better > 0.95:
                recommendations.append("Strong Bayesian evidence favoring variant")
            elif bayes.risk_of_loss < 0.05:
                recommendations.append("Low risk of implementing variant")
        
        # Check sequential analysis
        if 'sequential_analysis' in results:
            seq = results['sequential_analysis']
            if seq.get('recommendation') == 'stop_early':
                recommendations.append(f"Early stopping recommended: {seq.get('reason')}")
        
        # Primary recommendation
        if not recommendations:
            primary = "Continue monitoring - inconclusive results"
        elif any("Implement variant" in r for r in recommendations):
            primary = "Implement variant"
        elif any("stop_early" in r for r in recommendations):
            primary = "Stop test early"
        else:
            primary = "Continue test"
        
        return {
            "primary_recommendation": primary,
            "detailed_reasons": recommendations,
            "confidence_level": str(self.confidence_level)
        }