// OpenCode 2 TUI part (V2 plugin API, issue #266). Registered in cli.json.
//
// Reads the startup-check report written by the server part and shows a short
// toast when the TUI starts. The full report stays in
// ~/.config/sandbox-kit/startup-checks.report (and in the session context).
import { Plugin } from "@opencode/plugin/tui"
import { readFileSync } from "node:fs"

const home = process.env.HOME || "/home/agent"
const reportFile = `${home}/.config/sandbox-kit/startup-checks.report`

function summary() {
  try {
    const report = readFileSync(reportFile, "utf8").trim()
    if (!report) return undefined
    const failed = report.split(/\s+/).filter((token) => token.endsWith(":FAIL"))
    return failed.length ? `Startup checks: ${failed.join(" ")}` : "Startup checks: all OK"
  } catch {
    return undefined
  }
}

export default Plugin.define({
  id: "kit.startup-checks-tui",
  async setup(context) {
    const text = summary()
    if (!text) return
    context.ui.toast.show({
      title: "sandbox-kit",
      message: text,
      variant: text.includes(":FAIL") ? "warning" : "success",
      duration: 8000,
    })
  },
})
