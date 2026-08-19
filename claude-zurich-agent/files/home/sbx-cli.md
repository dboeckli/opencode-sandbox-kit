# sbx CLI Reference (offline)

Kompakte Offline-Referenz der **Docker Sandboxes CLI (`sbx`)** — generiert aus den authentischen
`--help`-Outputs der **v0.38.0**-Release-Binary (`docker/sbx-releases`). Includiert NICHT das
interaktive TUI; aktualisieren durch Neugenerierung aus der Binary (`sbx <cmd> --help`).
Detaillierte Hintergrunddoku (Kits, Policy, Proxy, Troubleshooting): `npx ctx7 docs /docker/docs <query>`
(nur teilweise abgedeckt — die CLI selbst ist NICHT in Context7). Kit-Grammatik v2:
`https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md`.

## sbx --help
```
Docker Sandboxes creates isolated sandbox environments for AI agents, powered by Docker.

Run without a command to launch interactive mode, or pass a command for CLI usage.

Usage:
  sbx
  sbx [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  cp          Copy files or directories between a sandbox and the host
  create      Create a sandbox for an agent
  daemon      Manage sandboxd daemon
  diagnose    Diagnose common issues with your sbx installation
  exec        Execute a command inside a sandbox
  help        Help about any command
  kit         (Experimental) Manage kit artifacts
  login       Sign in to Docker
  logout      Stop all running sandboxes and sign out of Docker
  ls          List sandboxes
  mcp         Manage MCP servers
  policy      Manage sandbox policies
  ports       Manage sandbox port publishing
  reset       Reset all sandboxes and clean up state
  rm          Remove one or more sandboxes
  run         Run an agent in a sandbox
  secret      Manage stored secrets
  setup       (Experimental) Detect host configuration and prepare Docker Sandboxes
  skills      (Experimental) Manage skills shared across sandboxes
  stop        Stop one or more sandboxes without removing them
  template    Manage sandbox templates
  tui         Open the interactive TUI dashboard
  version     Show Docker Sandboxes version information

Flags:
  -D, --debug   Enable debug logging
  -h, --help    help for sbx

Use "sbx [command] --help" for more information about a command.
```

## sbx completion --help
```
Generate the autocompletion script for sbx for the specified shell.
See each sub-command's help for details on how to use the generated script.

Usage:
  sbx completion [command]

Available Commands:
  bash        Generate the autocompletion script for bash
  fish        Generate the autocompletion script for fish
  powershell  Generate the autocompletion script for powershell
  zsh         Generate the autocompletion script for zsh

Flags:
  -h, --help   help for completion

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx completion [command] --help" for more information about a command.
```

## sbx cp --help
```
Either SRC or DST must be a sandbox path, written as SANDBOX:PATH.
The other must be a local path. Copying between two sandboxes is not supported.

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

Flags:
  -L, --follow-link   Follow symbolic links in the source path
  -h, --help          help for cp

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx create --help
```
Create a sandbox with access to a host workspace for an agent.

Use "sbx run --name SANDBOX" to attach to the agent after creation.

Usage:
  sbx create [flags] AGENT PATH [PATH...]
  sbx create [command]

Examples:
  # Create a sandbox for Claude in the current directory
  sbx create claude .

  # Create a sandbox with a custom name
  sbx create --name my-project claude /path/to/project

  # Create with additional read-only workspaces
  sbx create claude . /path/to/docs:ro

  # Run the agent on an in-container clone of the host repo, wired back via a git-daemon
  sbx create --clone claude .

Available Commands:
  claude         Create a sandbox for claude
  codex          Create a sandbox for codex
  copilot        Create a sandbox for copilot
  cursor         Create a sandbox for cursor
  docker-agent   Create a sandbox for docker-agent
  droid          Create a sandbox for droid
  gemini         Create a sandbox for gemini
  kiro           Create a sandbox for kiro
  opencode       Create a sandbox for opencode
  shell          Create a sandbox for shell

Flags:
      --clone                               Run the agent on a private in-container clone of the host Git repository (mounted read-only) instead of bind-mounting the workspace; the agent's commits are accessible via the sandbox-<name> git remote on the host
      --cpus int                            Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs)
      --deny-network sbx policy ls <NAME>   Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with sbx policy ls <NAME> / `sbx policy rm network --sandbox <NAME> --resource <HOST>`. Safe under centralized governance because a local deny can only narrow, never widen, egress.
  -h, --help                                help for create
      --kit strings                         (Experimental) Kit reference (directory, ZIP, or OCI). Can be specified multiple times
  -m, --memory string                       Memory limit in binary units (e.g., 1024m, 8g). Default: 50% of host memory, max 32 GiB
      --name string                         Name for the sandbox (default: <agent>-<workdir>, letters, numbers, hyphens, periods, plus signs and minus signs only)
      --profile string                      Governance profile to assign to the sandbox
  -p, --publish stringArray                 Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
  -q, --quiet                               Suppress verbose output
      --static-mcp strings                  MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time.
  -t, --template string                     Container image to use for the sandbox (default: agent-specific image)

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx create [command] --help" for more information about a command.
```

## sbx daemon --help
```
Manage sandboxd daemon

Usage:
  sbx daemon [command]

Available Commands:
  log-level   Inspect or change sandboxd's per-category log levels
  restart     Restart the sandboxd daemon
  start       Start the sandboxd daemon
  status      Check sandboxd daemon status
  stop        Stop the sandboxd daemon

Flags:
  -h, --help   help for daemon

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx daemon [command] --help" for more information about a command.
```

## sbx diagnose --help
```
Diagnose common issues with your sbx installation

Usage:
  sbx diagnose

Flags:
  -h, --help            help for diagnose
  -o, --output string   Output format: "json" or "github-issue"
      --upload          Upload diagnostics to Docker support

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx exec --help
```
Execute a command in a sandbox. If the sandbox is stopped, it is started first.

Flags match the behavior of "docker exec".

Usage:
  sbx exec [flags] SANDBOX COMMAND [ARG...]

Examples:
  # Open a shell inside a sandbox
  sbx exec -it my-sandbox bash

  # Run a command in the background
  sbx exec -d my-sandbox npm start

  # Run as root
  sbx exec -u root my-sandbox apt-get update

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
  -D, --debug   Enable debug logging
```

## sbx help --help
```
Help provides help for any command in the application.
Simply type sbx help [path to command] for full details.

Usage:
  sbx help [command] [flags]

Flags:
  -h, --help   help for help

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx kit --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Manage kit artifacts.

Kits are declarative YAML artifacts that extend sandbox agents with additional
credentials, network policies, environment variables, startup commands, and files.

Usage:
  sbx kit COMMAND
  sbx kit [command]

Available Commands:
  add         Add a kit to a sandbox
  inspect     Display details about a kit artifact
  pack        Package a directory as a kit artifact
  pull        Pull a kit artifact from an OCI registry
  push        Push a kit artifact to an OCI registry
  validate    Validate a kit artifact

Flags:
  -h, --help   help for kit

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx kit [command] --help" for more information about a command.
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
  -D, --debug   Enable debug logging
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
  -D, --debug   Enable debug logging
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
  -D, --debug   Enable debug logging
```

## sbx mcp --help
```
Register and manage MCP servers for use with sandbox sessions.

Usage:
  sbx mcp [command]

Available Commands:
  add         Register an MCP server
  auth        Authorize MCP servers
  inspect     Show MCP server details
  load        Load an already-registered MCP server into a running sandbox
  ls          List registered MCP servers
  rm          Remove a registered MCP server

Flags:
  -h, --help   help for mcp

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx mcp [command] --help" for more information about a command.
```

## sbx policy --help
```
Manage persistent access policies for sandboxes.

Policies contain rules that control what sandboxes can access. Local rules
can apply globally across all sandboxes or be scoped to one sandbox. Use
subcommands to allow, deny, list, or remove rules.

Usage:
  sbx policy COMMAND
  sbx policy [command]

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
  -D, --debug   Enable debug logging

Use "sbx policy [command] --help" for more information about a command.
```

## sbx ports --help
```
Manage sandbox port publishing.

List, publish, or unpublish ports for a running sandbox. Without --publish or
--unpublish flags, lists all published ports.

Port spec format: [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
If HOST_PORT is omitted, an ephemeral port is allocated automatically.
If HOST_IP is omitted, the port is bound on loopback, expanded based on
PROTOCOL and the sandbox's address families: tcp/udp binds both 127.0.0.1
and ::1 (or only 127.0.0.1 if the sandbox is IPv4-only); tcp4/udp4 binds
only 127.0.0.1; tcp6/udp6 binds only ::1. PROTOCOL defaults to tcp.
Supported protocols: tcp, tcp4, tcp6, udp, udp4, udp6.

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

Flags:
  -h, --help                    help for ports
      --json                    Output in JSON format (for port listing)
      --publish stringArray     Publish a port (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
      --unpublish stringArray   Unpublish a port (can be repeated): [HOST_IP:]HOST_PORT:SANDBOX_PORT[/PROTOCOL]

Global Flags:
  -D, --debug   Enable debug logging
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
  -D, --debug   Enable debug logging
```

## sbx rm --help
```
Remove one or more sandboxes and all associated resources.

Stops running sandboxes, removes their containers, cleans up any Git
worktrees, and deletes sandbox state. This action cannot be undone.

Removal requires confirmation; use --force to skip confirmation prompts
(for non-interactive scripts) and to delete a sandbox that is in use
(e.g. an open SSH connection). Use --all to remove every sandbox.

Usage:
  sbx rm [SANDBOX...] [flags]

Aliases:
  rm, remove, delete

Flags:
      --all     Remove all sandboxes
  -f, --force   Skip confirmation prompts and delete even if in use (e.g. an open SSH connection)
  -h, --help    help for rm

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx run --help
```
Run an agent in a sandbox, creating the sandbox if it does not already exist.

The first positional argument is the agent to run. To re-attach to an existing
sandbox by name, use --name; the agent positional is optional when the named
sandbox already exists and is read from its spec.

Pass agent arguments after the "--" separator. Additional workspaces can be
provided as extra arguments. Append ":ro" to mount them read-only.

To create a sandbox without attaching, use "sbx create" instead, or
pass --detached (-d) to print the sandbox ID and exit without opening an
interactive session.

Available agents: claude, codex, copilot, cursor, docker-agent, droid, gemini, kiro, opencode, shell

Usage:
  sbx run [flags] [AGENT] [PATH...] [-- AGENT_ARGS...]

Examples:
  # Create and run a sandbox with claude in current directory
  sbx run claude

  # Create and run with additional workspaces (read-only)
  sbx run claude . /path/to/docs:ro

  # Re-attach to an existing sandbox by name (agent read from its spec)
  sbx run --name existing-sandbox

  # Re-attach to an existing sandbox by name and verify the expected agent
  sbx run claude --name existing-sandbox

  # Run a sandbox with agent arguments
  sbx run claude -- --continue

Flags:
      --clone                               Run the agent on a private in-container clone of the host Git repository; must be set at sandbox creation time (no-op when re-attaching to an existing clone-mode sandbox)
      --cpus int                            Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs)
      --deny-network sbx policy ls <NAME>   Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with sbx policy ls <NAME> / `sbx policy rm network --sandbox <NAME> --resource <HOST>`. Safe under centralized governance because a local deny can only narrow, never widen, egress.
  -h, --help                                help for run
      --kit strings                         (Experimental) Kit reference (directory, ZIP, or OCI). Can be specified multiple times
  -m, --memory string                       Memory limit in binary units (e.g., 1024m, 8g). Default: 50% of host memory, max 32 GiB
      --name string                         Name for the sandbox (default: <agent>-<workdir>)
      --profile string                      Governance profile to assign to the sandbox
  -p, --publish stringArray                 Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]. Applied when the sandbox is created; ignored when re-attaching (use "sbx ports")
      --static-mcp strings                  MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time and cannot be changed when re-attaching to an existing sandbox.
  -t, --template string                     Container image to use for the sandbox (default: agent-specific image)

Global Flags:
  -D, --debug   Enable debug logging
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
  sbx secret [command]

Available Commands:
  import      Import secrets detected in host environment variables
  ls          List stored secrets
  rm          Remove a secret
  set         Create or update a secret
  set-custom  (Experimental) Create or update a custom secret

Flags:
  -h, --help   help for secret

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx secret [command] --help" for more information about a command.
```

## sbx setup --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Detect what is already configured on your host and prepare Docker Sandboxes.

Agent secrets are detected from the built-in agent kit specs and the
env vars set on this host, and accepted secrets are imported into the global
secrets store (the same store as "sbx secret set").

Usage:
  sbx setup
  sbx setup [command]

Available Commands:
  ssh         Set up SSH client config for the sandbox endpoint

Flags:
  -h, --help   help for setup

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx setup [command] --help" for more information about a command.
```

## sbx skills --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Manage the persistent agent skills store shared across sandboxes.

Copy skills from supported agent directories on the host into the store with:
  sbx skills import

Sandboxes with skills sharing enabled mount the store read-write. Use
--no-share-skills when creating a sandbox to opt out.

Usage:
  sbx skills [command]

Available Commands:
  import      Import skills from supported agent directories

Flags:
  -h, --help   help for skills

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx skills [command] --help" for more information about a command.
```

## sbx stop --help
```
Stop one or more running sandboxes without removing them.

Stopped sandboxes retain their state and can be restarted with "sbx run".

Usage:
  sbx stop SANDBOX [SANDBOX...]

Flags:
  -h, --help   help for stop

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx template --help
```
Manage sandbox templates.

Templates are saved snapshots of sandboxes that can be reused to create new
sandboxes with: sbx run -t TAG AGENT [WORKSPACE]

Usage:
  sbx template COMMAND
  sbx template [command]

Available Commands:
  load        Load an image from a tar file into the sandbox runtime
  ls          List template images
  rm          Remove a template image
  save        Save a snapshot of the sandbox as a template

Flags:
  -h, --help   help for template

Global Flags:
  -D, --debug   Enable debug logging

Use "sbx template [command] --help" for more information about a command.
```

## sbx tui --help
```
Open the interactive TUI dashboard

Usage:
  sbx tui [flags]

Flags:
  -h, --help   help for tui

Global Flags:
  -D, --debug   Enable debug logging
```

## sbx version --help
```
Show Docker Sandboxes version information

Usage:
  sbx version

Flags:
  -h, --help   help for version

Global Flags:
  -D, --debug   Enable debug logging
```
