"""Draw eddy's animated diagrams.

    python3 docs/diagrams/diagrams.py docs/diagrams
        the wide layout of each, standalone, for the README and the book:
        eddy.svg, parts.svg, disk.svg, contribute.svg

    python3 docs/diagrams/diagrams.py --scoped site/src/generated
        the site's copies (site/scripts/diagrams.mjs): a wide and a narrow
        layout of each, <name>-wide.svg and <name>-narrow.svg, with every
        class, keyframe and id prefixed so two copies on one page never meet,
        and their colors taken from the page's (.eddy-diagram in
        site/src/styles/brand.css), so they follow the site's theme toggle

Each diagram makes one claim, and its loop shows the mechanism behind it.
CSS keyframes only, so a standalone copy animates inside an <img> on
GitHub. Under prefers-reduced-motion every animation stops at one frame
that holds the whole claim (`still`), and every caption shows.
"""

import re
import sys
from pathlib import Path

SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CH = 0.6  # a monospace character's advance, in ems

# The standalone palette: the family's ink and paper, eddy's violet.
LIGHT = (
    "--bg:#ebe9e2;--panel:#fbfaf7;--fg:#0e1116;--muted:#5d6370;--rule:#d0cdc3;"
    "--soft:#e0ddd4;--accent:#6b4fd8;--accent-soft:#e4ddfb;--ok:#1f8a4c;--bad:#c0392b;--ink:#fbfaf7"
)
DARK = (
    "--bg:#14181f;--panel:#1b2029;--fg:#f2f1ec;--muted:#9a9fab;--rule:#2f3540;"
    "--soft:#232933;--accent:#a68cff;--accent-soft:#2c2547;--ok:#45c27a;--bad:#f08a7e;--ink:#14181f"
)

BASE = """
text{font-family:SANS;fill:var(--fg)}
.mono{font-family:MONO}
.t{fill:var(--fg)} .m{fill:var(--muted)} .a{fill:var(--accent)} .ok{fill:var(--ok)} .bad{fill:var(--bad)} .ink{fill:var(--ink)}
.b{font-weight:600} .h{font-size:17px;font-weight:700}
.hd{font-size:11px;letter-spacing:.07em;fill:var(--muted);font-weight:600}
.sm{font-size:13px} .xs{font-size:11.5px} .xxs{font-size:10.5px} .f12{font-size:12px}
.bg{fill:var(--bg)} .soft{fill:var(--soft)}
.panel{fill:var(--panel);stroke:var(--rule);stroke-width:1.2}
.own{fill:var(--panel);stroke:var(--accent);stroke-width:1.5}
.mchip{fill:var(--soft);stroke:var(--rule);stroke-width:1}
.achip{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.2}
.chip{fill:var(--accent)}
.hl{fill:none;stroke:var(--accent);stroke-width:2}
.hlbar{fill:var(--accent-soft)}
.edge{fill:none;stroke:var(--muted);stroke-width:1.5}
.aedge{fill:none;stroke:var(--accent);stroke-width:2}
.dash{stroke-dasharray:4 4}
.slot{fill:none;stroke:var(--rule);stroke-width:1.5;stroke-dasharray:5 4}
.tick{fill:none;stroke:var(--ok);stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.cross{fill:none;stroke:var(--bad);stroke-width:2.2;stroke-linecap:round}
.ring{fill:var(--panel);stroke:var(--rule);stroke-width:1.2}
.file{fill:var(--panel);stroke:var(--muted);stroke-width:1}
.badge{fill:var(--accent)} .badget{fill:var(--ink);font-size:12px;font-weight:700}
.ah{fill:var(--accent)}
.pulse{transform-box:fill-box;transform-origin:center}
.draw{stroke-dasharray:100}
.ghost{opacity:.5}
""".replace("SANS", SANS).replace("MONO", MONO)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Diagram:
    """One layout of one diagram: its markup, its keyframes, its loop."""

    def __init__(self, key, w, h, T, still, title, desc):
        self.key, self.w, self.h, self.T, self.still = key, w, h, T, still
        self.title, self.desc = title, desc
        self.svg, self.css = [], []
        self.n = 0

    # ---- markup ----------------------------------------------------------
    def add(self, s):
        self.svg.append(s)

    def text(self, x, y, s, cls="t", anchor=None, raw=False):
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.add(f'<text class="{cls}" x="{x:g}" y="{y:g}"{a}>{s if raw else esc(s)}</text>')

    def rect(self, x, y, w, h, cls, rx=6, extra=""):
        self.add(f'<rect class="{cls}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}"{extra}/>')

    def file(self, x, y, k=1):
        self.add(f'<path class="file" d="M{x:g},{y:g} h{7 * k:g} l{3 * k:g},{3 * k:g} v{9 * k:g} h{-10 * k:g} z"/>')

    def tick(self, x, y, cls=""):
        self.add(f'<path class="tick {cls}" d="M{x - 4:g},{y:g} l3,3.2 l5.6,-6.4"/>')

    def cross(self, x, y, cls=""):
        self.add(f'<path class="cross {cls}" d="M{x - 3.5:g},{y - 3.5:g} l7,7 m0,-7 l-7,7"/>')

    def open(self, cls):
        self.add(f'<g class="{cls}">')

    def close(self):
        self.add("</g>")

    # ---- motion ----------------------------------------------------------
    def uid(self, base):
        self.n += 1
        return f"{base}{self.n}"

    def kf(self, name, frames):
        body = " ".join(f"{p:g}%{{{v}}}" for p, v in frames)
        self.css.append(f"@keyframes k-{name}{{{body}}}")
        self.css.append(f".{name}{{animation:k-{name} {self.T}s linear infinite}}")
        return name

    def show(self, a, b, lo=0, hi=1, fade=0.8, base="s"):
        """A class whose opacity is hi inside [a, b] and lo outside."""
        name = self.uid(base)
        if a <= 0:
            fr = [(0, hi), (b, hi), (b + fade, lo), (100 - fade, lo), (100, hi)]
        else:
            fr = [(0, lo), (max(a - fade, 0), lo), (a, hi), (b, hi), (min(b + fade, 100), lo)]
            if b + fade < 100:
                fr.append((100, lo))
        return self.kf(name, [(p, f"opacity:{v:g}") for p, v in fr])

    def fly(self, dx, dy, t0, t1, a=None, b=96, fade=0.8):
        """A class that moves from (dx, dy) to where it is drawn over [t0, t1],
        visible from a (default t0) until b."""
        a = t0 if a is None else a
        name = self.uid("f")
        off, on = f"transform:translate({dx:g}px,{dy:g}px)", "transform:translate(0px,0px)"
        fr = [(0, f"{off};opacity:0"), (max(a - fade, 0), f"{off};opacity:0"), (a, f"{off};opacity:1"),
              (t0, f"{off};opacity:1"), (t1, f"{on};opacity:1"), (b, f"{on};opacity:1"),
              (min(b + fade, 100), f"{on};opacity:0")]
        if b + fade < 100:
            fr.append((100, f"{on};opacity:0"))
        return self.kf(name, fr)

    def travel(self, dx, dy, t0, t1, a=None, b=None, fade=0.8):
        """A class drawn at its start that moves by (dx, dy) over [t0, t1] and
        is gone at b (default t1 + 1)."""
        a = t0 if a is None else a
        b = t1 + 1 if b is None else b
        name = self.uid("v")
        on, off = "transform:translate(0px,0px)", f"transform:translate({dx:g}px,{dy:g}px)"
        fr = [(0, f"{on};opacity:0"), (max(a - fade, 0), f"{on};opacity:0"), (a, f"{on};opacity:1"),
              (t0, f"{on};opacity:1"), (t1, f"{off};opacity:1"), (b, f"{off};opacity:1"),
              (min(b + fade, 100), f"{off};opacity:0")]
        if b + fade < 100:
            fr.append((100, f"{off};opacity:0"))
        return self.kf(name, fr)

    def draw(self, a, b, hold=96):
        """A class for a path with pathLength 100, drawn over [a, b]."""
        name = self.uid("d")
        return self.kf(name, [(0, "stroke-dashoffset:100;opacity:0"), (a - 0.5, "stroke-dashoffset:100;opacity:0"),
                              (a, "stroke-dashoffset:100;opacity:1"),
                              (b, "stroke-dashoffset:0;opacity:1"), (hold, "stroke-dashoffset:0;opacity:1"),
                              (hold + 0.8, "stroke-dashoffset:0;opacity:0"), (100, "stroke-dashoffset:100;opacity:0")])

    def pulse(self, times, width=3, scale=1.3):
        name = self.uid("p")
        fr = [(0, "transform:scale(1)")]
        for t in times:
            fr += [(t, "transform:scale(1)"), (t + width / 2, f"transform:scale({scale})"), (t + width, "transform:scale(1)")]
        fr.append((100, "transform:scale(1)"))
        return self.kf(name, fr)

    # ---- shared furniture -------------------------------------------------
    def header(self, title, sub, sub_x=None, narrow=False):
        self.text(16 if narrow else 20, 30 if narrow else 32, title, "h")
        if narrow:
            self.text(16, 50, sub, "m xs")
        else:
            self.text(sub_x, 32, sub, "m sm")

    def captions_wide(self, caps, y, width):
        for i, (l1, l2, a, b) in enumerate(caps):
            x = 20 + i * width
            cls = self.show(a, b, lo=0.35, base="cap")
            self.open(f"cap {cls}")
            self.add(f'<circle class="badge" cx="{x + 12}" cy="{y + 4}" r="11"/>')
            self.text(x + 12, y + 8, str(i + 1), "badget", "middle")
            self.text(x + 30, y, l1, "t sm")
            self.text(x + 30, y + 17, l2, "t sm")
            self.close()

    def captions_narrow(self, caps, y):
        yy = y
        for i, cap in enumerate(caps):
            *lines, a, b = cap
            cls = self.show(a, b, lo=0.35, base="cap")
            self.open(f"cap {cls}")
            self.add(f'<circle class="badge" cx="27" cy="{yy - 4}" r="10"/>')
            self.text(27, yy, str(i + 1), "badget", "middle")
            for k, line in enumerate(lines):
                self.text(44, yy + k * 16, line, "t xs")
            self.close()
            yy += 24 + 16 * (len(lines) - 1)

    # ---- output -----------------------------------------------------------
    def render(self, scoped):
        p = f"ed-{self.key}-"
        delay = self.still / 100 * self.T
        root = f".{p}root " if scoped else ""
        motion = (f"@media (prefers-reduced-motion:reduce){{{root}*{{animation-play-state:paused!important;"
                  f"animation-delay:-{delay:g}s!important}}{root}.cap{{animation:none!important;opacity:1!important}}}}")
        if scoped:
            base = BASE.replace(f"font-family:{SANS}", f"font-family:var(--sl-font),{SANS}")
            base = base.replace(f"font-family:{MONO}", f"font-family:var(--sl-font-mono),{MONO}")
            tokens = ""
        else:
            base = BASE
            tokens = f":root{{{LIGHT}}}@media (prefers-color-scheme:dark){{:root{{{DARK}}}}}"
        style = tokens + base + motion + "".join(self.css)
        # Prefix every class, keyframe and id with the diagram's key.
        style = re.sub(r"\.(?=[a-zA-Z])", f".{p}", style)
        style = re.sub(r"\bk-", f"{p}k-", style)
        style = style.replace(f".{p}{p}root", f".{p}root")
        style = style.replace("text{font-family", f":where(.{p}root) text{{font-family" if scoped else "text{font-family", 1)
        body = "\n".join(self.svg)
        body = re.sub(r'class="([^"]*)"', lambda m: 'class="' + " ".join(p + c for c in m.group(1).split()) + '"', body)
        body = re.sub(r'id="([^"]*)"', lambda m: f'id="{p}{m.group(1)}"', body)
        body = re.sub(r"url\(#([^)]*)\)", lambda m: f"url(#{p}{m.group(1)})", body)
        size = f'class="eddy-diagram {p}root"' if scoped else f'width="{self.w}" height="{self.h}"'
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" {size} '
            f'role="img" aria-labelledby="{p}ttl {p}dsc">\n'
            f'<title id="{p}ttl">{esc(self.title)}</title>\n<desc id="{p}dsc">{esc(self.desc)}</desc>\n'
            f"<style>{style}</style>\n"
            f'<defs><marker id="{p}ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
            f'orient="auto"><path class="{p}ah" d="M0,0 L10,5 L0,10 z"/></marker></defs>\n'
            f'<rect class="{p}bg" width="{self.w}" height="{self.h}" rx="10"/>\n{body}\n</svg>\n'
        )


def key_text(service, mid):
    return f'meeting/<tspan class="a">{service}</tspan>/{mid}'


# =============================================================================
# 1. The mechanism: a part per service lists, no model runs, each meeting is
#    kept under its key with its transcript whole, and a session reads later.
# =============================================================================

HERO_TITLE = "eddy: a program lists meetings, a session reads them later"
HERO_DESC = (
    "Three meeting services, Wispr Flow, Webex and Microsoft Teams, hold recorded meetings. eddy has one part "
    "per service. Each part lists its service's meetings and fetches them while the count of model calls "
    "stays at zero, and a two-minute check-in is skipped as too short to matter. eddy keeps each other "
    "meeting under its key, meeting slash service slash the meeting's id, with the transcript as the service "
    "served it and a plain copy with one line per turn. Later, and outside eddy, a Claude session reads one "
    "transcript and writes signals through millpond."
)

SERVICES = [
    ("Wispr Flow", "Wispr Flow", "wispr", "7f3c2a", "transcript.json",
     [("design review · 48 min", "review · 48m", 48), ("check-in · 2 min", "check-in · 2m", 2)]),
    ("Webex", "Webex", "webex", "3d77a1", "transcript.vtt", [("vendor call · 31 min", "vendor · 31m", 31)]),
    ("Microsoft Teams", "Teams", "teams", "9b1e04", "transcript.vtt", [("planning · 55 min", "planning · 55m", 55)]),
]
DETAILS = ["design review · 48 min · 4 people", "vendor call · 31 min · 3 people", "planning · 55 min · 6 people"]
LENGTHS = ["48 min", "31 min", "55 min"]
READ = ["Ana: export ships Friday", "Raj: legal needs a week", "Ana: then the 24th", "Mei: I'll tell them"]

# The loop, in percent: services record 2-14, parts list 16-30, the short
# one is skipped at 30, captures are kept 44-60, a session reads 64-94.
CHIP_AT = [[3, 6], [9], [12]]
FLY_AT = [[16, 19], [22], [25]]
CARD_AT = [44, 48, 52]


def hero(narrow):
    if narrow:
        d = Diagram("eddy-n", 360, 920, 20, 86, HERO_TITLE, HERO_DESC)
        d.header("eddy", "lists recorded meetings; a session reads them later", narrow=True)
        d.text(16, 80, "SERVICES", "hd")
        part_x = [20, 132, 244]
        for i, (_, short, part, mid, served, chips) in enumerate(SERVICES):
            bx = 16 + i * 112
            d.rect(bx, 88, 104, 96, "panel")
            d.text(bx + 8, 108, short, "t sm b")
            for j, (_, label, mins) in enumerate(chips):
                y = 120 + j * 24
                c = d.show(CHIP_AT[i][j], 96)
                d.open(c)
                d.rect(bx + 6, y, 92, 18, "mchip", 4)
                d.text(bx + 12, y + 13, label, "t xxs")
                d.close()
        # eddy
        d.rect(8, 200, 344, 232, "soft", 8)
        d.text(20, 222, "EDDY · A PART PER SERVICE", "hd")
        d.text(286, 222, "model calls", "m xxs", "end")
        p = d.pulse([18, 24, 30, 36], 3, 1.5)
        d.text(306, 224, "0", f"a h pulse {p}", "end")
        for i, (_, short, part, *_r) in enumerate(SERVICES):
            px = part_x[i]
            d.rect(px, 234, 96, 32, "panel", 5)
            d.text(px + 48, 255, part, "mono sm b", "middle")
            on = d.show(FLY_AT[i][0] + 3, FLY_AT[i][-1] + 6)
            d.rect(px, 234, 96, 32, f"hl {on}", 5)
        d.text(28, 283, "skipped: check-in, 2 min", f"m xxs {d.show(31, 96)}")
        d.rect(20, 298, 320, 120, "panel", 6)
        d.text(32, 318, "SHARED BY EVERY PART", "hd")
        rows = [("key", "meeting/&lt;service&gt;/&lt;meeting id&gt;"), ("details", "title · start · length · attendees"),
                ("raw", "as served, plus one line per turn"), ("skip", "a meeting too short to matter")]
        for j, (k, v) in enumerate(rows):
            d.text(32, 340 + j * 20, k, "mono xxs b")
            d.text(90, 340 + j * 20, v, "xxs", raw=True)
        # flights: each meeting from its service into its part
        for i, (_, short, part, mid, served, chips) in enumerate(SERVICES):
            bx = 16 + i * 112
            for j, (_, label, mins) in enumerate(chips):
                y = 120 + j * 24
                t0 = FLY_AT[i][j]
                short_one = mins < 10
                dx, dy = part_x[i] + 2 - (bx + 6), (270 if short_one else 241) - y
                c = d.travel(dx, dy, t0, t0 + 4, b=30 if short_one else None)
                d.open(c)
                d.rect(bx + 6, y, 92, 18, "achip", 4)
                d.text(bx + 12, y + 13, label, "t xxs")
                d.close()
        # captures
        d.text(16, 458, "CAPTURES", "hd")
        for i, (_, short, part, mid, served, chips) in enumerate(SERVICES):
            y = 468 + i * 70
            t = CARD_AT[i]
            d.open(d.fly(0, -16, t, t + 2))
            d.rect(16, y, 328, 62, "panel")
            d.text(28, y + 20, key_text(part, mid), "mono xs b", raw=True)
            d.text(332, y + 20, LENGTHS[i], "m xxs", "end")
            d.close()
            for k, (fname, note) in enumerate([(served, "as served"), ("transcript.txt", "one line per turn")]):
                d.open(d.show(t + 2 + k * 2, 96))
                d.file(28, y + 29 + k * 16)
                d.text(44, y + 38 + k * 16, fname, "mono xxs")
                d.text(332, y + 38 + k * 16, note, "m xxs", "end")
                d.close()
        # the reader, later
        d.text(16, 696, "A READER · LATER", "hd")
        dim = d.show(64, 94, lo=0.4)
        d.open(dim)
        d.rect(16, 706, 328, 96, "panel")
        d.text(28, 726, "a Claude session", "t sm b")
        d.text(332, 726, "reads transcript.txt", "m xxs", "end")
        d.close()
        d.rect(16, 706, 328, 96, f"hl {d.show(64, 94)}")
        for k, line in enumerate(READ[:3]):
            d.text(28, 748 + k * 17, line, f"mono xxs {d.show(68 + k * 3, 94)}")
        for k, (sig, w) in enumerate([("decision", 64), ("ask", 40)]):
            c = d.fly(0, -8, 80 + k * 3, 82 + k * 3, b=94)
            d.open(c)
            d.rect(332 - w, 740 + k * 26, w, 20, "chip", 10)
            d.text(332 - w / 2, 754 + k * 26, sig, "ink xxs b", "middle")
            d.close()
        d.text(332, 795, "signals, through millpond", f"m xxs {d.show(84, 94)}", "end")
        d.add(f'<path class="aedge draw {d.draw(64, 68, 94)}" pathLength="100" d="M344,499 H352 V754 H346" '
              f'marker-end="url(#ah)"/>')
        d.captions_narrow([
            ("A part per service lists the meetings.", 2, 30),
            ("No model runs. A short one is skipped.", 30, 44),
            ("Each is kept by its key, transcript whole.", 44, 64),
            ("A session reads it later. eddy never does.", 64, 94),
        ], 828)
        return d

    d = Diagram("eddy-w", 900, 500, 20, 86, HERO_TITLE, HERO_DESC)
    d.header("eddy", "lists recorded meetings; a session reads them later", sub_x=64)
    R = [76, 162, 248]
    d.text(20, 64, "SERVICES", "hd")
    for i, (name, _, part, mid, served, chips) in enumerate(SERVICES):
        y = R[i]
        d.rect(20, y, 176, 80, "panel")
        d.text(34, y + 22, name, "t sm b")
        for j, (label, _, mins) in enumerate(chips):
            c = d.show(CHIP_AT[i][j], 96)
            d.open(c)
            d.rect(32, y + 34 + j * 22, 152, 18, "mchip", 4)
            d.text(40, y + 47 + j * 22, label, "t xxs")
            d.close()
    # eddy
    d.rect(216, 44, 220, 380, "soft", 8)
    d.text(230, 64, "EDDY · A PART PER SERVICE", "hd")
    d.rect(230, 384, 192, 32, "panel", 5)
    d.text(244, 404, "model calls while listing", "m xs")
    p = d.pulse([17, 23, 29, 35, 41], 3, 1.5)
    d.text(408, 406, "0", f"a h pulse {p}", "end")
    for i, (_, _, part, *_r) in enumerate(SERVICES):
        cy = R[i] + 40
        d.rect(230, cy - 17, 192, 34, "panel", 5)
        d.text(244, cy + 5, part, "mono sm b")
        d.text(408, cy + 4, "lists · fetches", "m xxs", "end")
        on = d.show(FLY_AT[i][0] + 3, FLY_AT[i][-1] + 6)
        d.rect(230, cy - 17, 192, 34, f"hl {on}", 5)
    d.text(258, 149, "skipped: check-in, 2 min", f"m xxs {d.show(31, 96)}")
    d.rect(230, 318, 192, 58, "panel", 5)
    d.text(244, 335, "SHARED BY EVERY PART", "hd")
    d.text(244, 352, "the key · the details", "xxs")
    d.text(244, 367, "the raw layout · the skip", "xxs")
    # flights
    for i, (label_, _, part, mid, served, chips) in enumerate(SERVICES):
        y = R[i]
        cy = y + 40
        for j, (label, _, mins) in enumerate(chips):
            t0 = FLY_AT[i][j]
            sy = y + 34 + j * 22
            short_one = mins < 10
            dx, dy = 250 - 32, (136 if short_one else cy - 9) - sy
            c = d.travel(dx, dy, t0, t0 + 4, b=30 if short_one else None)
            d.open(c)
            d.rect(32, sy, 152, 18, "achip", 4)
            d.text(40, sy + 13, label, "t xxs")
            d.close()
    # captures
    d.text(456, 64, "CAPTURES · KEYED", "hd")
    for i, (_, _, part, mid, served, chips) in enumerate(SERVICES):
        y, t = R[i], CARD_AT[i]
        d.add(f'<path class="aedge {d.show(t - 1, 96)}" d="M424,{y + 40} H450" marker-end="url(#ah)"/>')
        d.open(d.fly(-24, 0, t, t + 2))
        d.rect(456, y, 220, 80, "panel")
        d.text(468, y + 20, key_text(part, mid), "mono xs b", raw=True)
        d.text(468, y + 36, DETAILS[i], "m xxs")
        d.close()
        for k, (fname, note) in enumerate([(served, "as served"), ("transcript.txt", "one line per turn")]):
            d.open(d.show(t + 2 + k * 2, 96))
            d.file(468, y + 45 + k * 16)
            d.text(484, y + 54 + k * 16, fname, "mono xxs")
            d.text(664, y + 54 + k * 16, note, "m xxs", "end")
            d.close()
    # where eddy ends
    d.add('<path class="edge dash" d="M686,72 V412"/>')
    d.text(686, 428, "eddy ends here", "m xxs", "middle")
    # the reader, later
    d.text(696, 64, "A READER · LATER", "hd")
    d.open(d.show(64, 94, lo=0.4))
    d.rect(696, 76, 184, 166, "panel")
    d.text(710, 98, "a Claude session", "t sm b")
    d.text(710, 115, "reads transcript.txt", "m xs")
    d.close()
    d.rect(696, 76, 184, 166, f"hl {d.show(64, 94)}")
    for k, line in enumerate(READ):
        d.text(710, 142 + k * 22, line, f"mono xxs {d.show(68 + k * 3, 94)}")
    for k, (sig, x, w) in enumerate([("decision", 696, 72), ("ask", 776, 44)]):
        d.open(d.fly(0, -10, 81 + k * 3, 83 + k * 3, b=94))
        d.rect(x, 254, w, 22, "chip", 11)
        d.text(x + w / 2, 269, sig, "ink xs b", "middle")
        d.close()
    d.text(696, 296, "signals, written through", f"m xxs {d.show(85, 94)}")
    d.text(696, 311, "millpond, never by eddy", f"m xxs {d.show(85, 94)}")
    d.add(f'<path class="aedge draw {d.draw(64, 67, 94)}" pathLength="100" d="M676,106 C686,106 684,136 692,136" '
          f'marker-end="url(#ah)"/>')
    d.captions_wide([
        ("A part per service lists", "the meetings recorded there.", 2, 30),
        ("No model runs. A meeting", "too short to matter is skipped.", 30, 44),
        ("Each is kept by its key,", "the transcript whole.", 44, 64),
        ("A session reads it later.", "eddy never does.", 64, 94),
    ], 456, 220)
    return d


# =============================================================================
# 2. One part per service: a part's own code lists and fetches; the details,
#    the skip, the key and the raw layout are shared, so every capture has
#    one shape.
# =============================================================================

PARTS_TITLE = "eddy's parts share everything but the service"
PARTS_DESC = (
    "Three parts, wispr, webex and teams. Each part's own code lists its service's meetings since its cursor "
    "and fetches each transcript: Wispr Flow's MCP endpoint, Webex's transcripts API, and Microsoft Graph's "
    "meeting transcripts. Each fetched transcript then passes through the code every part shares: it reads the "
    "meeting's title, start, length and attendees, skips a meeting too short to matter, keys the meeting as "
    "meeting slash service slash id, and writes the transcript as served plus a plain copy with one line per "
    "turn. The three captures come out the same shape; only the service in the key differs."
)
SOURCES = ["MCP endpoint over HTTP", "transcripts API", "Graph meeting transcripts"]
LANES = [("details", lambda i: DETAILS[i]), ("skip", lambda i: f"{LENGTHS[i]} · long enough · kept"),
         ("key", lambda i: key_text(SERVICES[i][2], SERVICES[i][3])),
         ("raw", lambda i: f"{SERVICES[i][4]} + transcript.txt")]


def parts(narrow):
    if narrow:
        d = Diagram("parts-n", 360, 740, 14, 84, PARTS_TITLE, PARTS_DESC)
        d.header("One part per service", "a part's own code lists and fetches", narrow=True)
        d.text(16, 80, "THE PART'S OWN CODE", "hd")
        for i, (_, short, part, mid, served, _c) in enumerate(SERVICES):
            bx = 16 + i * 112
            d.rect(bx, 88, 104, 84, "own")
            d.text(bx + 10, 110, part, "mono sm b")
            d.text(bx + 10, 127, short, "m xxs")
            for k, word in enumerate(["list", "fetch"]):
                t = 4 + i * 3 + k * 5
                d.rect(bx + 8 + k * 44, 140, 40, 20, f"hlbar {d.show(t, t + 6)}", 4)
                d.text(bx + 28 + k * 44, 154, word, "xxs", "middle")
        d.rect(16, 198, 328, 128, "soft", 8)
        d.text(28, 218, "SHARED BY EVERY PART", "hd")
        rows = [("details", "title · start · length · attendees"), ("skip", "a meeting too short to matter"),
                ("key", "meeting/&lt;service&gt;/&lt;meeting id&gt;"), ("raw", "as served, plus one line per turn")]
        for j, (k, v) in enumerate(rows):
            d.text(28, 242 + j * 22, k, "mono xxs b")
            d.text(86, 242 + j * 22, v, "xxs", raw=True)
        d.text(16, 352, "EACH CAPTURE", "hd")
        for i in range(3):
            y = 362 + i * 92
            t0 = 30 + i * 6
            d.rect(16, y, 328, 84, "panel")
            d.text(28, y + 19, LANES[2][1](i), f"mono xs b {d.show(t0 + 10, 96)}", raw=True)
            d.text(28, y + 37, LANES[0][1](i), f"m xxs {d.show(t0 + 4, 96)}")
            d.text(28, y + 54, LANES[1][1](i), f"xxs {d.show(t0 + 7, 96)}")
            d.text(28, y + 71, LANES[3][1](i), f"mono xxs {d.show(t0 + 13, 96)}")
            d.rect(16, y, 328, 84, f"hl {d.show(70, 92)}")
        for i in range(3):
            bx = 16 + i * 112
            t0 = 30 + i * 6
            sx, sy = bx + 46, 176
            ty = 362 + i * 92 + 8
            c = d.travel(320 - sx, ty - sy, t0, t0 + 14, a=12 + i * 3, b=t0 + 15)
            d.open(c)
            d.file(sx - 4, sy - 4, 1.6)
            d.close()
        d.captions_narrow([
            ("Each part lists and fetches from its service.", 3, 30),
            ("The shared code checks, keys and writes it.", 30, 70),
            ("Every capture comes out the same shape.", 70, 94),
        ], 664)
        return d

    d = Diagram("parts-w", 900, 470, 14, 84, PARTS_TITLE, PARTS_DESC)
    d.header("One part per service", "a part's own code lists and fetches; the rest is shared", sub_x=206)
    cols = [110 + i * 258 for i in range(3)]
    W = 244
    d.text(20, 70, "SERVICE", "hd")
    d.text(20, 126, "THE PART", "hd")
    for i, (name, _, part, mid, served, _c) in enumerate(SERVICES):
        x = cols[i]
        d.text(x, 66, name, "t sm b")
        d.text(x, 82, SOURCES[i], "m xs")
        d.rect(x, 94, W, 76, "own")
        d.text(x + 14, 116, part, "mono sm b")
        for k, word in enumerate(["list meetings since the cursor", "fetch each transcript"]):
            t = 4 + i * 3 + k * 5
            d.rect(x + 8, 125 + k * 20, W - 16, 18, f"hlbar {d.show(t, t + 6)}", 4)
            d.text(x + 14, 138 + k * 20, f"{k + 1}  {word}", "xs")
    d.rect(20, 214, 859, 164, "soft", 8)
    d.text(34, 236, "SHARED BY EVERY PART", "hd")
    lane_y = [262, 290, 318, 346]
    for j, (lane, _f) in enumerate(LANES):
        d.text(34, lane_y[j], lane, "mono xs b")
    for i in range(3):
        x = cols[i]
        t0 = 30 + i * 4
        span = 22
        for j, (lane, f) in enumerate(LANES):
            t = t0 + span * (lane_y[j] - 180) / (372 - 180)
            cls = "mono xxs" if lane in ("key", "raw") else "xxs"
            d.text(x + 6, lane_y[j], f(i), f"{cls} {d.show(t, 96)}", raw=True)
        # the transcript, falling through the shared code
        c = d.travel(0, 192, t0, t0 + span, a=12 + i * 3, b=t0 + span)
        d.open(c)
        d.file(x + W - 26, 172, 1.8)
        d.close()
        d.add(f'<path class="edge {d.show(70, 94)}" d="M{x + 6},388 h{W - 12}"/>')
        d.text(x + W / 2, 404, "one capture, the same shape", f"m xxs {d.show(70, 94)}", "middle")
        d.rect(x, 248, W, 108, f"hl {d.show(72, 92)}", 4)
    d.captions_wide([
        ("Each part lists and fetches", "from its own service.", 3, 30),
        ("The shared code checks, keys", "and writes every meeting.", 30, 70),
        ("Every part's capture comes", "out the same shape.", 70, 94),
    ], 432, 293)
    return d


# =============================================================================
# 3. What a meeting becomes: the transcript as served, a plain copy with one
#    line per turn, and one small capture line for the inbox; the transcript
#    stays on the host.
# =============================================================================

DISK_TITLE = "What a meeting becomes: two raw files on the host and one capture line"
DISK_DESC = (
    "The transcript as the service served it: timed segments, each with a speaker and a few words. eddy "
    "writes it whole as transcript.json, then joins each speaker's consecutive segments into a plain copy, "
    "transcript.txt, with one line per turn: Ana, so the export ships Friday; Raj, legal needs a week first; "
    "Ana, then the 24th; Mei, I'll tell the customer. Then one capture line describes the meeting: its key "
    "meeting slash wispr slash 7f3c2a, source meeting, event_at when the meeting started, its title, the two "
    "raw files, and no excerpt, since a reader reads it. The two files stay on the host and never enter git; "
    "millpond writes the line into the inbox."
)
FRAGS = [("00:12", "Ana", "so the export"), ("00:14", "Ana", "ships Friday"), ("00:15", "Raj", "legal needs"),
         ("00:17", "Raj", "a week first"), ("00:19", "Ana", "then the 24th"), ("00:21", "Mei", "I'll tell"),
         ("00:22", "Mei", "the customer")]
TURNS = [("Ana", [0, 1]), ("Raj", [2, 3]), ("Ana", [4]), ("Mei", [5, 6])]
FIELDS = [("key", key_text("wispr", "7f3c2a"), True), ("source", "meeting", False),
          ("event_at", "2026-10-16T14:00:00Z", False), ("title", "design review", False),
          ("raw", "transcript.json", False), ("", "transcript.txt", False), ("excerpt", "none: a reader reads it", False)]
FRAG_AT = [18 + j * 4 for j in range(7)]
FIELD_AT = [50, 54, 58, 63, 67, 69, 73]


def frag_targets(x0, ys):
    """Where each fragment lands in the plain copy: after its turn's speaker
    and the fragments before it, at 12px monospace."""
    out = {}
    adv = 12 * CH
    for k, (spk, idx) in enumerate(TURNS):
        x = x0 + (len(spk) + 2) * adv
        for j in idx:
            out[j] = (x, ys[k])
            x += (len(FRAGS[j][2]) + 1) * adv
    return out


def disk(narrow):
    if narrow:
        d = Diagram("disk-n", 360, 980, 16, 88, DISK_TITLE, DISK_DESC)
        d.header("What a meeting becomes", "one line for the inbox; two files stay on this host", narrow=True)
        # as served
        d.rect(16, 66, 328, 236, "panel")
        d.text(28, 86, "AS SERVED · transcript.json", "hd")
        src = {}
        for j, (ts, spk, words) in enumerate(FRAGS):
            y = 112 + j * 24
            src[j] = (106, y)
            d.open(d.show(3 + j * 2, 96))
            d.text(28, y, ts, "mono xxs m")
            d.text(68, y, spk, "xs b")
            d.text(106, y, words, "mono f12")
            d.close()
        d.text(28, 290, "timed segments, as the service sent them", "m xxs")
        # one line per turn
        d.rect(16, 318, 328, 200, "panel")
        d.text(28, 338, "ONE LINE PER TURN · transcript.txt", "hd")
        ys = [370 + k * 32 for k in range(4)]
        tgt = frag_targets(28, ys)
        for k, (spk, idx) in enumerate(TURNS):
            d.text(28, ys[k], f"{spk}:", f"mono f12 b {d.show(FRAG_AT[idx[0]] + 3, 96)}")
        for j, (ts, spk, words) in enumerate(FRAGS):
            (sx, sy), (tx, ty) = src[j], tgt[j]
            d.text(tx, ty, words, f"mono f12 {d.fly(sx - tx, sy - ty, FRAG_AT[j], FRAG_AT[j] + 3)}")
        d.text(28, 506, "speakers as served; a reader names the rest", "m xxs")
        # the line
        d.rect(16, 534, 328, 250, "panel")
        d.text(28, 554, "THE CAPTURE LINE · to millpond", "hd")
        d.text(28, 578, '{"capture": {', f"mono xxs m {d.show(48, 96)}")
        for k, (label, value, raw) in enumerate(FIELDS):
            y = 600 + k * 22 + (12 if k > 2 else 0)
            d.open(d.show(FIELD_AT[k], 96))
            d.text(40, y, label, "mono xxs m")
            d.text(106, y, value, "mono xxs" + (" b" if k == 0 else ""), raw=raw)
            d.close()
        d.text(106, 600 + 2 * 22 + 13, "when the meeting started", f"a xxs {d.show(60, 96)}")
        d.text(28, 772, "}}", f"mono xxs m {d.show(48, 96)}")
        # the boundary
        for k, (line, cls) in enumerate([("The two files stay on this host, never in git.", "t xs"),
                                         ("millpond writes the line into the inbox.", "a xs")]):
            d.text(16, 816 + k * 20, line, f"{cls} {d.show(80, 96)}")
        d.captions_narrow([
            ("eddy writes the transcript as served,", 3, 18),
            ("and a plain copy, one line per turn.", 18, 50),
            ("One small line describes the meeting.", 50, 80),
            ("The files stay here. The line enters git.", 80, 94),
        ], 890)
        return d

    d = Diagram("disk-w", 900, 480, 16, 88, DISK_TITLE, DISK_DESC)
    d.header("What a meeting becomes", "one line for the inbox, and two files that stay on this host", sub_x=232)
    # as served
    d.rect(20, 52, 270, 296, "panel")
    d.text(34, 72, "AS SERVED · transcript.json", "hd")
    src = {}
    for j, (ts, spk, words) in enumerate(FRAGS):
        y = 100 + j * 30
        src[j] = (114, y)
        d.open(d.show(3 + j * 2, 96))
        d.text(34, y, ts, "mono xxs m")
        d.text(78, y, spk, "xs b")
        d.text(114, y, words, "mono f12")
        d.close()
    d.text(34, 330, "timed segments, as the service sent them", "m xxs")
    # one line per turn
    d.rect(310, 52, 290, 296, "panel")
    d.text(324, 72, "ONE LINE PER TURN · transcript.txt", "hd")
    ys = [118 + k * 44 for k in range(4)]
    tgt = frag_targets(324, ys)
    for k, (spk, idx) in enumerate(TURNS):
        d.text(324, ys[k], f"{spk}:", f"mono f12 b {d.show(FRAG_AT[idx[0]] + 3, 96)}")
    for j, (ts, spk, words) in enumerate(FRAGS):
        (sx, sy), (tx, ty) = src[j], tgt[j]
        d.text(tx, ty, words, f"mono f12 {d.fly(sx - tx, sy - ty, FRAG_AT[j], FRAG_AT[j] + 3)}")
    d.text(324, 330, "speakers as served; a reader names the rest", "m xxs")
    # the line
    d.rect(620, 52, 260, 296, "panel")
    d.text(634, 72, "THE CAPTURE LINE · to millpond", "hd")
    d.text(634, 96, '{"capture": {', f"mono xxs m {d.show(48, 96)}")
    for k, (label, value, raw) in enumerate(FIELDS):
        y = 120 + k * 26 + (12 if k > 2 else 0)
        d.open(d.show(FIELD_AT[k], 96))
        d.text(646, y, label, "mono xxs m")
        d.text(706, y, value, "mono xxs" + (" b" if k == 0 else ""), raw=raw)
        d.close()
    d.text(706, 120 + 2 * 26 + 14, "when the meeting started", f"a xxs {d.show(60, 96)}")
    d.text(634, 330, "}}", f"mono xxs m {d.show(48, 96)}")
    # the boundary
    b = d.show(80, 96)
    d.add(f'<path class="edge {b}" d="M24,362 v8 h572 v-8 M310,370 v8"/>')
    d.text(310, 396, "stays on this host, in its raw bank · never enters git", f"t xs {b}", "middle")
    d.add(f'<path class="aedge {b}" d="M624,362 v8 h252 v-8 M750,370 v8"/>')
    d.text(750, 396, "millpond writes it into the inbox", f"a xs {b}", "middle")
    d.captions_wide([
        ("eddy writes the transcript", "as the service served it,", 3, 18),
        ("and a plain copy with", "one line per turn.", 18, 50),
        ("One small line describes", "the meeting for the inbox.", 50, 80),
        ("The files stay on this host.", "Only the line enters git.", 80, 94),
    ], 438, 220)
    return d


# =============================================================================
# 4. How others contribute: a part counts when it passes the meeting checks;
#    the generic MCP part and the folder drop take the long tail.
# =============================================================================

CONTRIB_TITLE = "Anyone can add a meeting service: a part counts once it passes the meeting checks"
CONTRIB_DESC = (
    "Three parts wait to be checked: eddy's own webex part, your plugin's part, and another plugin's part. "
    "The meeting checks in the conformance pack test each in turn: its key is meeting slash service slash "
    "meeting id; event_at is when the meeting started; the raw files are the transcript as served plus one "
    "line per turn; it skips a meeting too short to matter; it carries no excerpt. webex and your part pass "
    "and join the plugin index beside eddy's wispr. The other part stamps event_at with the capture time, "
    "fails, and is not listed. For the long tail, a generic MCP part lists meetings from any MCP endpoint that "
    "serves transcripts, and millpond's folder drop takes any file dropped in a folder as one capture."
)
CHECKS = ["key is meeting/<service>/<meeting id>", "event_at is when the meeting started",
          "raw: as served, plus one line per turn", "skips a meeting too short to matter", "carries no excerpt"]
CANDS = [("webex", "eddy's · recorded responses", "eddy's"), ("your-service", "your plugin", "your plugin"),
         ("another-part", "another plugin", "another")]
# per candidate: arrives at the gate, its checks, leaves; the third fails its second check
GATE = [(3, [9, 12, 15, 18, 21], 24), (31, [37, 40, 43, 46, 49], 52), (57, [63, 66], 69)]


def contribute(narrow):
    if narrow:
        d = Diagram("contribute-n", 360, 960, 18, 90, CONTRIB_TITLE, CONTRIB_DESC)
        d.header("Anyone can add a service", "a part counts once it passes the meeting checks", narrow=True)
        d.text(16, 80, "PARTS", "hd")
        slot = (128, 192)
        d.rect(16, 156, 328, 256, "panel")
        d.text(28, 176, "THE MEETING CHECKS", "hd")
        d.rect(118, 186, 124, 60, "slot", 8)
        rows_y = [278 + r * 28 for r in range(5)]
        for r, check in enumerate(CHECKS):
            d.add(f'<circle class="ring" cx="36" cy="{rows_y[r] - 4}" r="8"/>')
            d.text(54, rows_y[r], check, "xs")
        d.text(16, 440, "THE PLUGIN INDEX", "hd")
        entries = [("wispr", "eddy's", None), ("webex", "eddy's", 27), ("your-service", "yours", 55)]
        for e, (n, who, t) in enumerate(entries):
            y = 450 + e * 40
            cls = d.show(t, 96) if t else ""
            d.open(cls) if cls else None
            d.rect(16, y, 328, 32, "panel", 5)
            d.text(28, y + 21, n, "mono xs b")
            d.text(332, y + 21, who, "m xxs", "end")
            d.close() if cls else None
        for c, (name, _s, _short) in enumerate(CANDS):
            d.rect(16 + c * 112, 88, 104, 48, "slot", 6)
            d.text(16 + c * 112 + 8, 108, name, "mono xs m ghost")
        d.text(16, 588, "NOT LISTED", f"hd {d.show(72, 96)}")
        refused = (16, 598)
        for c, (name, sub, short) in enumerate(CANDS):
            bx, by = 16 + c * 112, 88
            arrive, checks, leave = GATE[c]
            if c < 2:
                e = 1 + c
                tx, ty = 16, 450 + e * 40
                fr = [(0, f"transform:translate(0px,0px);opacity:1"), (arrive, "transform:translate(0px,0px);opacity:1"),
                      (arrive + 4, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                      (leave, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                      (leave + 4, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                      (leave + 4.6, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                      (99, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                      (100, "transform:translate(0px,0px);opacity:1")]
            else:
                tx, ty = refused
                fr = [(0, "transform:translate(0px,0px);opacity:1"), (arrive, "transform:translate(0px,0px);opacity:1"),
                      (arrive + 4, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                      (leave, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                      (leave + 4, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                      (96, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                      (98, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                      (99, "transform:translate(0px,0px);opacity:0"), (100, "transform:translate(0px,0px);opacity:1")]
            d.open(d.kf(d.uid("c"), fr))
            d.rect(bx, by, 104, 48, "achip" if c == 1 else "panel", 6)
            d.text(bx + 8, by + 20, name, "mono xs b")
            d.text(bx + 8, by + 37, short, "m xxs")
            d.close()
            for r, t in enumerate(checks):
                end = 96 if c == 2 else leave + 3
                cls = d.show(t, end)
                if c == 2 and r == 1:
                    d.cross(36, rows_y[r] - 4, cls)
                else:
                    d.tick(36, rows_y[r] - 4, cls)
        d.text(16, 668, "event_at was the capture time", f"bad xxs {d.show(72, 96)}")
        d.text(16, 704, "THE LONG TAIL", "hd")
        tail = [("generic MCP part", "any MCP endpoint that serves transcripts"),
                ("folder drop · millpond's", "a dropped file is one capture")]
        for k, (n, desc) in enumerate(tail):
            y = 714 + k * 56
            d.rect(16, y, 328, 48, "panel")
            d.rect(16, y, 328, 48, f"hl {d.show(76, 94)}")
            d.text(28, y + 20, n, "mono xs b")
            d.text(28, y + 37, desc, "m xxs")
        d.open(d.fly(0, -26, 80, 84, b=94))
        d.file(318, 778, 1.6)
        d.close()
        d.captions_narrow([
            ("eddy's own parts pass on recorded responses.", 2, 30),
            ("Your plugin counts once it passes too.", 30, 56),
            ("A part that fails a check is not listed.", 56, 76),
            ("A generic MCP part and the folder drop", "take the rest.", 76, 94),
        ], 848)
        return d

    d = Diagram("contribute-w", 900, 520, 18, 90, CONTRIB_TITLE, CONTRIB_DESC)
    d.header("Anyone can add a service", "a part counts once it passes the meeting checks", sub_x=236)
    d.text(20, 72, "PARTS", "hd")
    d.rect(270, 52, 340, 296, "panel")
    d.text(284, 72, "THE MEETING CHECKS · CONFORMANCE PACK", "hd")
    d.rect(290, 82, 300, 62, "slot", 8)
    slot = (335, 86)
    rows_y = [172 + r * 34 for r in range(5)]
    for r, check in enumerate(CHECKS):
        d.add(f'<circle class="ring" cx="298" cy="{rows_y[r] - 4}" r="9"/>')
        d.text(316, rows_y[r], check, "xs")
    d.rect(650, 52, 230, 296, "panel")
    d.text(664, 72, "THE PLUGIN INDEX", "hd")
    entries = [("wispr", "eddy's", None), ("webex", "eddy's", 27), ("your-service", "yours", 55)]
    for e, (n, who, t) in enumerate(entries):
        y = 86 + e * 46
        cls = d.show(t, 96) if t else None
        if cls:
            d.open(cls)
        d.rect(664, y, 202, 38, "panel", 5)
        d.text(678, y + 24, n, "mono xs b")
        d.text(854, y + 24, who, "m xxs", "end")
        if cls:
            d.close()
    d.text(664, 330, "listed beside eddy's own", "m xxs")
    for c, (name, _s, _short) in enumerate(CANDS):
        d.rect(20, 82 + c * 64, 210, 54, "slot", 6)
        d.text(34, 82 + c * 64 + 23, name, "mono sm m ghost")
    d.text(20, 286, "NOT LISTED", f"hd {d.show(72, 96)}")
    refused = (20, 296)
    for c, (name, sub, short) in enumerate(CANDS):
        bx, by = 20, 82 + c * 64
        arrive, checks, leave = GATE[c]
        if c < 2:
            tx, ty = 660, 86 + (1 + c) * 46 - 8
            fr = [(0, "transform:translate(0px,0px);opacity:1"), (arrive, "transform:translate(0px,0px);opacity:1"),
                  (arrive + 4, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                  (leave, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                  (leave + 4, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                  (leave + 4.6, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                  (99, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                  (100, "transform:translate(0px,0px);opacity:1")]
        else:
            tx, ty = refused
            fr = [(0, "transform:translate(0px,0px);opacity:1"), (arrive, "transform:translate(0px,0px);opacity:1"),
                  (arrive + 4, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                  (leave, f"transform:translate({slot[0] - bx}px,{slot[1] - by}px);opacity:1"),
                  (leave + 4, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                  (96, f"transform:translate({tx - bx}px,{ty - by}px);opacity:1"),
                  (98, f"transform:translate({tx - bx}px,{ty - by}px);opacity:0"),
                  (99, "transform:translate(0px,0px);opacity:0"), (100, "transform:translate(0px,0px);opacity:1")]
        d.open(d.kf(d.uid("c"), fr))
        d.rect(bx, by, 210, 54, "achip" if c == 1 else "panel", 6)
        d.text(bx + 14, by + 23, name, "mono sm b")
        d.text(bx + 14, by + 41, sub, "m xs")
        d.close()
        for r, t in enumerate(checks):
            end = 96 if c == 2 else leave + 3
            cls = d.show(t, end)
            if c == 2 and r == 1:
                d.cross(298, rows_y[r] - 4, cls)
            else:
                d.tick(298, rows_y[r] - 4, cls)
    d.text(20, 368, "event_at was the capture time", f"bad xxs {d.show(72, 96)}")
    d.rect(20, 382, 860, 74, "soft", 8)
    d.text(34, 402, "THE LONG TAIL", "hd")
    tail = [("generic MCP part", "lists meetings from any MCP endpoint that serves transcripts"),
            ("folder drop · millpond's", "a file dropped in a folder is one capture: folder/<name>/<sha256>")]
    for k, (n, desc) in enumerate(tail):
        x = 34 + k * 426
        d.rect(x, 410, 406, 38, "panel", 5)
        d.rect(x, 410, 406, 38, f"hl {d.show(76, 94)}", 5)
        d.text(x + 12, 425, n, "mono xs b")
        d.text(x + 12, 441, desc, "m xxs")
    d.open(d.fly(0, -30, 80, 84, b=94))
    d.file(850, 414, 1.8)
    d.close()
    d.captions_wide([
        ("eddy's own parts pass", "on recorded responses.", 2, 30),
        ("Your plugin counts once", "it passes the same checks.", 30, 56),
        ("A part that fails a check", "is not listed.", 56, 76),
        ("A generic MCP part and the", "folder drop take the rest.", 76, 94),
    ], 486, 220)
    return d


DIAGRAMS = {"eddy": hero, "parts": parts, "disk": disk, "contribute": contribute}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scoped = "--scoped" in sys.argv
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    for name, make in DIAGRAMS.items():
        if scoped:
            (out / f"{name}-wide.svg").write_text(make(False).render(True))
            (out / f"{name}-narrow.svg").write_text(make(True).render(True))
        else:
            (out / f"{name}.svg").write_text(make(False).render(False))
