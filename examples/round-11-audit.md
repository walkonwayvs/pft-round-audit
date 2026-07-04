# Post Fiat Round Audit — Round 11

**Verdict: CONSISTENT**

- Generated (UTC): 2026-07-04T22:33:10Z
- Tool: pft-round-audit v1.0
- Scope: independent consistency audit from public artifacts only. Does not re-run scoring or assert score correctness.

## Artifact fingerprints (SHA-256)

- `scores`: `61fc1d878defb28d0ab25008e3a0a9c2e080fc314f42fea6ed36a5342d9af9e7`
- `unl`: `71b1cd87773dd58b9b8789d1be0383de76978fc7fa68168cdba8993b8deb2594`
- `evidence`: `2a800903ab3447a99333c95350551fededdf0bdb5dc1f14a372771ae87af05f1`
- `map`: `c45ad96399e8ae30f72a27bf0eaeed76f18ce362f1bbc4007335512837b05663`

## Checks

| Check | Result | Detail |
|---|---|---|
| C1_artifacts_present | PASS | all four artifacts present and valid JSON |
| C2_round_number | PASS | evidence round_number == 11 |
| C3_map_covers_scores | PASS | scores and map cover identical 44 validators |
| C4_unl_in_scores | PASS | all 20 UNL members present in scores |
| C5a_unl_size | PASS | UNL size == 20 |
| C5b_eligibility | PASS | all UNL members score >= 40 (eligibility cutoff) |
| C5c_churn_gap | PASS | no excluded validator beats the weakest UNL member (score 85) by the churn gap of 5; selection consistent with anti-churn rule |
| C6_no_duplicates | PASS | no duplicate score entries; UNL and alternates disjoint |
| C7_component_bounds | PASS | all scores and components within [0,100] |
| C8_evidence_keys_match | PASS | signing keys agree between evidence and map for all shared validators |
| C9_alternates_valid | PASS | all 21 alternates scored and within the churn gap of the UNL cut |

**11/11 checks passed.**

_Reproduce: run `pft_round_audit.py --round 11` against the same public artifacts to regenerate this receipt._
