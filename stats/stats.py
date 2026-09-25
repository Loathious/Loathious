#!/usr/bin/env python3
"""Draw assets/stats.svg from my commits and the code in my repositories.

The Stats workflow runs this every night with two repository secrets:
STATS_REPOS, the repository names separated by commas, and STATS_TOKEN, a
fine-grained token with read-only Contents access to those repositories.
The names stay out of this public repository and its logs.

    python3 stats/stats.py                        # blobless clones from GitHub
    python3 stats/stats.py --local NAME=PATH ...  # existing clones, at their origin branch

Standard library only.
"""
import argparse
import base64
import collections
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

OWNER = "Loathious"
AUTHOR = "78258757+Loathious@users.noreply.github.com"

LANGS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".py": "Python", ".html": "HTML", ".css": "CSS",
    ".cpp": "C++", ".hpp": "C++", ".h": "C++", ".ino": "C++", ".c": "C",
    ".java": "Java", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell",
}
SKIP_DIRS = {"node_modules", "vendor", "out", ".next", "dist", "build", ".pio", ".vercel"}
MAX_LINE = 2000  # a longer line means minified or generated code
MAX_WEEKS = 52

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "stats.svg")
FONTS = os.path.join(ROOT, "stats", "fonts")

W, H = 1200, 400           # the same 3:1 frame as the other images in the README
X0, X1 = 72, 1128
C = dict(bg="#0f0b0a", line="#2c1f1c", text="#f0e6da", dim="#a09286", faint="#76675e",
         ember="#c7813b", bar="#b8402b", peak="#e3a863")
LANG_COLORS = ["#9e2b1e", "#b8402b", "#d44a31", "#c7813b", "#e3a863"]
OTHER_COLOR = "#76675e"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
SANS = 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'

SECRETS = []  # replaced with *** in every error message


class GitError(Exception):
    pass


def scrub(text):
    for secret in SECRETS:
        text = text.replace(secret, "***")
    return text


def git(repo, *args, env=None, data=None):
    p = subprocess.run(["git", "-C", repo, *args], input=data, capture_output=True, env=env)
    if p.returncode:
        err = p.stderr.decode("utf-8", "replace").strip()
        raise GitError(scrub(f"git {args[0]} failed: {err}"))
    return p.stdout


def github_env(token):
    """Git settings for GitHub. The token travels as a header set through the
    environment, so it never lands in a URL, a config file or a log."""
    config = [("credential.helper", ""), ("http.https://github.com/.extraheader", "")]
    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        SECRETS.extend([token, basic])
        config.append(("http.https://github.com/.extraheader", f"AUTHORIZATION: basic {basic}"))
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT=str(len(config)))
    for i, (key, value) in enumerate(config):
        env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"] = key, value
    return env


def clone(url, dest, env):
    """Blobless clone that downloads only the files with a language extension."""
    git(os.path.dirname(dest), "clone", "--quiet", "--filter=blob:none", "--sparse", url, dest, env=env)
    git(dest, "sparse-checkout", "set", "--no-cone", *sorted("*" + ext for ext in LANGS), env=env)
    return dest, "HEAD"


def origin_ref(path):
    """The last pushed state of an existing clone, so unpushed work stays out."""
    for ref in ("origin/HEAD", "origin/main", "origin/master"):
        p = subprocess.run(["git", "-C", path, "rev-parse", "--verify", "--quiet", ref + "^{commit}"],
                           capture_output=True)
        if p.returncode == 0:
            return path, ref
    raise GitError(f"{path} has no origin branch")


def language(path):
    parts = path.split("/")
    if SKIP_DIRS.intersection(parts[:-1]) or ".min." in parts[-1]:
        return None
    return LANGS.get(os.path.splitext(parts[-1])[1].lower())


def commit_dates(repo, ref, env=None):
    out = git(repo, "log", ref, "--fixed-strings", f"--author={AUTHOR}",
              "--format=%ad", "--date=short", env=env)
    return [dt.date.fromisoformat(d) for d in out.decode().split()]


def code_lines(repo, ref, env=None):
    """Non-blank lines per language in the files at ref."""
    wanted = []
    for entry in git(repo, "ls-tree", "-r", "-z", ref, env=env).split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        mode, kind, oid = meta.split()
        if kind == b"blob" and mode != b"120000":
            lang = language(path.decode("utf-8", "replace"))
            if lang:
                wanted.append((oid, lang))
    counts = collections.Counter()
    if not wanted:
        return counts
    out = git(repo, "cat-file", "--batch", data=b"".join(oid + b"\n" for oid, _ in wanted), env=env)
    pos = 0
    for oid, lang in wanted:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        if len(header) != 3:
            raise GitError(f"object {oid.decode()} is missing")
        size = int(header[2])
        lines = out[end + 1:end + 1 + size].decode("utf-8", "replace").splitlines()
        pos = end + 1 + size + 1
        if not any(len(line) > MAX_LINE for line in lines):
            counts[lang] += sum(1 for line in lines if line.strip())
    return counts


def collect(sources, env=None):
    dates, loc = [], collections.Counter()
    for label, repo, ref in sources:
        try:
            d, c = commit_dates(repo, ref, env), code_lines(repo, ref, env)
        except GitError as err:
            raise GitError(f"{label}: {err}") from None
        print(f"{label}: {len(d)} commits, {sum(c.values())} lines", file=sys.stderr)
        dates += d
        loc.update(c)
    return dates, loc


def from_github(names, token):
    env = github_env(token)
    SECRETS.extend(f"{OWNER}/{name}" for name in names)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        sources = []
        for i, name in enumerate(names, 1):
            label = f"Repository {i} of {len(names)}"
            try:
                repo, ref = clone(f"https://github.com/{OWNER}/{name}.git", os.path.join(tmp, f"r{i}"), env)
            except GitError as err:
                raise GitError(f"{label}: {err}\nCheck that STATS_TOKEN has not expired "
                               "and can read this repository.") from None
            sources.append((label, repo, ref))
        return collect(sources, env)


# ---------------------------------------------------------------- drawing
def monday(d):
    return d - dt.timedelta(days=d.weekday())


def weekly(dates, today):
    end = monday(today)
    start = max(monday(min(dates)), end - dt.timedelta(weeks=MAX_WEEKS - 1))
    counts = [0] * ((end - start).days // 7 + 1)
    for d in dates:
        i = (monday(d) - start).days // 7
        if 0 <= i < len(counts):
            counts[i] += 1
    return start, counts


def num(n):
    return f"{n:,}"


def kilo(n):
    if n < 1000:
        return str(n)
    if n < 100_000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{round(n / 1000)}k"


def plural(n, one, many=None):
    return one if n == 1 else many or one + "s"


def day(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def font_css():
    css = []
    for weight in (400, 500, 600):
        with open(os.path.join(FONTS, f"geist-{weight}.woff2"), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        css.append(f"@font-face{{font-family:G{weight};font-weight:{weight};"
                   f'src:url(data:font/woff2;base64,{b64}) format("woff2")}}')
    css.append(f"text{{font-family:G400,{SANS};font-weight:400;fill:{C['dim']}}}")
    css.append(f".h{{font-family:G600,{SANS};font-weight:600;fill:{C['text']}}}")
    css.append(f".s{{font-family:G500,{SANS};font-weight:500;fill:{C['ember']}}}")
    css.append(f".b{{font-family:G500,{SANS};font-weight:500;fill:{C['text']}}}")
    css.append(f".f{{fill:{C['faint']}}}")
    return "".join(css)


def bar(x, y, w, h, fill, r=3.0):
    """A bar with rounded top corners."""
    r = min(r, w / 2, h)
    return (f'<path d="M{fmt(x)} {fmt(y + h)}V{fmt(y + r)}Q{fmt(x)} {fmt(y)} {fmt(x + r)} {fmt(y)}'
            f'H{fmt(x + w - r)}Q{fmt(x + w)} {fmt(y)} {fmt(x + w)} {fmt(y + r)}V{fmt(y + h)}Z" fill="{fill}"/>')


def render(dates, loc, repos, today):
    commits, lines = len(dates), sum(loc.values())
    first = min(dates)
    start, weeks = weekly(dates, today)
    since = f"{MONTHS[first.month - 1]} {first.year}"

    top = loc.most_common(5)
    parts = [(name, n, LANG_COLORS[i]) for i, (name, n) in enumerate(top)]
    rest = lines - sum(n for _, n in top)
    if rest:
        parts.append(("Other", rest, OTHER_COLOR))
    pct = [f"{n / lines * 100:.1f}%" for _, n, _ in parts]

    headline = f"{num(commits)} {plural(commits, 'commit')} and {kilo(lines)} lines of code"
    hs = min(46, int((X1 - X0) / (0.62 * len(headline))))   # Geist 600 runs under 0.62 em a character here
    y1, y2 = 100, 140        # headline and subline baselines
    c0, c1 = 200, 296        # bar chart top and baseline
    cx1 = 584                # bar chart right edge
    my = 328                 # month labels, level with the last legend row
    lx = 640                 # languages column
    lh = 36                  # legend row spacing

    els = [f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="11.25" '
           f'fill="{C["bg"]}" stroke="{C["line"]}" stroke-width="1.5"/>']
    els.append(f'<text class="h" x="{X0}" y="{y1}" font-size="{hs}" letter-spacing="{fmt(-0.02 * hs)}">'
               f'{escape(headline)}</text>')
    els.append(f'<text class="s" x="{X0}" y="{y2}" font-size="30" letter-spacing="-0.3">across {repos} '
               f'{plural(repos, "repository", "repositories")} since {since}</text>')
    els.append(f'<text class="f" x="{X1}" y="{y2}" font-size="22" text-anchor="end">Updated {day(today)}</text>')

    # commits per week
    slot = (cx1 - X0) / len(weeks)
    bw = max(2.0, min(slot * 0.62, 18.0))
    peak = max(weeks)
    peak_i = weeks.index(peak)
    for i, n in enumerate(weeks):
        x = X0 + i * slot + (slot - bw) / 2
        if n:
            h = max(3.0, (c1 - c0) * n / peak)
            els.append(bar(x, c1 - h, bw, h, C["peak"] if i == peak_i else C["bar"]))
        else:
            els.append(f'<rect x="{fmt(x)}" y="{c1 - 3}" width="{fmt(bw)}" height="3" fill="{C["line"]}"/>')
    px = X0 + peak_i * slot + slot / 2
    els.append(f'<text class="b" x="{fmt(px)}" y="{c0 - 12}" font-size="20" text-anchor="middle">{peak}</text>')

    labels = []
    for i in range(len(weeks)):
        wk = start + dt.timedelta(weeks=i)
        firsts = [d for d in (wk + dt.timedelta(days=k) for k in range(7)) if d.day == 1]
        if firsts:
            labels.append((i, firsts[0].month))
        elif i == 0:
            labels.append((i, (wk + dt.timedelta(days=3)).month))
    xs = [X0 + i * slot + (slot - bw) / 2 for i, _ in labels]
    if len(xs) > 1 and labels[0][0] == 0 and xs[1] - xs[0] < 64:
        labels, xs = labels[1:], xs[1:]
    last = -1e9
    for (i, m), x in zip(labels, xs):
        if x - last >= 64:
            els.append(f'<text class="f" x="{fmt(x)}" y="{my}" font-size="20">{MONTHS[m - 1]}</text>')
            last = x

    # languages: one bar, then two columns of three
    ly, lw = c0, X1 - lx
    els.append(f'<clipPath id="lang"><rect x="{lx}" y="{ly}" width="{lw}" height="12" rx="6"/></clipPath>')
    gap = 4
    avail = lw - gap * (len(parts) - 1)
    x, segs = float(lx), []
    for name, n, col in parts:
        w = avail * n / lines
        segs.append(f'<rect x="{fmt(x)}" y="{ly}" width="{fmt(w)}" height="12" fill="{col}"/>')
        x += w + gap
    els.append(f'<g clip-path="url(#lang)">{"".join(segs)}</g>')
    for i, ((name, n, col), p) in enumerate(zip(parts, pct)):
        x = lx + (i // 3) * lw / 2
        y = my - (2 - i % 3) * lh
        els.append(f'<rect x="{fmt(x)}" y="{y - 15}" width="14" height="14" rx="3" fill="{col}"/>')
        els.append(f'<text x="{fmt(x + 24)}" y="{y}" font-size="22"><tspan class="b">{escape(name)}</tspan> {p}</text>')

    summary = (f"{num(commits)} {plural(commits, 'commit')} and {kilo(lines)} lines of code across {repos} "
               f"{plural(repos, 'repository', 'repositories')} since {since}. Busiest week: {peak} "
               f"{plural(peak, 'commit')}. Languages: "
               + ", ".join(f"{name} {p}" for (name, _, _), p in zip(parts, pct)) + f". Updated {day(today)}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">Commit and language stats</title>'
            f'<desc id="d">{escape(summary)}</desc>\n<style>{font_css()}</style>\n' + "\n".join(els) + "\n</svg>\n")


def write(svg):
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    os.replace(tmp, OUT)


def main():
    ap = argparse.ArgumentParser(description="Draw assets/stats.svg.")
    ap.add_argument("--local", nargs="+", metavar="NAME=PATH",
                    help="read existing clones at their origin branch instead of cloning")
    ap.add_argument("--today", type=dt.date.fromisoformat, help=argparse.SUPPRESS)
    args = ap.parse_args()
    today = args.today or dt.datetime.now(dt.timezone.utc).date()
    try:
        if args.local:
            sources = []
            for arg in args.local:
                name, _, path = arg.partition("=")
                if not name or not path:
                    ap.error(f"expected NAME=PATH, got {arg!r}")
                sources.append((name, *origin_ref(path)))
            dates, loc = collect(sources)
            repos = len(sources)
        else:
            token = os.environ.get("STATS_TOKEN", "").strip()
            names = [n.rsplit("/", 1)[-1] for n in re.findall(r"[^\s,]+", os.environ.get("STATS_REPOS", ""))]
            if not token or not names:
                sys.exit("Set the STATS_TOKEN and STATS_REPOS secrets first. assets/stats.svg was left as it was.")
            if not all(re.fullmatch(r"[\w.-]+", n) for n in names):
                sys.exit("STATS_REPOS should list repository names separated by commas.")
            dates, loc = from_github(names, token)
            repos = len(names)
    except GitError as err:
        sys.exit(f"{err}\nassets/stats.svg was left as it was.")
    if not dates or not loc:
        sys.exit(f"Found no commits by {AUTHOR}, or no code. assets/stats.svg was left as it was.")
    write(render(dates, loc, repos, today))
    print(f"Wrote {os.path.relpath(OUT, ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
