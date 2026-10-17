# eddy

eddy lists and fetches recorded meetings across meeting services, one
part per service, and keeps each transcript whole for a session to read
later. It is designed, not built.

## The design

The design is `design/capture/design.md` in agentplot/blueprints, the
section "Meetings: eddy", with the order of work in `plan.md` beside it
(steps E1 and E2). The design book is
https://agentplot.github.io/blueprints/eddy/. eddy's own statement of
invariants will be `design/eddy/requirements.md` there; once it lands,
this repository cites its clauses by number and never restates them.

The rules (`docs/architecture/`), the decisions (`docs/adr/`) and the
code follow the statement. Until then this repository holds the site
(`site/`) and the diagrams it draws (`docs/diagrams/`).

## Checks

moon runs them, in one layer so far:

- `check-fast`: the site's prose, by Vale (`moon run site:prose`, or
  `devenv shell -- prose`). Seconds.

The site's build (`moon run site:build`) is the Pages workflow's and
gates nothing.

Run every tool through the shell, one command at a time:
`devenv shell -- <command>`.

## Commits

Stage by pathspec and commit the paths you wrote: `git add <paths>`,
then `git commit -m "<subject>" -- <paths>`. Never `-a`, never `add .`.
Conventional Commits subjects, scope the part of the tree touched.
