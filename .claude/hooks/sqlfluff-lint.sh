#!/usr/bin/env bash
# PostToolUse (Edit|Write) hook.
#
# Lints an edited dbt SQL model with sqlfluff and reports any findings back
# to the model as advisory context. It never blocks the edit. It no-ops
# silently when the file is not a dbt model, or when sqlfluff is not
# installed (for example a fresh checkout before bin/setup has run).
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)
[ -z "$file" ] && exit 0

# Only dbt SQL models.
case "$file" in
  */dbt/*.sql) ;;
  *) exit 0 ;;
esac

# Project root is the parent of the dbt/ directory in the path.
project_root="${file%%/dbt/*}"
[ -f "$project_root/dbt/dbt_project.yml" ] || exit 0

# Prefer the project virtualenv, fall back to PATH. No-op if neither has it.
if [ -x "$project_root/.venv/bin/sqlfluff" ]; then
  sqlfluff_bin="$project_root/.venv/bin/sqlfluff"
elif command -v sqlfluff >/dev/null 2>&1; then
  sqlfluff_bin="sqlfluff"
else
  exit 0
fi

out=$(cd "$project_root/dbt" && "$sqlfluff_bin" lint "$file" 2>&1)
[ $? -eq 0 ] && exit 0

jq -n --arg out "$out" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("sqlfluff flagged style issues in the dbt model just edited. Review and fix them, or run `sqlfluff fix` on the file. Findings:\n" + $out)
  }
}'
exit 0
