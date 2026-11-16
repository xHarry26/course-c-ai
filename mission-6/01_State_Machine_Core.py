"""
USSE Noosphere • Expedition Lovelace • Conversational AI (CAI)
Week 06: The Agentic Shift — System 1 vs. System 2 Thinking
Mission Deliverable 01: Native Python Agent State Machine Core

Station: Systems Architect (Lead Engineer)
Cadet: Shazim Ali Mughal (Lead Systems Architect)
Squadron: Squadron Turing (Alpha-1)
Waypoint: Sector SEC-06-CAR (Homunculus Nebula / Eta Carinae)
"""

import enum
from typing import Dict, List, Optional, Set, Tuple


class AgentStatus(enum.Enum):
    """Discrete lifecycle states of the autonomous agent state machine."""
    INITIALIZING = "INITIALIZING"
    THINKING = "THINKING"
    ACTING = "ACTING"
    OBSERVING = "OBSERVING"
    REFLECTING = "REFLECTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentEvent(enum.Enum):
    """Triggers driving discrete state transitions."""
    BOOTSTRAP = "BOOTSTRAP"
    PROPOSE_ACTION = "PROPOSE_ACTION"
    EMIT_FINAL_ANSWER = "EMIT_FINAL_ANSWER"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    RECEIVE_OBSERVATION = "RECEIVE_OBSERVATION"
    DETECT_CYCLE = "DETECT_CYCLE"
    RESOLVE_REFLECTION = "RESOLVE_REFLECTION"
    EXCEED_BUDGET = "EXCEED_BUDGET"
    ABORT = "ABORT"


class InvalidTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    pass


class AgentStateMachineCore:
    """
    Deterministic Finite State Machine governing the autonomous agent lifecycle.
    Decouples stochastic proposal generation from deterministic system control.
    """

    # Formal state transition table: (CurrentState, Event) -> NextState
    VALID_TRANSITIONS: Dict[Tuple[AgentStatus, AgentEvent], AgentStatus] = {
        # Initialization
        (AgentStatus.INITIALIZING, AgentEvent.BOOTSTRAP): AgentStatus.THINKING,
        (AgentStatus.INITIALIZING, AgentEvent.ABORT): AgentStatus.FAILED,

        # Deliberation / Thinking
        (AgentStatus.THINKING, AgentEvent.PROPOSE_ACTION): AgentStatus.ACTING,
        (AgentStatus.THINKING, AgentEvent.EMIT_FINAL_ANSWER): AgentStatus.COMPLETED,
        (AgentStatus.THINKING, AgentEvent.DETECT_CYCLE): AgentStatus.REFLECTING,
        (AgentStatus.THINKING, AgentEvent.EXCEED_BUDGET): AgentStatus.FAILED,
        (AgentStatus.THINKING, AgentEvent.ABORT): AgentStatus.FAILED,

        # Acting
        (AgentStatus.ACTING, AgentEvent.EXECUTE_TOOL): AgentStatus.OBSERVING,
        (AgentStatus.ACTING, AgentEvent.ABORT): AgentStatus.FAILED,

        # Observing
        (AgentStatus.OBSERVING, AgentEvent.RECEIVE_OBSERVATION): AgentStatus.THINKING,
        (AgentStatus.OBSERVING, AgentEvent.EXCEED_BUDGET): AgentStatus.FAILED,
        (AgentStatus.OBSERVING, AgentEvent.ABORT): AgentStatus.FAILED,

        # Reflecting (Loop Escape)
        (AgentStatus.REFLECTING, AgentEvent.RESOLVE_REFLECTION): AgentStatus.THINKING,
        (AgentStatus.REFLECTING, AgentEvent.EXCEED_BUDGET): AgentStatus.FAILED,
        (AgentStatus.REFLECTING, AgentEvent.ABORT): AgentStatus.FAILED,
    }

    def __init__(self, agent_id: str, max_steps: int = 10):
        self.agent_id = agent_id
        self.max_steps = max_steps
        self.current_state = AgentStatus.INITIALIZING
        self.step_count = 0
        self.history: List[Tuple[AgentStatus, AgentEvent, AgentStatus]] = []

    def trigger(self, event: AgentEvent) -> AgentStatus:
        """
        Executes a deterministic state transition delta(s, e) -> s'.
        Enforces step budgets and rejects invalid state jumps.
        """
        if self.current_state in (AgentStatus.COMPLETED, AgentStatus.FAILED):
            raise InvalidTransitionError(
                f"Agent '{self.agent_id}' is in terminal state '{self.current_state.value}'. "
                f"No further transitions permitted."
            )

        # Check budget constraint
        if self.step_count >= self.max_steps and event not in (AgentEvent.EMIT_FINAL_ANSWER, AgentEvent.EXCEED_BUDGET):
            event = AgentEvent.EXCEED_BUDGET

        transition_key = (self.current_state, event)
        if transition_key not in self.VALID_TRANSITIONS:
            raise InvalidTransitionError(
                f"Illegal state transition attempted: CurrentState={self.current_state.value}, "
                f"Event={event.value}. Transition is undefined in state matrix."
            )

        next_state = self.VALID_TRANSITIONS[transition_key]
        self.history.append((self.current_state, event, next_state))
        self.current_state = next_state

        if self.current_state == AgentStatus.THINKING:
            self.step_count += 1

        return self.current_state

    def is_terminal(self) -> bool:
        return self.current_state in (AgentStatus.COMPLETED, AgentStatus.FAILED)

    def print_trace(self):
        print(f"\n--- State Transition Trace for Agent: {self.agent_id} ---")
        for i, (src, evt, dst) in enumerate(self.history, 1):
            print(f"  Step {i:02d}: [{src.value:<12}] --({evt.value:<20})--> [{dst.value:<12}]")
        print(f"Terminal State: {self.current_state.value} (Steps: {self.step_count}/{self.max_steps})\n")


# =====================================================================
# Systems Architect Verification Suite
# =====================================================================

def verify_state_machine_core():
    print("=" * 80)
    print("MISSION 06 • DELIVERABLE 01: STATE MACHINE CORE VERIFICATION")
    print("Station: Systems Architect | USSE Noosphere Subsystem 06 Restoration")
    print("=" * 80)

    # Test 1: Standard Nominal Lifecycle
    print("\n[Test 1] Executing Standard Nominal Lifecycle...")
    sm = AgentStateMachineCore(agent_id="AURA-CORE-01", max_steps=5)
    assert sm.current_state == AgentStatus.INITIALIZING

    sm.trigger(AgentEvent.BOOTSTRAP)
    assert sm.current_state == AgentStatus.THINKING
    assert sm.step_count == 1

    sm.trigger(AgentEvent.PROPOSE_ACTION)
    assert sm.current_state == AgentStatus.ACTING

    sm.trigger(AgentEvent.EXECUTE_TOOL)
    assert sm.current_state == AgentStatus.OBSERVING

    sm.trigger(AgentEvent.RECEIVE_OBSERVATION)
    assert sm.current_state == AgentStatus.THINKING
    assert sm.step_count == 2

    sm.trigger(AgentEvent.EMIT_FINAL_ANSWER)
    assert sm.current_state == AgentStatus.COMPLETED
    assert sm.is_terminal()
    sm.print_trace()
    print("✓ Test 1 Passed: Nominal lifecycle completed successfully.")

    # Test 2: Reflection & Cycle Recovery Lifecycle
    print("[Test 2] Executing Reflection & Cycle Recovery...")
    sm2 = AgentStateMachineCore(agent_id="AURA-CORE-02", max_steps=5)
    sm2.trigger(AgentEvent.BOOTSTRAP)
    sm2.trigger(AgentEvent.DETECT_CYCLE)
    assert sm2.current_state == AgentStatus.REFLECTING

    sm2.trigger(AgentEvent.RESOLVE_REFLECTION)
    assert sm2.current_state == AgentStatus.THINKING

    sm2.trigger(AgentEvent.EMIT_FINAL_ANSWER)
    assert sm2.current_state == AgentStatus.COMPLETED
    print("✓ Test 2 Passed: Reflection loop correctly navigated.")

    # Test 3: Rejection of Illegal Transitions
    print("[Test 3] Verifying Rejection of Illegal Transitions...")
    sm3 = AgentStateMachineCore(agent_id="AURA-CORE-03", max_steps=5)
    try:
        # Cannot jump from INITIALIZING directly to ACTING without BOOTSTRAP
        sm3.trigger(AgentEvent.PROPOSE_ACTION)
        assert False, "Failed to raise InvalidTransitionError on illegal jump!"
    except InvalidTransitionError as e:
        print(f"  Caught expected transition violation: {e}")
    print("✓ Test 3 Passed: Illegal transitions properly rejected.")

    # Test 4: Hard Step Budget Guard
    print("[Test 4] Verifying Hard Step Budget Guard...")
    sm4 = AgentStateMachineCore(agent_id="AURA-CORE-04", max_steps=3)
    sm4.trigger(AgentEvent.BOOTSTRAP)  # Step 1
    sm4.trigger(AgentEvent.PROPOSE_ACTION)
    sm4.trigger(AgentEvent.EXECUTE_TOOL)
    sm4.trigger(AgentEvent.RECEIVE_OBSERVATION)  # Step 2
    sm4.trigger(AgentEvent.PROPOSE_ACTION)
    sm4.trigger(AgentEvent.EXECUTE_TOOL)
    sm4.trigger(AgentEvent.RECEIVE_OBSERVATION)  # Step 3
    # Step 3 reached; next transition triggers EXCEED_BUDGET
    sm4.trigger(AgentEvent.PROPOSE_ACTION)
    assert sm4.current_state == AgentStatus.FAILED
    print(f"✓ Test 4 Passed: Budget cap enforced. Terminal state={sm4.current_state.value}")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED: State Machine Core is mathematically sound (Exit Code 0).")
    print("=" * 80)


if __name__ == "__main__":
    verify_state_machine_core()

