// Read-only whitelist and run-config guard for the sbx MCP gateway tools.
//
// Pi has no permission system, so this policy is enforced by the mcp-guard
// extension (see ../extensions/mcp-guard.ts) in a tool_call hook: read-only
// tools are allowed, write/exec tools are denied (Pi cannot ask on the fly).
// mcp-gateway_execute_run_configuration is limited to the validate-only run
// configuration.
//
// Pi registers gateway tools as `mcp__mcp_gateway__<tool>` (server name
// `mcp-gateway` sanitized to `mcp_gateway`). The policy normalizes that prefix
// to the canonical `mcp-gateway_` form used by the shared whitelist.

export interface ToolDecision {
	allowed: boolean;
	reason?: string;
}

const PI_PREFIX = "mcp__mcp_gateway__";
const CANONICAL_PREFIX = "mcp-gateway_";

const ALLOWED_EXACT = new Set([
	"mcp-gateway_analyze_calls",
	"mcp-gateway_api_resources_list",
	"mcp-gateway_build_project",
	"mcp-gateway_buildx_list",
	"mcp-gateway_buildx_history",
	"mcp-gateway_buildx_logs",
	"mcp-gateway_buildx_du",
	"mcp-gateway_buildx_inspect",
	"mcp-gateway_container_inspect",
	"mcp-gateway_container_processes",
	"mcp-gateway_container_stats",
	"mcp-gateway_image_history",
	"mcp-gateway_image_inspect",
	"mcp-gateway_system_df",
	"mcp-gateway_system_info",
	"mcp-gateway_version",
	"mcp-gateway_fetch_container_logs",
	"mcp-gateway_fetch_query_result",
	"mcp-gateway_git_status",
	"mcp-gateway_introspect_schema",
	"mcp-gateway_lint_files",
	"mcp-gateway_events_list",
	"mcp-gateway_helm_list",
	"mcp-gateway_namespaces_list",
	"mcp-gateway_nodes_log",
	"mcp-gateway_nodes_stats_summary",
	"mcp-gateway_nodes_top",
	"mcp-gateway_pods_get",
	"mcp-gateway_pods_list",
	"mcp-gateway_pods_list_in_namespace",
	"mcp-gateway_pods_log",
	"mcp-gateway_pods_top",
	"mcp-gateway_projects_list",
	"mcp-gateway_resources_get",
	"mcp-gateway_resources_list",
	"mcp-gateway_open_file_in_editor",
	"mcp-gateway_preview_table_data",
	"mcp-gateway_run_inspection_kts",
	"mcp-gateway_test_database_connection",
	"mcp-gateway_validate_inspection_kts",
]);

const ALLOWED_PREFIXES = [
	"mcp-gateway_get_",
	"mcp-gateway_list_",
	"mcp-gateway_search_",
	"mcp-gateway_read",
	"mcp-gateway_generate_",
	"mcp-gateway_xdebug_get_",
	"mcp-gateway_xdebug_list_",
];

const RUN_CONFIG_TOOL = "mcp-gateway_execute_run_configuration";
const ALLOWED_RUN_CONFIG = "local-test-kits-validate-only";

function deny(reason: string): ToolDecision {
	return { allowed: false, reason };
}

/** Map Pi's `mcp__mcp_gateway__<tool>` to the canonical `mcp-gateway_<tool>`. */
export function canonicalToolName(toolName: string): string {
	if (toolName.startsWith(PI_PREFIX)) {
		return CANONICAL_PREFIX + toolName.slice(PI_PREFIX.length);
	}
	return toolName;
}

export function isAllowedTool(toolName: string, input: unknown): ToolDecision {
	const canonical = canonicalToolName(toolName);
	if (!canonical.startsWith(CANONICAL_PREFIX)) {
		return { allowed: true };
	}

	if (canonical === RUN_CONFIG_TOOL) {
		const configurationName =
			typeof input === "object" && input !== null
				? (input as Record<string, unknown>).configurationName
				: undefined;
		if (configurationName === ALLOWED_RUN_CONFIG) {
			return { allowed: true };
		}
		return deny(
			`run configuration ${String(configurationName)} is not allowed (only ${ALLOWED_RUN_CONFIG})`,
		);
	}

	if (ALLOWED_EXACT.has(canonical)) {
		return { allowed: true };
	}
	if (ALLOWED_PREFIXES.some((prefix) => canonical.startsWith(prefix))) {
		return { allowed: true };
	}

	return deny(`tool ${toolName} is not on the read-only whitelist`);
}
