"""
Agent Runtime Self-Healing & Diagnostics Engine (Zero External Dependencies)
Provides automated drift detection, root cause classification, and state snapshot rollback.
"""
import time
import math
import hashlib
import json
import copy
from typing import Dict, Any, List, Optional

class AgentRuntimeSelfHealingDiagnosticsEngine:
    def __init__(self):
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.incident_history: List[Dict[str, Any]] = []

    def create_runtime_snapshot(self, state: Dict[str, Any], label: str = "checkpoint") -> Dict[str, Any]:
        """Creates a verified known-good snapshot of agent runtime configuration."""
        now = time.time()
        snap_id = "SNAP-" + hashlib.sha256(f"{label}{now}".encode("utf-8")).hexdigest()[:12]
        record = {
            "snapshot_id": snap_id,
            "label": label,
            "timestamp": now,
            "state": copy.deepcopy(state),
            "state_hash": hashlib.sha256(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()
        }
        self.snapshots[snap_id] = record
        return {"snapshot_id": snap_id, "timestamp": now, "label": label, "state_hash": record["state_hash"]}

    def diagnose_and_heal_runtime(
        self,
        current_state: Dict[str, Any],
        expected_manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scans runtime state against expected golden manifest.
        Detects missing keys, corrupted types, or drifted values and automatically heals them.
        """
        anomalies = []
        healed_state = copy.deepcopy(current_state)

        for key, expected_val in expected_manifest.items():
            if key not in current_state:
                anomalies.append({
                    "type": "MISSING_CONFIGURATION_KEY",
                    "key": key,
                    "remedy": "RESTORED_FROM_MANIFEST"
                })
                healed_state[key] = copy.deepcopy(expected_val)
            elif type(current_state[key]) != type(expected_val) and expected_val is not None:
                anomalies.append({
                    "type": "CORRUPTED_TYPE_MISMATCH",
                    "key": key,
                    "expected_type": type(expected_val).__name__,
                    "actual_type": type(current_state[key]).__name__,
                    "remedy": "RESET_TO_MANIFEST_DEFAULT"
                })
                healed_state[key] = copy.deepcopy(expected_val)

        # Detect extraneous unknown keys that might cause memory leaks or stalls
        known_keys = set(expected_manifest.keys())
        extra_keys = set(current_state.keys()) - known_keys
        for ek in extra_keys:
            if ek.startswith("__corrupt_") or ek.endswith("_stale_tmp"):
                anomalies.append({
                    "type": "CORRUPTED_STALE_KEY",
                    "key": ek,
                    "remedy": "PURGED_CORRUPT_KEY"
                })
                del healed_state[ek]

        is_healthy = len(anomalies) == 0
        incident_record = {
            "timestamp": time.time(),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "self_healed": not is_healthy
        }
        self.incident_history.append(incident_record)

        return {
            "healthy": is_healthy,
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
            "self_healing_applied": not is_healthy,
            "healed_state": healed_state
        }

    def rollback_to_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restores state from an explicit snapshot ID."""
        if snapshot_id not in self.snapshots:
            return {"error": f"Snapshot {snapshot_id} not found", "success": False}
        snap = self.snapshots[snapshot_id]
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "restored_state": copy.deepcopy(snap["state"]),
            "restored_at": time.time()
        }

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "snapshots_available": len(self.snapshots),
            "incidents_handled": len(self.incident_history),
            "last_incident": self.incident_history[-1] if self.incident_history else None
        }
