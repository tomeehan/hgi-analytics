---
name: lightdash-change
description: >-
  Use when changing a Lightdash chart or dashboard. Trigger phrases: "edit
  a Lightdash chart", "change a dashboard", "update a chart description or
  tile", "add a Lightdash chart", "tweak a dashboard tile". Covers the
  develop / preview / PR workflow for the YAML-as-code dashboards in
  lightdash/charts/ and lightdash/dashboards/.
---

# Change a Lightdash chart or dashboard

Charts and dashboards are managed as YAML, one file per object, in
`lightdash/charts/<slug>.yml` and `lightdash/dashboards/<slug>.yml`. A
`git diff` on those files is the audit trail. Do not call the Lightdash
REST API directly for chart or dashboard CRUD.

## Workflow

1. Branch off `main`. Never work on `main` directly.
2. `lightdash download` to refresh the local YAML from production, so you
   start editing from live state.
3. Edit the YAML for the chart(s) or dashboard(s) you are changing.
4. `lightdash lint` to validate the YAML against Lightdash's JSON schema
   (no network).
5. Optional: `lightdash run-chart lightdash/charts/<slug>.yml` to confirm
   the chart's query still runs against the warehouse.
6. Create a preview project and push the YAML into it:

   ```sh
   lightdash start-preview --name "$(git branch --show-current)" \
     --project-dir dbt --profiles-dir dbt
   # take the preview project UUID from the printed preview URL, then:
   lightdash upload --force --validate --project <preview-uuid>
   ```

   Open the preview URL in the browser to see the change live on a
   throwaway project, with production untouched. Iterate by editing the
   YAML and re-running the `lightdash upload` command above.
7. Tear the preview down when finished:

   ```sh
   lightdash stop-preview --name "$(git branch --show-current)"
   ```

8. Commit only the changed `lightdash/**/*.yml` files. That diff is the
   review. Open a PR, never push to `main`.
9. On merge, the `lightdash_deploy.yml` workflow runs `lightdash deploy`
   (semantic layer) then `lightdash upload --force` (content). Verify the
   result via the Lightdash API once the workflow run is green.

## Caveats

- **SQL Runner charts are not covered** by content-as-code. If a dashboard
  has one, that tile stays UI-only.
- **`lightdash/migrations/` is frozen** legacy history. Never add to it and
  never re-run it.
- **Default to horizontal bar charts** (`flipAxes: true`) for category
  breakdowns. Use vertical bars only for time series.
- **Descriptions describe meaning, not plumbing.** A chart or dashboard
  description should explain what the metric means to a reader. It must not
  reference internal table names, model names, or source documents (e.g.
  PDF page numbers).
- `lightdash deploy` only refreshes the semantic layer (dbt metrics and
  dimensions). `lightdash upload` is what pushes chart and dashboard YAML.
