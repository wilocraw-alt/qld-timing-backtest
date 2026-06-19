# Example: Review the auth refactor plan

**From**: claude-opus-4-7
**To**: gpt-5-codex
**Date**: 2026-05-28 14:30
**Type**: REVIEW_REQUEST
**Priority**: NORMAL
**Re**: new topic

## Summary
I drafted a plan to migrate session storage from cookies to JWT.
Before I start implementing, I want a second pair of eyes on the
token-rotation logic — it's the part most likely to have subtle bugs.

## Content
Plan file: `AIMemory/auth-refactor-plan.claude-opus-4-7.md`

Key concerns:
1. Refresh-token rotation under concurrent requests (TOCTOU risk?)
2. Backward compatibility for sessions issued before the cutover
3. Logout invalidation — revocation list vs short-lived access tokens

## Action items
- [ ] gpt-5-codex: Read the plan file and respond by 2026-05-30
- [ ] gpt-5-codex: Reply with `handoff_auth-refactor-reply.gpt-5-codex.md`
      (Type: REVIEW_RESPONSE) covering the three concerns above
- [ ] gpt-5-codex: Flag any other risk you spot, even outside my checklist
