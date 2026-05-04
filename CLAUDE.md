## Subagent model selection

**Default: always dispatch subagents with `model: opus`.**

Downgrade is permitted ONLY if the task falls entirely within one of these
categories. If a task spans multiple categories or is ambiguous, use opus.

### Permitted `haiku` tasks
- Pure lookup: grep/glob searches, listing files, extracting a specific
  value from a known file.
- Mechanical single-file edits with a precise spec: rename a symbol,
  apply an exact find/replace, reformat.

### Permitted `sonnet` tasks
- Documentation writing/updating: README, docstrings, inline comments,
  changelog entries, commit messages, PR descriptions.
- Mechanical multi-file refactors where the pattern is fully specified
  (e.g. "apply this same change across these 12 files").

### Always use `opus`
- Design, architecture, or planning work.
- Debugging, root-cause analysis, test failures.
- Code review (spec compliance, quality, security).
- Multi-file integration where the subagent must make judgment calls.
- Anything ambiguous, underspecified, or novel.

When in doubt: opus. Never downgrade to save cost if the task could
plausibly need judgment.

## Git commit rules

- Commit author: talha only — no co-author lines, no footer attributions.
- Do NOT add `Co-Authored-By:` trailers or any generated-by footers.
- Commit messages: concise subject line, optional body. Nothing else.
