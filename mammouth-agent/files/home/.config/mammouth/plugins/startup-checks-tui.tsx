/** @jsxImportSource @opentui/solid */
import { createSignal } from "solid-js"
import { readFileSync, readdirSync } from "node:fs"
import { exec } from "node:child_process"
import type { TuiPlugin, TuiPluginModule } from "@opencode-ai/plugin/tui"

const REPORT_FILE = `${process.env.HOME}/.config/sandbox-kit/startup-checks.report`
const SKILLS_DIR = `${process.env.HOME}/.agents/skills`
const INFRA_SCRIPT = `${process.env.HOME}/.config/sandbox-kit/check-infra.sh`

const runInfra = (): Promise<string> =>
  new Promise((resolve) => {
    exec(`bash ${INFRA_SCRIPT}`, { timeout: 15000 }, (err, stdout) => {
      const line = (stdout || "").trim()
      if (err || !line) resolve("docker:FAIL kubernetes:FAIL")
      else resolve(line)
    })
  })

const fallback = {
  panel: "#1d1d1d",
  border: "#4a4a4a",
  text: "#f0f0f0",
  muted: "#a5a5a5",
  accent: "#5f87ff",
}

const look = (map) => ({
  panel: typeof map?.backgroundPanel === "string" ? map.backgroundPanel : fallback.panel,
  border: typeof map?.border === "string" ? map.border : fallback.border,
  text: typeof map?.text === "string" ? map.text : fallback.text,
  muted: typeof map?.textMuted === "string" ? map.textMuted : fallback.muted,
  accent: typeof map?.primary === "string" ? map.primary : fallback.accent,
})

const readReport = () => {
  try {
    return readFileSync(REPORT_FILE, "utf8").trim()
  } catch (e) {
    return ""
  }
}

const readSkills = () => {
  try {
    return readdirSync(SKILLS_DIR, { withFileTypes: true })
      .filter((d) => d.isDirectory() && readdirSync(`${SKILLS_DIR}/${d.name}`).includes("SKILL.md"))
      .map((d) => d.name)
      .sort()
  } catch (e) {
    return []
  }
}

const tui: TuiPlugin = async (api) => {
  api.slots.register({
    order: 150,
    slots: {
      sidebar_content(ctx, props) {
        const skin = look(ctx.theme.current)
        const [report, setReport] = createSignal(readReport())

        const timer = setInterval(() => {
          const next = readReport()
          if (next !== report()) setReport(next)
        }, 3000)

        api.lifecycle.onDispose(() => clearInterval(timer))

        return (
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
              <b>Startup checks</b>
            </text>
            <text fg={report() ? skin.text : skin.muted}>
              {report() || "running…"}
            </text>
          </box>
        )
      },
    },
  })

  api.slots.register({
    order: 155,
    slots: {
      sidebar_content(ctx, props) {
        const skin = look(ctx.theme.current)
        const [skills, setSkills] = createSignal(readSkills())

        const timer = setInterval(() => {
          const next = readSkills()
          if (next.join(",") !== skills().join(",")) setSkills(next)
        }, 5000)

        api.lifecycle.onDispose(() => clearInterval(timer))

        return (
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
              <b>Skills</b>
            </text>
            <text fg={skills().length ? skin.text : skin.muted}>
              {skills().length ? skills().join("\n") : "none installed"}
            </text>
          </box>
        )
      },
    },
  })

  api.slots.register({
    order: 160,
    slots: {
      sidebar_content(ctx, props) {
        const skin = look(ctx.theme.current)
        const [infra, setInfra] = createSignal("running…")

        let disposed = false
        let timer
        const refresh = async () => {
          const line = await runInfra()
          if (disposed) return
          setInfra(line)
          timer = setTimeout(refresh, 10000)
        }
        timer = setTimeout(refresh, 0)

        api.lifecycle.onDispose(() => {
          disposed = true
          if (timer) clearTimeout(timer)
        })

        return (
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
              <b>Docker / Kubernetes</b>
            </text>
            {infra() === "running…" ? (
              <text fg={skin.muted}>running…</text>
            ) : (
              <box flexDirection="row" flexWrap="wrap">
                {infra()
                  .trim()
                  .split(/\s+/)
                  .filter(Boolean)
                  .map((t) => {
                    const status = t.split(":")[1]
                    const fg = status === "OK" ? "#5faf5f" : status === "FAIL" ? "#ff5f5f" : skin.muted
                    return <text fg={fg}>{t} </text>
                  })}
              </box>
            )}
          </box>
        )
      },
    },
  })
}

const plugin: TuiPluginModule & { id: string } = {
  id: "sandbox-kit.startup-checks",
  tui,
}

export default plugin
