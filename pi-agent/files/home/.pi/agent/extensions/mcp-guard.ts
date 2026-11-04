// Sandbox guard for sbx MCP gateway tools.
//
// Pi auto-loads extensions from ~/.pi/agent/extensions/ (one default export per
// file — helper modules must live outside this directory). The gateway tools are
// registered as `mcp__mcp_gateway__<tool>`; this hook enforces the read-only
// whitelist plus the run-config guard implemented in ../lib/mcp-guard-policy.ts
// (shared read-only allow-list).
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

import { isAllowedTool } from "../lib/mcp-guard-policy.ts";

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event) => {
		if (
			!event.toolName.startsWith("mcp__mcp_gateway__") &&
			!event.toolName.startsWith("mcp-gateway_")
		) {
			return;
		}
		const decision = isAllowedTool(event.toolName, event.input);
		if (!decision.allowed) {
			return {
				block: true,
				reason: decision.reason ?? "blocked by the sandbox MCP policy",
			};
		}
	});
}
