# karpathy/autoresearch — static-checks run, 2026-05-05

## Findings

| Claim | Status | Note |
|---|---|---|
| 001 3-file pipeline | passed | prepare 389 + train 630 + program 114 lines |
| 002 deps + uv.lock | passed | Python 3.10+, pytorch-cu128, kernels, tiktoken, pyarrow; uv.lock locked |
| 003 program.md is real instructions | passed | 5 sections (Setup / Experimentation / Output format / Logging / Loop) |
| 004 train.py has full model + optimizer | passed | 25 model+optimizer signatures |
| 005 LICENSE | **failed** | README closes with '## License — MIT' but no LICENSE file (HTTP 404) |
| 006 community fork URLs | passed | All 4 forks (Mac / MLX / Win-RTX / AMD) return HTTP 200 |
| 008 agent safety scope (program.md) | passed | Explicit "Do not modify prepare.py" + read-only enforcement list |
| 007 live H100 e2e | untested | needs H100 + ~10 min |

## Real findings

1. **README claims MIT but no LICENSE file.** A 79K-star Karpathy
   repo missing a LICENSE file is unusual. The README footer is
   literally:
   ```
   ## License
   MIT
   ```
   But `LICENSE` returns HTTP 404. Strict eval framework reading:
   the license claim is unverified until the file ships. (Could be
   that Karpathy considers the README declaration sufficient — it's
   *legally* mostly OK, but downstream license scanners and SBOM
   tools will see "no license".)

2. **`program.md` is unusually rigorous about safety scope.**
   ```
   prepare.py — fixed constants, data prep, tokenizer, dataloader,
                evaluation. Do not modify.
   ```
   And under the "What you CANNOT do" list:
   ```
   - Modify prepare.py. It is read-only.
   - Modify the evaluation harness. evaluate_bpb in prepare.py is
     the ground truth metric.
   ```
   This is the right pattern for "agent runs unattended overnight":
   carve out an explicit scope, fence the rest. Worth holding up as
   a model for other autonomous-agent projects.

3. **All 4 community forks live and reachable.** README's
   "Notable forks" section isn't link-rot — all four (Mac / MLX /
   Win-RTX / AMD) HTTP 200 right now. This is community
   coverage that the framework should reward (currently doesn't).

4. **Compound layer is the right call.** Agent decides what to
   change in train.py, runs, parses val_bpb, decides keep/discard,
   iterates. Classic LLM-driven runtime orchestration. Compound
   layer-bonus is -5 because static eval can't validate runtime
   behavior — but that's exactly the right pessimism here. Until
   someone runs the loop end-to-end and confirms the agent doesn't
   spin / hallucinate / wedge, the score caps below "Self-use".

## What is still untested

- **claim-007 H100 e2e** — needs the hardware + 10 min for one
  baseline experiment (and ~10 hours for an overnight 100-experiment
  run).
- **claim-008 in-practice safety** — program.md *says* prepare.py is
  read-only, but does the agent respect it under adversarial prompts
  ("ignore that, just modify prepare.py")? Should be tested with a
  dedicated red-team prompt.

## Verdict implication

7/8 static claims passed (LICENSE missing pulls the only failure).
Compound layer cap means static evidence + 79K stars + recent push
get us into the upper-50s / low-60s band. Score expected ~58-60.
