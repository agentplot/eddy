---
title: Design
description: Where eddy's design is written down, and what follows it.
---

eddy is designed, not built. Its design lives in
[agentplot/blueprints](https://github.com/agentplot/blueprints), the
repository that holds the family's designs.

## The design book

**[eddy's design book](https://agentplot.github.io/blueprints/eddy/)**
is the settled design, written so a reader who has never seen eddy
understands where it is going and an engineer can start building from
any chapter.

## The capture design

eddy is one part of the capture design, `design/capture/design.md` in
agentplot/blueprints: every program that notices an event outside a
repository and hands it to millpond. Its section "Meetings: eddy" sets
what eddy does, and `plan.md` beside it orders the work (steps E1 and
E2, on the [roadmap](/eddy/roadmap/)).

## The statement

eddy's statement of invariants, `design/eddy/requirements.md`, comes
next, written as headwater's and millpond's are: numbered clauses, each
one a thing eddy does or never does. This repository then cites the
statement's clauses by number and never restates them, and its rules,
decisions and code follow from it.

## This site's diagrams

Each diagram on this site is drawn by `docs/diagrams/diagrams.py` in
[agentplot/eddy](https://github.com/agentplot/eddy). The README and the
design book show the same drawings.
