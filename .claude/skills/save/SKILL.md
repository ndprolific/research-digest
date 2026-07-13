---
name: save
description: Save your changes to GitHub — stages everything, writes a commit message automatically, and pushes. Use whenever the user wants to save, publish, sync, backup, or upload their work, or says things like "save my changes", "push this", "upload to github".
user-invocable: true
allowed-tools:
  - Bash(git *)
---

# /save — Save your work to GitHub

This skill exists so a non-technical user never has to type a git command
themselves. Run the whole sequence yourself and only report the result —
do not ask the user to confirm each step, and do not show them raw git
commands or output unless something goes wrong.

## Steps

1. `git status --porcelain` — if this is empty, tell the user "Nothing to
   save — no changes since your last save." and stop. Do not commit or push.
2. `git add -A` — stage everything (new, modified, deleted files).
3. Look at `git diff --staged` to see what actually changed, and write one
   short commit message that describes it in plain language (imperative
   mood, e.g. "Update weekly digest script", "Add new report template").
   Pick this yourself — never ask the user to write or approve a commit
   message.
4. `git commit -m "<your message>"`.
5. `git push`. If it fails because there is no upstream branch yet, run
   `git push -u origin HEAD` instead. If it fails because the remote has
   newer commits, run `git pull --rebase` and then `git push` once more.
6. If a real conflict comes up during the rebase that you cannot resolve
   safely, stop and explain plainly what happened and what the user should
   do next — don't force-push or discard anything.

## Reporting back

On success, reply with one short, plain-language sentence — no jargon,
no file paths, no command output. For example: "Saved and uploaded your
changes." If nothing needed saving, say that instead.
