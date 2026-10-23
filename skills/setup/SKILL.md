---
name: setup
description: Install or upgrade the agent-reach CLI that cn-reach uses, keep its own skill out of Claude Code, and check each channel
disable-model-invocation: true
---

Set up the cn-reach plugin. Before each step, tell the user in one sentence what it does. Step 2 changes the user's machine: get a clear yes first.

## 1. Check what is installed

Run `agent-reach version`:
- JSON with version 1.6 or later: go to step 3.
- A plain line such as `Agent Reach v1.5.0`: an old version; upgrade in step 2. Keys and settings carry over, and the 1.6 setup removes the old program.
- Command not found: install in step 2.

On Windows, also check where uv keeps its tools: if the user environment variable `UV_TOOL_DIR` is unset and `uv tool dir` prints a path under `AppData\Roaming`, an existing install may live in the Claude app's private storage (see step 2) and fail in the user's own terminal with `uv trampoline failed`. Treat that as an upgrade and go through step 2.

## 2. Install or upgrade (ask first)

Explain the steps below and wait for the user's agreement:
0. Windows only. The Claude desktop app is a packaged app: files it writes under `AppData` go to a private copy that the user's own terminal cannot see. Keep uv's tools and Python out of `AppData`:
   - If the user environment variables are unset, set them persistently: `UV_TOOL_DIR` = `%USERPROFILE%\.local\share\uv\tools` and `UV_PYTHON_INSTALL_DIR` = `%USERPROFILE%\.local\share\uv\python` (PowerShell: `[Environment]::SetEnvironmentVariable(name, value, 'User')`). Mention these two variables when asking for agreement.
   - If an earlier install sits in the private copy (`uv tool dir` without the variables prints a path under `AppData\Roaming`, and `uv tool list` there shows agent-reach), remove it first with `uv tool uninstall agent-reach`, still without the variables. Do this before installing: both installs share the launcher in `~/.local/bin`, so uninstalling later would delete the new launcher.
   - Claude does not see new user variables until it restarts, so from here on set both in the shell for every `uv` and `agent-reach` command in this setup (PowerShell `$env:NAME = ...`, bash `export NAME=...`).
1. If `uv --version` fails, install uv (Astral's installer for command-line tools; no admin rights needed):
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

   The installer puts `uv` in `~/.local/bin`. Until Claude restarts, that folder may not be on PATH: call `~/.local/bin/uv` by its full path.
2. `uv tool install --force https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip`
   (The PyPI package named `agent-reach` is a different project; install from this GitHub URL.)
3. Find the new program: `uv tool dir --bin` prints its folder; the program is `agent-reach.exe` there on Windows, `agent-reach` elsewhere. Run it by full path with `version` and confirm it prints JSON. On Windows, also confirm `uv tool dir` now prints the `UV_TOOL_DIR` path from item 0.
4. Run plain `agent-reach version` too. If it still prints the old plain line (an old install such as `~/.agent-reach-venv/Scripts` comes first in PATH, or the uv folder is not on PATH yet), use the full path from item 3 for every `agent-reach` command in steps 3 to 6, so the old version's interactive setup never runs. Then run `uv tool update-shell` and, in the final report, tell the user to restart Claude.

## 3. Run agent-reach setup

Run `agent-reach setup` and show `result.installation_report.markdown` to the user as is.

## 4. Keep agent-reach's own skill out of Claude Code

`agent-reach setup` and `update` place their own skill at `~/.claude/skills/agent-reach`, which would overlap with cn-reach. agent-reach leaves that path alone when something else already occupies it, so:
1. If `~/.claude/skills/agent-reach` is a symlink, or holds a `SKILL.md` whose frontmatter says `name: agent-reach`, remove that path (that path only).
2. Create the folder `~/.claude/skills/agent-reach/` again containing only a `README.txt` with: "Placeholder created by the cn-reach plugin so that agent-reach does not install its own skill for Claude Code. Delete this folder to undo." The folder must not contain a SKILL.md.
3. Leave `~/.agents/skills/agent-reach` and other agents' folders (such as Codex) unchanged.

## 5. Optional channels

Ask whether to add Xiaohongshu (`agent-reach add xiaohongshu`; needs a login, a secondary account is recommended) and Xueqiu (`agent-reach add xueqiu`). Add only what the user picks. For logins, the user runs `agent-reach login <channel>` and signs in in the window that opens.

## 6. Check

- `agent-reach doctor --text`
- The WeChat script sits next to this skill: `python "<this skill's base directory>/../cn-reach/scripts/wechat.py" search "人工智能" --limit 2` (`python3` on macOS / Linux)

## 7. Report

Give the user a short table: each channel, whether it works, and anything left for them to do (log in, add a key). Logins are run by the user in their own terminal: `agent-reach login <channel>`. On Windows, if step 2 set new environment variables, ask the user to restart Claude so later `agent-reach update` runs use the same location.
