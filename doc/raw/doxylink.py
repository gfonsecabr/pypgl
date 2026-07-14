#!/usr/bin/env python3
"""Auto-link API mentions in the reference pages to pgl's doxygen site.

The pypgl port of pgl's own doc/raw/doxylink.py, with one structural change: the
authority on *what exists* is the built extension, not the C++ headers. pypgl
binds a subset of pgl (`Segment.yAtX` is a pgl method, not a pypgl one), so a
mention is linked only when the method is actually **bound**, and the C++
reference merely supplies the url and the tooltip.

The editable source pages live in doc/raw/*.md (no links). This script reads
those, rewrites inline-code API mentions such as `s.midpoint()` or
`pgl.convexHull(points)` into links to pgl's generated C++ reference (the API
mirrors it name for name), and writes the result to doc/*.md (the copies GitHub
renders). Always edit the raw versions; doc/*.md is generated and carries a
"do not edit" banner.

Two inputs feed it:

  * `import pypgl` -- every class and every public method the extension actually
    exposes. Run the script with the interpreter pypgl is installed in
    (`.venv/bin/python doc/raw/doxylink.py`).
  * doxygen over the pinned pgl checkout (.pgl-ref by default; --pgl-dir to point
    elsewhere) -- the tag file maps each member to its html page + anchor, and the
    XML output carries the @brief text used as the link's hover tooltip. Pass
    --no-doxygen to reuse whatever is already in <pgl-dir>/build/doc.

Resolution is *context-aware* and *fail-closed*:

  * The current class context comes from the nearest section heading whose text
    names a bound class (`### Segment` -> Segment, `### Oriented Segment` ->
    OrientedSegment, `### Shape Tree` -> ShapeTree, ...). Method names collide
    heavily across classes (`contains` lives on 14 of them), so the receiver token
    (`s`, `l`, `t`) is ignored -- only the heading decides.
  * A mention is linked only when its method name is bound on the context class.
    A cross-type mention (`t.collinear(point)` under `### Segment`) is left
    untouched and reported -- never mis-linked.
  * A name that pgl has but pypgl does not bind is reported as `not-bound`: the
    page is describing an API the reader cannot call. That is the drift this
    script exists to catch.
  * A bound name with no C++ counterpart (Python-only sugar, e.g. `_repr_svg_`)
    is reported as `no-doxygen` and left unlinked -- there is nothing to link to.
  * An overloaded name (several members, several anchors) links to the class page
    with no anchor, landing the reader on the right class.

A line consisting only of `- Other methods:` in a class section is a placeholder:
it is filled with links to every bound method of that class that did not get a
link in the section (so a method merely mentioned inside another method's
description, which never links, still shows up here). It is dropped when there is
nothing left to list.

Default mode is report-only. Pass --write to (re)generate doc/*.md from doc/raw.

Override syntax: append {ClassName} immediately after the code span to force the
context class for that one mention, e.g.  `t.collinear()`{Point}

Usage:
  .venv/bin/python doc/raw/doxylink.py                 # regenerate tags, report
  .venv/bin/python doc/raw/doxylink.py --write         # regenerate tags, write doc/*.md
  .venv/bin/python doc/raw/doxylink.py --no-doxygen    # reuse the existing tag/xml
  .venv/bin/python doc/raw/doxylink.py --pgl-dir ../pgl
  .venv/bin/python doc/raw/doxylink.py doc/raw/foo.md  # specific source files
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

DEFAULT_BASE = "https://gfonsecabr.github.io/pgl/"
DEFAULT_PGL = ".pgl-ref"      # the same offline checkout CMakeLists.txt prefers
TAG_REL = "build/doc/pgl.tag"  # relative to the pgl checkout (see its Doxyfile)
XML_REL = "build/doc/xml"
DEFAULT_RAW = "doc/raw"
DEFAULT_OUT = "doc"
BANNER = ("<!-- AUTO-GENERATED from {src} by doc/raw/doxylink.py — do not edit; "
          "edit the raw version and regenerate. -->")

# A code span is an API mention if it is, optionally, a `pgl.`/`pypgl.` module
# qualifier and/or a `receiver.`, then a method name, then optional parentheses.
# Groups: 1 = module qualifier (an explicit module-level reference), 2 = receiver,
# 3 = method name, 4 = parentheses.
MENTION_RE = re.compile(
    r"^(?:(pgl|pypgl)\.)?(?:([A-Za-z_]\w*)\.)?([A-Za-z_]\w*)(\(.*\))?$")

# Inline code spans not already wrapped in a markdown link.
SPAN_RE = re.compile(r"(?<!\[)`([^`]+)`(?:\{([A-Za-z_]\w*)\})?")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# An "Other methods:" placeholder the author leaves in the raw markdown; the
# script fills it with the section's bound methods that got no link above.
PLACEHOLDER_RE = re.compile(r"^(\s*[-*]\s*Other methods:?)\s*$")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_bound(module):
    """Return (classes, functions) -- what the built extension actually exposes.

    classes:   class name -> set of its method names (dunders dropped, but
               single-underscore names such as `_repr_svg_` kept, so that a
               mention of one resolves as bound rather than as a typo).
    functions: the module-level function names (convexHull, hilbertSort, ...).

    Only classes defined by pypgl itself are considered: the module also re-exports
    a few names from the standard library (importlib's PackageNotFoundError).
    """
    try:
        mod = __import__(module)
    except ImportError as exc:
        sys.exit(f"cannot import {module}: {exc}\n"
                 f"run this with the interpreter pypgl is installed in, e.g.\n"
                 f"  .venv/bin/python doc/raw/doxylink.py")
    classes, functions = {}, set()
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        origin = getattr(obj, "__module__", "") or ""
        if not (origin == module or origin.startswith(module + ".")):
            continue
        if isinstance(obj, type):
            classes[name] = {m for m in dir(obj) if not m.startswith("__")}
        elif callable(obj):
            functions.add(name)
    return classes, functions


def load_tag(path):
    """Return (methods, class_page) read from pgl's doxygen tag file.

    methods:    full class name (pgl::Segment) -> method name -> [(anchorfile, anchor)],
                plus the pgl namespace itself under the key "pgl" for free functions.
    class_page: full class name -> its html page (for linking a bare class name).

    Unlike pgl's own script this does not build a class index of its own: which
    names are classes, and which are methods of what, is decided by the bound
    module (load_bound), and the tag file is consulted only for urls.
    """
    root = ET.parse(path).getroot()
    methods = defaultdict(lambda: defaultdict(list))
    class_page = {}
    for comp in root.findall("compound"):
        kind = comp.get("kind")
        full = comp.findtext("name")
        if kind in ("struct", "class"):
            # Prefer the top-level class over a nested one (Triangle vs Triangle::Iter).
            if full not in class_page or "::" not in full:
                class_page[full] = comp.findtext("filename")
        elif kind != "namespace":
            continue
        sink = methods[full]
        for m in comp.findall("member"):
            if m.get("kind") != "function":
                continue
            name = m.findtext("name")
            af = m.findtext("anchorfile")
            an = m.findtext("anchor")
            if name and af and an:
                sink[name].append((af, an))
    return methods, class_page


def load_briefs(xml_dir):
    """Return (anchor_brief, page_brief) from the doxygen XML output.

    anchor_brief: html anchor -> @brief text (members + free functions).
    page_brief:   html page    -> @brief text (classes/namespaces, for class links).
    The tag file has no descriptions, so the XML is the source of @brief text.
    """
    anchor_brief, page_brief = {}, {}
    if not xml_dir or not os.path.isdir(xml_dir):
        return anchor_brief, page_brief

    def text(el):
        if el is None:
            return ""
        return " ".join("".join(el.itertext()).split())

    for path in glob.glob(os.path.join(xml_dir, "*.xml")):
        if path.endswith("index.xml"):
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for comp in root.findall("compounddef"):
            if comp.get("kind") not in ("struct", "class", "namespace"):
                continue
            cid = comp.get("id")
            b = text(comp.find("briefdescription"))
            if b:
                page_brief.setdefault(f"{cid}.html", b)
            for md in comp.iter("memberdef"):
                if md.get("kind") != "function":
                    continue
                mid = md.get("id") or ""
                # member id is "<compound-id>_1<anchor>"
                if mid.startswith(cid + "_1"):
                    anchor = mid[len(cid) + 2:]
                    mb = text(md.find("briefdescription"))
                    if mb:
                        anchor_brief.setdefault(anchor, mb)
    return anchor_brief, page_brief


class Index:
    """Everything needed to resolve a mention: what pypgl binds, where pgl documents it."""

    def __init__(self, classes, functions, methods, class_page, briefs, base):
        self.classes = classes            # pypgl class name -> bound method names
        self.functions = functions        # bound module-level function names
        self.methods = methods            # pgl:: full class name -> member -> anchors
        self.class_page = class_page      # pgl:: full class name -> html page
        self.anchor_brief, self.page_brief = briefs
        self.base = base
        # Bound class name -> the C++ class documenting it. pypgl mirrors pgl's
        # names, so this is a straight lookup; a class doxygen does not know about
        # simply maps to None and never links.
        by_norm = {norm(f.split("::")[-1]): f for f in class_page
                   if f.startswith("pgl::") and "::" not in f[len("pgl::"):]}
        self.cxx = {c: by_norm.get(norm(c)) for c in classes}
        self.by_norm = {norm(c): c for c in classes}   # heading text -> bound class

    def member_anchors(self, cls, method):
        """Anchors documenting `method` of the bound class `cls`, or None.

        Falls back to the pgl namespace: a few C++ free functions are bound as
        methods (canvas manipulators -- `pgl::stroke` becomes `Canvas.stroke`), so
        the member lookup misses them but the namespace lookup finds them.
        """
        cxx = self.cxx.get(cls)
        return (self.methods.get(cxx, {}).get(method)
                or self.methods.get("pgl", {}).get(method))

    def link(self, text, rel_url):
        """Render a markdown link, adding the @brief as a hover title when known."""
        if "#" in rel_url:
            b = self.anchor_brief.get(rel_url.split("#", 1)[1])
        else:
            b = self.page_brief.get(rel_url)
        if b:
            return f'[`{text}`]({self.base}{rel_url} "{b.replace(chr(34), chr(39))}")'
        return f"[`{text}`]({self.base}{rel_url})"


def _member_url(anchors):
    """URL for a member. Overloads share no common anchor, so point at the first
    one; doxygen lists the rest consecutively right below it."""
    af, an = anchors[0]
    return f"{af}#{an}"


def _hit(anchors, target):
    """Turn a resolved anchor list into a (status, url, detail) result."""
    if len(anchors) > 1:
        return ("overloaded", _member_url(anchors), f"{target} ({len(anchors)} overloads)")
    return ("linked", _member_url(anchors), target)


def resolve(content, override, context, idx):
    """Classify a code span. Returns (status, url_or_none, detail).

    A span is a "call form" if it carries a receiver dot, a module qualifier, or
    parentheses (`s.midpoint()`, `pgl.convexHull(ps)`, `flip(e)`); otherwise it is
    a "bare" name (`edgesIntersecting`, `triangles`). Resolution tries, in order: a
    standalone class name (`OrientedLine` -> its class page), a bound method of the
    heading's class, then a bound module-level function (`convexHull`, ...). Call
    forms are reported loudly when nothing resolves (drift detection), while bare
    names that don't resolve are silently left alone -- a bare word is just as
    likely to be a variable, value, or type as a method.
    """
    m = MENTION_RE.match(content)
    if not m:
        return ("not-a-mention", None, None)
    qualified = m.group(1) is not None
    receiver = m.group(2)
    method = m.group(3)
    parens = m.group(4)
    is_call = qualified or receiver is not None or parens is not None

    # A token that names a bound class. Standing alone (optionally `pgl.`-qualified),
    # link it to its class page; with a receiver or arguments it is not a plain
    # mention. Class names are capitalized, so a lowercase token never names one:
    # `shape` is a variable, and `triangulation` is Polygon.triangulation(), not the
    # Triangulation class. Without this guard both would be captured here -- the
    # first mis-linked to the class page, the second swallowed as not-a-mention
    # before method resolution runs.
    if method[:1].isupper() and method in idx.classes:
        if receiver is None and parens is None:
            page = idx.class_page.get(idx.cxx.get(method))
            if page:
                return ("linked", page, f"{method} (class)")
            return ("no-doxygen", None, f"{method} (class) not documented by pgl")
        return ("not-a-mention", None, None)

    cls = None
    if override:
        cls = idx.by_norm.get(norm(override))
        if cls is None:
            return ("bad-override", None, override)
    elif not qualified:
        cls = context

    # 1. A method bound on the heading's class (unless explicitly module-qualified,
    #    which always means a module-level function).
    if cls is not None and not qualified and method in idx.classes[cls]:
        anchors = idx.member_anchors(cls, method)
        if anchors:
            return _hit(anchors, f"{method} -> {cls}")
        # Bound, but pgl documents nothing by that name: Python-only sugar.
        if method.startswith("_"):
            return ("not-a-mention", None, None)
        return ("no-doxygen", None, f"{method} -> {cls} (python-only)")

    # 2. A bound module-level function (context-independent).
    if method in idx.functions:
        anchors = idx.methods.get("pgl", {}).get(method)
        if anchors:
            return _hit(anchors, f"{method} -> pypgl (module)")
        return ("no-doxygen", None, f"{method} (module) (python-only)")

    # 3. Not bound. Say so loudly when pgl does have it -- the page is documenting
    #    an API pypgl does not expose.
    if not is_call:
        return ("not-a-mention", None, None)
    if cls is not None and idx.member_anchors(cls, method):
        return ("not-bound", None, f"{method} is a pgl method, not bound on {cls}")
    if qualified and idx.methods.get("pgl", {}).get(method):
        return ("not-bound", None, f"{method} is a pgl function, not bound in pypgl")
    if cls is None:
        return ("no-context", None, method)
    return ("not-in-context", None, f"{method} not bound on {cls}")


def process(src, dst, idx, write):
    with open(src) as fh:
        text = fh.read()
    lines = text.split("\n")
    context = None
    section = -1                       # bumps on every heading
    in_fence = False
    stats = defaultdict(int)
    details = []
    out_lines = []
    linked_here = defaultdict(set)     # section -> bound method names that got a link
    placeholders = []                  # (out_index, section, cls, prefix)

    for lineno, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        h = HEADING_RE.match(line)
        if h:
            section += 1
            cls = idx.by_norm.get(norm(h.group(2)))
            if cls is not None:
                context = cls
            out_lines.append(line)
            continue

        ph = PLACEHOLDER_RE.match(line)
        if ph and context is not None:
            placeholders.append((len(out_lines), section, context, ph.group(1)))
            out_lines.append(line)     # filled in after the whole section is seen
            continue

        def repl(mo):
            content = mo.group(1)
            override = mo.group(2)
            status, url, detail = resolve(content, override, context, idx)
            stats[status] += 1
            if status not in ("not-a-mention",):
                details.append((lineno, status, content, detail))
            if status in ("linked", "overloaded"):
                mm = MENTION_RE.match(content)
                if mm and context and mm.group(3) in idx.classes[context]:
                    linked_here[section].add(mm.group(3))
                return idx.link(content, url)
            return mo.group(0)

        out_lines.append(SPAN_RE.sub(repl, line))

    # Fill the placeholders now that every link in their section is known. A bound
    # method with no C++ counterpart is listed unlinked rather than dropped: it is
    # still a method the reader can call.
    for i, sec, cls, prefix in placeholders:
        others = sorted(m for m in idx.classes[cls]
                        if not m.startswith("_") and m not in linked_here[sec])
        stats["other-filled"] += len(others)
        items = []
        for m in others:
            anchors = idx.member_anchors(cls, m)
            items.append(idx.link(m, _member_url(anchors)) if anchors else f"`{m}`")
        out_lines[i] = f"{prefix} {', '.join(items)}." if items else None

    if write:
        body = "\n".join(l for l in out_lines if l is not None)
        with open(dst, "w") as fh:
            fh.write(BANNER.format(src=src) + "\n\n" + body)
    return stats, details


def regenerate_tags(pgl_dir):
    """Run doxygen over the pgl checkout so the tag file and XML reflect its current
    headers. The Doxyfile's paths are relative to the checkout, so run it from there;
    HTML is switched off (we link to the published site, never a local build) and its
    output is shown only on failure, to keep a normal run quiet."""
    doxyfile = os.path.join(pgl_dir, "Doxyfile")
    if not os.path.exists(doxyfile):
        sys.exit(f"Doxyfile not found: {doxyfile}\n"
                 f"pass --pgl-dir /path/to/pgl (a checkout of github.com/gfonsecabr/pgl), "
                 f"or --no-doxygen to reuse an existing {TAG_REL}")
    with open(doxyfile) as fh:
        config = fh.read() + "\nGENERATE_HTML = NO\nGENERATE_LATEX = NO\n"
    try:
        proc = subprocess.run(["doxygen", "-"], input=config, cwd=pgl_dir,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True)
    except FileNotFoundError:
        sys.exit("doxygen not found on PATH; install it or pass --no-doxygen")
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.exit(f"doxygen failed (exit {proc.returncode})")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*",
                    help="source markdown files (default: doc/raw/*.md)")
    ap.add_argument("--pgl-dir", default=DEFAULT_PGL,
                    help=f"pgl checkout to run doxygen in (default: {DEFAULT_PGL})")
    ap.add_argument("--no-doxygen", action="store_true",
                    help="skip running doxygen; reuse the existing tag/xml in the checkout")
    ap.add_argument("--module", default="pypgl",
                    help="the module to introspect for bound methods (default: pypgl)")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--raw", default=DEFAULT_RAW, help="source dir (default: doc/raw)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output dir (default: doc)")
    ap.add_argument("--write", action="store_true",
                    help="(re)generate the output files from the raw sources")
    ap.add_argument("--verbose", action="store_true",
                    help="list every linked/skipped mention")
    args = ap.parse_args()

    base = args.base if args.base.endswith("/") else args.base + "/"

    if not args.no_doxygen:
        regenerate_tags(args.pgl_dir)

    tag = os.path.join(args.pgl_dir, TAG_REL)
    if not os.path.exists(tag):
        hint = ("doxygen failed to emit it" if not args.no_doxygen else
                "drop --no-doxygen to generate it")
        sys.exit(f"tag file not found: {tag}\n{hint}")

    classes, functions = load_bound(args.module)
    methods, class_page = load_tag(tag)
    briefs = load_briefs(os.path.join(args.pgl_dir, XML_REL))
    idx = Index(classes, functions, methods, class_page, briefs, base)

    files = args.files or sorted(glob.glob(os.path.join(args.raw, "*.md")))
    totals = defaultdict(int)
    # Everything the author should look at: a broken cross-reference, or a page
    # describing an API that is not there.
    loud = ("not-bound", "not-in-context", "bad-override")
    for path in files:
        dst = os.path.join(args.out, os.path.basename(path))
        stats, details = process(path, dst, idx, args.write)
        if not stats:
            continue
        summary = "  ".join(f"{k}={v}" for k, v in sorted(stats.items())
                            if k != "not-a-mention")
        if summary:
            print(f"{path}: {summary}")
        for k, v in stats.items():
            totals[k] += v
        for lineno, status, content, detail in details:
            if args.verbose or status in loud:
                print(f"    {path}:{lineno} [{status}] `{content}`  {detail or ''}")

    print("\nTOT:", "  ".join(f"{k}={v}" for k, v in sorted(totals.items())
                              if k != "not-a-mention"))
    if args.write:
        print(f"(wrote {len(files)} file(s) to {args.out}/)")
    else:
        print("(report only; pass --write to generate)")


if __name__ == "__main__":
    main()
