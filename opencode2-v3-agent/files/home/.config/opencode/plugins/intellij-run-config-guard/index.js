// OpenCode 2 server plugin (V2 plugin API, issue #266).
//
// Allowlist for mcp-gateway_execute_run_configuration (IntelliJ MCP via the sbx
// MCP gateway). Everything else is blocked. This cannot be expressed via the
// `permissions` config, because MCP tool inputs are not visible to the
// permission system (the rule only sees the tool name), so the
// configurationName is only visible here in the tool execute.before hook.
import { Plugin } from "@opencode/plugin"

const ALLOWED_RUN_CONFIGS = new Set(["local-test-kits-validate-only"])

export default Plugin.define({
  id: "kit.intellij-run-config-guard",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "mcp-gateway_execute_run_configuration") return
      const name = event.input?.configurationName
      if (typeof name !== "string" || !ALLOWED_RUN_CONFIGS.has(name)) {
        throw new Error(
          `Run configuration "${name ?? "(none)"}" is not allowed. Allowed: ${[...ALLOWED_RUN_CONFIGS].join(", ")}`,
        )
      }
    })
  },
})
