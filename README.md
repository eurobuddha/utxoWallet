# utxoWallet

A Minima MiniDapp wallet that lets you **explicitly pick which UTXOs** to spend.
Every wallet address is listed with its individual coins underneath; you tick the
boxes for the coins you want, and the dapp builds the transaction from exactly
those inputs.

Styled to match Brain Wallet / BIP39 (lime `#80e600` on dark `#0a0a0f`).

## Build

```bash
./build.sh
```

Produces `utxoWallet_<version>.mds.zip`. The script verifies `dapp.conf` is the
first entry in the archive (MDS installs silently fail otherwise).

## Install

```
mds action:install file:utxoWallet_1.0.0.mds.zip trust:write
```

Or via MiniHub at `https://127.0.0.1:9003` — install, then **grant WRITE
permission**. utxoWallet requires WRITE; without it the boot-time probe will
detect READ-only and gate the Send button (a hard block, not a soft warning).

## Safety model

- **Only uses your 64 seed-derived default addresses.** Change addresses come
  from `getaddress` (which cycles the defaults). Never calls `newaddress` — a
  `newaddress` keypair lives outside the default set and is silently lost on a
  seed re-sync.
- Strict 3-step posting: `txnsign` → `txnbasics` → `txncheck` → `txnpost`.
  Never `txnpost auto:true` (silent Script-FAIL trap).
- `txncheck` confirms `valid.basic && valid.scripts` before any tx is broadcast.
- `coinAmt()` enforces human-readable amounts for token sends
  (`coin.tokenamount`), never raw Minima-scale amounts — prevents the token-burn
  bug previously seen on `Limit/feedback_minima_tx.md:60-64`.
- Pre-INSERT audit row before the tx broadcasts — if the dapp dies mid-flight,
  the watcher reconciles on the next launch.
- Stale-txn sweeper on boot only touches IDs matching `^uw_…$`.
- All MiniNumber math uses native `BigInt` with shared-scale normalization
  (44-decimal precision).
- All DOM writes go through `textContent`. No `innerHTML`, no `eval`, no CDN.

## Files

| File         | Purpose                                                   |
|--------------|-----------------------------------------------------------|
| `dapp.conf`  | Name / version / icon — MUST be first entry in the zip    |
| `index.html` | Entire UI + JS, single file, no external libs             |
| `mds.js`     | Copied verbatim from sibling brain-lint-dapp              |
| `favicon.png`| 32×32 lime coin glyph                                     |
| `build.sh`   | Reproducible build with explicit zip ordering + verify    |

## Test plan

1. `./build.sh`
2. Install via MiniHub, leave permission as **READ**.
3. Open utxoWallet → Settings tab shows ❌ WRITE not granted; Send button
   disabled.
4. Grant WRITE in MiniHub → click Re-test → ✅. Send button enables.
5. Wallet view shows every relevant address with its UTXOs nested. Unconfirmed
   coins are visible but with disabled checkboxes.
6. Tick a Minima coin then click a token coin → refusal toast. Untick all →
   refusal lifts.
7. Send a tiny amount (0.01) to a different default address. Confirm modal
   shows inputs, outputs, change. After post: History row appears as `posted`;
   on the next NEWBLOCK the watcher flips it to `confirmed`.
8. Kill the dapp mid-build → relaunch → sweeper logs released input coins.
9. Address fuzz: `Mx1`, `0x123`, `; rm -rf`, empty → all rejected. Amount
   fuzz: `+1`, `1e5`, `NaN`, `-1`, `> total` → all rejected.
