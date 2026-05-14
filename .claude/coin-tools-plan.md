# utxoWallet — coin-tools expansion: Consolidate, Split, Cointrack/untrack, QR receive, Distribute

> **Handoff note.** This plan was researched in the *webWallet* project conversation but the
> implementation belongs to the **utxoWallet** project. It is intended to be copied into
> `/Users/eurobuddha/Projects/utxoWallet/` (e.g. `.claude/coin-tools-plan.md`) plus a memory
> entry in the utxoWallet memory dir, so the utxoWallet agent can execute it. Everything the
> next agent needs is in this file — it is deliberately self-contained.

## Context

The user reviewed `my-coins-internal-0.4.7.mds.zip` (the "CoinManager" MiniDapp) to mine ideas
for **utxoWallet** (current shipping version **v1.0.29**, a hand-written single-file explicit-UTXO
wallet). Goal: add five features. Four are inspired by my-coins; the fifth (**Distribute**) is a
new idea from the user.

The five features:
1. **QR receive code** — add a QR to the existing Receive modal
2. **Cointrack / untrack** — track/untrack coins via the `cointrack` MDS command
3. **Consolidate** — explicit "merge my dust" via the `consolidate` MDS command
4. **Split** — split a coin/selection into N equal coins
5. **Distribute** — send a user-defined amount to every wallet address in the node, or to a pasted external address list

## Source-material findings (my-coins-internal-0.4.7)

- **It is a minified Vite/React + Tailwind production build.** `assets/index-3894721e.js` is
  1.19 MB minified; `assets/index-181d59ab.css` is 40 KB minified Tailwind. **No source is
  available — nothing can be copy-pasted.** All five features are clean reimplementations.
- **Confirmed real features** (from actual MDS command strings in the bundle, not keyword noise):
  `consolidate` (`se.cmd.consolidate({params:{tokenid, coinage, maxcoins}})`), `split`
  (a "split-form" with `splitType`/`splitAmount`/`splits[]`), `cointrack`
  (`se.cmd.cointrack({params:{coinid, enable}})`, both single and bulk-untrack loops),
  manual txn building (`txncreate` + `txninput` loop), `balance`, `coins`, `status`.
- **Disproved** (keyword counts were misleading): **no** `coinexport`/`coinimport`, **no**
  coin labels/tags (the `localStorage` hits were all theme/splash state, not coin annotation).
- **Style: nothing worth taking.** my-coins is Tailwind + Manrope + teal/purple/orange on a
  light-ish theme. utxoWallet is a deliberate lime-on-near-black terminal aesthetic with
  monospace amounts — the stronger, more distinctive identity. Importing my-coins' look would
  be a regression. At most its layout *patterns* are mild inspiration.

## utxoWallet architecture map (v1.0.29) — what the next agent must know

Single file: `/Users/eurobuddha/Projects/utxoWallet/index.html` (~4382 lines: CSS lines 8–1364,
HTML 1365–1532, JS 1534–4382). Plus `mds.js`, `favicon.png`, `dapp.conf`, `build.sh`.

**CSS design tokens** (`:root`, lines 12–37): `--bg #0a0a0f`, `--surface #151520`,
`--surface2 #1c1c2a`, `--surface3 #24242e`, `--border #2a2a3a`, `--accent #80e600`,
`--text #c8c8d4`, `--dim #7a7a8a`, `--heading #fff`, `--red #ff4466`, `--amber #f0c040`,
`--blue #6699ff`, `--mono` (monospace stack). Reuse these — do not introduce new colours.

**Reusable CSS classes** (already defined): `.modal-backdrop` / `.modal-backdrop.open`
(line 503/515), `.modal` (516), `.modal-title` (525), `.modal-actions` (533),
`.field` / `.field-label` / `.field-label .label` / `.field-label .action` / `.field input[type=text]`
/ `.field-note` (+`.ok/.info/.warn/.error` variants with ::before icons) (438–500),
`.btn` / `.btn.primary` / `.btn.ghost` / `.btn.small` / `.btn.danger` (383–432),
`.selection-bar` / `.sb-info` / `.sb-count` / `.sb-total` / `.sb-actions` (344–380),
`.setting-block` / `.setting-title` / `.setting-desc` / `.radio-row` (1202+),
`.posting-stages` / `.stage` (`.active`/`.done`) (602–627),
`.card` / `.tx-section` / `.tx-row` / `.tx-section-label` / `.toast-stack`.

**HTML structure** (1365–1532): `.nav` → `.wrap` → `.tabs` (4 buttons: `data-tab` =
`wallet`/`balances`/`history`/`settings`) → `<section id="tab-wallet|balances|history|settings">`.
Three modals already exist: `#sendModal`, `#confirmModal`, `#receiveModal`. `#toastStack` at end.
The wallet tab has `#selectionBar` (with `#sbCount`, `#sbTotal`, `#clearBtn`, `#sendBtn`) and
`#walletBody`.

**JS is one IIFE** (`(function(){ "use strict"; … })()`). Key pieces:

- `state` object (lines 1543–1575): `coins[]`, `groups` Map, `selected` Set (of coinids),
  `selectedTokenid`, `myWalletAddresses` Set, `myScriptAddresses` Set, `chainBlock`,
  `activeTab`, `pendingTxId`, `settings{defaultChangeMode,writeConfirmed,nodeLocked,…}`,
  `history[]`, `pendingApproval`, `resumeInFlight`. Const `UTXOWALLET_VERSION = "1.0.29"`.
- **MDS wrappers** (1604–1662): `mds(cmd)` → Promise; rejects `{stage:"pending"}` on a queued
  response (`isPendingResponse` detects both `{pending:true}` and `{status:false,error:"…pending…"}`).
  `sql(query)` → Promise resolving `res.rows`. **Every new feature must go through `mds()`/`sql()`
  and be pending-aware.**
- **BigInt math** (1664–1689): `bigAdd`, `bigSub`, `bigGt`, `bigLte`, `bigEq`, `isPositive`,
  `_splitDec`, `_scaleTo`, `_unscale`. Decimal-safe — use these for all amount math, never JS floats.
- **Validation** (1691–1721): `validateAddress`, `normalizeAmount`, `validateAmount`,
  `validateBurn`, `validateTxnId`. `AMOUNT_RE` const at 1602.
- **UI helpers**: `el(tag, attrs, …children)` (JSX-like creator; supports `{class,text,title,on:{}}`),
  `clearNode`, `copyToClipboard(text, btnEl)`, `toast(msg, kind)`, `truncMid`, `formatAmount`,
  `compactAmount`, `compactAmountSpan`, `setNote(id,msg,kind)`.
- **Coins**: `loadCoins()` (2335 — `coins relevant:true` → `state.coins`, then `rebuildGroups`),
  `loadBalance()` (2385 — `balance` → `TOKEN_DATA`/`TOKEN_NAMES`), `rebuildGroups()` (2407),
  `loadMyAddresses()` (2435 — runs `scripts`, fills `state.myWalletAddresses` /
  `state.myScriptAddresses`; **this is the source for Distribute's "node addresses"**),
  `refreshDefaultAddress()` (2456), `debouncedLoadCoins()` (2328).
- **Wallet render**: `renderWallet` (2465), `renderAddressCard` (2500), `renderUTXOGroup` (2540),
  `renderUTXORow(c, tokenid)` (2571 — this is where a per-row track/untrack control would go),
  `isConfirmed(coin)` (2563).
- **Selection** (2616–2667): `onToggleUTXO`, `onClearSelection`, `selectedCoins()`,
  `selectedTotal()`, `renderSelectionBar()`. One-token-per-selection is enforced
  (`state.selectedTokenid`).
- **Send flow**: `openSendModal` (3003), `closeSendModal` (3070), `resolveDefaultChangeAddr`
  (3073), `getNextDefaultChangeAddr` (3088 — always `getaddress`, NEVER `newaddress`),
  `addrRecognition` (3099), `validateSendInputs` (3106), `previewTx` (3205),
  `backToSend` (3285), `confirmSend` (3308).
- **`buildTransaction(preview, onStage)`** (3490) — THE staged txn builder. Stages:
  record → create (`txncreate`) → inputs (`txninput` loop) → outputs (`txnoutput` recipient,
  `txnoutput` change if positive) → sign (`signAndPost` = `txnsign … publickey:auto
  txnpostauto:true txndelete:true`). Pending-aware: a mid-chain `{stage:"pending"}` rejection
  stashes `state.pendingApproval` and is resumed by `resumePendingBuild()` on NEWBLOCK.
  Logs to the SQL `history` table throughout. `signAndPost` (3360), `findTxpowidByOutput`
  (3378), `extractRealTxnid` (3464), `withTimeout` (3446).
- **History** (2169 `ensureTable`, + `recordHistoryPosting`, `finalizeHistoryPosted`,
  `markHistoryStatus`, `loadHistory`, `renderHistory` 3942, `renderHistoryRow` 4021).
- **Settings**: `renderSettings` (4223), `renderSettingsPermBlock` (4234),
  `openReceiveModal` (4261), `closeReceiveModal` (4274).
- **`wire()`** (4279) — ALL event handlers are registered here. New buttons/modals get wired here.
- **`MDS.init`** (4336) — boot sequence (`ensureTable → probeWritePermission → probeNodeLock →
  refreshDefaultAddress → sweepStaleTxns → loadCoins → loadMyAddresses → rebuildGroups →
  renderWallet → renderSelectionBar → loadHistory`); NEWBALANCE → `debouncedLoadCoins`;
  NEWBLOCK → `loadCoins → resumePendingBuild → watchPendingConfirmations`.

**Conventions to respect**: WRITE-permission gating before any write (`state.settings.writeConfirmed`,
`probeWritePermission`); node-lock check (`probeNodeLock`) before signing; one-token-per-selection;
`getaddress` only, never `newaddress` (memory: re-sync loses non-default keys); all writes
pending-aware; SQL column names come back UPPERCASE.

## Feature 1 — QR receive code  (easy, isolated)

The Receive modal (`#receiveModal`, `openReceiveModal` at 4261) currently shows the default
address as text + copy button only.

- Add a QR render below the address row. To preserve utxoWallet's **single-file purity**
  (`build.sh` enumerates files explicitly — adding an asset means editing build.sh), **inline a
  minimal QR generator** into the `<script>` block rather than bundling `qrcode.min.js`. A ~3 KB
  pure-JS QR generator (e.g. the public-domain `qrcode-generator` core, or `nayuki` QR) inlined
  as a small IIFE-scoped helper is the cleanest fit.
- New helper `renderQRCode(targetEl, text)` drawing to a `<canvas>` (style it on `--surface`
  with `--text`/`--bg` modules so it matches the dark theme; QR needs sufficient quiet-zone
  contrast — use white modules on a light card or invert carefully and test scannability).
- Call it from `openReceiveModal` after appending the address row.
- No build.sh change, no new asset, no version-drift risk beyond the normal version bump.

## Feature 2 — Cointrack / untrack  (easy–medium, isolated)

MDS command: `cointrack enable:true|false coinid:0x…`. Note: `coins relevant:true` only returns
*tracked* coins, so untracking a coin removes it from the wallet view, and you cannot re-track a
coin you can't see (you must paste its coinid).

- **Bulk untrack**: when coins are selected, expose an "Untrack" action (see "Selection-bar UX"
  open question below). Handler loops `cointrack enable:false coinid:…` over `selectedCoins()`,
  pending-aware, then `onClearSelection()` + `loadCoins()`. Confirm via a toast (e.g.
  "Untrack N coins? They'll disappear from the wallet view.") — a lightweight `confirm()` or a
  small confirm modal.
- **Track a coin**: a new `setting-block` in the Settings tab with a coinid text input +
  "Track" button → `cointrack enable:true coinid:…` → `loadCoins()`. Validate the coinid
  format first (`/^0x[0-9a-fA-F]{1,}$/`).
- Both paths are write operations — gate on `state.settings.writeConfirmed`.

## Feature 3 — Consolidate  (medium, isolated from txn-building)

MDS command does the whole job in ONE call: `consolidate tokenid:<id> coinage:<n> maxcoins:<3-20>
maxsigs:<1-5> burn:<n> dryrun:true|false`. Requires ≥3 coins of that token. `dryrun:true`
simulates without posting. In READ mode the single command queues one pending action — handle
via the existing `mds()` pending path.

- **New `#consolidateModal`** (clone the `.modal` structure). Fields: token (read-only — set by
  launch context), `maxcoins` (input/stepper 3–20, default ~20), `coinage` (min confirmations,
  default 3), optional `burn` (Minima only). Two actions: **Dry run** (`consolidate … dryrun:true`,
  show the simulated input-count / output / burn in the modal) and **Consolidate**
  (`consolidate … dryrun:false`).
- **Launch point**: the Balances tab — `renderBalanceCard` (2902) already shows a per-token UTXO
  count. Add a "Consolidate" button on the card when count ≥ 3. Pre-fills the modal's token.
- After a real consolidate: `toast`, `loadCoins()`. Optionally log a `history` row (send-to-self)
  — simplest acceptable v1 is toast + coin-list refresh; a history row is a nice-to-have.

## Feature 4 — Split  (medium–hard) and Feature 5 — Distribute (hard)

Both are **multi-output transactions** built from the user's selected input coins. They should
**not** call the bare `send` command — that bypasses utxoWallet's careful staged/pending/resume/
history machinery. Instead:

### Shared: `buildMultiOutputTransaction(preview, onStage)`

Generalise `buildTransaction` (3490) into a multi-output builder. `preview.outputs` is an array
of `{address, amount}`; everything else (record → `txncreate` → `txninput` loop → **N×`txnoutput`**
→ change `txnoutput` if positive → `signAndPost`) stays identical, including the pending-rejection
stash into `state.pendingApproval` and the `history` logging. `resumePendingBuild` must be taught
to resume a multi-output context (store the `outputs[]` array in `pendingApproval.context`).
Keep `buildTransaction` as a thin wrapper (`outputs:[{address:recipient,amount}]`) or fold it in.

### Feature 4 — Split

A "split selected coins into N equal coins, sent to your own addresses" flow.
- **New `#splitModal`**: shows selected coins + total; field `N` (count, 2–~50); derived
  "each coin ≈ total/N"; optional burn. Change/remainder handling: if `total` isn't divisible by
  `N`, last output takes the remainder (or emit a change output) — use BigInt math.
- Outputs: N addresses from `getNextDefaultChangeAddr()` (rotate the 64 defaults) — or all to one
  default address; **decide** (rotating gives privacy + matches the existing change-mode ethos).
- Calls `buildMultiOutputTransaction`.

### Feature 5 — Distribute

"Send a user-defined amount to every wallet address in the node, or to a pasted external list."
- **New `#distributeModal`**: a source toggle — **(a) My node addresses** (use
  `state.myWalletAddresses`; see open question on scope) or **(b) External list** (a `<textarea>`,
  accept newline/comma/space-separated `Mx…`/`0x…`, validate each via `validateAddress`, dedupe).
  Field: amount (see open question on semantics). Optional burn. Live summary:
  "N addresses × amount = total + burn — vs selected total".
- Inputs = `selectedCoins()`. Outputs = one `{address, amount}` per target. Change = selected
  total − (N × amount) − burn.
- Calls `buildMultiOutputTransaction`.
- **Many-outputs caveat**: a node with many wallet addresses → many outputs in one TxPoW. There
  is a practical TxPoW-size limit. Warn (and/or batch into multiple txns) above a threshold
  (~50 outputs is a safe soft cap to start). Note this in the modal.

## Open design decisions — RESOLVE BEFORE CODING Split/Distribute

The user has not yet answered these (asked, deferred to the handoff). The utxoWallet agent should
confirm them with the user first:

1. **Distribute address scope** — "every address in the node" = `state.myWalletAddresses` only
   (recommended — sending to script/contract addresses can lock funds), or also
   `state.myScriptAddresses`?
2. **Distribute amount semantics** — fixed amount to EACH address (recommended; matches
   "a user-defined amount of coins to every address"), or a total split evenly across all?
3. **Selection-bar UX** — when coins are selected, how to surface Split / Distribute / Untrack
   alongside Send? Options: (a) extra small buttons in the selection bar (busy on 540 px mobile);
   (b) a "Tools ▾" popover next to Send (clean, one extra tap); (c) one unified action modal with
   a (Send│Split│Distribute) mode toggle (fewer modals, more conditional form JS). Untrack likely
   stays a separate small button regardless.
4. (Minor) Split — N outputs to N rotated default addresses, or all to one default address?

## Build / versioning (utxoWallet project rules — from memory)

- `build.sh` extracts `version` from `dapp.conf` AND greps `UTXOWALLET_VERSION = "…"` from
  `index.html`; **the build fails on drift**. Bump BOTH in lockstep.
- Bump the version on EVERY rebuild; **never overwrite an existing `utxoWallet_*.mds.zip`**.
- `dapp.conf` must be the literal first entry in the zip (build.sh handles this).
- Commit + tag `v<version>` + push on every version bump — the repo is the source of truth.
- The "About" line in Settings is driven by `UTXOWALLET_VERSION`.
- If QR ends up needing an asset after all (it shouldn't — inline it), `build.sh` line 30 must be
  edited to include it.

## Suggested sequencing

- **Phase A — QR receive**: smallest, fully isolated, no txn risk. Good warm-up.
- **Phase B — Cointrack/untrack**: isolated, no txn-building. Resolve open question #3 (selection
  bar) here since bulk-untrack needs a home.
- **Phase C — Consolidate**: one MDS command + a modal + Balances-tab button. Isolated from
  `buildTransaction`.
- **Phase D — `buildMultiOutputTransaction` + Split + Distribute**: the big one. Do the shared
  builder first, then Split (simpler), then Distribute. Resolve open questions #1, #2, #4 first.

Each phase = its own version bump, build, commit, tag, push.

## Verification

- Build with `./build.sh` (must pass the version-drift guard).
- Install the `.mds.zip` on a local Minima node via MiniHub; grant WRITE permission.
- **QR**: open Receive modal → QR renders, scans correctly with a phone camera, resolves to the
  address.
- **Cointrack**: untrack selected coins → they vanish from the wallet view; track a coinid in
  Settings → it reappears after `loadCoins`.
- **Consolidate**: on a token with ≥3 UTXOs → Dry run shows a sane simulation → real consolidate
  reduces the UTXO count for that token (verify in the wallet view after the next block).
- **Split**: select a coin → split into N → wallet shows N new ~equal coins at your addresses.
- **Distribute**: select inputs → distribute fixed amount to node addresses → each target address
  shows the amount; external-list mode → pasted addresses each receive it. Verify change returns
  correctly and the History row records it.
- Test **both WRITE and READ mode** for every write path — READ mode must queue a pending action
  and the resume-on-NEWBLOCK path must complete it (this is utxoWallet's trickiest invariant).
- Test on a **locked node** — sends/consolidates must fail gracefully with the lock toast.

## Files

- `/Users/eurobuddha/Projects/utxoWallet/index.html` — all five features land here (single file).
- `/Users/eurobuddha/Projects/utxoWallet/dapp.conf` — version bump.
- `/Users/eurobuddha/Projects/utxoWallet/build.sh` — only touch if QR needs an external asset
  (it shouldn't).
- This plan, once handed off, should live at
  `/Users/eurobuddha/Projects/utxoWallet/.claude/coin-tools-plan.md` plus a memory entry in
  `/Users/eurobuddha/.claude/projects/-Users-eurobuddha-Projects-utxoWallet/memory/`.
