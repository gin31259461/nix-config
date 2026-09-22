# Shared task progress

This module gives the workstation's Bash and Python tools one Rich display.
The active task updates on one terminal line; its final result and elapsed time
remain in scrollback. Callers own task execution, subprocess I/O, errors, and
recovery. The module owns presentation only.

## Try it without changing workstation state

From the repository root, enter `nix develop`, then run this synthetic example:

```bash
PYTHONPATH="$PWD/lib/cli/progress" python - <<'PY'
import subprocess
import sys
import time
from progress import Progress

with Progress("Example") as progress:
    with progress.task("Check sample inputs", total=3) as task:
        for completed in range(1, 4):
            time.sleep(0.2)
            task.update(completed)
    with progress.task("Run a sample child") as task:
        with task.external_output():
            subprocess.run(
                [sys.executable, "-c", "print('Original child output')"],
                check=True,
            )
PY
```

The example leaves two completed task records and the child's original output.
Work without a known total displays a spinner. Counts describe actual completed
work, not elapsed-time estimates. Use static, non-sensitive task labels; never
pass command arguments, environment contents, credentials, or registration data.

## Python interface

Import `Progress` from `progress`. A `Progress` context closes its display on
exit; a `task` context records success or failure without suppressing the task's
exception. `task.update(completed, total=...)` reports measured progress and
`task.finish("skip")` records an explicit skip. Sequential and nested tasks use
the same display owner.

Use `task.external_output()` before any subprocess or local print that writes
directly to the terminal. The context clears and suspends the active row before
yielding, then resumes after the writer returns. Existing captured or suppressed
subprocess streams must retain that handling. In particular, a progress display
does not make sensitive command output suitable for logging.

## Bash and Nix composition

Import [default.nix](default.nix) with `{ inherit pkgs; }`. It provides the Rich
Python environment (`python`), module import directory (`pythonPath`), renderer
package (`renderer`), and a Bash preamble (`shell`). Concatenate `shell` before
the application's Bash source in `writeShellApplication`. Python applications
use `python` and set `PYTHONPATH` to `pythonPath` in their Nix-built entry point.

The Bash interface is:

```bash
progress_init "Example" 0  # Second argument is the verbose flag (0 or 1).
trap 'status=$?; progress_exit "$status"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
progress_start "Check sample inputs" 3
for completed in 1 2 3; do
  sleep 0.2
  progress_update "$completed"
done
progress_finish 'done'
```

`progress_suspend` and `progress_resume` hand the terminal to an external writer.
The suspend operation waits for the renderer to acknowledge the handoff before
the writer starts. `progress_finish` accepts `done`, `skip`, or `failed`.
`progress_exit` takes the saved numeric exit status and closes the renderer;
applications with existing cleanup must call it from their own cleanup handler.
The module does not replace application traps. Call `progress_close` before an
`exec` handoff and let the new process report its own result.

The Bash adapter uses dedicated control channels. It does not consume application
stdin, redirect child output, or send commands to the renderer. Display failures
must not replace the application's result or erase its diagnostics.

## Terminal behavior and tests

Progress writes to stderr. Non-terminal output, verbose mode, `TERM=dumb`, and
the presence of `NO_COLOR`, and nonempty `CI` select plain transition records. Native tools retain
their own output while the shared display is suspended. The display uses the
normal terminal scrollback, not an alternate screen.

Run the isolated renderer and bridge tests with:

```bash
nix build --no-link --show-trace --print-build-logs \
  .#checks.x86_64-linux.progress-ui
```

See the [operator runbook](../../../docs/deployment.md#progress-display) for how
the workstation commands present progress.
