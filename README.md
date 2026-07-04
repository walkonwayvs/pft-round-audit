# pft-round-audit

An independent, reproducible audit of a published [Post Fiat](https://postfiat.org)
validator-scoring round — built **only** from that round's public artifacts.

Every week Post Fiat selects its validator list (the UNL) and publishes the
evidence behind the decision: the scores, the inputs, and the resulting list.
The network's whole premise is that this selection is *auditable* rather than
opaque. But publishing evidence and having someone independently *check* it are
two different things. Until now, nobody has independently verified that each
round's published evidence is complete and internally consistent.

`pft-round-audit` is that check. Point it at a round, and it fetches the public
artifacts, verifies they agree with each other, and produces a deterministic
**audit receipt** anyone can reproduce.

## What it proves — and what it doesn't

**It proves** a published round is **complete and internally consistent, and that
it obeys Post Fiat's published selection rules**:
- all expected artifacts are present and valid,
- they agree with each other (the scored set, the map, and the evidence line up),
- the UNL is the documented size (20), every member meets the eligibility cutoff (40),
  and the selection obeys the published churn gap (5) — no excluded eligible validator
  beats the weakest UNL member by 5 or more,
- there are no missing, duplicate, or contradictory entries.

**It does not** re-run the LLM scoring pipeline or claim the individual scores are
"correct." Reproducing the scoring model from frozen inputs is the network's own,
heavier verification method. This tool verifies the *published rules were followed*
and the *artifacts are mutually consistent* — the layer that is checkable directly
from public data and currently has no independent check.

Because every finding is derived only from the public files, **anyone can re-run
this tool on the same round and get the same receipt.** That reproducibility is
the point.

## The checks

| Check | What it verifies |
|---|---|
| C1 artifacts present | all four public artifacts exist and are valid JSON |
| C2 round number | the evidence's `round_number` matches the round audited |
| C3 map covers scores | the scored set and the validator map cover the identical validators |
| C4 UNL in scores | every selected UNL validator was actually scored this round |
| C5a UNL size | the UNL contains exactly the documented maximum (20) |
| C5b eligibility | every UNL member meets the documented eligibility cutoff (score ≥ 40) |
| C5c churn gap | **core check** — no excluded, eligible validator beats the weakest UNL member by the documented churn gap (5) or more; i.e. the selection obeys the published anti-churn rule |
| C6 no duplicates | no duplicate score entries; UNL and alternates are disjoint |
| C7 component bounds | every overall and component score is within `[0, 100]` |
| C8 evidence/map keys | signing keys agree between the evidence and the map for shared validators |
| C9 alternates valid | alternates are all scored and none beat the UNL cut by the churn gap (which would require promotion) |

These rules are the ones Post Fiat publishes on the explorer's "How Scoring Works"
panel: **eligibility cutoff 40, max UNL size 20, churn gap 5.** The tool checks that
the published round obeys them and that its artifacts are mutually consistent.

The verdict is **CONSISTENT**, **CONSISTENT_WITH_WARNINGS**, or **INCONSISTENT**.
The tool exits non-zero on an inconsistent round, so it can gate CI or automation.

## Usage

```bash
# Audit a round straight from the public explorer:
python3 pft_round_audit.py --round 12

# Or audit local copies of the artifacts:
python3 pft_round_audit.py --round 12 --from-dir ./fixtures
```

It writes two files:
- `round-<N>-audit.md` — human-readable receipt,
- `round-<N>-audit.json` — machine-readable receipt (checks, verdict, artifact SHA-256s).

### Public artifacts it reads (per round N)

```
/api/scoring/rounds/N/outputs/validator_scores.json
/api/scoring/rounds/N/outputs/selected_unl.json
/api/scoring/rounds/N/inputs/validator_evidence.json
/api/scoring/rounds/N/inputs/validator_map.json
```

## Example

[`examples/round-12-audit.md`](examples/round-12-audit.md) is a real receipt for
round 12 — 9/9 checks passed, verdict CONSISTENT. The `fixtures/` directory holds
that round's actual public artifacts so you can reproduce the receipt offline:

```bash
python3 pft_round_audit.py --round 12 --from-dir ./fixtures
```

## Requirements

Python 3.8+. Standard library only — no dependencies.

## License

MIT — see [LICENSE](LICENSE).
