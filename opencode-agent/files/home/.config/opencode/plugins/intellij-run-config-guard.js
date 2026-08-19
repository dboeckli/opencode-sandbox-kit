// Allowlist for idea_execute_run_configuration. Everything else is blocked.
// This cannot be expressed via the `permission` config, because MCP tools always
// report resource "*" to the permission system (never the tool input), so the
// configurationName is only visible here in the tool.execute.before hook.
const ALLOWED_RUN_CONFIGS = new Set(["local-test-kits-validate-only"])

export const IntelliJRunConfigGuard = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "idea_execute_run_configuration") return
      const name = output.args?.configurationName
      if (typeof name !== "string" || !ALLOWED_RUN_CONFIGS.has(name)) {
        throw new Error(
          `Run configuration "${name ?? "(none)"}" is not allowed. Allowed: ${[...ALLOWED_RUN_CONFIGS].join(", ")}`,
        )
      }
    },
  }
}
