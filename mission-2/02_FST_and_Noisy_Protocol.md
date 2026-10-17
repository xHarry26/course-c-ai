# Deliverable 2: FST Dialogue Manager & Noisy Channel Protocol

**Station Role:** 📡 Communications & Protocol Officer (Interface Specialist & Transceiver Lead)  
**Appointed Officer:** Mazhar Uddin Abbasi  
**Sector Operation:** Sector `SEC-02-CMA` (Sirius Binary System / Sirius B "The Pup")  
**Target Subsystem:** AURA Subsystem 02 — Subspace Transceiver & Dialogue Decoder Matrix  
**Deliverable File:** `02_FST_and_Noisy_Protocol.md`  

---

## 1. Executive Protocol Briefing
In Sector `SEC-02-CMA`, extreme thermal X-ray emissions and gravitational redshift from Sirius B have severely degraded the *USSE Noosphere's* subspace communication bandwidth. To prevent unconstrained neural hallucination and ensure reliable mission execution, communication protocols are divided into two complementary strata:

1. **Deterministic Dialogue Flow:** Governed by an explicit, formally verifiable **Mealy Finite State Transducer (`FSTDialogueManager`)** with slot-filling memory.
2. **Noisy Channel Strategy:** Governed by Shannon's Noisy Channel Coding Theorem ($C = W \log_2(1 + S/N)$), enforcing a strict **7-word transmission buffer** and a structured signal reduction protocol to withstand mandatory alien noise token substitution.

---

## 2. Formal Mealy FST Architecture (`FSTDialogueManager`)

The dialogue manager is formalized as a deterministic 7-tuple:
$$M_{\text{AURA}} = \langle Q, \Sigma, \Gamma, \delta, \omega, q_0, F \rangle$$

### Tuple Specifications:
- **States ($Q$):**
  $$Q = \{q_{\text{init}}, \, q_{\text{greeting}}, \, q_{\text{collect\_slots}}, \, q_{\text{confirmation}}, \, q_{\text{fallback}}, \, q_{\text{terminal}}\}$$
- **Input Alphabet ($\Sigma$):** Parsed intent primitives and slot entity tuples:
  $$\Sigma = \{\text{INITIATE}, \, \text{GREET}, \, \text{PROVIDE\_INTENT}, \, \text{PROVIDE\_SYSTEM}, \, \text{AFFIRM}, \, \text{DENY}, \, \text{RESET}, \, \text{UNCLEAR}\}$$
- **Output Alphabet ($\Gamma$):** Standardized, bandwidth-optimized response tokens and action triggers:
  $$\Gamma = \{\text{PROMPT\_GREETING}, \, \text{REQUEST\_SLOTS}, \, \text{CONFIRM\_ACTION}, \, \text{EXECUTE\_ACTION}, \, \text{EMIT\_FALLBACK}, \, \text{ABORT\_SESSION}\}$$
- **State Transition Function ($\delta: Q \times \Sigma \to Q$):**
  - $\delta(q_{\text{init}}, \text{INITIATE}) \to q_{\text{greeting}}$
  - $\delta(q_{\text{greeting}}, \text{PROVIDE\_INTENT}) \to q_{\text{collect\_slots}}$
  - $\delta(q_{\text{collect\_slots}}, \text{PROVIDE\_SLOTS\_COMPLETE}) \to q_{\text{confirmation}}$
  - $\delta(q_{\text{collect\_slots}}, \text{PROVIDE\_SLOTS\_PARTIAL}) \to q_{\text{collect\_slots}}$
  - $\delta(q_{\text{confirmation}}, \text{AFFIRM}) \to q_{\text{terminal}}$
  - $\delta(q_{\text{confirmation}}, \text{DENY}) \to q_{\text{collect\_slots}}$
  - $\delta(q, \text{UNCLEAR}) \to q_{\text{fallback}}$
- **Output Emission Function ($\omega: Q \times \Sigma \to \Gamma$):** Emits synchronous responses tied directly to both current state and incoming input symbol.
- **Initial State:** $q_0 = q_{\text{init}}$ (`INIT`)
- **Terminal States:** $F = \{q_{\text{terminal}}\}$ (`TERMINAL`)

---

## 3. Python Implementation: `FSTDialogueManager` Class Specification

```python
import re
from enum import Enum
from typing import Dict, Any, Tuple, Optional, List

class DialogueState(str, Enum):
    INIT = "INIT"
    GREETING = "GREETING"
    COLLECT_SLOTS = "COLLECT_SLOTS"
    CONFIRMATION = "CONFIRMATION"
    FALLBACK = "FALLBACK"
    TERMINAL = "TERMINAL"

class FSTDialogueManager:
    """
    Deterministic Mealy Finite State Transducer per ps02 specification:
    M = <Q, Sigma, Gamma, delta, omega, q0, F>
    Tracks conversation state across 5 required states:
    - INIT
    - GREETING
    - COLLECT_SLOTS (destination, speed, clearance code)
    - CONFIRMATION
    - TERMINAL / FALLBACK
    Maintains slot_memory = {} with regex pattern extraction rules.
    """
    DESTINATIONS = ["sirius", "sirius a", "sirius b", "the pup", "earth", "sol", "centauri", "barycenter"]
    SPEED_PATTERN = r"(warp\s*\d+|\d+(?:\.\d+)?c|sublight|impulse|\d+\s*(?:km/s|m/s))"
    CLEARANCE_PATTERN = r"([a-zA-Z0-9]+-[a-zA-Z0-9]+|code-\d+|0x[0-9a-fA-F]+|alpha-\d+|sec-\d+)"

    def __init__(self, max_fallback_retries: int = 3):
        self.state = DialogueState.INIT
        self.slot_memory: Dict[str, Optional[str]] = {
            "destination": None,     # Target celestial body / waypoint
            "speed": None,           # Flight velocity / warp factor
            "clearance_code": None,  # Cryptographic fleet clearance code
            "confirmed": False       # Boolean authorization gate
        }
        self.slots = self.slot_memory
        self.fallback_count = 0
        self.max_fallback_retries = max_fallback_retries
        self.history = []

    def reset(self):
        self.state = DialogueState.INIT
        self.slot_memory = {
            "destination": None,
            "speed": None,
            "clearance_code": None,
            "confirmed": False
        }
        self.slots = self.slot_memory
        self.fallback_count = 0
        self.history.clear()

    def extract_slots(self, text: str) -> Dict[str, str]:
        """Regex and pattern-based slot extractor per ps02 directive."""
        extracted = {}
        tl = text.lower()

        # 1. Destination pattern matching
        for dest in self.DESTINATIONS:
            if dest in tl:
                extracted["destination"] = dest.title()
                break

        # 2. Speed pattern matching (e.g., Warp 2, 0.5c)
        speed_match = re.search(self.SPEED_PATTERN, tl, re.IGNORECASE)
        if speed_match:
            extracted["speed"] = speed_match.group(1).upper()

        # 3. Clearance code matching (e.g., SEC-02, ALPHA-9)
        code_match = re.search(self.CLEARANCE_PATTERN, tl, re.IGNORECASE)
        if code_match:
            extracted["clearance_code"] = code_match.group(1).upper()

        return extracted

    def has_all_slots(self) -> bool:
        return bool(self.slot_memory["destination"] and self.slot_memory["speed"] and self.slot_memory["clearance_code"])

    def missing_slots(self) -> List[str]:
        return [k for k in ["destination", "speed", "clearance_code"] if not self.slot_memory.get(k)]

    def transition(self, user_intent: str, user_text: str = "") -> Tuple[DialogueState, str]:
        extracted = self.extract_slots(user_text)
        for k, v in extracted.items():
            self.slot_memory[k] = v

        prev_state = self.state
        output_emission = ""

        if self.state == DialogueState.INIT:
            self.state = DialogueState.GREETING
            output_emission = "USSE Noosphere Transceiver Online. State destination."

        elif self.state == DialogueState.GREETING:
            if self.has_all_slots():
                self.state = DialogueState.CONFIRMATION
                output_emission = f"Confirm jump to {self.slot_memory['destination']} at {self.slot_memory['speed']} code {self.slot_memory['clearance_code']}?"
            else:
                self.state = DialogueState.COLLECT_SLOTS
                missing = ", ".join(self.missing_slots())
                output_emission = f"Provide required flight slots: {missing}."

        elif self.state == DialogueState.COLLECT_SLOTS:
            if self.has_all_slots():
                self.fallback_count = 0
                self.state = DialogueState.CONFIRMATION
                output_emission = f"Confirm jump to {self.slot_memory['destination']} at {self.slot_memory['speed']} code {self.slot_memory['clearance_code']}?"
            elif any(extracted.values()):
                self.fallback_count = 0
                missing = ", ".join(self.missing_slots())
                output_emission = f"Slots captured. Still missing: {missing}."
            else:
                self.fallback_count += 1
                if self.fallback_count >= self.max_fallback_retries:
                    self.state = DialogueState.FALLBACK
                    output_emission = "Max retries exceeded. Routing to fallback."
                else:
                    missing = ", ".join(self.missing_slots())
                    output_emission = f"Missing {missing}. Clarify flight parameters."

        elif self.state == DialogueState.CONFIRMATION:
            if user_intent in ["AFFIRM", "YES", "CONFIRM"]:
                self.slot_memory["confirmed"] = True
                self.state = DialogueState.TERMINAL
                output_emission = f"Flight authorized: {self.slot_memory['destination']} at {self.slot_memory['speed']}."
            elif user_intent in ["DENY", "NO", "CANCEL"]:
                self.slot_memory["confirmed"] = False
                self.slot_memory["speed"] = None
                self.state = DialogueState.COLLECT_SLOTS
                output_emission = "Course canceled. Provide updated flight speed."
            else:
                self.state = DialogueState.FALLBACK
                output_emission = "Ambiguous confirmation. Affirm or deny."

        elif self.state == DialogueState.FALLBACK:
            if user_intent == "RESET":
                self.reset()
                output_emission = "State machine reset to INIT."
            elif self.has_all_slots():
                self.state = DialogueState.CONFIRMATION
                output_emission = f"Recovered slots. Confirm jump to {self.slot_memory['destination']} at {self.slot_memory['speed']}?"
            else:
                self.state = DialogueState.COLLECT_SLOTS
                output_emission = "Fallback recovery active. State flight parameters."

        self.history.append((prev_state, user_intent, self.state, output_emission))
        return self.state, output_emission
```

---

## 4. Noisy Subspace Channel Constraints & Noise Set

Under the Sirius B plasma wake, physical subspace transceiver packets are governed by strict channel physics:

### Physical Constraints:
1. **Strict Buffer Limit:** Exactly **$\le 7$ words** per conversational turn. Any packet containing more than 7 words is truncated and dropped by the transceiver firmware.
2. **Mandatory Noise Token Injection:** Every transmitted message passing through the uncalibrated channel undergoes stochastic token substitution from the Sirius B Anomaly Set:
   $$\mathcal{V}_{\text{noise}} = \{\text{Banana}, \, \text{Labyrinth}, \, \text{Quantum}, \, \text{Midnight}, \, \text{Velocity}, \, \text{Green}, \, \text{Cosmological}\}$$
3. **Noise Perturbation Model:** For each token position $i \in \{1, \dots, 7\}$, a token is replaced with probability $p_{\text{noise}} \in [0.15, 0.30]$ by a uniformly sampled element from $\mathcal{V}_{\text{noise}}$.

---

## 5. Signal Reduction Strategy: Maximizing Mutual Information $I(X; Y)$

To convey complex philosophical and technical concepts under a 7-word budget subject to noise substitution, cadets must apply Shannon's principles:
$$I(X; Y) = H(X) - H(X \mid Y)$$

### Architectural Compression Rules:
1. **Elimination of Low-Entropy Syntactic Padding:**  
   Strip conversational filler (*"Hello"*, *"Could you please"*, *"I would like to"*, *"As an AI assistant"*). These tokens carry near-zero information ($I(x) \approx 0$) while occupying critical word slots.
2. **Dense Action-Entity Primitives:**  
   Format transmissions as high-density semantic vectors:
   $$\text{Packet} = \langle \text{Command}, \, \text{Target}, \, \text{Param}, \, \text{Checksum} \rangle$$
   *Example:* `"Calibrate transceiver frequency 434MHz confirm"` (5 words).
3. **Semantic Parity Framing:**  
   Repeat the invariant semantic root using two orthogonal synonyms or context anchors so that if one token is substituted by a noise word (e.g., `"Banana"`), the decoder reconstructs intent from the remaining signal.
   *Example:* `"Status check: report transceiver health now"` (6 words). If corrupted to `"Status Banana: report transceiver health now"`, the semantic intent remains recoverable.
4. **Ship Anomaly 02 Response Solution (Sirius Pup Subspace Challenge):**  
   *Concept to convey:* Lovelace's Objection (machines execute rules without originating thought).  
   *7-Word Strategy:*
   $$\mathbf{w} = \text{["Rules", "execute", "symbols", "without", "originating", "conscious", "thought"]}$$
   - Word count: Exactly 7 words.
   - Information density: 100% semantic payload.
   - Robustness: Even if token 3 is corrupted to `"Quantum"` (*"Rules execute Quantum without originating conscious thought"*), the philosophical core ($\text{Origination} = \emptyset$) remains decodable.

---

## 6. Station Sign-Off

```
=============================================================================
STATION CERTIFICATION: COMMUNICATIONS & PROTOCOL OFFICER
=============================================================================
Officer: Mazhar Uddin Abbasi (Communications & Protocol Officer)
Station: AURA Subspace Transceiver Gateway — Protocols Division
Status: APPROVED & SIGNED OFF
Integrity Contribution: +1.775% toward Subsystem 02 Milestone
Signature: [PROTOCOL-OFFICER-SEC02-FST-NOISY-PROTOCOL-VERIFIED]
=============================================================================
```
