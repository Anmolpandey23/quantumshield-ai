<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->

## Project rules

- All page data flows through `src/services/quantumshield.service.ts` (mock vs FastAPI switch via `VITE_USE_MOCK_DATA`); pages never import `src/data/mock` for data so the backend can be swapped in one place.
- Backend paths live only in `src/services/api/endpoints.ts`; types in `src/types/quantumshield.ts` are the API contract.
- Demo data must be deterministic (seeded RNG, fixed epoch, UTC formatting) to avoid SSR hydration mismatches.
- Simulation state is a single React context (`src/features/simulation`) mounted in `__root.tsx` so any page can trigger or display a run.
- Every surface showing sample values carries a `DemoBadge` or demo label; never present simulated results as real.
