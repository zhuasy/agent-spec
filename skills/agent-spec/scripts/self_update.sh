#!/usr/bin/env bash
# Update this skill from its source, at most once a day. Usage: self_update.sh [--force]
# Prints "updated" when files changed (read SKILL.md again), "current" when they did not,
# and "skipped: <reason>" when no check ran. Never fails the caller: the exit code is always 0.
# Set AGENT_SPEC_NO_UPDATE=1 to switch the check off.
main() {
  local here skill stamp root scope before after
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  skill="$(dirname "$here")"
  stamp="${XDG_CACHE_HOME:-$HOME/.cache}/agent-spec/last-update-check"

  [ "${AGENT_SPEC_NO_UPDATE:-0}" = 1 ] && { echo "skipped: AGENT_SPEC_NO_UPDATE is set"; return; }
  if [ "${1:-}" != "--force" ] && [ -n "$(find "$stamp" -mmin -1440 2>/dev/null)" ]; then
    echo "skipped: checked in the last 24 hours"; return
  fi
  [ -d "$skill/../../.git" ] && [ -f "$skill/../../README.md" ] && { echo "skipped: this is the source repository"; return; }
  command -v npx >/dev/null 2>&1 || { echo "skipped: npx is not installed"; return; }

  # A project install has skills-lock.json in a parent folder. A global install does not.
  root="$skill"; scope="-g"
  while [ "$root" != "/" ]; do
    root="$(dirname "$root")"
    [ -f "$root/skills-lock.json" ] && { scope="-p"; break; }
  done
  [ "$scope" = "-g" ] && root="$HOME"

  mkdir -p "$(dirname "$stamp")" && touch "$stamp"
  before="$(cd "$skill" && find . -type f ! -path '*/__pycache__/*' -exec cksum {} + 2>/dev/null | sort | cksum)"
  if ! (cd "$root" && timeout 120 npx --yes skills update agent-spec "$scope" -y >/dev/null 2>&1); then
    echo "skipped: the update command failed (no network, or the skill was not installed with \"npx skills add\")"; return
  fi
  after="$(cd "$skill" && find . -type f ! -path '*/__pycache__/*' -exec cksum {} + 2>/dev/null | sort | cksum)"
  [ "$before" = "$after" ] && echo "current" || echo "updated"
}
main "$@"
exit 0
