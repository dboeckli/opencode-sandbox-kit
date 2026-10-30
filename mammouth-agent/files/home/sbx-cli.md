# sbx CLI Reference (offline)

Kompakte Offline-Referenz der **Docker Sandboxes CLI (`sbx`)** — generiert aus den authentischen
`--help`-Outputs der **v0.50.1**-Release-Binary (`docker/sbx-releases`). Includiert NICHT das
interaktive TUI; aktualisieren durch Neugenerierung aus der Binary (`sbx <cmd> --help`).
Detaillierte Hintergrunddoku (Kits, Policy, Proxy, Troubleshooting): `npx ctx7 docs /docker/docs <query>`
(deckt Commands/Flags + Manuels ab, indexiert aber den Docs-`main`-Branch statt des Pins;
/docker/sbx-releases liefert nur Installation/Releases. Die exakten `--help`-Flags der gepinnten
Version liefert ausschliesslich diese Offline-Referenz). Kit-Grammatik v2:
`https://github.com/docker/sbx-kits-contrib/blob/main/spec/SPEC-v2.md`.

## sbx --help
```
Description:
  Docker Sandboxes creates isolated sandbox environments for AI agents, powered by Docker.

  Run without a command to launch interactive mode, or pass a command for CLI usage.

Usage:
  sbx COMMAND

Sandbox Commands:
  attach      Attach to a cloud sandbox, starting it first if it is stopped
  cp          Copy files or directories between a sandbox and the host
  create      Create a sandbox for an agent
  exec        Execute a command inside a sandbox
  ls          List sandboxes
  move        Move a sandbox between local and cloud
  ports       Manage sandbox port publishing
  prune       Remove all stopped sandboxes
  rm          Remove one or more sandboxes
  run         Run an agent in a sandbox
  stop        Stop one or more sandboxes without removing them
  ttl         Show or extend a cloud sandbox's TTL

Management Commands:
  daemon      Manage sandboxd daemon
  diagnose    Diagnose common issues with your sbx installation
  mcp         Manage MCP servers
  policy      Manage sandbox policies
  reset       Reset all sandboxes and clean up state
  secret      Manage stored secrets
  settings    Manage Docker Sandboxes settings
  template    Manage sandbox templates
  tui         Open the interactive TUI dashboard
  volume      Manage persistent volumes (cloud-only)

Experimental Commands:
  env         (Experimental) Manage sandboxes declaratively from an sbxenv.yaml file
  kit         (Experimental) Manage kit artifacts
  setup       (Experimental) Detect host configuration and prepare Docker Sandboxes
  skills      (Experimental) Manage skills available in sandboxes

Other Commands:
  completion  Generate the autocompletion script for the specified shell
  help        Help about any command
  login       Sign in to Docker
  logout      Stop running local sandboxes and sign out of Docker
  version     Show Docker Sandboxes version information

Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
  -h, --help    help for sbx

Use "sbx COMMAND --help" for more information about a command.
```

## sbx attach --help
```
Description:
  Attach an interactive terminal session to a cloud sandbox.

  SANDBOX is the cloud sandbox ID (sbx_*) or name from "sbx --cloud ls".

  Opens a PTY-backed exec session against the sandbox's agent process. The
  sandbox must already exist; a stopped one is started first. Use
  `sbx --cloud run` to create a sandbox and attach in one step.

  Only supported with --cloud. See https://docs.docker.com/ai/sandboxes/ for the cloud sandbox model.

Usage:
  sbx attach SANDBOX [flags]

Examples:
  # Attach to a sandbox by ID or name
  sbx --cloud attach sbx_abc123
  sbx --cloud attach claude/my-sandbox

Flags:
      --detach-keys string   Override the detach gesture that leaves the session running (Docker-style, e.g. "ctrl-\", "ctrl-x,ctrl-d"). Default: Ctrl-\. Use this when the default collides with an agent's keymap (cloud only).
  -h, --help                 help for attach

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx cp --help
```
Description:
  Either SRC or DST must be a sandbox path, written as SANDBOX:PATH.
  The other must be a local path. Copying between two sandboxes is not supported. Or — with --cloud — the cloud sandbox
  ID (sbx_*) or name from "sbx --cloud ls". Cloud transfers go through the Docker
  Sandboxes Cloud file API instead of the local sandboxd.

  When copying a directory, the directory itself is placed at the destination.
  If the destination path does not exist it is created; if it already exists
  as a directory, the source is placed inside it.

  When a local path is inside a sandbox workspace, sbx cp refuses symbolic
  links that lead out of the workspace, even with --follow-link, including
  when the workspace is reached through a symbolic link or junction to it.

Usage:
  sbx cp SRC DST [flags]

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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx create --help
```
Description:
  Create a sandbox with access to a host workspace for an agent.

  The first positional argument may be a built-in agent name or a sandbox kit
  reference. Sandbox kit references may be local directories, ZIP files, git
  repositories, or OCI references. Relative local references must be explicit
  paths such as ./my-kit or ../my-kit.zip. A kit.shortcuts.<agent> setting
  (sbx settings set kit.shortcuts.claude sbx/claude:latest) makes that agent name
  resolve to the configured kit reference instead for local sandboxes; cloud
  sandboxes ignore it.

  Omit the path to create a sandbox without a workspace bind mount: the agent
  then works in the container's own filesystem instead of on your files.

  Use "sbx run --name SANDBOX" to attach to the agent after creation.

  Available agents: claude, codex, copilot, cursor, devin, docker-agent, droid, gemini, kiro, opencode, shell

  With --cloud:
  Create a cloud sandbox for an agent.

  Cloud sandboxes have no host workspace, so no path follows the agent. Sizing
  comes from --cpus and --memory and must land on a billable shape; without them
  a cloud sandbox gets 2 CPUs and 4 GiB. A template named with -t / --template
  must already exist in the cloud registry.

  Cloud sandboxes use cloud network policies. Host network and HTTP policies
  do not apply. Set cloud account defaults with
  "sbx --cloud policy init <allow-all|balanced|deny-all>".

  Use "sbx --cloud run <agent> --name SANDBOX" to attach to the agent after
  creation: cloud needs the agent, since a name alone is not a unique handle.

Usage:
  sbx create AGENT|SANDBOX_KIT [PATH...] [flags]
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

  # Create a cloud sandbox for claude
  sbx --cloud create claude

  # Create a named cloud sandbox with a mixin baked in
  sbx --cloud create --name my-project claude --kit ./my-mixin/

  # Create from a template that already exists in the cloud registry
  sbx --cloud create -t TEMPLATE

Available Commands:
  claude         Create a sandbox for claude
  codex          Create a sandbox for codex
  cursor         Create a sandbox for cursor
  devin          Create a sandbox for devin
  docker-agent   Create a sandbox for docker-agent
  gemini         Create a sandbox for gemini
  opencode       Create a sandbox for opencode
  shell          Create a sandbox for shell

Flags:
      --allow-network strings       Network pattern to allow for cloud sandbox egress (cloud only; can be specified multiple times)
      --clone                       Run the agent on a private in-container clone of the host Git repository (mounted read-only) instead of bind-mounting the workspace; the agent's commits are accessible via the sandbox-<name> git remote on the host
      --cpus int                    Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs, at most 16 on Linux arm64)
      --deny-network strings        Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with 'sbx policy ls <NAME>' or 'sbx policy rm network --sandbox <NAME> --resource <HOST>'. Safe under centralized governance because a local deny can only narrow, never widen, egress.
  -e, --env stringArray             Set an environment variable in the sandbox (can be repeated): KEY=VALUE, or a bare KEY to take the value from the current environment
      --env-file stringArray        Read environment variables from a file (can be repeated). --env wins over any file; a later file wins over an earlier one
  -h, --help                        help for create
      --image-ref string            OCI image reference for inline-mode cloud create (mutually exclusive with --template; requires --cpus and --memory)
      --kit strings                 (Experimental) Additional kit reference (must be a mixin; directory, ZIP, git, or OCI). Can be specified multiple times
      --kit-arg stringArray         (Experimental) Value for an argument the kit declares, as name=value for every kit or kit.name=value for one (can be repeated)
      --kit-args-file stringArray   (Experimental) File of name=value kit arguments, one per line (can be repeated); --kit-arg overrides
  -m, --memory string               Memory limit in binary units (e.g., 512m, 8g). Minimum: 512 MiB. Default: 50% of host memory, clamped to 512 MiB–32 GiB. Maximum: max(75% of host memory, 512 MiB)
      --mount stringArray           Bind a host directory to a kit host-mount@1 path (can be repeated): HOST:SANDBOX_PATH. Can only be used when creating a new sandbox.
      --name string                 Name for the sandbox (defaults to <agent>-<workdir>; at least two characters, starting with a letter or number, containing only letters, numbers, hyphens and periods (periods are rejected with --cloud); 'default' is reserved)
      --no-progress                 Suppress progress output
      --on-timeout string           What happens when --ttl lapses: 'stop' stops the sandbox in place so it can be started again later, 'restart' keeps it running by stopping and immediately starting it, or 'delete' removes it. Omit the flag and the server stops the sandbox when it can be started again later, and deletes it otherwise. With 'restart' a supplied --ttl must be at least 1h (cloud only).
      --platform string             Target platform: linux/amd64 or linux/arm64 (cloud only). With --image-ref, omitting it lets the server resolve the platform from the image and the CLI sends the local CPU as a hint for multi-platform images. With --template, omitting it inherits the template platform. With a sandbox kit, the kit's template is built for this platform and cached apart from other platforms; omitting it keeps the server's choice.
      --profile string              Governance profile to assign to the sandbox
  -p, --publish stringArray         Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]
      --pull string                 Image pull policy (always|missing|never; default: never for saved local snapshots, missing for v3 kit compositions, otherwise always)
      --skills string               Shared skills store mode for the agent's skills directory (e.g. ~/.claude/skills): off, readonly (store linked in read-only, directory stays writable), or readwrite (store mounted over it, writes are shared). Default: readonly, or the configured skills.defaultMode setting.
      --static-mcp strings          MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time. Local sandboxes take names registered with 'sbx mcp add'. Cloud sandboxes resolve names on the cloud MCP gateway.
  -t, --template string             Container image to use for the sandbox (default: agent-specific image)
      --ttl duration                Cloud sandbox time-to-live before it times out (e.g. 30m, 2h, 1h30m; units are case-insensitive; cloud only; default: server-side)
  -v, --volume stringArray          (Experimental) Attach an existing persistent volume, NAME:MOUNTPATH (cloud only, experimental; repeatable)

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx create COMMAND --help" for more information about a command.
```

## sbx exec --help
```
Description:
  Execute a command in a sandbox. If the sandbox is stopped, it is started first. Or — with --cloud — the cloud sandbox
  ID (sbx_*) or name from "sbx --cloud ls".

  Flags match the behavior of "docker exec", except detached exec (-d/--detach)
  is not supported. Some flags (-d, --user, --privileged)
  are not supported with --cloud and are rejected rather than silently ignored.
  --detach-keys applies only to an interactive (-i/-t) cloud exec.

  Exit status is that of the command. sbx exits 125 if it could not run the command,
  for example because the sandbox does not exist. A missing command exits 127,
  unless a cloud backend reports it as an error rather than a status, which exits 125.

Usage:
  sbx exec [flags] SANDBOX COMMAND [ARG...]

Examples:
  # Open a shell inside a sandbox
  sbx exec -it my-sandbox bash

  # Run as root
  sbx exec -u root my-sandbox apt-get update

  # Cloud: run a command in a cloud sandbox by ID or name
  sbx --cloud exec -it sbx_abc123 bash
  sbx --cloud exec -it claude/my-sandbox bash

Flags:
  -d, --detach                 Detached mode (not supported)
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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx ls --help
```
Description:
  List all sandboxes with their agent, status, published ports, and workspace.

Usage:
  sbx ls [flags]

Aliases:
  ls, list

Examples:
  sbx ls

  # Names only, for scripting
  sbx ls -q

  # Machine-readable output
  sbx ls --format json

Flags:
      --format string   Output format: table, json or yaml
  -h, --help            help for ls
      --json            Output in JSON format
  -q, --quiet           Only display sandbox names

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx move --help
```
Description:
  Move a sandbox between the local host and Docker's hosted Sandboxes service.

  Move captures the sandbox's filesystem as a container image and starts a new
  sandbox from it on the destination. Running processes and in-memory state do
  not travel. The destination sandbox gets a new ID; name it with --name.

  Neither direction deletes the source. Moving to cloud stops the local
  sandbox; restart it with 'sbx run --name <name>'. Moving to local asks the
  cloud source to stop; a refused or unconfirmed stop warns without failing
  the move, and the stop may still be finishing when the move returns.
  'sbx --cloud ls' shows it. A cloud sandbox with no agent is left running.
  A stopped cloud source keeps its ID and state: 'sbx --cloud run <id>'
  resumes it, 'sbx --cloud rm <id>' deletes it.

  A failed or cancelled move restores what it can. It restarts a local source
  that was running and removes the transfer templates it created. The restart
  re-runs the entrypoint; processes you started by hand are not revived. If a
  cleanup step fails, the output names what is left and the command that
  recovers it.

  What does not travel:
    - The workspace bind mount and other host mounts. Files moved to local
      stay inside the sandbox at the image's working directory; copy them out
      with 'sbx cp'.
    - Secrets managed by sbx. The destination picks its own secrets, so
      you may need to sign in again. Credentials saved in copied files
      still travel.
    - Volumes and environment variables attached to a cloud sandbox, when
      moving to local. A local sandbox's environment is part of its image
      and travels to the cloud.
    - Network rules you added locally. The sandbox's kit network rules do
      travel: moving to cloud applies them, as 'sbx create --cloud' does. If
      the kit can't be resolved, move warns and the account's cloud policy
      applies. Moving to local starts with the host's default policy. Active
      local L7 (HTTP) rules prompt before a move to cloud; --force skips the
      prompt but keeps the warning.
    - Cloud URLs and host port bindings. Moving to cloud republishes TCP
      ports under new cloud URLs; a port the cloud refuses is skipped with a
      warning. Moving to local saves the published TCP ports and binds them
      on loopback while the sandbox runs. Host ports can change on restart;
      'sbx ports SANDBOX' shows them. A cloud port published with an
      explicit host binding stops a move to local.

  Sizing and disk:
    - Moving to cloud rounds recorded CPU and memory limits up to a cloud
      shape. Missing limits use cloud defaults with a warning. Limits above
      the largest shape stop the move before anything is captured. Moving to
      local uses local defaults.
    - Moving to local stages downloaded layers in the host's temporary
      directory. Reusing local layers can take up to 32 GiB in addition to
      the local runtime's image storage. If reuse fails, the layers are
      downloaded. If staging runs out of space, the move falls back to the
      export stream.

  The cloud sandbox a move creates expires. The default is the server's TTL,
  typically 1h: stopped in place on expiry when the account and sandbox
  support it, deleted otherwise. Choose with --ttl and --on-timeout;
  '--on-timeout restart' keeps the destination running instead of expiring.
  Extend later with 'sbx --cloud ttl'.

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
  -f, --force               Skip the move confirmation prompt
  -h, --help                help for move
      --name string         Name for the destination sandbox (default: 'moved-' + the source name; a cloud destination always adds a short unique suffix, a local one only when that name is already taken)
      --on-timeout string   What happens to the destination cloud sandbox when its TTL lapses: 'stop' stops it in place so it can be started again later, 'restart' keeps it running by stopping and immediately starting it, or 'delete' removes it. Not every sandbox supports 'stop', and an explicit request the server refuses fails the move after the source has been stopped and uploaded, so the sandbox is restored but the transfer is spent. With 'restart' a supplied --ttl must be at least 1h. Default: stop when the sandbox supports it, else the server default (delete). Only with --to cloud
      --to string           Destination of the move: 'local' (cloud to local) or 'cloud' (local to cloud)
      --ttl duration        Time-to-live for the destination cloud sandbox (15s to 24h, e.g. 30m, 2h; only with --to cloud; default: server-side)

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx ports --help
```
Description:
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

  With --cloud:
  Manage the exposed ports of a cloud sandbox.

  List, publish, or unpublish ports on a cloud sandbox given by ID (sbx_*) or
  name. Without --publish or --unpublish flags, lists the exposed ports.

  A port is the sandbox port number alone or with a /tcp suffix; UDP and host
  bindings are refused. The cloud control plane assigns a publicly reachable URL
  for each exposed port.

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
  sbx --cloud ports sbx_abc123 --publish 8080

  # Remove an exposed port from a cloud sandbox
  sbx --cloud ports sbx_abc123 --unpublish 8080

Flags:
      --format string           Output format: table, json or yaml
  -h, --help                    help for ports
      --json                    Output in JSON format
      --publish stringArray     Publish a port (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL] (local) or SANDBOX_PORT[/tcp] (cloud)
      --unpublish stringArray   Unpublish a port (can be repeated): [HOST_IP:]HOST_PORT:SANDBOX_PORT[/PROTOCOL] (local) or SANDBOX_PORT[/tcp] (cloud)

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx prune --help
```
Description:
  Remove all stopped sandboxes and their associated resources.

  Only stopped sandboxes are candidates — a running sandbox is never removed,
  which makes this safe to run habitually. Stop a sandbox first with
  "sbx stop" if you want it pruned. To remove a specific sandbox regardless of
  state, use "sbx rm SANDBOX".

  Use --filter until=TIMESTAMP to narrow the set to sandboxes that stopped before
  TIMESTAMP. The value can be an RFC 3339 timestamp, Unix timestamp, or Go duration
  relative to now (e.g. until=168h keeps anything stopped within the last week).
  A sandbox whose stop time the daemon cannot report is left alone, since how long
  it has been stopped cannot be established.

  Use --dry-run to list what would be removed without removing anything, and
  --format json or --format yaml with it for machine-readable output.

  Pruning requires confirmation; use --force to skip the confirmation prompt
  (for non-interactive scripts) and to remove a sandbox that is in use (e.g. an
  open SSH connection). This action cannot be undone.

  Secrets scoped to each successfully pruned sandbox are also deleted.

  Local-only: cloud sandboxes expire via their TTL.

Usage:
  sbx prune [flags]

Examples:
  # Show what would be removed
  sbx prune --dry-run

  # Remove without asking
  sbx prune --force

  # Only sandboxes stopped before a point in time
  sbx prune --filter until=2026-01-01T00:00:00Z

Flags:
      --dry-run              List the sandboxes that would be removed without removing them
      --filter stringArray   Filter candidates (supported: until=TIMESTAMP — stopped before TIMESTAMP)
  -f, --force                Skip confirmation prompts and remove even if in use (e.g. an open SSH connection)
      --format string        Output format: table, json or yaml
  -h, --help                 help for prune
      --json                 Output in JSON format

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx rm --help
```
Description:
  Remove one or more sandboxes. Or — with --cloud — the cloud sandbox
  ID (sbx_*) or name from "sbx --cloud ls".

  For local sandboxes, stops them, removes their containers, cleans up any Git
  worktrees, deletes sandbox state, and deletes secrets scoped to each removed
  sandbox. Host-mount directories and persistent volume@1 storage created with
  retention support are kept; creating the same sandbox name with the same kit
  reattaches its persistent volumes. This action cannot be undone. With --cloud, deletes
  the sandbox in Docker Sandboxes Cloud. This action cannot be undone. Once the
  server accepts the request, rm waits up to 60 seconds per sandbox for the
  deletion. A removal still completing after that exits 0. Verify it later with
  "sbx --cloud ls".

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

Examples:
  sbx rm my-sandbox

  # Remove several at once
  sbx rm one two

  # Remove every sandbox without asking
  sbx rm --all --force

Flags:
      --all             Remove all sandboxes
  -f, --force           Skip confirmation prompts and delete even if in use (e.g. an open SSH connection)
      --format string   Output format: table, json or yaml
  -h, --help            help for rm
      --json            Output in JSON format

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx run --help
```
Description:
  Run an agent in a sandbox, creating the sandbox if it does not already exist.

  The first positional argument identifies the agent to run. It may be a built-in
  agent name or a sandbox kit reference. Sandbox kit references may be local
  directories, ZIP files, git repositories, or OCI references. Relative local
  references must be explicit paths such as ./my-kit or ../my-kit.zip; bare values
  retain their agent or sandbox-name meaning. A kit.shortcuts.<agent> setting (sbx
  settings set kit.shortcuts.claude sbx/claude:latest) makes that agent name
  resolve to the configured kit reference instead for local sandboxes; cloud
  sandboxes ignore it. To re-attach to an existing sandbox
  by name, use --name; the agent positional is optional when the named sandbox
  already exists and is read from its spec.

  Pass agent arguments after the "--" separator. Additional workspaces can be
  provided as extra arguments. Append ":ro" to mount them read-only; a read-only
  argument may name a single file, which holds that one path out of reach inside a
  workspace the sandbox can otherwise write.

  Omit the path to mount the current directory. Pass a path to mount a different
  workspace.

  To create a sandbox without attaching, use "sbx create" instead, or
  pass --detach (-d) to print the sandbox ID and exit without opening an
  interactive session.

  Available agents: claude, codex, copilot, cursor, devin, docker-agent, droid, gemini, kiro, opencode, shell

  With --cloud:
  Run an agent in a cloud sandbox, creating the sandbox if it does not already exist.

  The first positional argument identifies the agent to run: a built-in agent
  name or a sandbox kit reference (a local directory, ZIP file, git repository,
  or OCI reference). Relative local references must be explicit paths such as
  ./my-kit or ../my-kit.zip. Cloud sandboxes have no host workspace, so no path
  follows the agent. Pass agent arguments after the "--" separator.

  Running an agent that has existing sandboxes, running or stopped, prompts you
  to pick one to reuse or to create a new one. Pass --new to skip the prompt and
  always create a fresh sandbox. --name NAME reuses and restarts the sandbox of
  that name when it exists and creates it otherwise. A sandbox kit launch always
  creates fresh, as does a launch that bakes a mixin with build content.
  --detach skips the prompt: with --name it restarts that sandbox when it
  exists, otherwise it creates a new one. A non-interactive run without
  --detach is refused, so scripts pass --detach (e.g.
  sbx --cloud run -d claude && sbx --cloud exec ...).

  Sizing comes from --cpus and --memory and must land on a billable shape; without
  them a cloud sandbox gets 2 CPUs and 4 GiB. A template named with -t / --template
  must already exist in the cloud registry; the CLI does not upload it. See
  https://docs.docker.com/ai/sandboxes/ for the cloud sandbox model.

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

  # Run claude in a new cloud sandbox
  sbx --cloud run claude

  # Create a cloud sandbox non-interactively and print its ID
  sbx --cloud run --detach claude

  # Reuse the cloud sandbox of that name, creating it when it does not exist
  sbx --cloud run --name my-project claude

  # Run with agent arguments
  sbx --cloud run claude -- --continue

Flags:
      --allow-network strings       Network pattern to allow for cloud sandbox egress (cloud only; can be specified multiple times)
      --clone                       Run the agent on a private in-container clone of the host Git repository; must be set at sandbox creation time (no-op when re-attaching to an existing clone-mode sandbox)
      --cpus int                    Number of CPUs to allocate to the sandbox (0 = auto: all host CPUs, at most 16 on Linux arm64)
      --deny-network strings        Add a per-sandbox network deny rule at creation time. Can be specified multiple times. The rule applies only to the new sandbox and can be listed or removed later with 'sbx policy ls <NAME>' or 'sbx policy rm network --sandbox <NAME> --resource <HOST>'. Safe under centralized governance because a local deny can only narrow, never widen, egress.
  -d, --detach                      Start the sandbox and print its ID without opening an agent session
      --detach-keys string          Override the detach gesture that leaves the session running (Docker-style, e.g. "ctrl-\", "ctrl-x,ctrl-d"). Default: Ctrl-\. Use this when the default collides with an agent's keymap (cloud only).
  -e, --env stringArray             Set an environment variable in the sandbox (can be repeated): KEY=VALUE, or a bare KEY to take the value from the current environment. Applies to the agent session, so it takes effect on a re-attach too; also baked into the sandbox when this run creates it
      --env-file stringArray        Read environment variables from a file (can be repeated). --env wins over any file; a later file wins over an earlier one. Applies to the agent session, so it takes effect on a re-attach too; also baked into the sandbox when this run creates it
  -h, --help                        help for run
      --image-ref string            OCI image reference for inline-mode cloud create (mutually exclusive with --template; requires --cpus and --memory)
      --kit strings                 (Experimental) Additional kit reference (must be a mixin; directory, ZIP, git, or OCI). Can be specified multiple times
      --kit-arg stringArray         (Experimental) Value for an argument the kit declares, as name=value for every kit or kit.name=value for one (can be repeated)
      --kit-args-file stringArray   (Experimental) File of name=value kit arguments, one per line (can be repeated); --kit-arg overrides
  -m, --memory string               Memory limit in binary units (e.g., 512m, 8g). Minimum: 512 MiB. Default: 50% of host memory, clamped to 512 MiB–32 GiB. Maximum: max(75% of host memory, 512 MiB)
      --mount stringArray           Bind a host directory to a kit host-mount@1 path (can be repeated): HOST:SANDBOX_PATH. Can only be used when creating a new sandbox.
      --name string                 Name for the sandbox (default: <agent>-<workdir>)
      --new                         Always create a new cloud sandbox instead of prompting to reuse an existing one (cloud only)
      --on-timeout string           What happens when --ttl lapses: 'stop' stops the sandbox in place so it can be started again later, 'restart' keeps it running by stopping and immediately starting it, or 'delete' removes it. Omit the flag and the server stops the sandbox when it can be started again later, and deletes it otherwise. With 'restart' a supplied --ttl must be at least 1h (cloud only).
      --platform string             Target platform: linux/amd64 or linux/arm64 (cloud only). With --image-ref, omitting it lets the server resolve the platform from the image and the CLI sends the local CPU as a hint for multi-platform images. With --template, omitting it inherits the template platform. With a sandbox kit, the kit's template is built for this platform and cached apart from other platforms; omitting it keeps the server's choice.
      --profile string              Governance profile to assign to the sandbox
  -p, --publish stringArray         Publish a sandbox port to the host (can be repeated): [[HOST_IP:]HOST_PORT:]SANDBOX_PORT[/PROTOCOL]. Applied when the sandbox is created; ignored when re-attaching (use "sbx ports")
      --pull string                 Image pull policy (always|missing|never; default: never for saved local snapshots, missing for v3 kit compositions, otherwise always)
      --rm                          Remove the sandbox after the agent session exits
      --skills string               Shared skills store mode for the agent's skills directory (e.g. ~/.claude/skills): off, readonly (store linked in read-only, directory stays writable), or readwrite (store mounted over it, writes are shared). Default: readonly, or the configured skills.defaultMode setting. Can only be used when creating a new sandbox.
      --static-mcp strings          MCP server names that form the sandbox's fixed (static) MCP set. Accepts a comma-separated list (--static-mcp notion,atlassian), repeated flags (--static-mcp notion --static-mcp atlassian), or a mix; all forms accumulate into the same set. The set is chosen once at creation time and cannot be changed when re-attaching to an existing sandbox. Local sandboxes take names registered with 'sbx mcp add'. Cloud sandboxes resolve names on the cloud MCP gateway.
  -t, --template string             Container image to use for the sandbox (default: agent-specific image)
      --ttl duration                Cloud sandbox time-to-live before it times out (e.g. 30m, 2h, 1h30m; units are case-insensitive; cloud only; default: server-side)
  -v, --volume stringArray          (Experimental) Attach an existing persistent volume, NAME:MOUNTPATH (cloud only, experimental; repeatable)

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx stop --help
```
Description:
  Stop one or more running sandboxes without removing them. Or — with --cloud — the cloud sandbox
  ID (sbx_*) or name from "sbx --cloud ls".

  Stopped sandboxes retain their state and can be restarted with "sbx run".

  With --cloud, stop suspends each sandbox in place: its full state (memory +
  disk) is preserved, the host is released, and the sandbox keeps its ID. Stop
  returns once the request is accepted. Watch the sandbox reach the stopped
  state with "sbx --cloud ls".
  Restart it — same ID — with "sbx --cloud attach SANDBOX", with
  "sbx --cloud run AGENT --name NAME" (also non-interactively with --detach),
  or by running its agent again and picking it from the prompt.

  Stop does not create a template and does not delete the sandbox. To capture
  a durable, shareable template from a running sandbox instead, use
  "sbx --cloud template save SANDBOX TAG" (which leaves the sandbox
  running).

Usage:
  sbx stop SANDBOX... [flags]

Examples:
  sbx stop my-sandbox

  # Stop several at once
  sbx stop one two

Flags:
      --format string   Output format: table, json or yaml
  -h, --help            help for stop
      --json            Output in JSON format

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx ttl --help
```
Description:
  Inspect or extend a cloud sandbox's TTL.

  With one argument, prints the current expiration and the maximum
  remaining time before the sandbox's hard 24h-from-creation ceiling.

  With two arguments — a duration prefixed with '+' followed by a sandbox
  ID or name — extends the TTL by that amount, subject to the server-enforced
  ceiling. The server cannot shorten an expiration, so DURATION must be
  positive. Units are Go's duration units (h, m, s, ms, us, ns), in either
  case (+2h, +2H, +1h30m).

  SANDBOX may be given by ID (sbx_*) or name, as shown by "sbx --cloud ls".

  Cloud-only: local sandboxes are not TTL-managed.

Usage:
  sbx ttl [+DURATION] SANDBOX [flags]

Examples:
  # Show the remaining TTL
  sbx --cloud ttl my-sandbox

  # Extend it by two hours
  sbx --cloud ttl +2h my-sandbox

Flags:
      --format string   Output format: table, json or yaml
  -h, --help            help for ttl
      --json            Output in JSON format

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx daemon --help
```
Description:
  Manage sandboxd daemon

Usage:
  sbx daemon COMMAND

Available Commands:
  log-level   Show or change sandboxd's per-category log levels
  restart     Restart the sandboxd daemon
  start       Start the sandboxd daemon
  status      Show sandboxd daemon status
  stop        Stop the sandboxd daemon

Flags:
  -h, --help   help for daemon

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx daemon COMMAND --help" for more information about a command.
```

## sbx diagnose --help
```
Description:
  Diagnose common issues with your sbx installation

Usage:
  sbx diagnose [flags]

Examples:
  sbx diagnose

  # Print the report as JSON
  sbx diagnose --format json

  # Upload the report to Docker support
  sbx diagnose --upload

Flags:
      --format string   Output format: table, json, yaml or github-issue
  -h, --help            help for diagnose
      --json            Output in JSON format
      --upload          Upload diagnostics to Docker support

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx mcp --help
```
Description:
  Register and manage MCP servers for use with sandbox sessions.

Usage:
  sbx mcp COMMAND

Available Commands:
  add         Register an MCP server
  auth        Authorize MCP servers
  inspect     Show MCP server details
  load        Load an already-registered MCP server into a sandbox
  ls          List MCP servers
  rm          Remove a registered MCP server
  unload      Unload an MCP server from a running sandbox

Flags:
  -h, --help   help for mcp

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx mcp COMMAND --help" for more information about a command.
```

## sbx policy --help
```
Description:
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
  inspect     Show policy or rule details
  log         Show sandbox policy logs
  ls          List sandbox policies
  profile     Manage policy profiles
  refresh     Force an immediate policy refresh
  reset       Reset policies to defaults
  rm          Remove a policy rule

Flags:
  -h, --help   help for policy

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx policy COMMAND --help" for more information about a command.
```

## sbx reset --help
```
Description:
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

Examples:
  sbx reset

  # Skip the confirmation prompt and keep stored secrets
  sbx reset --force --preserve-secrets

Flags:
  -f, --force              Skip confirmation prompt
  -h, --help               help for reset
      --preserve-secrets   Keep stored secrets

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx secret --help
```
Description:
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

Aliases:
  secret, secrets

Available Commands:
  import      Import secrets detected in host environment variables
  ls          List stored secrets
  rm          Remove a secret
  set         Create or update a secret
  set-custom  (Experimental) Create or update a custom secret

Flags:
  -h, --help   help for secret

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx secret COMMAND --help" for more information about a command.
```

## sbx settings --help
```
Description:
  View and manage settings for Docker Sandboxes.

  Settings can come from defaults, environment variables, or user overrides.
  These commands use the local daemon to read evaluated values and manage
  overrides, starting it if necessary.

  Most changes take effect within about five seconds. Some require a daemon
  restart.

Usage:
  sbx settings COMMAND

Available Commands:
  get         Get the value of a setting
  ls          List settings
  set         Set a setting override
  unset       Remove a setting override

Flags:
  -h, --help   help for settings

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx settings COMMAND --help" for more information about a command.
```

## sbx template --help
```
Description:
  Manage sandbox templates.

  Templates are saved snapshots of sandboxes that can be reused to create new
  sandboxes with: sbx run --pull never -t TAG AGENT [WORKSPACE]

  With --cloud:
  Manage cloud sandbox templates.

  Reuse a saved template with: sbx --cloud run --template TEMPLATE

  Cloud snapshots and loads typically produce multi-GB artifacts and take
  several minutes. See https://docs.docker.com/ai/sandboxes/ for details.

Usage:
  sbx template COMMAND

Available Commands:
  inspect     Show template details
  load        Load an image from a tar file into the sandbox runtime
  ls          List template images
  rm          Remove a template image
  save        Save a snapshot of the sandbox as a template

Flags:
  -h, --help   help for template

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx template COMMAND --help" for more information about a command.
```

## sbx tui --help
```
Description:
  Open the interactive TUI dashboard

Usage:
  sbx tui [flags]

Examples:
  sbx tui

Flags:
  -h, --help   help for tui

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx volume --help
```
Description:
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
  inspect     Show volume details
  ls          List persistent volumes
  rm          Remove a persistent volume

Flags:
  -h, --help   help for volume

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx volume COMMAND --help" for more information about a command.
```

## sbx env --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Description:
  Manage a sandbox declared in an sbxenv.yaml file. The file selects the agent,
  kits, workspace mounts, environment variables, secrets, and credential bindings.

  Use create to provision the sandbox, run to start or join its agent session,
  exec to run a command, and rm to remove it and its provisioned secrets.
  Use plan to preview changes. Changes require approval; --force skips the prompt.

  Lifecycle commands, command-based secrets, and command-backed MCP servers execute
  on the host with your permissions. Keep secret helpers and their dependencies
  outside writable sandbox mounts, and use absolute helper paths.

  MCP command approval persists across sandbox and daemon restarts. Use
  --skip-host-commands to skip lifecycle commands and disable owned host MCP
  commands until a later "sbx env run" without the flag. If initialize creates
  a missing MCP executable or changes its resolved path, a second approval is
  required before registration or sandbox creation.

  The environment file is mounted read-only by default when shared with the
  sandbox. Set sandboxOptions.writableEnvFiles only when you trust the agent
  to change what future invocations run on the host.

  With --cloud, manage a cloud sandbox from the same file. Host workspace mounts,
  host port bindings, MCP definitions, registry credentials, and unsnapshotted
  dynamic secret sources are unsupported. Clone the project inside the sandbox instead.

  Secrets and bindings are provisioned at creation; changes require recreating
  the sandbox. Removal deletes secrets provisioned by this environment; bindings
  are retained unless --prune-bindings is passed. Use the same cloud target,
  identity, and ordered files for subsequent commands.

  For file syntax and workflows, see:
  https://docs.docker.com/ai/sandboxes/configuration/environment-files/

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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx env COMMAND --help" for more information about a command.
```

## sbx kit --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Description:
  Manage kit artifacts.

  Kits are declarative YAML artifacts that define sandbox agents or extend them
  with additional credentials, network policies, environment variables, startup
  commands, and files.

Usage:
  sbx kit COMMAND

Available Commands:
  add         Add a mixin to a sandbox
  builder     Manage the kit builder sandbox
  inspect     Show kit artifact details
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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx kit COMMAND --help" for more information about a command.
```

## sbx setup --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Description:
  Detect what is already configured on your host and prepare Docker Sandboxes.

  Agent secrets are detected from the built-in agent kit specs and the
  env vars set on this host, and accepted secrets are imported into the global
  secrets store (the same store as "sbx secret set"). Setup can enable SSH-agent
  forwarding using each client's SSH_AUTH_SOCK, or the native Windows OpenSSH
  agent pipe when that variable is unset. A fixed endpoint can also be configured.

Usage:
  sbx setup [COMMAND]

Available Commands:
  ssh         Set up SSH client config for the sandbox endpoint

Flags:
  -h, --help   help for setup

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx setup COMMAND --help" for more information about a command.
```

## sbx skills --help
```
EXPERIMENTAL: this command may change or be removed in future releases.

Description:
  Manage skills available to agents in Docker Sandboxes.

  Skills are shared across sandboxes by default: the store's entries are linked
  into the agent's skills directory read-only, which stays writable so kits can
  install skills beside them. Linking happens at container start, so editing an
  existing skill is live through the link, while adding a store entry reaches a
  running sandbox only on its next start. Removing one takes effect immediately:
  the link in a running sandbox stops resolving at once, and the next start is
  what clears the stale link away. Use --skills=off when creating a sandbox to
  opt out, or --skills=readwrite to mount the store over that directory so the
  sandbox's own writes are shared.

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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx skills COMMAND --help" for more information about a command.
```

## sbx completion --help
```
Description:
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
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging

Use "sbx completion COMMAND --help" for more information about a command.
```

## sbx help --help
```
Description:
  Help provides help for any command in the application.
  Simply type sbx help [path to command] for full details.

Usage:
  sbx help [COMMAND]

Flags:
  -h, --help   help for help

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx login --help
```
Description:
  Sign in to Docker

Usage:
  sbx login [flags]

Examples:
  sbx login

  # Non-interactive sign-in, for CI
  echo "$DOCKER_PAT" | sbx login --username me --password-stdin

Flags:
  -h, --help              help for login
      --password-stdin    Read password or access token from stdin
      --username string   Docker username for non-interactive login

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx logout --help
```
Description:
  Stop running local sandboxes and sign out of Docker

Usage:
  sbx logout [flags]

Examples:
  sbx logout

  # Skip the confirmation prompt
  sbx logout --force

Flags:
  -f, --force   Skip confirmation prompt
  -h, --help    help for logout

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```

## sbx version --help
```
Description:
  Show Docker Sandboxes version information

Usage:
  sbx version [flags]

Examples:
  sbx version

  # Include daemon and build details
  sbx version --debug

Flags:
      --format string   Output format: table, json or yaml
  -h, --help            help for version
      --json            Output in JSON format

Global Flags:
      --cloud   Dispatch to Docker Cloud Sandboxes API instead of local sandboxd (supported by a growing set of verbs — run 'sbx --cloud --help' for the current list)
  -D, --debug   Enable debug logging
```
