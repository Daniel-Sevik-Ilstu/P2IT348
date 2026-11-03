# Project 2: Malware Classification Under Data Drift

This project classifies Android apps as malware or benign from API-call counts (2014 to 2021) and checks what happens when the test apps come from later years than the training apps. Models trained on 2014 to 2016 work well on 2017 and 2018 but fall to chance level in 2019 to 2021, and retraining only helps once the shifted year has been labelled.

This repository was built with the Project 2 harness. See HARNESS.md for how the builder, reviewer, and tester agents were run.

## Agents used

| Role | Tool | Model |
| --- | --- | --- |
| Builder | Claude Code (VS Code extension) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Reviewer | Claude Code (VS Code extension) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| Tester | Claude Code (VS Code extension) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |

I used the same tool and model for all three roles, but every session started with a fresh context and a role prompt from the harness. The sessions are in `transcripts/`, and the harness checker confirms no session is shared between roles.

## How to run

1. Install packages: `pip install -r requirements.txt`
2. Put the 16 dataset files (`sampled_<year>_<malware|benign>_api.csv`) in `input_data/`.
3. Run the whole project from the repo root with `python -m src.main`. To run just one step use `python -m src.main --step N` (N = 1 to 7). Results (CSV and Markdown tables, PNG figures) are written to `results/`, and the written reports are in `docs/`. Step 7 takes about five minutes on my laptop.
4. Run all tests: `python harness.py test all`

Other useful commands: `python harness.py status` (progress per step) and `python harness.py check` (submission check).

## Results

Short version (details in `docs/step5_evaluation.md`, `docs/step6_test_results.md` and `docs/step7_sustainable_approach.md`):

- I train on 2014 to 2016 and test on 2017 to 2021. Pooled over all test years, accuracy looks decent (around 0.84 to 0.87 depending on the model).
- That pooled number hides a collapse. All three models score above 0.9 on 2017 and 2018, then drop to about 0.5 in 2019, 2020 and 2021. In those years they catch almost all malware but also flag almost every benign app, so they behave like "always say malware".
- Updating the model (expanding window, sliding 3-year window, incremental SGD) fixes 2020 and 2021, where accuracy goes back to roughly 0.9. Nothing fixes 2019 itself, because the models have not seen any 2019 labels yet.

## Hand-written code

None of the code in `src/` or `tests/` was written by hand, because it was all written by the builder and tester agents. What I wrote or edited by hand: the `AGENTS.md`, `REFLECTION.md`, `README.md` and `REPORT.md` files, two paragraphs in `docs/step7_sustainable_approach.md` (commit b4b40df), all the decision-log rows in `reviews/` and `tests/`, and several prompts.
