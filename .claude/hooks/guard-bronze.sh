#!/usr/bin/env bash
# PreToolUse (Edit|Write) hook.
#
# Bronze is immutable: it is raw Airbyte output and only Airbyte writes
# there. dbt must never materialise a model into a BRONZE_* schema. The only
# file allowed under dbt/models/bronze/ is _sources.yml (the source
# declarations). This hook blocks any Edit/Write to another file in that
# directory.
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$file" ] && exit 0

case "$file" in
  */dbt/models/bronze/*)
    if [ "$(basename "$file")" != "_sources.yml" ]; then
      jq -n --arg f "$(basename "$file")" '{
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: ("Bronze is immutable. dbt/models/bronze/ holds only _sources.yml; it must not contain models. \($f) cannot be written here. If Bronze data is wrong, fix the Airbyte connection or re-sync rather than modelling around it.")
        }
      }'
      exit 0
    fi
    ;;
esac
exit 0
