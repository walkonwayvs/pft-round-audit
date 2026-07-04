# Post Fiat Round Audit — Round 10

**Verdict: CONSISTENT**

- Generated (UTC): 2026-07-04T22:33:09Z
- Tool: pft-round-audit v1.0
- Scope: independent consistency audit from public artifacts only. Does not re-run scoring or assert score correctness.

## Artifact fingerprints (SHA-256)

- `scores`: `8612ef7a3106038be3a26f610d549d9bbb4b4c773d5b7a37b2b8e6b0b90bc35e`
- `unl`: `ed46c4b18a461aab7f6ca74a95ede3efce79166086a020d9da4d7a46ddd2eada`
- `evidence`: `29223a4ea6f7d524224669891d853914f7c5fee0ae50b32af0325e2446a29fc2`
- `map`: `dbf81b0953426aa317a0c48c5a5e3b5a48a8d1ca94f64b33cb7b99a6c318a5a9`

## Checks

| Check | Result | Detail |
|---|---|---|
| C1_artifacts_present | PASS | all four artifacts present and valid JSON |
| C2_round_number | PASS | evidence round_number == 10 |
| C3_map_covers_scores | PASS | scores and map cover identical 49 validators |
| C4_unl_in_scores | PASS | all 20 UNL members present in scores |
| C5a_unl_size | PASS | UNL size == 20 |
| C5b_eligibility | PASS | all UNL members score >= 40 (eligibility cutoff) |
| C5c_churn_gap | PASS | no excluded validator beats the weakest UNL member (score 86) by the churn gap of 5; selection consistent with anti-churn rule |
| C6_no_duplicates | PASS | no duplicate score entries; UNL and alternates disjoint |
| C7_component_bounds | PASS | all scores and components within [0,100] |
| C8_evidence_keys_match | PASS | signing keys agree between evidence and map for all shared validators |
| C9_alternates_valid | PASS | all 23 alternates scored and within the churn gap of the UNL cut |

**11/11 checks passed.**

_Reproduce: run `pft_round_audit.py --round 10` against the same public artifacts to regenerate this receipt._
