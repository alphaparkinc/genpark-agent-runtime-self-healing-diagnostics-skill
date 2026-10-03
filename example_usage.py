"""Example usage for AgentRuntimeSelfHealingDiagnosticsEngine."""
import sys
import json
from client import AgentRuntimeSelfHealingDiagnosticsEngine

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== Agent Runtime Self-Healing & Diagnostics Engine Demo ===")
    engine = AgentRuntimeSelfHealingDiagnosticsEngine()

    golden_manifest = {
        "max_retries": 3,
        "timeout_seconds": 45,
        "active_models": ["claude-3-5-sonnet", "gpt-4o"],
        "rate_limit_per_min": 120
    }

    # 1. Create known-good checkpoint
    snap = engine.create_runtime_snapshot(golden_manifest, label="initial_golden_config")
    print("Checkpoint Saved:", json.dumps(snap, indent=2))

    # 2. Simulate corrupted/drifted runtime state
    drifted_runtime = {
        "max_retries": "unparseable_string", # Corrupted type
        # missing timeout_seconds
        "active_models": ["claude-3-5-sonnet"],
        "__corrupt_stale_tmp": 99999 # Stale garbage
    }

    print("\n--- Diagnosing and Automatically Healing Runtime ---")
    healing_result = engine.diagnose_and_heal_runtime(drifted_runtime, golden_manifest)
    print(f"Total Anomalies Caught: {healing_result['total_anomalies']}")
    print("Anomalies Remediation Log:")
    print(json.dumps(healing_result["anomalies"], indent=2))
    print("\nHealed Runtime Configuration:")
    print(json.dumps(healing_result["healed_state"], indent=2))

if __name__ == "__main__":
    main()
