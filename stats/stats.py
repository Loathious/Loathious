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

W, PAD = 520, 24
C = dict(bg="#0f0b0a", line="#2c1f1c", text="#f0e6da", dim="#a09286", faint="#76675e",
         bar="#b8402b", now="#e3a863")
LANG_COLORS = ["#d44a31", "#e3a863", "#9e2b1e", "#c7813b", "#f0e6da"]
OTHER_COLOR = "#4a3632"
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
    for weight in (400, 500):
        with open(os.path.join(FONTS, f"geist-{weight}.woff2"), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        css.append(f"@font-face{{font-family:G{weight};font-weight:{weight};"
                   f'src:url(data:font/woff2;base64,{b64}) format("woff2")}}')
    css.append(f"text{{font-family:G400,{SANS};font-weight:400;fill:{C['dim']}}}")
    css.append(f".b{{font-family:G500,{SANS};font-weight:500;fill:{C['text']}}}")
    css.append(f".f{{fill:{C['faint']}}}")
    return "".join(css)


def bar(x, y, w, h, fill, r=2.0):
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

    y1, y2 = 40, 62          # sentence baselines
    c0, c1 = 92, 140         # bar chart top and baseline
    my = 158                 # month labels
    ly = 176                 # language bar
    gy = 206                 # first legend row
    rows = (len(parts) + 2) // 3
    H = gy + (rows - 1) * 22 + 24
    cw = W - 2 * PAD

    els = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="{C["bg"]}" stroke="{C["line"]}"/>']
    els.append(f'<text x="{PAD}" y="{y1}" font-size="16"><tspan class="b">{num(commits)}</tspan> '
               f'{plural(commits, "commit")} and <tspan class="b">{kilo(lines)}</tspan> lines of code</text>')
    els.append(f'<text x="{PAD}" y="{y2}" font-size="16">across <tspan class="b">{repos}</tspan> '
               f'{plural(repos, "repository", "repositories")} since {since}</text>')
    els.append(f'<text x="{W - PAD}" y="{y1}" font-size="12" class="f" text-anchor="end">Updated {day(today)}</text>')

    # commits per week
    slot = cw / len(weeks)
    bw = max(2.0, min(slot * 0.62, 14.0))
    peak = max(weeks)
    peak_i = weeks.index(peak)
    for i, n in enumerate(weeks):
        x = PAD + i * slot + (slot - bw) / 2
        if n:
            h = max(2.0, (c1 - c0) * n / peak)
            els.append(bar(x, c1 - h, bw, h, C["now"] if i == len(weeks) - 1 else C["bar"]))
        else:
            els.append(f'<rect x="{fmt(x)}" y="{c1 - 2}" width="{fmt(bw)}" height="2" fill="{C["line"]}"/>')
    px = PAD + peak_i * slot + slot / 2
    els.append(f'<text x="{fmt(px)}" y="{c0 - 7}" font-size="11" class="f" text-anchor="middle">{peak}</text>')

    labels = []
    for i in range(len(weeks)):
        wk = start + dt.timedelta(weeks=i)
        firsts = [d for d in (wk + dt.timedelta(days=k) for k in range(7)) if d.day == 1]
        if firsts:
            labels.append((i, firsts[0].month))
        elif i == 0:
            labels.append((i, (wk + dt.timedelta(days=3)).month))
    xs = [PAD + i * slot + (slot - bw) / 2 for i, _ in labels]
    if len(xs) > 1 and labels[0][0] == 0 and xs[1] - xs[0] < 34:
        labels, xs = labels[1:], xs[1:]
    last = -1e9
    for (i, m), x in zip(labels, xs):
        if x - last >= 34:
            els.append(f'<text x="{fmt(x)}" y="{my}" font-size="11" class="f">{MONTHS[m - 1]}</text>')
            last = x

    # languages
    els.append(f'<clipPath id="lang"><rect x="{PAD}" y="{ly}" width="{cw}" height="8" rx="4"/></clipPath>')
    gap = 2
    avail = cw - gap * (len(parts) - 1)
    x, segs = float(PAD), []
    for name, n, col in parts:
        w = avail * n / lines
        segs.append(f'<rect x="{fmt(x)}" y="{ly}" width="{fmt(w)}" height="8" fill="{col}"/>')
        x += w + gap
    els.append(f'<g clip-path="url(#lang)">{"".join(segs)}</g>')
    col_w = cw / 3
    for i, ((name, n, col), p) in enumerate(zip(parts, pct)):
        x = PAD + (i % 3) * col_w
        y = gy + (i // 3) * 22
        els.append(f'<circle cx="{fmt(x + 4)}" cy="{y - 4}" r="4" fill="{col}"/>')
        els.append(f'<text x="{fmt(x + 14)}" y="{y}" font-size="13"><tspan class="b">{escape(name)}</tspan> {p}</text>')

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
