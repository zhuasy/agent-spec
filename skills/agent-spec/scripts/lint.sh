#!/usr/bin/env bash
# Run both linters on a spec. Usage: lint.sh SPEC.md [--glossary FILE] [--repo PATH] [--strict]
# spec_lint.py checks structure, lengths, requirement patterns and the glossary.
# Vale checks prose style. Exit code 1 when a check fails, 2 when Vale is missing.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 1 ]; then
  echo "usage: lint.sh SPEC.md [--glossary FILE] [--repo PATH] [--strict]" >&2
  exit 2
fi
spec="$1"
strict=0
for arg in "$@"; do [ "$arg" = "--strict" ] && strict=1; done

python3 "$here/spec_lint.py" "$@"
structure=$?

if ! command -v vale >/dev/null 2>&1; then
  echo "vale is not installed, so the prose style rules (G1, G3, G4) did not run." >&2
  echo "Install it from https://vale.sh/docs/install and run this script again." >&2
  exit 2
fi
out="$(vale --config "$here/../assets/vale/.vale.ini" --output line "$spec")"
style=$?
[ -n "$out" ] && echo "$out"
[ "$strict" = 1 ] && [ -n "$out" ] && style=1

[ "$structure" = 0 ] && [ "$style" = 0 ] && echo "spec passes" && exit 0
exit 1
