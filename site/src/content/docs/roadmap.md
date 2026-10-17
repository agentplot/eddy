---
title: Roadmap
description: What eddy's first steps build, and the parts that follow.
---

eddy is designed, not built. Two steps of the capture plan are eddy's.
Each one ends with something running on real work.

## E1: eddy

eddy itself, in Rust, built on the capture crate and conformance pack
from flywheel-next, so it waits on those (step F2).

- **The code every part shares:** the key, the meeting's details, the
  raw layout and the skip.
- **The `wispr` part:** an MCP client of Wispr Flow's endpoint, with its
  own sign-in and a cursor, tested by replaying recorded responses.
- **The Claude Code plugin**, which pulls a transcript into a session,
  and **the herdr plugin**, which shows the day's meetings.

eddy prints the capture contract's lines and carries no excerpt.

Done when the conformance pack's meeting checks pass, a listing of last
week's meetings matches the service's own list, and no model runs
during a listing.

## E2: the old meeting pipeline retires

A meeting pipeline already runs for one partition. It retires once eddy
and the folder drop run on the fleet and a reader has turned a week of
meetings into signals. millpond imports the meetings that pipeline
already read into the partition's inbox, once, and the pipeline's sweep
and its scheduled job stop.

Done when no scheduled job runs the old sweep, and a meeting from the
old corpus is found in the inbox by its key.

## The parts that follow

| Part | Joins when |
|---|---|
| `webex` | a partition records on Webex |
| `teams` | a tenant's administrator consents to Microsoft Graph's meeting transcripts |
| a generic MCP part | a service serves transcripts over MCP and needs no part of its own |
| your service | its plugin passes the meeting checks |

## Before the code

eddy's statement is written and ruled first. This repository's rules,
its founding decisions and its sluice gate follow the statement, then
the code.
