# Post Fiat Round Audit — Round 12

**Verdict: CONSISTENT**

- Generated (UTC): 2026-07-04T22:25:16Z
- Tool: pft-round-audit v1.0
- Scope: independent consistency audit from public artifacts only. Does not re-run scoring or assert score correctness.

## Artifact fingerprints (SHA-256)

- `scores`: `b5cb646601baadf0e0f3d4ee3a026b9e3f57d3261b2ab9085291d6afc7fd8206`
- `unl`: `40780f8e601df217bdffd7ffd73bd285afe5cfa05535009614201e8967953eec`
- `evidence`: `9eb906a5dadefd46f36da813a6b3a02ebb718f4b4e077e5ec0d1a081aaeef5cc`
- `map`: `06c6f797dfe949dc10ea473e31d37e0f59902af513c843192bd10e3fb14c4405`

## Checks

| Check | Result | Detail |
|---|---|---|
| C1_artifacts_present | PASS | all four artifacts present and valid JSON |
| C2_round_number | PASS | evidence round_number == 12 |
| C3_map_covers_scores | PASS | scores and map cover identical 45 validators |
| C4_unl_in_scores | PASS | all 20 UNL members present in scores |
| C5a_unl_size | PASS | UNL size == 20 |
| C5b_eligibility | PASS | all UNL members score >= 40 (eligibility cutoff) |
| C5c_churn_gap | PASS | no excluded validator beats the weakest UNL member (score 87) by the churn gap of 5; selection consistent with anti-churn rule |
| C6_no_duplicates | PASS | no duplicate score entries; UNL and alternates disjoint |
| C7_component_bounds | PASS | all scores and components within [0,100] |
| C8_evidence_keys_match | PASS | signing keys agree between evidence and map for all shared validators |
| C9_alternates_valid | PASS | all 23 alternates scored and within the churn gap of the UNL cut |

**11/11 checks passed.**

_Reproduce: run `pft_round_audit.py --round 12` against the same public artifacts to regenerate this receipt._
