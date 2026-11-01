#!/usr/bin/env python3
"""
USSE NOOSPHERE • MISSION 04: DELIVERABLE 02
Station: Communications & Protocol Officer (Mazhar Uddin Abbasi)
Module: Implicit Reward Evaluator & Bradley-Terry Calibration Engine

Deliverable Specifications:
- Extract scalar implicit rewards for chosen and rejected completions: r(x, y) = beta * (log pi_theta - log pi_ref).
- Compute pairwise win-rate, reward margin separation: Delta r = r(x, y_w) - r(x, y_l).
- Generate calibration metrics comparing predicted Bradley-Terry probabilities sigma(Delta r) against empirical accuracy.
- Evaluate policy alignment over multi-turn communication transmissions.
"""

import math
import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple

class ImplicitRewardEvaluator:
    """
    Evaluates implicit rewards and Bradley-Terry choice probabilities
    from active policy and reference model log-probabilities.
    """
    def __init__(self, beta: float = 0.1):
        self.beta = beta

    def compute_implicit_rewards(
        self,
        policy_logps: torch.Tensor,
        reference_logps: torch.Tensor
    ) -> torch.Tensor:
        """
        r(x, y) = beta * (log pi_theta(y|x) - log pi_ref(y|x))
        """
        return self.beta * (policy_logps - reference_logps)

    def evaluate_preference_pairs(
        self,
        policy_chosen_logps: torch.Tensor,
        policy_rejected_logps: torch.Tensor,
        reference_chosen_logps: torch.Tensor,
        reference_rejected_logps: torch.Tensor
    ) -> Dict[str, float]:
        """
        Computes comprehensive preference metrics across a batch of evaluation pairs.
        """
        chosen_rewards = self.compute_implicit_rewards(policy_chosen_logps, reference_chosen_logps)
        rejected_rewards = self.compute_implicit_rewards(policy_rejected_logps, reference_rejected_logps)
        
        # Reward margin: Delta r = r_w - r_l
        margins = chosen_rewards - rejected_rewards
        
        # Predicted preference probability under Bradley-Terry: P(y_w > y_l) = sigma(Delta r)
        # Note: Delta r already contains beta multiplier
        predicted_probs = torch.sigmoid(margins)
        
        # Empirical accuracy: fraction where r_w > r_l
        pairwise_accuracy = (margins > 0.0).float().mean().item()
        
        # Margin statistics
        mean_margin = margins.mean().item()
        std_margin = margins.std().item()
        mean_chosen_reward = chosen_rewards.mean().item()
        mean_rejected_reward = rejected_rewards.mean().item()
        
        return {
            "pairwise_accuracy": pairwise_accuracy,
            "mean_margin": mean_margin,
            "std_margin": std_margin,
            "mean_chosen_reward": mean_chosen_reward,
            "mean_rejected_reward": mean_rejected_reward,
            "mean_predicted_prob": predicted_probs.mean().item(),
            "chosen_rewards": chosen_rewards.detach().cpu().numpy(),
            "rejected_rewards": rejected_rewards.detach().cpu().numpy(),
            "margins": margins.detach().cpu().numpy()
        }

    def compute_calibration_curve(
        self,
        margins: np.ndarray,
        labels: np.ndarray,
        n_bins: int = 5
    ) -> List[Tuple[float, float, int]]:
        """
        Computes reliability calibration: binned predicted probability vs. empirical win rate.
        """
        predicted_probs = 1.0 / (1.0 + np.exp(-margins))
        bins = np.linspace(0.0, 1.0, n_bins + 1)
        calibration_data = []
        
        for i in range(n_bins):
            bin_lower = bins[i]
            bin_upper = bins[i + 1]
            mask = (predicted_probs >= bin_lower) & (predicted_probs < bin_upper)
            if np.sum(mask) > 0:
                bin_prob = np.mean(predicted_probs[mask])
                bin_acc = np.mean(labels[mask])
                count = int(np.sum(mask))
                calibration_data.append((float(bin_prob), float(bin_acc), count))
                
        return calibration_data

def run_protocol_officer_verification():
    print("=" * 78)
    print("USSE NOOSPHERE • COMMUNICATIONS & PROTOCOL OFFICER VERIFICATION")
    print("Officer: Mazhar Uddin Abbasi • Sector SEC-04-ORI")
    print("Module: Implicit Reward Evaluator & Bradley-Terry Calibration")
    print("=" * 78)
    
    torch.manual_seed(101)
    np.random.seed(101)
    evaluator = ImplicitRewardEvaluator(beta=0.1)
    
    # Simulate an evaluation suite of 200 telemetry communications
    n_pairs = 200
    ref_chosen = torch.randn(n_pairs) * 5.0 - 50.0
    ref_rejected = torch.randn(n_pairs) * 5.0 - 52.0
    
    # Aligned policy pushes chosen logps higher and rejected lower
    policy_chosen = ref_chosen + torch.randn(n_pairs) * 1.5 + 4.0
    policy_rejected = ref_rejected - torch.randn(n_pairs) * 1.5 - 3.0
    
    metrics = evaluator.evaluate_preference_pairs(
        policy_chosen, policy_rejected, ref_chosen, ref_rejected
    )
    
    print("\n[Step 1: Preference Separation & Implicit Reward Metrics]")
    print(f"  * Pairwise Preference Accuracy : {metrics['pairwise_accuracy'] * 100.0:.2f}%")
    print(f"  * Mean Reward Separation Margin : {metrics['mean_margin']:+.4f} (std: {metrics['std_margin']:.4f})")
    print(f"  * Mean Chosen Completion Reward : {metrics['mean_chosen_reward']:+.4f}")
    print(f"  * Mean Rejected Completion Reward: {metrics['mean_rejected_reward']:+.4f}")
    print(f"  * Mean Bradley-Terry Win Prob   : {metrics['mean_predicted_prob'] * 100.0:.2f}%")
    
    # Calibration Analysis
    labels = np.ones(n_pairs) # All pairs are ground-truth chosen > rejected
    calib = evaluator.compute_calibration_curve(metrics["margins"], labels, n_bins=5)
    print("\n[Step 2: Bradley-Terry Calibration Curve Bins]")
    print("   Bin Range | Pred Win-Prob | Empirical Win-Rate | Sample Count")
    print("   " + "-" * 56)
    for p_pred, p_emp, cnt in calib:
        print(f"   [{p_pred:.3f}]   |    {p_pred * 100:6.2f}%   |     {p_emp * 100:6.2f}%      | {cnt:4d}")
        
    assert metrics["pairwise_accuracy"] > 0.90, "Pairwise accuracy failed quality threshold!"
    assert metrics["mean_margin"] > 0.0, "Chosen completions must maintain positive margin separation!"
    
    print("\n" + "=" * 78)
    print("PROTOCOL OFFICER SIGNOFF: Implicit reward telemetry and BT metrics certified.")
    print("=" * 78)

if __name__ == "__main__":
    run_protocol_officer_verification()

