# Complete Module

Use when a module should be executed recursively until complete or genuinely blocked.

Operational summary:

- for application Programs: validate predecessor gate, then this Module’s gate via validate-application-pipeline.mjs
- load the module, phases, and issues
- compute ready work from dependencies and gates
- execute issues through proof, review, and integration
- do not treat issue completion alone as full module completion
- stop only when the module definition of done is satisfied or the module is genuinely blocked (Module 6 → release_ready)

Read and execute `.cursor/prompts/execution/COMPLETE-MODULE.md`.
