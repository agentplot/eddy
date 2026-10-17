# The site

eddy's site at https://agentplot.github.io/eddy, an
[Astro](https://astro.build) site with
[Starlight](https://starlight.astro.build), published by
`.github/workflows/pages.yml` on every push to `main` that touches
`site/` or the diagrams.

```sh
cd site
bun install            # the pinned dependencies, from bun.lock
bun run dev            # http://localhost:4321/eddy/
bun run build          # dist/, with every internal link checked
bun run shots -- <dir> # every page at 1280 and 390, light and dark, from a
                       # running preview (scripts/shots.mjs)
```

[Vale](https://vale.sh) checks the prose from the repository root, with
the rules in `styles/Eddy` and the settings in `.vale.ini`:
`devenv shell -- prose`, or `moon run site:prose`, which the fast layer
runs.

## Where the pages live

`src/content/docs/`, one file per page, in the sidebar order
`astro.config.mjs` sets:

| page | what |
|---|---|
| `index.mdx` | the start page: the hero, why, the four steps, the three ways to run eddy, the services |
| `how-it-works.mdx` | one part per service, what a meeting becomes, how others add a service |
| `how-it-fits.mdx` | eddy beside headwater, millpond, sluice and Flywheel |
| `design.md` | where the design is written down |
| `roadmap.md` | steps E1 and E2, and the parts that follow |

## The look and the diagrams

| file | what |
|---|---|
| `src/styles/brand.css` | eddy's accent, `--eddy-accent`, and the family's type and colors over Starlight's, in both themes; the diagrams' colors |
| `src/components/Hero.astro` | the start page's hero, with the animated diagram; other pages keep Starlight's |
| `src/components/Diagram.astro` | a diagram, inlined: its wide layout, and its narrow one on a phone |
| `src/components/Flow.astro`, `Step.astro` | the start page's four steps; their prose is in `index.mdx` |
| `src/components/FamilyDiagramPlaceholder.astro` | **a placeholder** for `@agentplot/site-theme`'s family diagram, on the "How it fits" page |

`src/generated/` is **generated**, by `scripts/diagrams.mjs` running
`docs/diagrams/diagrams.py --scoped` before every build and dev, and is
not committed. Change a diagram in `diagrams.py`, then regenerate the
README's copies with `devenv shell -- diagrams`.

Every diagram makes one claim, and its loop shows the mechanism behind
it. Under `prefers-reduced-motion` each stops at one frame that holds
the whole claim. No diagram draws a service's logo; services appear by
name.
