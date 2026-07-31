export const StartupChecks = async ({ $ }) => {
  let report = null

  const run = async () => {
    if (report !== null) return report
    try {
      report = (await $`bash ~/.config/sandbox-kit/run-checks.sh`.text()).trim()
    } catch (e) {
      report = "[startup-checks] FAILED to run checks"
    }
    try {
      const reportFile = `${process.env.HOME}/.config/sandbox-kit/startup-checks.report`
      await Bun.write(reportFile, report)
    } catch (e) {
      // report file is optional (used by the TUI sidebar plugin)
    }
    return report
  }

  return {
    "experimental.chat.system.transform": async (input, output) => {
      output.system.push(await run())
    },
  }
}
