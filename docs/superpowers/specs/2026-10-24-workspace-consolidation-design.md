# Consolidate workspace projects into Master_AgenticAI

## Intent and scope

Publish all six workspace projects as full folders in
https://github.com/Chandra-P/Master_AgenticAI, visible on its default `main`
branch: `kidspark`, `Campaign-Intelligence-Hub`, `Mastering-Agentic-AI-Week1`,
`Mastering-Agentic-AI-Week2-Session1`, `Dhumsharath`, and `ncua-rag-demo`.
The user chose workspace projects only and full-folder imports merged into main.

## Approaches

- Chosen: import full folders and merge into main. A normal clone includes all
  projects, and the GitHub landing page shows them.
- Full folders on kidspark-final only: preserves the current branch arrangement
  but leaves the default landing page incomplete.
- Submodules: preserve separate repository workflows but require extra clone
  steps and do not make project sources ordinary files in this repository.

## Changes

Keep the four already tracked projects. Add the clean Dhumsharath source tree
as ordinary files, preserving its existing repository metadata in an ignored
local backup and recording its upstream URL and commit as attribution. Add
ncua-rag-demo source and its public NCUA report corpus, honoring its ignore rules.
Update the root README with local links to all six projects and remove the
statement that Dhumsharath is excluded. Include Week 1 import attribution.

## Constraints and verification

Do not delete or archive any original GitHub repository. Preserve existing
Master_AgenticAI commit history and the Dhumsharath repository backup. Exclude
credentials, private environment files, dependency directories, model files,
local databases, runtime caches, and nested Git metadata. Inspect publishable
files for configured secret values and credential patterns; check blob sizes
and that Dhumsharath is a directory tree rather than a Git submodule.
Verify README project links and imported source counts. Run relevant existing
checks where available; do not change application behavior during this import.
Fetch before merging. Use a normal merge or fast-forward into main; never force
push. Push main and verify the remote commit and all six project directories.

## Builder decisions

The implementer chooses commands for preserving local nested Git metadata and
performing a clean import. Any merge conflict is resolved by preserving the
current project contents and making README links match the final structure.
Existing GitHub repositories remain available as historical sources.
