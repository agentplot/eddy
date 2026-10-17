# eddy

eddy lists and fetches recorded meetings across meeting services, with
no model running, and keeps each transcript whole for a session to read
later.

![eddy: a part per service lists recorded meetings, keeps each under its key with its transcript whole, and a session reads it later](docs/diagrams/eddy.svg)

**Status: designed, not built.** This repository holds the site and the
scaffold. The code follows eddy's statement.

- **The design book:** https://agentplot.github.io/blueprints/eddy/
- **The site:** https://agentplot.github.io/eddy
- **The design:** `design/capture/design.md` in
  [agentplot/blueprints](https://github.com/agentplot/blueprints), the
  section "Meetings: eddy", and `plan.md` beside it (steps E1 and E2).

## What eddy does

Listing meetings is arithmetic and reading them is judgment, so eddy
lists and a session reads later.

- **One part per service.** `wispr` comes first: an MCP client of Wispr
  Flow's endpoint, with its own sign-in. `webex` and `teams` follow when
  a partition records there.
- **The parts share everything but the service.** They share the key,
  `meeting/<service>/<meeting id>`, and the meeting's title, start,
  length and attendees. They share the raw layout, the transcript as
  served plus a plain copy with one line per turn. And they skip a
  meeting too short to hold anything.
- **eddy stands alone.** A Claude Code plugin pulls a transcript into a
  session, and a herdr plugin shows the day's meetings.
- **Its Flywheel plugin's parts feed millpond**, the inbox, where a
  reader session turns a transcript into signals. eddy never reads a
  meeting into signals.
- **Anyone can add a service.** A plugin counts as a meeting part when
  it passes the meeting checks. A generic MCP part and millpond's folder
  drop take the long tail.

## The family

eddy is one of agentplot's tools: headwater reports releases, eddy lists
meetings, millpond keeps the inbox, sluice lands the work, and Flywheel
is the umbrella.

## Working here

```sh
devenv shell -- prose                 # the site's prose, checked by Vale
cd site && bun install && bun run dev # http://localhost:4321/eddy/
```

`site/README.md` says where the pages and diagrams live.

## License

MIT, see `LICENSE`.
