"""``acms-verify`` command line interface (DESIGN.md §4.4).

Exit codes: 0 = everything verified OK; 1 = submission accepted but at
least one solution rejected; 2 = whole-submission rejection or failing
golden vectors; 3 = usage / IO error.

The reference verifier is for contestant self-checking only; the
server-side verifier is the sole authority for official results.
"""

import argparse
import collections
import json
import sys

from . import __version__, canon, golden, specs, submission


def _load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cmd_submission(args):
    manifest = _load_json(args.manifest)
    problems = specs.check_move_specs(manifest.get("move_specs"))
    if problems:
        print("error: manifest move_specs do not match this verifier's "
              "frozen move tables", file=sys.stderr)
        for p in problems:
            print("  %s" % p, file=sys.stderr)
        return 3
    with open(args.submission, "rb") as fh:
        raw = fh.read()
    verdict = submission.process_submission(raw, manifest)
    json.dump(verdict, sys.stdout, indent=2 if args.pretty else None,
              sort_keys=True)
    print()
    if not verdict["accepted"]:
        return 2
    if all(r.get("ok") for r in verdict["results"]):
        return 0
    return 1


def _cmd_golden(args):
    report = golden.run_file(args.golden)
    failed = [r for r in report if not r["passed"]]
    for r in report:
        status = "PASS" if r["passed"] else "FAIL"
        print("%s  %s" % (status, r["name"]))
        for m in r["mismatches"]:
            print("      %s" % m)
    print("%d/%d golden vectors passed" % (len(report) - len(failed), len(report)))
    return 2 if failed else 0


def _cmd_check_hashes(args):
    manifest = _load_json(args.manifest)
    problems = specs.check_move_specs(manifest.get("move_specs"))
    # Each challenge's instance_hash is bound to the spec IT names, so
    # the hash to feed the template is looked up per challenge, never
    # taken from a single manifest-level field.
    spec_hashes = specs.move_spec_hashes()
    hashes = []
    for c in manifest["challenges"]:
        spec_hash = spec_hashes.get(c["move_spec_version"])
        if spec_hash is None:
            problems.append("unknown move_spec_version %r: %s"
                            % (c["move_spec_version"], c["challenge_id"]))
            continue
        h = canon.instance_hash(
            c["challenge_id"], c["generators"], c["initial_relators"],
            c["target_relators"], c["move_spec_version"], spec_hash)
        hashes.append(h)
        if h != c["instance_hash"]:
            problems.append("instance_hash mismatch: %s" % c["challenge_id"])
    mh = canon.manifest_hash(hashes)
    if manifest.get("manifest_hash") != mh:
        problems.append("manifest_hash: manifest has %r, verifier computes %r"
                        % (manifest.get("manifest_hash"), mh))
    if problems:
        for p in problems:
            print("FAIL  %s" % p)
        return 2
    counts = collections.Counter(c["move_spec_version"]
                                 for c in manifest["challenges"])
    print("OK  %d challenges (%s); every move_spec_hash, instance_hash and "
          "manifest_hash verified"
          % (len(manifest["challenges"]),
             ", ".join("%d %s" % (counts[v], v) for v in specs.SPEC_ORDER
                       if counts[v])))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="acms-verify",
        description="ACMS reference verifier (move specs %s; verifier %s)"
        % (", ".join(specs.SPEC_ORDER), __version__))
    parser.add_argument("--manifest", help="path to manifest.json")
    parser.add_argument("--submission", help="path to submission.txt "
                        "(challenge_id: [moves], one per line; # comments)")
    parser.add_argument("--golden", help="run golden conformance vectors")
    parser.add_argument("--check-hashes", action="store_true",
                        help="recompute and verify all hashes in --manifest")
    parser.add_argument("--pretty", action="store_true",
                        help="pretty-print the verdict JSON")
    args = parser.parse_args(argv)

    try:
        if args.golden:
            return _cmd_golden(args)
        if args.check_hashes:
            if not args.manifest:
                parser.error("--check-hashes requires --manifest")
            return _cmd_check_hashes(args)
        if args.manifest and args.submission:
            return _cmd_submission(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 3
    parser.error("nothing to do: pass --manifest with --submission, "
                 "--golden, or --manifest with --check-hashes")


if __name__ == "__main__":
    sys.exit(main())
