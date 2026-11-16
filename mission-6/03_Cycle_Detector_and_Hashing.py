"""
USSE Noosphere • Expedition Lovelace • Conversational AI (CAI)
Week 06: The Agentic Shift — System 1 vs. System 2 Thinking
Mission Deliverable 03: MDP Trajectory Logger & Visited-State Hashing Engine

Station: Data & Payload Specialist
Cadet: Data & Payload Specialist
Squadron: Squadron Turing (Alpha-1)
Waypoint: Sector SEC-06-CAR (Homunculus Nebula / Eta Carinae)
"""

import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Set, Tuple


class TrajectoryStep:
    """Represents a single step in a Markov Decision Process (MDP) agent trajectory."""

    def __init__(
        self,
        step_idx: int,
        state: str,
        thought: str,
        action: str,
        args: Dict[str, Any],
        observation: Any,
        reward: float
    ):
        self.step_idx = step_idx
        self.state = state
        self.thought = thought
        self.action = action
        self.args = args
        self.observation = observation
        self.reward = reward
        self.state_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Computes SHA-256 fingerprint over (Thought, Action, Args)."""
        canonical_args = json.dumps(self.args, sort_keys=True)
        canonical_str = f"{self.thought.strip()}||{self.action.strip()}||{canonical_args}"
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_idx,
            "state": self.state,
            "thought": self.thought,
            "action": self.action,
            "args": self.args,
            "observation": self.observation,
            "reward": self.reward,
            "hash": self.state_hash
        }


class MDPTrajectoryLogger:
    """
    Manages episodic trajectory recording, state hashing, cycle detection,
    and empirical discounted return calculations across varying discount factors.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.steps: List[TrajectoryStep] = []
        self.hash_set: Set[str] = set()
        self.hash_list: List[str] = []

    def record_step(
        self,
        state: str,
        thought: str,
        action: str,
        args: Dict[str, Any],
        observation: Any,
        reward: float
    ) -> Tuple[TrajectoryStep, bool]:
        """
        Records a trajectory step and checks for state hash collision.
        Returns: (TrajectoryStep, is_collision_detected)
        """
        step_idx = len(self.steps) + 1
        step = TrajectoryStep(step_idx, state, thought, action, args, observation, reward)

        collision = step.state_hash in self.hash_set
        self.steps.append(step)
        self.hash_set.add(step.state_hash)
        self.hash_list.append(step.state_hash)

        return step, collision

    def compute_discounted_return(self, gamma: float) -> float:
        """
        Computes the empirical cumulative discounted return:
        G_0 = sum_{t=0}^{T-1} (gamma^t * R_{t+1})
        """
        if not (0.0 <= gamma <= 1.0):
            raise ValueError(f"Discount factor gamma must be in [0, 1], got {gamma}")

        total_return = 0.0
        for t, step in enumerate(self.steps):
            total_return += (gamma ** t) * step.reward
        return round(total_return, 4)

    def compute_return_matrix(self, gammas: List[float]) -> Dict[float, float]:
        """Evaluates discounted returns across multiple discount factors."""
        return {g: self.compute_discounted_return(g) for g in gammas}

    def summarize_trajectory(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "total_steps": len(self.steps),
            "unique_states": len(self.hash_set),
            "rewards": [s.reward for s in self.steps],
            "total_undiscounted_reward": round(sum(s.reward for s in self.steps), 4),
            "hashes": self.hash_list
        }


# =====================================================================
# Data Specialist Verification Suite
# =====================================================================

def verify_trajectory_and_hashing():
    print("=" * 80)
    print("MISSION 06 • DELIVERABLE 03: MDP TRAJECTORY & HASHING ENGINE")
    print("Station: Data & Payload Specialist | USSE Noosphere Subsystem 06")
    print("=" * 80)

    logger = MDPTrajectoryLogger(agent_name="AURA-Trajectory-Evaluator")

    # Step 1: Nominal sensor reading
    s1, coll1 = logger.record_step(
        state="OBSERVING",
        thought="Reading warp coil temperature.",
        action="ReadSensor",
        args={"channel": "TEMP_WARP_COIL"},
        observation={"temp_k": 485.0},
        reward=-0.1
    )
    assert coll1 is False, "Step 1 should not trigger a hash collision."
    print(f"[Step 1] Hash: {s1.state_hash[:16]}... Collision={coll1}")

    # Step 2: Cooling action
    s2, coll2 = logger.record_step(
        state="OBSERVING",
        thought="Coil temperature is 485 K. Cooling manifold with 6 kg/s liquid helium.",
        action="CoolManifold",
        args={"rate": 6.0},
        observation={"new_temp_k": 335.0},
        reward=-0.1
    )
    assert coll2 is False, "Step 2 should not trigger a hash collision."
    print(f"[Step 2] Hash: {s2.state_hash[:16]}... Collision={coll2}")

    # Step 3: Repeated Action with IDENTICAL Thought and Args (Simulated Loop)
    s3, coll3 = logger.record_step(
        state="OBSERVING",
        thought="Reading warp coil temperature.",
        action="ReadSensor",
        args={"channel": "TEMP_WARP_COIL"},
        observation={"temp_k": 485.0},
        reward=-1.0
    )
    assert coll3 is True, "Step 3 should trigger a state hash collision!"
    print(f"[Step 3] Hash: {s3.state_hash[:16]}... Collision={coll3} (COLLISION DETECTED!)")

    # Step 4: Successful calibration
    s4, coll4 = logger.record_step(
        state="OBSERVING",
        thought="Calibrating warp compensator coils to 14.82 micro-Henries.",
        action="CalibrateWarpCoils",
        args={"flux": 14.82},
        observation={"success": True},
        reward=5.0
    )
    print(f"[Step 4] Hash: {s4.state_hash[:16]}... Collision={coll4}")

    # Step 5: Final completion
    s5, coll5 = logger.record_step(
        state="COMPLETED",
        thought="Warp field stable. Mission objective accomplished.",
        action="FinalAnswer",
        args={"response": "Subsystem 06 restored."},
        observation="Nominal",
        reward=10.0
    )
    print(f"[Step 5] Hash: {s5.state_hash[:16]}... Collision={coll5}")

    # Empirical Discounted Return Verification
    gammas = [0.0, 0.5, 0.9, 0.95, 1.0]
    return_table = logger.compute_return_matrix(gammas)
    print("\n--- Empirical Discounted Return Evaluation J(pi) ---")
    for g, val in return_table.items():
        print(f"  gamma = {g:0.2f} : J(pi) = {val:>7.4f}")

    # Theoretical Verification:
    # At gamma=0.0: G_0 = R_1 = -0.1
    # At gamma=1.0: G_0 = -0.1 + (-0.1) + (-1.0) + 5.0 + 10.0 = 13.80
    assert return_table[0.0] == -0.1, f"Expected return at gamma=0 to be -0.1, got {return_table[0.0]}"
    assert return_table[1.0] == 13.8, f"Expected return at gamma=1.0 to be 13.8, got {return_table[1.0]}"

    summary = logger.summarize_trajectory()
    assert summary["total_steps"] == 5
    assert summary["unique_states"] == 4  # 5 steps with 1 collision = 4 unique hashes

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED: MDP Trajectory Logger & Hash Engine Verified (Exit Code 0).")
    print("=" * 80)


if __name__ == "__main__":
    verify_trajectory_and_hashing()

