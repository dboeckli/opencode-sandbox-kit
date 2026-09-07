# sbx CLI Reference (offline)

Kompakte Offline-Referenz der **Docker Sandboxes CLI (`sbx`)** — generiert aus den authentischen
`--help`-Outputs der **v0.42.0**-Release-Binary (`docker/sbx-releases`). Includiert NICHT das
interaktive TUI; aktualisieren durch Neugenerierung aus der Binary (`sbx <cmd> --help`).
Detaillierte Hintergrunddoku (Kits, Policy, Proxy, Troubleshooting): `npx ctx7 docs /docker/docs <query>`
(nur teilweise abgedeckt — die CLI selbst ist NICHT in Context7). Kit-Grammatik v2:
`https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md`.

## sbx --help
```
Docker Sandboxes creates isolated sandbox environments for AI agents, powered by Docker.

Run without a command to launch interactive mode, or pass a command for CLI usage.

Usage:
  sbx COMMAND

Available Commands:
  attach      Attach to a running cloud sandbox
  completion  Generate the autocompletion script for the specified shell
  cp          Copy files or directories between a sandbox and the host
  create      Create a sandbox for an agent
  daemon      Manage sandboxd daemon
  diagnose    Diagnose common issues with your sbx installation
  env         (Experimental) Manage sandboxes declaratively from an sbxenv.yaml file
  exec        Execute a command inside a sandbox
  help        Help about any command
  kit         (Experimental) Manage kit artifacts
  login       Sign in to Docker
  logout      Stop all running sandboxes and sign out of Docker
  ls          List sandboxes
  mcp         Manage MCP servers
  move        Move a sandbox between local and cloud
  policy      Manage sandbox policies
  ports       Manage sandbox port publishing
  prune       Remove all stopped sandboxes
  reset       Reset all sandboxes and clean up state
  rm          Remove one or more sandboxes
  run         Run an agent in a sandbox
  secret      Manage stored secrets
  setup       (Experimental) Detect host configuration and prepare Docker Sandboxes
  skills      (Experimental) Manage skills available in sandboxes
  stop        Stop one or more sandboxes without removing them
  template    Manage sandbox templates
  ttl         Inspect or extend a cloud sandbox's TTL
  tui         Open the interactive TUI dashboard
  version     Show Docker Sandboxes version information
  volume      Manage persistent volumes (cloud-only)

Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
  -h, --help                   help for sbx

Use "sbx COMMAND --help" for more information about a command.
```

## sbx attach --help
```
Attach an interactive terminal session to a running cloud sandbox.

SANDBOX is the cloud sandbox ID (sbx_*) or name from "sbx --cloud ls".

Opens a PTY-backed exec session against the sandbox's agent process. The
sandbox must already exist and be in a running state; use `sbx --cloud run`
to create a sandbox and attach in one step.

Only supported with --cloud. See https://docs.docker.com/ai/sandboxes/ for the cloud sandbox model.

Usage:
  sbx attach SANDBOX [flags]

Examples:
  # Attach to a running sandbox by ID or name
  sbx --cloud attach sbx_abc123
  sbx --cloud attach claude/my-sandbox

Flags:
      --detach-keys string   Override the detach gesture that leaves the agent running (Docker-style, e.g. "ctrl-\", "ctrl-x,ctrl-d"). Default: Ctrl-\. Use this when the default collides with an agent's keymap (cloud only).
  -h, --help                 help for attach

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx completion --help
```
Generate the autocompletion script for sbx for the specified shell.
See each sub-command's help for details on how to use the generated script.

Usage:
  sbx completion COMMAND

Available Commands:
  bash        Generate the autocompletion script for bash
  fish        Generate the autocompletion script for fish
  powershell  Generate the autocompletion script for powershell
  zsh         Generate the autocompletion script for zsh

Flags:
  -h, --help   help for completion

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx completion COMMAND --help" for more information about a command.
```

## sbx cp --help
```
Either SRC or DST must be a sandbox path, written as SANDBOX:PATH.
The other must be a local path. Copying between two sandboxes is not supported. Or — with --cloud — the cloud sandbox
ID (sbx_*) or name from "sbx --cloud ls". Cloud transfers go through the Docker
Sandboxes Cloud file API instead of the local sandboxd.

When copying a directory, the directory itself is placed at the destination.
If the destination path does not exist it is created; if it already exists
as a directory, the source is placed inside it.

Usage:
  sbx cp [flags] SRC DST

Examples:
  # Copy a file from host to sandbox
  sbx cp ./config.json my-sandbox:/home/user/

  # Copy a file from sandbox to host
  sbx cp my-sandbox:/home/user/output.log ./

  # Copy a directory
  sbx cp ./src/ my-sandbox:/home/user/src

  # Copy to/from a cloud sandbox
  sbx --cloud cp ./config.json sbx_abc:/workspace/config.json
  sbx --cloud cp sbx_abc:/workspace/out.log ./

Flags:
  -L, --follow-link   Follow symbolic links in the source path
  -h, --help          help for cp

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx create --help
```
Create a sandbox with access to a host workspace for an agent.

The first positional argument may be a built-in agent name or a sandbox kit
reference. Sandbox kit references may be local directories, ZIP files, git
repositories, or OCI references. Relative local references must be explicit
paths such as ./my-kit or ../my-kit.zip.

Omit the path to create a sandbox without a workspace bind mount: the agent
then works in the container's own filesystem instead of on your files.

Use "sbx run --name SANDBOX" to attach to the agent after creation.

Without --cpus/--memory a cloud sandbox defaults to 2 CPUs and 4 GiB.

Usage:
  sbx create [flags] AGENT|SANDBOX_KIT [PATH...]
  sbx create COMMAND

Examples:
  # Create a sandbox for Claude in the current directory
  sbx create claude .

  # Create a sandbox with a custom name
  sbx create --name my-project claude /path/to/project

  # Create with additional read-only workspaces
  sbx create claude . /path/to/docs:ro

  # Create without a workspace bind mount
  sbx create claude

  # Create from a local sandbox kit
  sbx create ../path/to/my-agent/

  # Add a mixin to a built-in agent
  sbx create claude --kit ./my-mixin/

  # Run the agent on an in-container clone of the host repo, wired back via a git-daemon
  sbx create --clone claude .

Available Commands:
  claude         Create a sandbox for claude
  codex          Create a sandbox for codex
  copilot        Create a sandbox for copilot
  cursor         Create a sandbox for cursor
  devin          Create a sandbox for devin
  docker-agent   Create a sandbox for docker-agent
  droid          Create a sandbox for droid
  gemini         Create a sandbox for gemini
  kiro           Create a sandbox for kiro
  opencode       Create a sandbox for opencode
  shell          Create a sandbox for shell

Flags:
      --allow-network strings               Network pattern to allow for cloud sandbox egress (cloud only; can be specified multiple times)
      --clone                               Run the agent on a private in-container clone of the host Git repository (mounted read-only) instead of bind-mounting the workspace; the agent's commits are accessible via the sandbox-<name> git remote on the host
      --cpus int                            Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs)
      --deny-network sbx policy ls <NAME>   Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with sbx policy ls <NAME> / `sbx policy rm network --sandbox <NAME> --resource <HOST>`. Safe under centralized governance because a local deny can only narrow, never widen, egress.
  -e, --env stringArray                     Set an environment variable in the sandbox (can be repeated): KEY=VALUE, or a bare KEY to take the value from the current environment
      --env-file stringArray                Read environment variables from a file (can be repeated). --env wins over any file; a later file wins over an earlier one
  -h, --help                                help for create
      --image-ref string                    OCI image reference for inline-mode cloud create (mutually exclusive with --template; requires --cpus and --memory)
      --kit strings                         (Experimental) Additional kit reference (must be a mixin; directory, ZIP, git, or OCI). Can be specified multiple times
      --kit-arg stringArray                 (Experimental) Value for an argument the kit declares, as name=value for every kit or kit.name=value for one (can be repeated)
      --kit-args-file stringArray           (Experimental) File of name=value kit arguments, one per line (can be repeated); --kit-arg overrides
  -m, --memory string                       Memory limit in binary units (e.g., 1024m, 8g). Default: 50% of host memory, max 32 GiB
      --name string                         Name for the sandbox (defaults to <agent>-<workdir>; at least two characters, starting with a letter or number, containing only letters, numbers, hyphens and periods; 'default' is reserved)
      --on-timeout string                   What happens when --ttl lapses: 'delete' (default) tombstones the sandbox, or 'stop' stops it in place so it can be started again later (cloud only; 'stop' requires your account to be entitled to it).
      --platform string                     Target platform: linux/amd64 or linux/arm64 (cloud only). With --image-ref, omitting it lets the server resolve the platform from the image and the CLI sends the local CPU as a hint for multi-platform images. With --template, omitting it inherits the template platform.
      --profile string                      Governance profile to assign to the sandbox
  -p, --publish stringArray                 Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
  -q, --quiet                               Suppress verbose output
      --static-mcp strings                  MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time.
  -t, --template string                     Container image to use for the sandbox (default: agent-specific image)
      --ttl duration                        Cloud sandbox time-to-live before it times out (e.g. 30m, 2h; cloud only; default: server-side)
  -v, --volume stringArray                  (Experimental) Attach an existing persistent volume, NAME:MOUNTPATH (cloud only, experimental; repeatable)

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx create COMMAND --help" for more information about a command.
```

## sbx daemon --help
```
Manage sandboxd daemon

Usage:
  sbx daemon COMMAND

Available Commands:
  log-level   Inspect or change sandboxd's per-category log levels
  restart     Restart the sandboxd daemon
  start       Start the sandboxd daemon
  status      Check sandboxd daemon status
  stop        Stop the sandboxd daemon

Flags:
  -h, --help   help for daemon

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx daemon COMMAND --help" for more information about a command.
```

## sbx diagnose --help
```
Diagnose common issues with your sbx installation

Usage:
  sbx diagnose

Flags:
  -h, --help            help for diagnose
      --json            Output in JSON format (alias for --output json)
  -o, --output string   Output format: "json" or "github-issue"
      --upload          Upload diagnostics to Docker support

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx env --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Manage a sandbox environment declared in an sbxenv.yaml file.

The file describes the agent, optional mixin kits, workspace mounts,
environment variables, secrets to provision, and per-service credential
bindings. Secrets are provisioned at the environment's sandbox scope so
`sbx env rm` can remove everything it created.

A file may declare its own inputs in an `args:` block, each with a default or
`required: true` and an optional description, enum, or pattern. Reference one
as `${{ env.args.NAME }}` anywhere a value appears and supply it with
`--env-arg NAME=VALUE`.

A `kits:` entry is either a bare reference or a mapping carrying the
arguments that kit declares, which `--kit-arg` overrides per invocation:

  kits:
    - ./mixins/base
    - source: ./mixins/tool
      args:
        version: ${{ env.args.channel }}

A kit source written as an explicit relative path — `./…`, `../…`, `.`, `..`, or one
ending in `.zip` — is resolved against the directory of the file that declares
it, so a checked-in file reaches the same kits from wherever `sbx` is run. Write a
local kit that way: a bare `kits/tool` is as much a registry reference as a
directory, so it is left as written and resolves from the current directory.

A `workspace:` names the directory mounted read/write into the sandbox,
resolved against the project directory: the one holding the first PATH, or the
current directory when none is named. `workspace: .` mounts the project from
whichever file declares it. Declaring none mounts nothing — as omitting PATH
does for `sbx create` — and the agent works in the container's own filesystem
instead of on your files. Unless the file sets `name:`, the sandbox is named
after the mounted directory, or after the project directory when nothing is
mounted, so an environment that mounts nothing is still the same sandbox every
time.

A `lifecycle:` block declares commands that run on the host — outside
the sandbox, with your own privileges — around the sandbox's life:

  lifecycle:
    initialize:
      - command: test -d app || git clone https://github.com/acme/app
    postCreate:
      - command: ./scripts/seed-fixtures.sh
    preRemove:
      - command: ./scripts/archive-state.sh

Each runs through your shell from the project directory — the one holding the
first PATH, which is also what a relative "workspace:" resolves against, and is
shared by commands merged in from a file elsewhere. Change it per command with
`workdir:`, and cap a command's runtime with `timeout:`.

"initialize" runs on every "create" and every "run", including one that only
attaches, so it can produce the workspace the sandbox mounts; write it to be
repeatable. "postCreate" runs once the sandbox exists, and "preRemove" after
"sbx env rm" is confirmed but before it deletes anything. Whatever stops
preRemove is only a warning, so a teardown that cannot run still cannot make an
environment unremovable; what one adds to the environment instead — a stored
credential, an approved domain — stops the removal, since what follows would
delete it without a plan row ever naming it. "sbx env exec" runs no commands at
all.

Commands appear in the environment plan with the directory each runs in, and are
approved with it before the invocation does any work. An environment that declares
any of them asks on every invocation, whether or not this one is what runs them,
since approving a command also trusts whatever it invokes, including a script
whose contents change after the answer. Use --skip-host-commands to run none of
them.

Everything an environment sets up — host commands, credentials, bindings, MCP
registrations, directories, published ports, the sandbox itself and the
variables it runs with — is shown as a plan and approved before anything runs:

  ── ENVIRONMENT PLAN
     claude-proj

     secrets:
  +    anthropic:
  +      ref: op://vault/anthropic/key
  +      refresh: 55m

     lifecycle:
       initialize:
  ~      - command: make setup -> make setup && make seed
           workdir: /Users/me/proj

     Plan: + 1 to add, ~ 1 to change, - 0 to destroy.

     Approve this plan? [y/N]

The plan is your file: the same keys, nested the same way, in the order the
blocks are declared in, so a line is looked up where it was written. What the
plan adds is the margin, and the two values a line moves between. The totals
name every symbol the margin can carry: "+ to add" and "~ to change" above,
"- to destroy" for what "sbx env rm" takes away, "> to run" for a command that
runs again — a command converges to nothing, so it runs on every apply that
reaches it — and "! to forget" for a resource this environment applied and no
longer declares. Where the file has nothing to
say, a note in the margin does: that a resource is missing, or that the work
waits for the next create, since a port, a credential, a kit or a postCreate
command comes with the sandbox, so attaching to one that already exists leaves it
for the next one that is built. A resource that is as it was, and already
approved, is left out: what is on screen is what there is to read.

An attribute shows what the environment declares, so an edited kit argument or
variable reads as what it was against what it becomes, and a "command:" or "ref:"
secret shows where the credential comes from — a command that resolves one runs on
this machine. A secret's literal "value:" is the one exception: a plan is both shown
here and written to state, so it is named and stands in as a "sha256:" digest.

     kits:
  ~    - source: ./mixins/tool
  ~      args:
  ~        version: 1.2.3 -> 1.2.4
     env:
  ~    GOFLAGS: -mod=mod -> -mod=readonly

What an attribute was is what this environment last applied here, or — for one it
approved and never applied, such as a binding or a port answered for while
attaching to a sandbox that already exists — what was approved. Either way an
edit shows the value the question is about, whatever the row itself does.

An environment file that a mount would hand over read-write — which is what
mounting the project directory holding it does — is bound read-only at its own
path inside that mount, leaving the rest of it writable. The file decides what a
later invocation runs on this machine, so an agent able to edit it decides what
the next plan asks about. Declare "sandboxOptions.writableEnvFiles: true" where an
agent is meant to edit it; the plan then says the file is writable, as it says
when a file sits below a mount's own directory, where renaming that directory
reaches it again.

What was approved is recorded per environment under sbx's state directory, not
next to the file, so a later invocation asks only about what moved — and applies
silently when nothing did. An environment that declares commands running on this
machine is asked about on every invocation, changed or not: the answer is about
the invocation, and what a command does depends on what the project holds when it
runs rather than on the text approved before. "sbx env plan" prints the plan and
changes nothing.

Use --auto-approve (-y) where there is no terminal to answer on. Where an
environment's commands are your own and run many times a day,
"sbx settings set env.rememberHostCommands true" asks about them only when
they change.

Usage:
  sbx env COMMAND

Available Commands:
  create      Create a sandbox environment from sbxenv.yaml
  exec        Execute a command inside a sandbox environment
  plan        Show what an environment would change outside the sandbox
  rm          Remove a sandbox environment and its scoped resources
  run         Create (if needed) and attach to a sandbox environment

Flags:
  -h, --help   help for env

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx env COMMAND --help" for more information about a command.
```

## sbx exec --help
```
Execute a command in a sandbox. If the sandbox is stopped, it is started first. Or — with --cloud — the cloud sandbox
ID (sbx_*) or name from "sbx --cloud ls".

Flags match the behavior of "docker exec". Some flags (-d, --user, --privileged)
are not supported with --cloud and are rejected rather than silently ignored.
--detach-keys applies only to an interactive (-i/-t) cloud exec.

Usage:
  sbx exec [flags] SANDBOX COMMAND [ARG...]

Examples:
  # Open a shell inside a sandbox
  sbx exec -it my-sandbox bash

  # Run a command in the background
  sbx exec -d my-sandbox npm start

  # Run as root
  sbx exec -u root my-sandbox apt-get update

  # Cloud: run a command in a cloud sandbox by ID or name
  sbx --cloud exec -it sbx_abc123 bash
  sbx --cloud exec -it claude/my-sandbox bash

Flags:
  -d, --detach                 Detached mode: run command in the background
      --detach-keys string     Override the key sequence for detaching a container
  -e, --env stringArray        Set environment variables
      --env-file stringArray   Read in a file of environment variables
  -h, --help                   help for exec
  -i, --interactive            Keep STDIN open even if not attached
      --privileged             Give extended privileges to the command
  -t, --tty                    Allocate a pseudo-TTY
  -u, --user string            Username or UID (format: <name|uid>[:<group|gid>])
  -w, --workdir string         Working directory inside the container

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx help --help
```
Help provides help for any command in the application.
Simply type sbx help [path to command] for full details.

Usage:
  sbx help [COMMAND]

Flags:
  -h, --help   help for help

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx kit --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Manage kit artifacts.

Kits are declarative YAML artifacts that define sandbox agents or extend them
with additional credentials, network policies, environment variables, startup
commands, and files.

Usage:
  sbx kit COMMAND

Available Commands:
  add         Add a mixin to a sandbox
  inspect     Display details about a kit artifact
  pack        Package a directory as a kit artifact
  provenance  Show the SLSA provenance attached to a kit
  pull        Pull a kit artifact from an OCI registry
  push        Push a kit artifact to an OCI registry
  sign        Sign a kit artifact
  validate    Validate a kit artifact
  verify      Verify a kit artifact's signature

Flags:
  -h, --help   help for kit

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx kit COMMAND --help" for more information about a command.
```

## sbx login --help
```
Sign in to Docker

Usage:
  sbx login [flags]

Flags:
  -h, --help              help for login
      --password-stdin    Read password or access token from stdin
      --username string   Docker username for non-interactive login

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx logout --help
```
Stop all running sandboxes and sign out of Docker

Usage:
  sbx logout [flags]

Flags:
  -h, --help   help for logout
  -y, --yes    Skip confirmation prompt

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx ls --help
```
List all sandboxes with their agent, status, published ports, and workspace.

Usage:
  sbx ls [flags]

Aliases:
  ls, list

Flags:
  -h, --help    help for ls
      --json    Output in JSON format
  -q, --quiet   Only display sandbox names

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx mcp --help
```
Register and manage MCP servers for use with sandbox sessions.

Usage:
  sbx mcp COMMAND

Available Commands:
  add         Register an MCP server
  auth        Authorize MCP servers
  inspect     Show MCP server details
  load        Load an already-registered MCP server into a running sandbox
  ls          List MCP servers, grouped by the gateway that serves them
  rm          Remove a registered MCP server

Flags:
  -h, --help   help for mcp

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx mcp COMMAND --help" for more information about a command.
```

## sbx move --help
```
Move a sandbox between the local host and Docker's hosted Sandboxes service.

Move captures the source sandbox's filesystem as a template, transports the
OCI image across the local↔cloud boundary, and launches a new sandbox from
it on the destination.

Semantics (per the May 2026 design):
  - Source disposition: neither direction deletes the source. A local→cloud
    move stops the local source. A cloud→local move also tries to stop a
    source with a structured agent (best-effort: an ineligible account, or a
    request/wait failure, leaves it running instead); once stopped it keeps
    its ID and full state, so 'sbx --cloud run <agent>' brings it back, and
    'sbx --cloud rm <id>' deletes it when you no longer need it. A source
    with no reported agent is left running instead.
  - The destination sandbox gets a new ID; pass --name to control its name.
  - Filesystem-only: in-memory state, running processes, and open sockets
    are NOT carried across.
  - Network policy: a local→cloud move carries the source's egress
    allow/deny rules onto the cloud sandbox. A cloud→local move starts the
    local sandbox with the host's default network posture (the cloud source's
    policy is not currently read back). Secrets never follow.

Usage:
  sbx move SANDBOX [flags]

Examples:
  # Move a cloud sandbox down to the local host
  sbx move sbx_abc123 --to local

  # Move a local sandbox up to the cloud
  sbx move my-sandbox --to cloud

  # Give the destination sandbox a custom name
  sbx move sbx_abc123 --to local --name big-refactor

Flags:
  -f, --force         Skip the confirmation prompt when moving a sandbox whose workspace files won't travel to the cloud
  -h, --help          help for move
      --name string   Name for the destination sandbox (default: derived from the source ID)
      --to string     Destination of the move: 'local' (cloud→local) or 'cloud' (local→cloud)

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx policy --help
```
Manage persistent access policies for sandboxes.

Policies contain rules that control what sandboxes can access. Local rules
can apply globally across all sandboxes or be scoped to one sandbox. Use
subcommands to allow, deny, list, or remove rules.

Usage:
  sbx policy COMMAND

Available Commands:
  allow       Add an allow rule for sandboxes
  check       Check whether policy allows an access request
  deny        Add a deny rule for sandboxes
  init        Initialize the global network policy
  inspect     Inspect policy or rule details
  log         Show sandbox policy logs
  ls          List sandbox policies
  profile     Manage policy profiles
  reset       Reset policies to defaults
  rm          Remove a policy rule

Flags:
  -h, --help   help for policy

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx policy COMMAND --help" for more information about a command.
```

## sbx ports --help
```
Manage sandbox port publishing.

List, publish, or unpublish sandbox ports. Publishing a local port starts a
stopped sandbox before creating the host binding. Without --publish or
--unpublish flags, lists all published ports.

Port spec format: [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
If HOST_PORT is omitted, an ephemeral port is allocated automatically.
If HOST_IP is omitted, the port is bound on loopback, expanded based on
PROTOCOL and the sandbox's address families: tcp/udp binds both 127.0.0.1
and ::1 (or only 127.0.0.1 if the sandbox is IPv4-only); tcp4/udp4 binds
only 127.0.0.1; tcp6/udp6 binds only ::1.
Supported protocols: tcp, tcp4, tcp6, udp, udp4, udp6.

When publishing without a PROTOCOL, tcp4 is used — so a sandbox service
listening only on IPv4 is reachable without a host client having to avoid
::1 — or tcp6 when HOST_IP is an IPv6 address. Publish tcp explicitly to
bind both families.

When unpublishing without a PROTOCOL, the mapping is removed whether it was
published with that same default or as dual-stack tcp. Name the protocol to
remove a tcp6 or udp mapping; anything left behind is reported.

In cloud mode (--cloud), the sandbox may be given by ID (sbx_*) or name, and
only the sandbox port number is accepted. The cloud control plane assigns a
publicly reachable URL for each exposed port.

Usage:
  sbx ports SANDBOX [flags]

Examples:
  # List published ports
  sbx ports my-sandbox

  # Publish sandbox port 8080 to an ephemeral host port
  sbx ports my-sandbox --publish 8080

  # Publish with a specific host port
  sbx ports my-sandbox --publish 3000:8080

  # Unpublish a port
  sbx ports my-sandbox --unpublish 3000:8080

  # Expose port 8080 on a cloud sandbox
  sbx ports sbx_abc123 --cloud --publish 8080

  # Remove an exposed port from a cloud sandbox
  sbx ports sbx_abc123 --cloud --unpublish 8080

Flags:
  -h, --help                    help for ports
      --json                    Output in JSON format (for port listing)
      --publish stringArray     Publish a port (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL] (local) or SANDBOX_PORT (cloud)
      --unpublish stringArray   Unpublish a port (can be repeated): [HOST_IP:]HOST_PORT:SANDBOX_PORT[/PROTOCOL] (local) or SANDBOX_PORT (cloud)

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx prune --help
```
Remove all stopped sandboxes and their associated resources.

Only stopped sandboxes are candidates — a running sandbox is never removed,
which makes this safe to run habitually. Stop a sandbox first with
"sbx stop" if you want it pruned. To remove a specific sandbox regardless of
state, use "sbx rm SANDBOX".

Use --filter since=DURATION to narrow the set to sandboxes that have been
stopped for longer than DURATION (e.g. since=168h to keep anything stopped
within the last week). A sandbox whose stop time the daemon cannot report is
left alone, since how long it has been stopped cannot be established.

Use --dry-run to list what would be removed without removing anything, and
--json with it for machine-readable output.

Pruning requires confirmation; use --force to skip the confirmation prompt
(for non-interactive scripts) and to remove a sandbox that is in use (e.g. an
open SSH connection). This action cannot be undone.

Secrets scoped to each successfully pruned sandbox are also deleted.

Local-only: cloud sandboxes expire via their TTL.

Usage:
  sbx prune [flags]

Flags:
      --dry-run              List the sandboxes that would be removed without removing them
      --filter stringArray   Filter candidates (supported: since=DURATION — stopped for longer than DURATION)
  -f, --force                Skip confirmation prompts and remove even if in use (e.g. an open SSH connection)
  -h, --help                 help for prune
      --json                 Output the --dry-run listing in JSON format

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx reset --help
```
Reset Docker Sandboxes to a freshly-installed state.

This command will:
- Stop all running sandboxes gracefully (30s timeout)
- Clear image cache
- Clear all internal registries
- Delete all sandbox state
- Remove all policies
- Remove the managed SSH configuration
- Clear the Gordon assistant's sessions and history
- Delete all stored secrets
- Sign out of Docker Sandboxes
- Stop the daemon
- Remove all state, cache, and config directories

WARNING: This is destructive and cannot be undone.
Running agents will be terminated and their work lost.
Cached images will be deleted and recreated on next use.
Stored secrets will need to be re-entered.

Use --preserve-secrets to keep stored secrets.
By default, you will be prompted to confirm (y/N).
Use --force to skip the confirmation prompt.

Usage:
  sbx reset [flags]

Flags:
  -f, --force              Skip confirmation prompt
  -h, --help               help for reset
      --preserve-secrets   Keep stored secrets

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx rm --help
```
Remove one or more sandboxes and all associated resources. Or — with --cloud — the cloud sandbox
ID (sbx_*) or name from "sbx --cloud ls".

For local sandboxes, stops them, removes their containers, cleans up any Git
worktrees, deletes sandbox state, and deletes secrets scoped to each removed
sandbox. This action cannot be undone. With --cloud, deletes
the sandbox in Docker Sandboxes Cloud. This action cannot be undone.

Removal requires confirmation; use --force to skip confirmation prompts
(for non-interactive scripts) and to delete a sandbox that is in use
(e.g. an open SSH connection). Use --all to remove every sandbox. With --cloud, --all is
intentionally disabled as a safety gate — the blast radius covers every
sandbox the credential can see, which may include shared or production
workloads. Pass IDs explicitly in --cloud mode.

Usage:
  sbx rm [SANDBOX...] [flags]

Aliases:
  rm, remove, delete

Flags:
      --all     Remove all sandboxes
  -f, --force   Skip confirmation prompts and delete even if in use (e.g. an open SSH connection)
  -h, --help    help for rm

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx run --help
```
Run an agent in a sandbox, creating the sandbox if it does not already exist.

The first positional argument identifies the agent to run. It may be a built-in
agent name or a sandbox kit reference. Sandbox kit references may be local
directories, ZIP files, git repositories, or OCI references. Relative local
references must be explicit paths such as ./my-kit or ../my-kit.zip; bare values
retain their agent or sandbox-name meaning. To re-attach to an existing sandbox
by name, use --name; the agent positional is optional when the named sandbox
already exists and is read from its spec.

Pass agent arguments after the "--" separator. Additional workspaces can be
provided as extra arguments. Append ":ro" to mount them read-only; a read-only
argument may name a single file, which holds that one path out of reach inside a
workspace the sandbox can otherwise write.

Omit the path to mount the current directory. Pass a path to mount a different
workspace.

To create a sandbox without attaching, use "sbx create" instead, or
pass --detached (-d) to print the sandbox ID and exit without opening an
interactive session.

With --cloud: the agent runs in the cloud sandbox image (started server-side).
Running an agent that has existing sandboxes (running or stopped) prompts you
to pick one to reuse or to create a new one. Pass --new to skip the prompt and
always create a fresh sandbox. --detached also skips the prompt and always
creates a new sandbox; a non-interactive run without --detached is refused.
Use --detached for non-interactive scripting (e.g.
sbx --cloud run -d claude && sbx --cloud exec ...).
Without --cpus/--memory a cloud sandbox defaults to 2 CPUs and 4 GiB.
Templates referenced via -t / --template must already exist in the cloud registry;
the CLI does not upload them automatically. See https://docs.docker.com/ai/sandboxes/ for the cloud sandbox model.

Available agents: claude, codex, copilot, cursor, devin, docker-agent, droid, gemini, kiro, opencode, shell

Usage:
  sbx run [flags] [AGENT|SANDBOX_KIT] [PATH...] [-- AGENT_ARGS...]

Examples:
  # Create and run a sandbox with claude in the current directory
  sbx run claude

  # Create and run from a local sandbox kit
  sbx run ../path/to/my-agent/

  # Create and run from an OCI sandbox kit
  sbx run ghcr.io/foo/my-agent:latest

  # Add a mixin to a built-in agent
  sbx run claude --kit ./my-mixin/

  # Create and run with additional workspaces (read-only)
  sbx run claude . /path/to/docs:ro

  # Re-attach to an existing sandbox by name (agent read from its spec)
  sbx run --name existing-sandbox

  # Re-attach to an existing sandbox by name and verify the expected agent
  sbx run claude --name existing-sandbox

  # Run a sandbox with agent arguments
  sbx run claude -- --continue

  # Create a cloud sandbox non-interactively and print its ID
  sbx --cloud run --detached claude

Flags:
      --allow-network strings               Network pattern to allow for cloud sandbox egress (cloud only; can be specified multiple times)
      --clone                               Run the agent on a private in-container clone of the host Git repository; must be set at sandbox creation time (no-op when re-attaching to an existing clone-mode sandbox)
      --cpus int                            Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs)
      --deny-network sbx policy ls <NAME>   Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with sbx policy ls <NAME> / `sbx policy rm network --sandbox <NAME> --resource <HOST>`. Safe under centralized governance because a local deny can only narrow, never widen, egress.
      --detach-keys string                  Override the detach gesture that leaves the agent running (Docker-style, e.g. "ctrl-\", "ctrl-x,ctrl-d"). Default: Ctrl-\. Use this when the default collides with an agent's keymap (cloud only).
  -e, --env stringArray                     Set an environment variable in the sandbox (can be repeated): KEY=VALUE, or a bare KEY to take the value from the current environment. Applies to the agent session, so it takes effect on a re-attach too; also baked into the sandbox when this run creates it
      --env-file stringArray                Read environment variables from a file (can be repeated). --env wins over any file; a later file wins over an earlier one. Applies to the agent session, so it takes effect on a re-attach too; also baked into the sandbox when this run creates it
  -h, --help                                help for run
      --image-ref string                    OCI image reference for inline-mode cloud create (mutually exclusive with --template; requires --cpus and --memory)
      --kit strings                         (Experimental) Additional kit reference (must be a mixin; directory, ZIP, git, or OCI). Can be specified multiple times
      --kit-arg stringArray                 (Experimental) Value for an argument the kit declares, as name=value for every kit or kit.name=value for one (can be repeated)
      --kit-args-file stringArray           (Experimental) File of name=value kit arguments, one per line (can be repeated); --kit-arg overrides
  -m, --memory string                       Memory limit in binary units (e.g., 1024m, 8g). Default: 50% of host memory, max 32 GiB
      --name string                         Name for the sandbox (default: <agent>-<workdir>)
      --new                                 Always create a new cloud sandbox instead of prompting to reuse an existing one (cloud only)
      --on-timeout string                   What happens when --ttl lapses: 'delete' (default) tombstones the sandbox, or 'stop' stops it in place so it can be started again later (cloud only; 'stop' requires your account to be entitled to it).
      --platform string                     Target platform: linux/amd64 or linux/arm64 (cloud only). With --image-ref, omitting it lets the server resolve the platform from the image and the CLI sends the local CPU as a hint for multi-platform images. With --template, omitting it inherits the template platform.
      --profile string                      Governance profile to assign to the sandbox
  -p, --publish stringArray                 Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]. Applied when the sandbox is created; ignored when re-attaching (use "sbx ports")
      --static-mcp strings                  MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time and cannot be changed when re-attaching to an existing sandbox.
  -t, --template string                     Container image to use for the sandbox (default: agent-specific image)
      --ttl duration                        Cloud sandbox time-to-live before it times out (e.g. 30m, 2h; cloud only; default: server-side)
  -v, --volume stringArray                  (Experimental) Attach an existing persistent volume, NAME:MOUNTPATH (cloud only, experimental; repeatable)

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx secret --help
```
Manage stored secrets for sandbox environments.

SERVICE SECRETS (e.g. "github", "anthropic", "openai")
  When a sandbox starts, the proxy uses stored secrets to authenticate API
  requests on behalf of the agent. The secret is never exposed directly.
  Scoped globally (shared across all sandboxes) or to a specific sandbox.

REGISTRY SECRETS (e.g. "ghcr.io", "myregistry.azurecr.io")
  Used to pull private template images and kit artifacts before sandbox
  creation. Unlike service secrets, registry credentials are host-only by
  default. They are not injected into sandboxes unless --all-sandboxes or
  --sandbox is set (the credential never enters the sandbox filesystem).
  Use "sbx secret set --registry <host> --password-stdin" to store them.

Usage:
  sbx secret COMMAND

Available Commands:
  import      Import secrets detected in host environment variables
  ls          List stored secrets
  rm          Remove a secret
  set         Create or update a secret
  set-custom  (Experimental) Create or update a custom secret

Flags:
  -h, --help   help for secret

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx secret COMMAND --help" for more information about a command.
```

## sbx setup --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Detect what is already configured on your host and prepare Docker Sandboxes.

Agent secrets are detected from the built-in agent kit specs and the
env vars set on this host, and accepted secrets are imported into the global
secrets store (the same store as "sbx secret set"). When SSH_AUTH_SOCK is set,
setup can enable SSH-agent forwarding and either use each client's current
socket or persist a fixed socket path.

Usage:
  sbx setup [COMMAND]

Available Commands:
  ssh         Set up SSH client config for the sandbox endpoint

Flags:
  -h, --help   help for setup

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx setup COMMAND --help" for more information about a command.
```

## sbx skills --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Manage skills available to agents in Docker Sandboxes.

Skills are shared across sandboxes by default. Use --no-share-skills when
creating a sandbox to opt out.

Usage:
  sbx skills COMMAND

Available Commands:
  add         Add skills from a Git repository
  import      Import skills from supported agent directories
  ls          List installed skills
  rm          Remove installed skills
  update      Update skills added from repositories

Flags:
  -h, --help   help for skills

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx skills COMMAND --help" for more information about a command.
```

## sbx stop --help
```
Stop one or more running sandboxes without removing them. Or — with --cloud — the cloud sandbox
ID (sbx_*) or name from "sbx --cloud ls".

Stopped sandboxes retain their state and can be restarted with "sbx run".

With --cloud, stop suspends each sandbox in place: its full state (memory +
disk) is preserved, the host is released, and the sandbox keeps its ID.
Restart it — same ID — by running its agent again ("sbx --cloud run <agent>")
and picking the stopped sandbox from the prompt. A detached run (--detached)
creates a new sandbox instead of restarting a stopped one.

Stop does not create a template and does not delete the sandbox. To capture
a durable, shareable template from a running sandbox instead, use
"sbx --cloud template save SANDBOX TAG" (which leaves the sandbox
running).

Usage:
  sbx stop SANDBOX [SANDBOX...]

Flags:
  -h, --help   help for stop

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx template --help
```
Manage sandbox templates.

Templates are saved snapshots of sandboxes that can be reused to create new
sandboxes with: sbx run -t TAG AGENT [WORKSPACE]

Cloud mode (--cloud) snapshots and loads typically produce multi-GB artifacts
and take several minutes. See https://docs.docker.com/ai/sandboxes/ for details.

Usage:
  sbx template COMMAND

Available Commands:
  inspect     Show full metadata for a single template
  load        Load an image from a tar file into the sandbox runtime
  ls          List template images
  rm          Remove a template image
  save        Save a snapshot of the sandbox as a template

Flags:
  -h, --help   help for template

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx template COMMAND --help" for more information about a command.
```

## sbx ttl --help
```
Inspect or extend a cloud sandbox's TTL.

With one argument, prints the current expiration and the maximum
remaining time before the sandbox's hard 24h-from-creation ceiling.

With two arguments — a duration prefixed with '+' followed by a sandbox
ID or name — extends the TTL by that amount, subject to the server-enforced
ceiling. The server cannot shorten an expiration, so DURATION must be
positive.

SANDBOX may be given by ID (sbx_*) or name, as shown by "sbx --cloud ls".

Cloud-only: local sandboxes are not TTL-managed.

Usage:
  sbx ttl [+DURATION] SANDBOX

Flags:
  -h, --help   help for ttl
      --json   Output as JSON

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx tui --help
```
Open the interactive TUI dashboard

Usage:
  sbx tui [flags]

Flags:
  -h, --help   help for tui

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx version --help
```
Show Docker Sandboxes version information

Usage:
  sbx version

Flags:
  -h, --help   help for version
      --json   Output in JSON format, including the server version and, when the backend reports them, the runtime component versions

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging
```

## sbx volume --help
```
Manage persistent volumes for cloud sandboxes.

Volumes provide persistent storage that survives across sandbox runs.
Data is saved as a snapshot when a sandbox exits, not continuously
synced. If multiple sandboxes mount the same volume concurrently, the
last sandbox to exit wins — its snapshot overwrites the others.

Volumes are a cloud-only feature; every subcommand requires --cloud.

Usage:
  sbx volume COMMAND

Available Commands:
  create      Create a new persistent volume
  inspect     Show details for a volume
  ls          List persistent volumes
  rm          Delete a persistent volume

Flags:
  -h, --help   help for volume

Global Flags:
      --cloud                  Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
      --cloud-api-url string   Cloud Sandboxes API base URL; only used with --cloud. Defaults to prod (https://api.sandboxes-cloud.docker.com). Set DOCKER_CLOUD_API_URL or pass this flag to override; a legacy value ending in /v1 is accepted. (default "https://api.sandboxes-cloud.docker.com")
  -D, --debug                  Enable debug logging

Use "sbx volume COMMAND --help" for more information about a command.
```
