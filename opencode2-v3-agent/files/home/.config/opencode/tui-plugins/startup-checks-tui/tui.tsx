/** @jsxImportSource @opentui/solid */
// OpenCode 2 TUI part (V2 plugin API, issue #266). Registered in cli.json.
//
// Renders the same three sandbox-kit panels as the opencode-v3 kit in the
// session sidebar and keeps the startup toast. V2 names the slot
// "sidebar.content" (dot notation) where v3 uses "sidebar_content"; claims are
// made through context.ui.slot({ append: … }).
//
// Data sources (identical to the v3 kit):
//   ~/.config/sandbox-kit/startup-checks.report  written by the server plugin
//   ~/.agents/skills/                            installed skill bundles
//   ~/.config/sandbox-kit/check-infra.sh         live MCP/host probes
import { createSignal } from "solid-js"
import type { JSX } from "@opentui/solid"
import { readFileSync, readdirSync } from "node:fs"
import { exec } from "node:child_process"
import { Plugin } from "@opencode/plugin/tui"

const home = process.env.HOME || "/home/agent"
const REPORT_FILE = `${home}/.config/sandbox-kit/startup-checks.report`
const SKILLS_DIR = `${home}/.agents/skills`
const INFRA_SCRIPT = `${home}/.config/sandbox-kit/check-infra.sh`

const readReport = () => {
  try {
    return readFileSync(REPORT_FILE, "utf8").trim()
  } catch {
    return ""
  }
}

const readSkills = () => {
  try {
    return readdirSync(SKILLS_DIR, { withFileTypes: true })
      .filter((d) => d.isDirectory() && readdirSync(`${SKILLS_DIR}/${d.name}`).includes("SKILL.md"))
      .map((d) => d.name)
      .sort()
  } catch {
    return []
  }
}

const runInfra = (): Promise<string> =>
  new Promise((resolve) => {
    exec(`bash ${INFRA_SCRIPT}`, { timeout: 15000 }, (err, stdout) => {
      const line = (stdout || "").trim()
      if (err || !line) resolve("mcp-gateway:FAIL mcp-idea:FAIL mcp-k8s:FAIL mcp-docker:FAIL mcp-client:FAIL")
      else resolve(line)
    })
  })

/** "a:OK b:FAIL" → [{ name, status }] */
const tokens = (line: string) =>
  line
    .replace(/^\[startup-checks\]\s*/, "")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => {
      const [name, status] = t.split(":")
      return { name, status }
    })

const summary = (report: string) => {
  if (!report) return undefined
  const failed = tokens(report).filter((t) => t.status === "FAIL")
  return failed.length
    ? `Startup checks: ${failed.map((t) => `${t.name}:FAIL`).join(" ")}`
    : "Startup checks: all OK"
}

export default Plugin.define({
  id: "kit.startup-checks-tui",
  async setup(context) {
    const skin = {
      panel: context.theme.background.raised.base,
      border: context.theme.border.base,
      text: context.theme.text.base,
      muted: context.theme.text.muted,
      accent: context.theme.text.action.primary.base,
      ok: context.theme.text.feedback.success.base,
      fail: context.theme.text.feedback.error.base,
    }
    const color = (status?: string) =>
      status === "OK" ? skin.ok : status === "FAIL" ? skin.fail : skin.muted

    const [report, setReport] = createSignal(readReport())
    const [skills, setSkills] = createSignal(readSkills())
    const [infra, setInfra] = createSignal("running…")

    const reportTimer = setInterval(() => {
      const next = readReport()
      if (next !== report()) setReport(next)
    }, 3000)

    const skillsTimer = setInterval(() => {
      const next = readSkills()
      if (next.join(",") !== skills().join(",")) setSkills(next)
    }, 5000)

    let infraTimer: ReturnType<typeof setTimeout> | undefined
    let disposed = false
    const refreshInfra = async () => {
      const line = await runInfra()
      if (disposed) return
      setInfra(line)
      infraTimer = setTimeout(refreshInfra, 10000)
    }
    infraTimer = setTimeout(refreshInfra, 0)

    const frame = (title: string, body: () => JSX.Element) => (
      <box
        border
        borderColor={skin.border}
        backgroundColor={skin.panel}
        paddingTop={1}
        paddingBottom={1}
        paddingLeft={2}
        paddingRight={2}
        flexDirection="column"
        gap={1}
      >
        <text fg={skin.accent}>
          <b>{title}</b>
        </text>
        {body()}
      </box>
    )

    const disposeReport = context.ui.slot({
      append: "sidebar.content",
      render: () =>
        frame("Startup checks", () =>
          report() ? (
            <box flexDirection="row" flexWrap="wrap">
              <text fg={skin.muted}>[startup-checks] </text>
              {tokens(report()).map((t) => (
                <text fg={color(t.status)}>{`${t.name}:${t.status} `}</text>
              ))}
            </box>
          ) : (
            <text fg={skin.muted}>running…</text>
          ),
        ),
    })

    const disposeSkills = context.ui.slot({
      append: "sidebar.content",
      render: () =>
        frame("Skills", () => (
          <text fg={skills().length ? skin.text : skin.muted}>
            {skills().length ? skills().join("\n") : "none installed"}
          </text>
        )),
    })

    const disposeInfra = context.ui.slot({
      append: "sidebar.content",
      render: () =>
        frame("MCP & Host Systems", () =>
          infra() === "running…" ? (
            <text fg={skin.muted}>running…</text>
          ) : (
            <box flexDirection="column">
              {tokens(infra()).map((t) => (
                <text fg={color(t.status)}>{`${t.name}:${t.status}`}</text>
              ))}
            </box>
          ),
        ),
    })

    const text = summary(report())
    if (text) {
      context.ui.toast.show({
        title: "sandbox-kit",
        message: text,
        variant: text.includes(":FAIL") ? "warning" : "success",
        duration: 8000,
      })
    }

    return () => {
      disposed = true
      clearInterval(reportTimer)
      clearInterval(skillsTimer)
      if (infraTimer) clearTimeout(infraTimer)
      disposeReport()
      disposeSkills()
      disposeInfra()
    }
  },
})
