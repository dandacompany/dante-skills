---
name: dream
description: Memory consolidation and optimization skill. Use when the user says "/dream", "dream", "consolidate memory", "clean up memory", "optimize memory", or when memory files have accumulated across many sessions and need maintenance. Dynamically discovers the project memory directory, removes stale facts, converts relative dates to absolute, resolves contradictions, merges duplicates, and rebuilds the index.
---

# Dream — Memory Consolidation

Consolidate, prune, and optimize project memory files. Analogous to how the brain consolidates memories during sleep — removes noise, strengthens signal, resolves contradictions.

## When to Run

- After many sessions (5+) without cleanup
- When memory files reference deleted code, renamed files, or outdated decisions
- When the MEMORY.md index is out of sync with actual memory files
- When the user explicitly requests memory optimization
- Proactively at the end of long sessions with significant project changes

## Memory Schema Reference

Before starting, load `references/memory-schema.md` to understand the expected file format, frontmatter fields, and index conventions. Use it to identify malformed files during Phase 2.

## Consolidation Process

Execute all 7 phases in order. Report findings after each phase.

### Phase 0: Memory Location Discovery

Before doing anything else, locate the active memory directory. Check the following locations in priority order:

1. **Claude Code auto-memory** — `~/.claude/projects/<hashed-cwd>/memory/`
   - Derive `<hashed-cwd>` by replacing `/` with `-` in the absolute working directory path (e.g. `/Users/alice/projects/foo` → `-Users-alice-projects-foo`)
   - Full path: `~/.claude/projects/<hashed-cwd>/memory/`
2. **Project-level memory** — `.claude/memory/` relative to the current working directory
3. **Bare memory folder** — `memory/` relative to the current working directory
4. **Docs subfolder** — `docs/memory/` relative to the current working directory
5. **User-specified** — if the user passed a path as an argument, use that

Use the first location that contains a `MEMORY.md` file. If none is found, list all candidate paths and ask the user which to use (or whether to create one).

Report: memory directory path, how it was discovered.

### Phase 1: Inventory

1. Read the `MEMORY.md` index from the discovered memory directory
2. List all `.md` files in the directory (excluding `MEMORY.md` itself)
3. Identify:
   - **Orphaned files**: exist on disk but not referenced in the index
   - **Broken links**: referenced in the index but file is missing
4. Report: total files, orphans, broken links

### Phase 2: Temporal Normalization

For each memory file:

1. Read the file content
2. Find relative date references: "yesterday", "today", "last week", "recently", "just now", "a few days ago", and equivalents in other languages
3. If the file is missing frontmatter `type` or `description`, flag it as malformed
4. Convert relative dates to absolute dates using the file's git last-modified date or frontmatter hints as an anchor
5. Write the file back if changes were made

### Phase 3: Staleness Verification

For each memory file:

1. If the memory references specific **file paths** — verify they still exist using Glob
2. If the memory references specific **function names, classes, or variables** — verify with Grep
3. If the memory references specific **URLs or endpoints** — note for manual verification
4. If the memory references **server/infra state** (container names, ports, domains) — verify against current config files
5. Mark memories as `STALE` if referenced artifacts no longer exist
6. For stale memories: remove them if purely factual (file X does Y), update them if the fact evolved (file X was renamed to Y)

### Phase 4: Contradiction Resolution

Compare memories that share the same topic (identified by filename prefix or frontmatter `name`):

1. Group memories by topic area (e.g., all `project_*`, all `feedback_*`)
2. Within each group, check for contradictions — different values for the same fact
3. Resolve contradictions by keeping the most recent version (check git log for last edit date)
4. If both are current and non-contradictory, merge into a single memory with combined facts

### Phase 5: Deduplication & Merging

1. Identify memories with overlapping content (>50% similar facts)
2. Merge overlapping memories into a single file with a unified structure
3. Keep the more descriptive filename; delete the other
4. Preserve all unique facts from both sources

### Phase 6: Index Rebuild

1. Regenerate `MEMORY.md` from the current memory files
2. Ensure each entry is one line, under 150 characters
3. Group by type: Project, Feedback, Reference, User, Archive
4. Sort within groups by relevance (active items first, archived last)
5. Trim index to under 200 lines

## Output Report

After all phases, output a summary:

```
## Dream Report

**Date**: YYYY-MM-DD
**Memory directory**: <path>
**Memory files**: X total (Y before)
**Changes**:
- Removed: [list of deleted files with reason]
- Updated: [list of modified files with change summary]
- Merged: [list of merge operations]
- Created: [list of new files, if any]
- Index: rebuilt / no changes

**Stale references found**: N
**Contradictions resolved**: N
**Duplicates merged**: N
```

## Rules

- Never delete a memory without verifying it is truly stale (check code, git log, config)
- When in doubt, update rather than delete
- Preserve the frontmatter structure (`name`, `description`, `type`)
- Do not modify memory content beyond what consolidation requires
- Always show the user what changed before writing files — ask for confirmation on deletions
- Archive session logs older than 30 days by moving to an "Archive" section in the index
