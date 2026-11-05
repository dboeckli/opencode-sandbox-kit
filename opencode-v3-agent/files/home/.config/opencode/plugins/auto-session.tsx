/** @jsxImportSource @opentui/solid */
import type { TuiPlugin, TuiPluginModule } from "@opencode-ai/plugin/tui"

const tui: TuiPlugin = async (api) => {
  const argv = process.argv.slice(2)
  const hasExplicitTarget = argv.some(
    (a) => a === "--continue" || a === "-c" || a === "--session" || a === "-s" || a === "--prompt" || a === "--fork",
  )
  if (hasExplicitTarget) return

  const timer = setInterval(async () => {
    if (!api.state.ready) return
    clearInterval(timer)
    if (api.route.current.name !== "home") return
    try {
      const result = await api.client.session.create({ body: {} })
      const sessionID = result.data?.id
      if (sessionID) api.route.navigate("session", { sessionID })
    } catch (e) {
      // fall back to manual start (home view)
    }
  }, 200)

  api.lifecycle.onDispose(() => clearInterval(timer))
}

const plugin: TuiPluginModule & { id: string } = {
  id: "sandbox-kit.auto-session",
  tui,
}

export default plugin
