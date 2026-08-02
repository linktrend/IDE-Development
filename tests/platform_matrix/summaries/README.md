# Machine-readable cross-platform matrix summaries

JSON files written by `python3 scripts/run_cross_platform_matrix.py` land here
(`matrix-<sys.platform>-<stamp>.json` and `matrix-<sys.platform>-latest.json`).

These `*.json` outputs are gitignored. CI uploads them as workflow artifacts.
Do not commit host-specific summaries.
