#!/usr/bin/env bash
# PreToolUse (Bash) hook.
#
# Production dbt builds run through the dbt_run.yml GitHub Action. This hook
# refuses to run a mutating dbt command against --target prod from an
# interactive session, so a local run cannot overwrite production Gold
# tables. Exits immediately for any command that is not a mutating dbt verb.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$cmd" ] && exit 0

# Only inspect mutating dbt verbs (build / run / seed / snapshot / clone /
# run-operation). Anything else, including read-only dbt commands, passes.
printf '%s' "$cmd" \
  | grep -Eq '(^|[^[:alnum:]_-])dbt[[:space:]]+(build|run|seed|snapshot|clone|run-operation)([^[:alnum:]_-]|$)' \
  || exit 0

# Does it target prod? Covers --target prod, --target=prod and -t prod.
if printf '%s' "$cmd" \
  | grep -Eq -- '(--target[= ]|[[:space:]]-t[[:space:]])[[:space:]]*prod([^[:alnum:]_-]|$)'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Refusing to run dbt against --target prod from an interactive session. Production builds run through the dbt_run.yml GitHub Action; local work uses the dev target. If a manual prod run is genuinely needed, run it yourself outside Claude."
    }
  }'
  exit 0
fi
exit 0
