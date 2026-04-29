#!/usr/bin/env python3
"""
<one-line summary of what this migration changes>.

PR: #<number> — <title>
Run after: <prerequisite, e.g. "lightdash_deploy.yml succeeds on main">
Status: pending  # flip to "applied YYYY-MM-DD" once it's run cleanly

This is a ONE-SHOT migration. Re-running may create duplicates or fail.
After running successfully, update Status above so future readers can
audit what landed when.

What this does:
  - <bullet list of operations>

Run:
  python3 lightdash/migrations/<this-file>.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402


def main():
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    # TODO: implement the migration. Examples:
    #
    #   # Delete an obsolete dashboard
    #   api("DELETE", f"/dashboards/<dashboard-uuid>", allow_404=True)
    #
    #   # Patch a saved chart's dimensions / column order
    #   chart = api("GET", f"/saved/<chart-uuid>")
    #   chart["metricQuery"]["dimensions"] = ["new_dim_1", "new_dim_2"]
    #   api("PATCH", f"/saved/<chart-uuid>", chart)
    raise NotImplementedError("fill in main()")


if __name__ == "__main__":
    main()
