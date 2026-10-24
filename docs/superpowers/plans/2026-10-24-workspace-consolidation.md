# Workspace Consolidation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan inline.

**Goal:** Publish all six workspace projects in Master_AgenticAI and merge TheGenAcademy into main.
**Architecture:** Full source folders in the existing repository; no submodules. Preserve nested Git metadata in an ignored local backup.
**Tech Stack:** Git, PowerShell, Python for manifest and credential verification.
**Spec:** ../specs/2026-10-24-workspace-consolidation-design.md

## Global constraints

No API keys, private environment files, dependency installations, runtime databases, caches, or model weights are published. Preserve original repositories and existing history. No force push. The user explicitly requested execution and merging into main on 2026-10-24.

## Review focus

Check nested repository imports are ordinary trees, hidden configuration files contain no credentials, public report artifacts fit GitHub limits, all six projects appear on main, and remote main changes are preserved.

## Tasks

- [x] Inventory importable files and fetch remote branch state.
- [x] Back up Dhumsharath Git metadata and import its tracked source files as a full folder. Import ncua-rag-demo using its ignore rules.
- [x] Update root ignore rules, README links, and import attribution.
- [x] Scan proposed files for configured secrets and token patterns; verify sizes, source manifests, directory modes, and documentation links. Run relevant existing offline checks.
- [ ] Review the staged changes, commit on TheGenAcademy, and push that branch.
- [ ] Merge TheGenAcademy into main without rewriting history; push and verify remote main contains all six project trees.

## Execution notes

Working in the existing checkout follows the user's explicit instruction to consolidate and merge the named branches. No application behavior changes are planned. Tests validate import integrity; application dependency installation and deployment are outside this task.

Verification: 48 NCUA Python tests, 3 web proxy tests, and 7 notebook tests passed.
All 215 original Dhumsharath tracked files match their recorded SHA-256 hashes.
The staged tree contains no gitlinks or private environment files; all root
README local links resolve. Configured credential and token-pattern scans passed.
Twenty PDF paths use Git LFS (ten distinct public reports); regular Git blobs
are below 100 MiB. Independent review found no important issues.

Ruling: Use Git LFS for public PDFs because one report is 118.77 MiB and exceeds
GitHub's regular blob limit. Full report contents are preserved; cloning the
corpus requires Git LFS. Original imported whitespace is preserved to avoid
altering the recorded upstream source files.
