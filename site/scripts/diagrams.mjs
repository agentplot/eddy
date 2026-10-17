// Writes the site's copies of the diagrams, docs/diagrams/diagrams.py
// --scoped, into src/generated/: a wide and a narrow layout of each, with
// their classes, keyframes and ids prefixed and their colors taken from
// the page's. Run before every build and dev (package.json); the copies are
// not committed.
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const target = resolve(here, '../src/generated');
mkdirSync(target, { recursive: true });
execFileSync('python3', [resolve(here, '../../docs/diagrams/diagrams.py'), '--scoped', target], {
  stdio: 'inherit',
});
