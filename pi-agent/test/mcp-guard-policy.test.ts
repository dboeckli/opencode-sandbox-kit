import assert from "node:assert/strict";
import test from "node:test";

import {
	canonicalToolName,
	isAllowedTool,
} from "../files/home/.pi/agent/lib/mcp-guard-policy.ts";

// Pi registers gateway tools as `mcp__mcp_gateway__<tool>`.
const pi = (name: string) => `mcp__mcp_gateway__${name}`;

test("normalizes Pi gateway tool names", () => {
	assert.equal(canonicalToolName(pi("pods_list")), "mcp-gateway_pods_list");
	assert.equal(canonicalToolName("mcp-gateway_pods_list"), "mcp-gateway_pods_list");
	assert.equal(canonicalToolName("bash"), "bash");
});

test("allows Pi-prefixed read-only Kubernetes tools", () => {
	assert.equal(isAllowedTool(pi("pods_list"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("resources_get"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("helm_list"), {}).allowed, true);
});

test("allows read-only prefix groups", () => {
	assert.equal(isAllowedTool(pi("get_symbol_info"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("list_containers"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("search_symbol"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("read_file"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("generate_psi_tree"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("buildx_list"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("buildx_history"), {}).allowed, true);
	assert.equal(isAllowedTool(pi("buildx_logs"), {}).allowed, true);
});

test("blocks Pi-prefixed write and exec tools", () => {
	for (const name of [
		"pods_delete",
		"pods_exec",
		"resources_create_or_update",
		"helm_install",
		"create_container",
		"run_container",
		"build_image",
		"apply_patch",
		"execute_terminal_command",
		"reformat_file",
	]) {
		assert.equal(isAllowedTool(pi(name), {}).allowed, false, name);
	}
});

test("allows execute_run_configuration only for local-test-kits-validate-only", () => {
	assert.equal(
		isAllowedTool(pi("execute_run_configuration"), {
			configurationName: "local-test-kits-validate-only",
		}).allowed,
		true,
	);
	assert.equal(
		isAllowedTool(pi("execute_run_configuration"), {
			configurationName: "build-and-publish-pi-image",
		}).allowed,
		false,
	);
	assert.equal(isAllowedTool(pi("execute_run_configuration"), {}).allowed, false);
});

test("keeps the legacy mcp-gateway_ names working", () => {
	assert.equal(isAllowedTool("mcp-gateway_pods_list", {}).allowed, true);
	assert.equal(isAllowedTool("mcp-gateway_pods_delete", {}).allowed, false);
});

test("leaves non-gateway tools untouched", () => {
	assert.equal(isAllowedTool("bash", {}).allowed, true);
	assert.equal(isAllowedTool("read", {}).allowed, true);
});
