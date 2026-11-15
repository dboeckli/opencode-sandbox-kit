// OpenCode 2 server plugin (V2 plugin API, issue #266).
//
// Runs the sandbox startup checks once at plugin load, writes the report for
// the TUI part and injects it into the session context (V2 replacement for the
// V1 `experimental.chat.system.transform` hook).
//
// `setup` must not await the checks: the plugin host waits for `setup` before
// the location is ready, and the deep probes can take a while. The promise is
// created once and awaited lazily in the context hook instead.
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { mkdirSync, writeFileSync } from "node:fs"
import path from "node:path"

const home = process.env.HOME || "/home/agent"
const reportFile = path.join(home, ".config/sandbox-kit/startup-checks.report")
const checksScript = path.join(home, ".config/sandbox-kit/run-checks.sh")

function runChecks() {
  return new Promise((resolve) => {
    execFile("bash", [checksScript], { timeout: 60000, maxBuffer: 1024 * 1024 }, (err, stdout) => {
      const report = String(stdout || "").trim()
      resolve(report || "[startup-checks] FAILED to run checks")
    })
  })
}

const report = runChecks()
report.then((text) => {
  try {
    mkdirSync(path.dirname(reportFile), { recursive: true })
    writeFileSync(reportFile, text)
  } catch {
    // report file is optional (used by the TUI part)
  }
})

export default Plugin.define({
  id: "kit.startup-checks",
  async setup(ctx) {
    await ctx.session.hook("context", async (event) => {
      event.system.push({ type: "text", text: await report })
    })
  },
})
