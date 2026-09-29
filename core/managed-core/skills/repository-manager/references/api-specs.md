# API Specs

## Progress Sync Schema
`{ "Status": "Done/Blocked/In-Progress", "Last_Action": "...", "Context_For_Next_Agent": "..." }`

## Git Prefix Rule
Only `feat/`, `fix/`, and `refactor/` branches are valid for new work.

## Safety Script
- `scripts/git-pre-commit.sh`
- Blocks commit when staged `.json` or `.bin` files are detected.
