"""MCP Server for Agent Runtime Self-Healing Diagnostics Engine."""
import sys
import json
import time
from client import AgentRuntimeSelfHealingDiagnosticsEngine

engine = AgentRuntimeSelfHealingDiagnosticsEngine()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "diagnose_and_heal_agent_runtime":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "get_health_status")
    if action == "diagnose_and_heal_runtime":
        return engine.diagnose_and_heal_runtime(
            current_state=args.get("runtime_state", {}),
            expected_manifest=args.get("expected_manifest", {})
        )
    elif action == "create_runtime_snapshot":
        return engine.create_runtime_snapshot(
            state=args.get("runtime_state", {}),
            label="mcp_snapshot"
        )
    elif action == "rollback_to_snapshot":
        return engine.rollback_to_snapshot(args.get("snapshot_id", ""))
    elif action == "get_health_status":
        return engine.get_health_status()
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        manifest = {"db_pool_size": 10, "timeout_sec": 30, "env": "prod"}
        broken_state = {"db_pool_size": "invalid_string", "__corrupt_flag": True}
        res = engine.diagnose_and_heal_runtime(broken_state, manifest)
        assert res["self_healing_applied"] is True
        assert res["healed_state"]["db_pool_size"] == 10
        assert "__corrupt_flag" not in res["healed_state"]
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "AgentRuntimeSelfHealingDiagnosticsEngine", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "diagnose_and_heal_agent_runtime",
                            "description": "Perform self-healing diagnostics: scan runtime state for corruption or drift, identify root causes, restore known-good snapshots, and verify recovery.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["diagnose_and_heal_runtime", "create_runtime_snapshot", "rollback_to_snapshot", "get_health_status"]},
                                    "runtime_state": {"type": "object"},
                                    "expected_manifest": {"type": "object"},
                                    "snapshot_id": {"type": "string"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
