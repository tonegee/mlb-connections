# MLB Connections

Connect MLB players through dated active-roster teammate links. The included 2024 dataset loads automatically when served over HTTP (including GitHub Pages). Opening `index.html` directly from Files does not support the fetch/worker flow; use `python -m http.server` for local play.

## Gameplay

- Practice has unlimited mistakes; Challenge allows five; Daily allows three.
- Easy pairs require two links, Medium three, and Hard four or more. Datasets without that distance fall back to another multi-link pair.
- Daily uses a deterministic medium pair per UTC date and dataset player IDs. Its versioned local progress cannot be restarted through the game controls.
- Hints name the club for a possible next link. A valid guess that shares a roster date with the target completes the final link automatically.
- MLB numeric player IDs load headshots from MLB's image service. Missing images and fictional IDs show initials.

## Data and performance

`mlb-connections-2024.json` contains 1,457 players and 143,820 daily observations (about 44 MB). The dataset remains unchanged to retain the original source citations. Initial transfer time depends on the connection; browser HTTP caching can reduce repeat downloads.

`dataset-worker.js` fetches, validates and indexes data outside the main thread. A per-club date sweep only compares overlapping records and retains the first dated evidence for each teammate pair. Pair selection uses breadth-first distance searches instead of all-pairs path enumeration. Path searches store predecessors instead of copying paths at each step.

Evidence establishes a shared date in the imported snapshots; the app cannot independently authenticate the historical accuracy of the upstream API. Unsampled dates are never inferred. Imports and fictional UI test data remain available. A load failure offers a retry or manual import.

## Verification

Run `node --test tests/game.test.cjs` (Node 18+). Tests cover inclusive date overlap, non-overlapping dates, self-link exclusion, every generated 2024 edge's source date, challenge completion, team hints and stable daily selection. The browser logic test uses DOM stubs; it does not verify visual layout or live headshot availability.
