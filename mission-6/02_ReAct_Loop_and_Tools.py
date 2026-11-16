"""
USSE Noosphere • Expedition Lovelace • Conversational AI (CAI)
Week 06: The Agentic Shift — System 1 vs. System 2 Thinking
Mission Deliverable 02: Tool Protocol Schema Validator & ReAct Loop Engine

Station: Communications & Protocol Officer
Cadet: Communications & Protocol Officer
Squadron: Squadron Turing (Alpha-1)
Waypoint: Sector SEC-06-CAR (Homunculus Nebula / Eta Carinae)
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class SchemaValidationError(Exception):
    """Raised when tool execution arguments violate the declared parameter schema."""
    pass


class ReActParseError(Exception):
    """Raised when generated model output fails the ReAct delimiter syntax."""
    pass


class ToolDefinition:
    """Encapsulates a typed tool, its JSON schema, and execution callable."""

    def __init__(self, name: str, description: str, schema: Dict[str, Any], func: Callable[..., Any]):
        self.name = name
        self.description = description
        self.schema = schema
        self.func = func

    def validate_arguments(self, args: Dict[str, Any]) -> None:
        """Validates input arguments against JSON-schema subset (required fields, types)."""
        required = self.schema.get("required", [])
        for field in required:
            if field not in args:
                raise SchemaValidationError(f"Missing required parameter '{field}' for tool '{self.name}'.")

        properties = self.schema.get("properties", {})
        for param, val in args.items():
            if param not in properties:
                raise SchemaValidationError(f"Unexpected parameter '{param}' passed to tool '{self.name}'.")
            spec = properties[param]
            expected_type = spec.get("type")
            if expected_type == "string" and not isinstance(val, str):
                raise SchemaValidationError(f"Parameter '{param}' must be string, got {type(val).__name__}")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                raise SchemaValidationError(f"Parameter '{param}' must be numeric, got {type(val).__name__}")
            elif expected_type == "integer" and not isinstance(val, int):
                raise SchemaValidationError(f"Parameter '{param}' must be integer, got {type(val).__name__}")
            elif expected_type == "boolean" and not isinstance(val, bool):
                raise SchemaValidationError(f"Parameter '{param}' must be boolean, got {type(val).__name__}")

    def execute(self, args: Dict[str, Any]) -> Any:
        self.validate_arguments(args)
        return self.func(**args)


class ReActProtocolEngine:
    """
    Protocol engine managing tool registration, schema enforcement,
    and regex parsing for ReAct Thought-Action-Observation loops.
    """

    REACT_PATTERN = re.compile(
        r"Thought:\s*(?P<thought>.*?)\s*\nAction:\s*(?P<action>[A-Za-z0-9_]+)\[(?P<args>.*?)\]",
        re.DOTALL
    )
    FINAL_ANSWER_PATTERN = re.compile(
        r"Thought:\s*(?P<thought>.*?)\s*\nFinal Answer:\s*(?P<answer>.*)",
        re.DOTALL
    )

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def register_tool(self, name: str, description: str, schema: Dict[str, Any]):
        def decorator(func: Callable[..., Any]):
            tool_def = ToolDefinition(name, description, schema, func)
            self.tools[name] = tool_def
            return func
        return decorator

    def parse_generation(self, raw_output: str) -> Tuple[str, str, Dict[str, Any], bool]:
        """
        Parses LLM output into (thought, action_name, action_args, is_final).
        Returns is_final=True if 'Final Answer:' delimiter is present.
        """
        # Check Final Answer first
        final_match = self.FINAL_ANSWER_PATTERN.search(raw_output)
        if final_match:
            thought = final_match.group("thought").strip()
            answer = final_match.group("answer").strip()
            return thought, "FinalAnswer", {"response": answer}, True

        # Check Action call
        action_match = self.REACT_PATTERN.search(raw_output)
        if action_match:
            thought = action_match.group("thought").strip()
            action_name = action_match.group("action").strip()
            raw_args = action_match.group("args").strip()

            # Attempt JSON parse or fallback to empty dict
            if not raw_args:
                args_dict = {}
            else:
                try:
                    args_dict = json.loads(raw_args)
                except json.JSONDecodeError:
                    # Support key=val or raw string
                    if "=" in raw_args:
                        args_dict = {}
                        for pair in raw_args.split(","):
                            k, v = pair.split("=", 1)
                            args_dict[k.strip()] = v.strip().strip('"\'')
                    else:
                        args_dict = {"input": raw_args}

            return thought, action_name, args_dict, False

        raise ReActParseError(
            f"Failed to parse generation into ReAct delimiters. Output was:\n{raw_output}"
        )

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool and wraps return value in standard telemetry response envelope."""
        if tool_name not in self.tools:
            raise SchemaValidationError(f"Tool '{tool_name}' not registered. Available tools: {list(self.tools.keys())}")
        result = self.tools[tool_name].execute(args)
        return {"tool": tool_name, "status": "SUCCESS", "output": result}


# =====================================================================
# Telemetry Toolset Registration & Verification
# =====================================================================

def create_telemetry_protocol() -> ReActProtocolEngine:
    engine = ReActProtocolEngine()

    # Tool 1: ReadSensor
    engine.register_tool(
        name="ReadSensor",
        description="Query starship sensor telemetry by channel id.",
        schema={
            "type": "object",
            "properties": {"sensor_channel": {"type": "string"}},
            "required": ["sensor_channel"]
        }
    )(lambda sensor_channel: {
        "channel": sensor_channel,
        "value": 482.5 if sensor_channel == "TEMP_WARP_COIL" else 14.1,
        "unit": "Kelvin" if sensor_channel == "TEMP_WARP_COIL" else "micro-Henries"
    })

    # Tool 2: AdjustShield
    engine.register_tool(
        name="AdjustShield",
        description="Modify plasma deflector shield frequency harmonic.",
        schema={
            "type": "object",
            "properties": {
                "harmonic_ghz": {"type": "number"},
                "polarity": {"type": "string"}
            },
            "required": ["harmonic_ghz", "polarity"]
        }
    )(lambda harmonic_ghz, polarity: {
        "shield_status": "LOCKED",
        "harmonic_ghz": harmonic_ghz,
        "polarity": polarity,
        "attenuation_db": 42.1
    })

    return engine


def verify_react_protocol():
    print("=" * 80)
    print("MISSION 06 • DELIVERABLE 02: REACT PROTOCOL & TOOL ENGINE")
    print("Station: Communications & Protocol Officer | USSE Noosphere Subsystem 06")
    print("=" * 80)

    engine = create_telemetry_protocol()

    # Test 1: ReAct Generation Parsing
    print("\n[Test 1] Parsing Standard ReAct Action Generation...")
    sample_gen = (
        "Thought: We must read the current warp coil temperature before taking action.\n"
        'Action: ReadSensor[{"sensor_channel": "TEMP_WARP_COIL"}]'
    )
    thought, action, args, is_final = engine.parse_generation(sample_gen)
    assert thought == "We must read the current warp coil temperature before taking action."
    assert action == "ReadSensor"
    assert args == {"sensor_channel": "TEMP_WARP_COIL"}
    assert is_final is False
    print(f"  Parsed Thought: {thought}")
    print(f"  Parsed Action:  {action} with args {args}")
    print("✓ Test 1 Passed: ReAct format parsed accurately.")

    # Test 2: Tool Execution with Schema Validation
    print("\n[Test 2] Executing Tool with Schema Validation...")
    result = engine.execute_tool(action, args)
    assert result["status"] == "SUCCESS"
    assert result["output"]["value"] == 482.5
    print(f"  Tool Execution Result: {result}")
    print("✓ Test 2 Passed: Schema validation and tool invocation succeeded.")

    # Test 3: Schema Validation Failure Rejection
    print("\n[Test 3] Verifying Schema Violation Rejection...")
    try:
        # Missing required parameter 'polarity'
        engine.execute_tool("AdjustShield", {"harmonic_ghz": 450.2})
        assert False, "Failed to reject missing required parameter!"
    except SchemaValidationError as e:
        print(f"  Caught expected schema violation: {e}")
    print("✓ Test 3 Passed: Missing parameters strictly caught.")

    # Test 4: Final Answer Parsing
    print("\n[Test 4] Parsing Final Answer Termination Delimiter...")
    final_gen = (
        "Thought: The warp field compensator coils are nominal and shields are locked.\n"
        "Final Answer: Mission complete. AURA Subsystem 06 stabilized at 42.6% integrity."
    )
    thought_f, action_f, args_f, is_final_f = engine.parse_generation(final_gen)
    assert is_final_f is True
    assert action_f == "FinalAnswer"
    assert "42.6% integrity" in args_f["response"]
    print(f"  Final Answer Detected: {args_f['response']}")
    print("✓ Test 4 Passed: Final Answer delimiter successfully terminated loop.")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED: Protocol Engine & ReAct Schema Validator Operational (Exit Code 0).")
    print("=" * 80)


if __name__ == "__main__":
    verify_react_protocol()

