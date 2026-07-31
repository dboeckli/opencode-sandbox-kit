export const StartupChecks = async ({ $ }) => {
  const run = async () => {
    let report = "[startup-checks] FAILED to run checks"
    try {
      report = (await $`bash ~/.config/sandbox-kit/run-checks.sh`.text()).trim()
    } catch (e) {
      // report stays FAILED
    }
    try {
      const reportFile = `${process.env.HOME}/.config/sandbox-kit/startup-checks.report`
      await Bun.write(reportFile, report)
    } catch (e) {
      // report file is optional (used by the TUI sidebar plugin)
    }
    return report
  }

  // Run checks immediately at startup so the report and TUI sidebar are
  // ready before the first user message (no lazy trigger needed).
  const reportPromise = run()

  return {
    "experimental.chat.system.transform": async (input, output) => {
      output.system.push(await reportPromise)
    },
  }
}
