#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pft-round-audit — independent, deterministic audit of a published Post Fiat
validator-scoring round, built only from that round's public artifacts.

WHAT IT PROVES (and does not)
  It proves a published round is COMPLETE and INTERNALLY CONSISTENT: the
  artifacts are all present, they agree with each other, and the published
  UNL is a valid, non-contradictory result of the published scores.
  It does NOT re-run the scoring pipeline or claim the scores themselves are
  "correct" — reproducing the model/tie-breaking is out of scope for v1.
  Every finding is derived only from the public files, so anyone can re-run
  this and get the same receipt.

PUBLIC ARTIFACTS (per round N)
  outputs/validator_scores.json   scores + components + network_report
  outputs/selected_unl.json       chosen UNL (20) + alternates
  inputs/validator_evidence.json  raw inputs (agreement, domain, version, ...)
  inputs/validator_map.json       vNNN -> {master_key, signing_key}

USAGE
  # from local files:
  pft_round_audit.py --round 12 --from-dir ./fixtures
  # from the public explorer (needs network access to the explorer host):
  pft_round_audit.py --round 12 --base-url https://explorer.testnet.postfiat.org
  # outputs: round-12-audit.md  and  round-12-audit.json
"""
import argparse, json, os, sys, hashlib, datetime, urllib.request

UNL_SIZE = 20                      # documented max UNL size
ELIGIBILITY_CUTOFF = 40            # documented minimum score to qualify
CHURN_GAP = 5                      # documented margin a challenger must beat an incumbent by
COMPONENTS = ["consensus", "reliability", "software", "diversity", "identity"]

ARTIFACTS = {
    "scores":   "outputs/validator_scores.json",
    "unl":      "outputs/selected_unl.json",
    "evidence": "inputs/validator_evidence.json",
    "map":      "inputs/validator_map.json",
}


# ----------------------------- loading -----------------------------
def _read_local(base_dir, rel):
    # local fixtures are stored flat (just the filename)
    path = os.path.join(base_dir, os.path.basename(rel))
    with open(path, "rb") as f:
        return f.read()

def _read_url(base_url, rnd, rel):
    url = f"{base_url.rstrip('/')}/api/scoring/rounds/{rnd}/{rel}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()

def load_artifacts(rnd, from_dir=None, base_url=None):
    raw, parsed, digests = {}, {}, {}
    for kind, rel in ARTIFACTS.items():
        try:
            b = _read_local(from_dir, rel) if from_dir else _read_url(base_url, rnd, rel)
        except Exception as e:
            raw[kind] = None; parsed[kind] = None; digests[kind] = None
            parsed.setdefault("_errors", {})[kind] = str(e)
            continue
        raw[kind] = b
        digests[kind] = hashlib.sha256(b).hexdigest()
        try:
            parsed[kind] = json.loads(b)
        except Exception as e:
            parsed[kind] = None
            parsed.setdefault("_errors", {})[kind] = f"invalid JSON: {e}"
    return parsed, digests


# ----------------------------- checks -----------------------------
class Receipt:
    def __init__(self, rnd):
        self.round = rnd
        self.checks = []   # list of (id, status, detail)  status in PASS/FAIL/WARN/SKIP
    def add(self, cid, status, detail):
        self.checks.append({"id": cid, "status": status, "detail": detail})
    def verdict(self):
        if any(c["status"] == "FAIL" for c in self.checks): return "INCONSISTENT"
        if any(c["status"] == "WARN" for c in self.checks): return "CONSISTENT_WITH_WARNINGS"
        return "CONSISTENT"


def run_checks(rnd, data):
    r = Receipt(rnd)
    errors = data.get("_errors", {})

    # C1 — all artifacts present and valid JSON
    missing = [k for k in ARTIFACTS if data.get(k) is None]
    if missing:
        r.add("C1_artifacts_present", "FAIL",
              f"missing or unparseable: {', '.join(missing)} ({errors})")
        # without all four we cannot run relational checks
        for cid in ["C2_round_number", "C3_map_covers_scores", "C4_unl_in_scores",
                    "C5c_churn_gap", "C6_no_duplicates", "C7_component_bounds",
                    "C8_evidence_keys_match", "C9_alternates_valid"]:
            r.add(cid, "SKIP", "prerequisite artifact missing")
        return r
    r.add("C1_artifacts_present", "PASS", "all four artifacts present and valid JSON")

    scores = data["scores"]["validator_scores"]
    unl = data["unl"]["unl"]
    alternates = data["unl"].get("alternates", [])
    vmap = data["map"]
    evidence = data["evidence"]

    score_keys = [v["master_key"] for v in scores]
    score_set = set(score_keys)
    map_keys = set(v["master_key"] for v in vmap.values())
    unl_set = set(unl)

    # C2 — round number in evidence matches requested round
    ev_round = evidence.get("round_number")
    if ev_round == rnd:
        r.add("C2_round_number", "PASS", f"evidence round_number == {rnd}")
    else:
        r.add("C2_round_number", "FAIL", f"evidence round_number={ev_round}, expected {rnd}")

    # C3 — every scored validator has a map entry, and vice versa
    if score_set == map_keys:
        r.add("C3_map_covers_scores", "PASS",
              f"scores and map cover identical {len(score_set)} validators")
    else:
        r.add("C3_map_covers_scores", "FAIL",
              f"scored-not-mapped={len(score_set-map_keys)}, mapped-not-scored={len(map_keys-score_set)}")

    # C4 — every UNL member was actually scored
    if unl_set <= score_set:
        r.add("C4_unl_in_scores", "PASS", f"all {len(unl_set)} UNL members present in scores")
    else:
        r.add("C4_unl_in_scores", "FAIL", f"UNL members missing from scores: {len(unl_set-score_set)}")

    # C5a — UNL size is exactly the documented maximum
    if len(unl) == UNL_SIZE:
        r.add("C5a_unl_size", "PASS", f"UNL size == {UNL_SIZE}")
    else:
        r.add("C5a_unl_size", "FAIL", f"UNL size is {len(unl)}, expected {UNL_SIZE}")

    # C5b — every UNL member meets the eligibility cutoff
    below = [v["master_key"] for v in scores if v["master_key"] in unl_set and v["score"] < ELIGIBILITY_CUTOFF]
    if not below:
        r.add("C5b_eligibility", "PASS",
              f"all UNL members score >= {ELIGIBILITY_CUTOFF} (eligibility cutoff)")
    else:
        r.add("C5b_eligibility", "FAIL",
              f"{len(below)} UNL member(s) below eligibility cutoff {ELIGIBILITY_CUTOFF}")

    # C5c — CORE CHECK: churn-gap rule.
    # An incumbent keeps its seat unless a challenger beats it by >= CHURN_GAP.
    # So no ELIGIBLE excluded validator may outscore the weakest UNL member by
    # CHURN_GAP or more. This is the documented anti-churn selection rule.
    score_by_key = {v["master_key"]: v["score"] for v in scores}
    if unl_set:
        weakest_unl = min(score_by_key[k] for k in unl_set)
        violations = [(k[:10], score_by_key[k]) for k in score_by_key
                      if k not in unl_set
                      and score_by_key[k] >= ELIGIBILITY_CUTOFF
                      and score_by_key[k] - weakest_unl >= CHURN_GAP]
        if not violations:
            r.add("C5c_churn_gap", "PASS",
                  f"no excluded validator beats the weakest UNL member (score {weakest_unl}) "
                  f"by the churn gap of {CHURN_GAP}; selection consistent with anti-churn rule")
        else:
            r.add("C5c_churn_gap", "FAIL",
                  f"{len(violations)} excluded validator(s) beat the weakest UNL member "
                  f"(score {weakest_unl}) by >= {CHURN_GAP}: {violations[:5]}")
    else:
        r.add("C5c_churn_gap", "SKIP", "empty UNL")

    # C6 — no duplicate master keys anywhere; UNL and alternates disjoint
    dup_scores = len(score_keys) != len(score_set)
    overlap = unl_set & set(alternates)
    if not dup_scores and not overlap:
        r.add("C6_no_duplicates", "PASS", "no duplicate score entries; UNL and alternates disjoint")
    else:
        bits = []
        if dup_scores: bits.append("duplicate master_key in scores")
        if overlap: bits.append(f"{len(overlap)} validators in both UNL and alternates")
        r.add("C6_no_duplicates", "FAIL", "; ".join(bits))

    # C7 — every component and overall score within 0..100
    bad = []
    for v in scores:
        for f in ["score"] + COMPONENTS:
            val = v.get(f)
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                bad.append(f"{v['master_key'][:10]}.{f}={val}")
    if not bad:
        r.add("C7_component_bounds", "PASS", "all scores and components within [0,100]")
    else:
        r.add("C7_component_bounds", "FAIL", f"{len(bad)} out-of-range value(s): {bad[:5]}")

    # C8 — evidence and map agree on signing keys for shared validators
    ev_by_key = {v["master_key"]: v for v in evidence["validators"]}
    map_by_key = {v["master_key"]: v for v in vmap.values()}
    mism = [k for k in (set(ev_by_key) & set(map_by_key))
            if ev_by_key[k].get("signing_key") != map_by_key[k].get("signing_key")]
    if not mism:
        r.add("C8_evidence_keys_match", "PASS",
              "signing keys agree between evidence and map for all shared validators")
    else:
        r.add("C8_evidence_keys_match", "FAIL", f"{len(mism)} signing-key mismatch(es)")

    # C9 — alternates are all scored, and none EXCEED the churn gap over the
    # weakest UNL member (an alternate scoring up to CHURN_GAP-1 above an
    # incumbent is correct under the anti-churn rule, not an anomaly).
    alt_set = set(alternates)
    if not alt_set <= score_set:
        r.add("C9_alternates_valid", "FAIL", f"{len(alt_set-score_set)} alternates not in scores")
    else:
        min_unl = min(v["score"] for v in scores if v["master_key"] in unl_set) if unl_set else 0
        churn_breakers = [v["master_key"] for v in scores
                          if v["master_key"] in alt_set and v["score"] - min_unl >= CHURN_GAP]
        if churn_breakers:
            r.add("C9_alternates_valid", "FAIL",
                  f"{len(churn_breakers)} alternate(s) beat the weakest UNL member by >= {CHURN_GAP} "
                  f"yet were not promoted (churn-rule violation)")
        else:
            r.add("C9_alternates_valid", "PASS",
                  f"all {len(alt_set)} alternates scored and within the churn gap of the UNL cut")
    return r


# ----------------------------- receipt output -----------------------------
def build_receipt_obj(rnd, data, digests, receipt):
    return {
        "tool": "pft-round-audit",
        "tool_version": "1.0",
        "round": rnd,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact_sha256": digests,
        "verdict": receipt.verdict(),
        "checks": receipt.checks,
        "note": ("Independent consistency audit from public artifacts only. Proves completeness "
                 "and internal consistency; does not re-run scoring or assert score correctness."),
    }

STATUS_MARK = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}

def render_markdown(obj):
    L = []
    L.append(f"# Post Fiat Round Audit — Round {obj['round']}")
    L.append("")
    L.append(f"**Verdict: {obj['verdict']}**")
    L.append("")
    L.append(f"- Generated (UTC): {obj['generated_utc']}")
    L.append(f"- Tool: {obj['tool']} v{obj['tool_version']}")
    L.append("- Scope: independent consistency audit from public artifacts only. "
             "Does not re-run scoring or assert score correctness.")
    L.append("")
    L.append("## Artifact fingerprints (SHA-256)")
    L.append("")
    for k, h in obj["artifact_sha256"].items():
        L.append(f"- `{k}`: `{h}`" if h else f"- `{k}`: (missing)")
    L.append("")
    L.append("## Checks")
    L.append("")
    L.append("| Check | Result | Detail |")
    L.append("|---|---|---|")
    for c in obj["checks"]:
        detail = c["detail"].replace("|", "\\|")
        L.append(f"| {c['id']} | {STATUS_MARK[c['status']]} | {detail} |")
    L.append("")
    passed = sum(1 for c in obj["checks"] if c["status"] == "PASS")
    total = len(obj["checks"])
    L.append(f"**{passed}/{total} checks passed.**")
    L.append("")
    L.append("_Reproduce: run `pft_round_audit.py --round "
             f"{obj['round']}` against the same public artifacts to regenerate this receipt._")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Audit a published Post Fiat scoring round from public artifacts.")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--from-dir", help="load artifacts from a local directory instead of the network")
    ap.add_argument("--base-url", default="https://explorer.testnet.postfiat.org",
                    help="explorer base URL (used when --from-dir is not given)")
    ap.add_argument("--out-dir", default=".", help="where to write the receipt files")
    args = ap.parse_args()

    data, digests = load_artifacts(args.round, from_dir=args.from_dir, base_url=args.base_url)
    receipt = run_checks(args.round, data)
    obj = build_receipt_obj(args.round, data, digests, receipt)

    md = render_markdown(obj)
    base = os.path.join(args.out_dir, f"round-{args.round}-audit")
    with open(base + ".json", "w") as f:
        json.dump(obj, f, indent=2)
    with open(base + ".md", "w") as f:
        f.write(md)

    print(md)
    print(f"\nWrote {base}.md and {base}.json")
    # exit non-zero if inconsistent, so CI can gate on it
    sys.exit(0 if obj["verdict"].startswith("CONSISTENT") else 2)


if __name__ == "__main__":
    main()
