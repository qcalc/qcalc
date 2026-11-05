# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.
"""Guards for the colour system (Light, Dark, Auto, print).

All checks read the compiled stylesheets, so they need no browser and no Django. Rebuild them with setup/run_sass.bat
before running if the SCSS changed.

What they protect
- every --q-* token used anywhere is defined by every theme (Dark/Auto cannot silently miss a token)
- first-party CSS does not hard-code colours: new colours must be tokens (see variables-common.scss, q-tokens mixin)
- text/background token pairs keep WCAG AA contrast in Light and Dark
- print and Auto stay wired to the right palettes
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "qsite" / "static"
CSS_DIR = STATIC / "css"
THEMES_JSON = ROOT.parent / "qcalc_res" / "json" / "themes.json"

# stylesheets that hold the rules (qcalc.css also holds every theme's token blocks)
RULE_FILES = [
    CSS_DIR / "qcalc.css",
    CSS_DIR / "tree.css",
    CSS_DIR / "tour.css",
    STATIC / "qsite" / "layout" / "layout.css",
    STATIC / "qsite" / "layout" / "components.css",
    STATIC / "qsite" / "css" / "qmd.css",
]
TEMPLATE_DIRS = [ROOT / "qsite" / "templates", ROOT / "catalog" / "templates", ROOT / "calc" / "templates"]


# ---------------------------------------------------------------------------------------------------------------------
# CSS reading helpers
# ---------------------------------------------------------------------------------------------------------------------
def _read(path: Path) -> str:
    if not path.exists():
        pytest.fail(f"{path.relative_to(ROOT)} is missing - run setup/run_sass.bat")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"@charset[^;]*;", "", text)  # a brace-less at-rule would otherwise swallow the next selector


def _parse(css: str, media=None):
    """Yield (media, selector, body) for every rule; @media blocks are entered, other at-rules are skipped."""
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        body = css[j + 1:k - 1]
        if head.startswith("@media"):
            yield from _parse(body, head[len("@media"):].strip())
        elif not head.startswith("@"):
            yield media, re.sub(r"\s+", " ", head), body
        i = k


def _declarations(body: str):
    for d in re.split(r";(?![^(]*\))", body):
        if ":" in d:
            prop, value = d.split(":", 1)
            yield prop.strip(), re.sub(r"\s+", " ", value.strip())


def _token_blocks():
    """Map theme name -> {token: value} read from the compiled qcalc.css (--q-* and --qmd-* blocks of one theme merge)."""
    blocks = {}
    for media, selector, body in _parse(_read(CSS_DIR / "qcalc.css")):
        if not _is_token_block(body):
            continue
        toks = {p: v for p, v in _declarations(body) if p.startswith(("--q-", "--qmd-"))}
        if media is None and selector == ":root":
            name = "light"
        elif media is None and selector == ":root[data-theme=dark]":
            name = "dark"
        elif media == "(prefers-color-scheme: dark)" and selector == ":root[data-theme=auto]":
            name = "auto-dark"
        elif media == "print" and selector == ":root[data-theme]":
            name = "print"
        else:
            blocks.setdefault("unexpected", []).append((media, selector))
            continue
        blocks.setdefault(name, {}).update(toks)
    return blocks


def _is_token_block(body: str) -> bool:
    """A block that defines theme tokens: the --q-* block (has --q-radius) or the --qmd-* block next to it."""
    props = [prop for prop, _ in _declarations(body)]
    return "--q-radius" in props or (bool(props) and all(p.startswith("--qmd-") for p in props))


@pytest.fixture(scope="module")
def blocks():
    return _token_blocks()


# ---------------------------------------------------------------------------------------------------------------------
# Wiring: themes.json, Auto, print
# ---------------------------------------------------------------------------------------------------------------------
def test_themes_json_ids_match_stylesheet(blocks):
    choices = json.loads(THEMES_JSON.read_text(encoding="utf-8"))["choices"]
    assert set(choices) == {"auto", "light", "dark"}, "add a token block (themes.scss) for every theme id and update this test"
    assert not blocks.get("unexpected"), f"unexpected token blocks: {blocks.get('unexpected')}"
    for needed in ("light", "dark", "auto-dark", "print"):
        assert needed in blocks, f"qcalc.css has no token block for '{needed}' - rebuild with setup/run_sass.bat"
    assert json.loads(THEMES_JSON.read_text(encoding="utf-8"))["initial"] == "auto"


def test_every_theme_defines_the_same_tokens(blocks):
    light = set(blocks["light"])
    for name in ("dark", "auto-dark", "print"):
        missing, extra = light - set(blocks[name]), set(blocks[name]) - light
        assert not missing and not extra, f"{name}: missing {sorted(missing)} extra {sorted(extra)}"


def test_auto_on_dark_device_uses_the_dark_palette(blocks):
    assert blocks["auto-dark"] == blocks["dark"]


def test_print_uses_the_light_palette_and_comes_last():
    assert _token_blocks()["print"] == _token_blocks()["light"]
    order = [(m, s) for m, s, b in _parse(_read(CSS_DIR / "qcalc.css")) if _is_token_block(b)]
    assert order[-1][0] == "print", "the print blocks must stay last: they win by source order"
    assert all(m == "print" for m, _ in order[-2:])


# ---------------------------------------------------------------------------------------------------------------------
# Tokens used but not defined
# ---------------------------------------------------------------------------------------------------------------------
def _used_tokens():
    used = {}
    sources = list(RULE_FILES)
    for d in TEMPLATE_DIRS:
        sources += [p for p in d.rglob("*.html") if not p.name.startswith("gen-")]
    for path in sources:
        text = path.read_text(encoding="utf-8", errors="ignore") if path.suffix == ".html" else _read(path)
        for m in re.finditer(r"var\(\s*(--q(?:md)?-[\w-]+)", text):
            used.setdefault(m.group(1), set()).add(path.name)
    return used


def test_every_used_token_is_defined(blocks):
    undefined = {t: sorted(f) for t, f in _used_tokens().items() if t not in blocks["light"]}
    assert not undefined, f"tokens used but not defined in any theme (add them to q-tokens): {undefined}"


# ---------------------------------------------------------------------------------------------------------------------
# No hard-coded colours in first-party CSS
# ---------------------------------------------------------------------------------------------------------------------
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FUNC = re.compile(r"\b(?:rgba?|hsla?)\(")
COLOUR_PROPS = re.compile(r"^(?:color|background(?:-color|-image)?|border(?:-(?:top|right|bottom|left))?(?:-color)?|outline(?:-color)?|"
                          r"box-shadow|text-shadow|fill|stroke|caret-color|accent-color|--(?!q-|qmd-)[\w-]+)$")
TOKEN_ALPHA = re.compile(r"rgba\(\s*var\(--q-[\w-]+\)\s*,\s*[\d.]+\s*\)")  # a token colour with an alpha, e.g. rgba(var(--q-lo-rgb), .2)
NAMED = re.compile(r"\b(?:white|black|red|green|blue|gray|grey|silver|orange|yellow|navy|teal|firebrick|papayawhip|"
                   r"whitesmoke|lightsteelblue|lightgray|lightgrey|darkgray|darkgrey)\b", re.I)

# Colours that are meant to be fixed. Each entry is (file, selector fragment, property); keep the list short and explain why.
ALLOWED_LITERALS = {
    # surfaces that are dark by design in every theme (code editor, console toolbar buttons)
    ("qcalc.css", ".elem-wrapper.dark-surface", "--fs-border"),
    ("qcalc.css", ".elem-wrapper.dark-surface", "--fs-border-hover"),
    ("qcalc.css", ".elem-wrapper.dark-surface", "--fs-fg"),
    # neutral modal backdrop and the dark help tooltip are the same in every theme
    ("layout.css", ".sidebar-mobile-backdrop", "background"),
    ("components.css", ".qcalc-help-tooltip", "background-color"),
}


def _strip_fallbacks(value: str) -> str:
    """var(--x, fallback) -> var(--x): the fallback restates the default value and may be a literal."""
    out, i = "", 0
    while True:
        j = value.find("var(", i)
        if j < 0:
            return out + value[i:]
        depth, k, comma = 1, j + 4, None
        while k < len(value) and depth:
            c = value[k]
            depth += {"(": 1, ")": -1}.get(c, 0)
            if c == "," and depth == 1 and comma is None:
                comma = k
            k += 1
        out += value[i:j] + (value[j:comma] + ")" if comma else value[j:k])
        i = k


def _literal_colours():
    found = []
    for path in RULE_FILES:
        for media, selector, body in _parse(_read(path)):
            if _is_token_block(body) or path.name == "qmd.css" and selector == ":root":
                continue  # token definitions are where literals belong (qmd.css :root holds the --qmd-* defaults)
            for prop, value in _declarations(body):
                if prop in ("content", "src", "font-family") or "url(" in value:
                    continue
                v = TOKEN_ALPHA.sub("", _strip_fallbacks(value))
                if HEX.search(v) or FUNC.search(v) or (COLOUR_PROPS.match(prop) and NAMED.search(v)):
                    found.append((path.name, selector, prop, value))
    return found


def test_allowed_literals_are_still_needed():
    live = _literal_colours()
    stale = [e for e in ALLOWED_LITERALS if not any(h[0] == e[0] and e[1] in h[1] and h[2] == e[2] for h in live)]
    assert not stale, f"remove entries that no longer match anything from ALLOWED_LITERALS: {stale}"


# ---------------------------------------------------------------------------------------------------------------------
# WCAG contrast of token pairs
# ---------------------------------------------------------------------------------------------------------------------
NAMED_COLOURS = {"white": "#ffffff", "black": "#000000", "red": "#ff0000", "firebrick": "#b22222", "papayawhip": "#ffefd5",
                 "lightsteelblue": "#b0c4de"}


def _parse_colour(value: str):
    """Return (r, g, b, a) with channels 0-255 and alpha 0-1, for the colour syntaxes the stylesheets use."""
    v = value.strip().lower()
    v = NAMED_COLOURS.get(v, v)
    if v.startswith("#"):
        h = v[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return r, g, b, (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", v)
    if m:
        return float(m[1]), float(m[2]), float(m[3]), float(m[4]) if m[4] is not None else 1.0
    raise ValueError(f"unsupported colour: {value!r}")


def _over(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def _luminance(c):
    def lin(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def _contrast(fg, bg):
    l1, l2 = _luminance(fg), _luminance(bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _resolve(theme_tokens, name, base=None):
    """A token (or '#hex' literal) as an opaque colour; translucent colours are composited over base."""
    c = _parse_colour(name if name.startswith("#") else theme_tokens[f"--q-{name}"] if f"--q-{name}" in theme_tokens
                      else theme_tokens[f"--{name}"])
    return _over(c, base) if base is not None and c[3] < 1 else c


# (foreground token, background token, minimum ratio, surface the background sits on when translucent)
SURFACES = ["surface", "body-bg", "bg-page", "bg-input", "bg-output-1", "bg-output-2", "hover-bg", "shell-light-bg",
            "tab-row-even", "tab-calcs-bg", "tab-menu-hover", "tab-selected-bg"]
PAIRS = (
    [("text", s, 4.5, "surface") for s in SURFACES]
    + [("text-soft", "surface", 4.5, "surface"), ("text-muted", "surface", 4.5, "surface"),
       ("text-field", "surface", 4.5, "surface"), ("text-muted", "bg-input", 4.5, "surface"),
       ("primary", "surface", 3.0, "surface"), ("primary", "bg-input", 3.0, "surface"),  # accent of checkbox/radio/range
       ("text-field", "select-multi-bg", 4.5, "surface")]
    + [(lk, s, 4.5, "surface") for lk in ("link", "link-visited", "link-hover", "link-active")
       for s in ("surface", "body-bg", "bg-input", "bg-output-1")]
    + [("on-accent", a, 4.5, "surface") for a in ("primary", "success", "info", "danger", "secondary", "bg-card-header",
                                                  "tab-accent", "tab-range-head", "select-hl")]
    + [("card-title-fg", "bg-card-header", 4.5, "surface"), ("button-cmd-fg", "bg-button-cmd", 4.5, "surface"),
       ("#324148", "warning", 4.5, "surface")]  # #324148 is Bootstrap's .text-dark, used by the warning toast
    + [(f"alert-{k}-{part}", f"alert-{k}-bg", 4.5, "surface") for k in ("info", "warning", "danger", "success")
       for part in ("fg", "link")]
    + [("navbar-link", "navbar-bg", 4.5, "surface"), ("navbar-link-hover", "navbar-bg", 4.5, "surface"),
       ("shell-dark-fg", "sidebar-dark-bg", 4.5, "surface"), ("shell-dark-nav-fg", "sidebar-dark-bg", 4.5, "surface"),
       ("shell-dark-fg-strong", "shell-dark-hover-bg", 4.5, "sidebar-dark-bg"),
       ("shell-dark-nav-fg", "shell-dark-nav-hover-bg", 4.5, "sidebar-dark-bg"),
       ("shell-light-fg", "shell-light-bg", 4.5, "surface"), ("shell-light-nav-fg", "shell-light-bg", 4.5, "surface"),
       ("shell-light-fg", "shell-light-hover-bg", 4.5, "shell-light-bg"),
       ("shell-light-nav-fg", "shell-light-hover-bg", 4.5, "shell-light-bg"),
       ("navbar-light-fg", "page-header-light-bg", 4.5, "surface"),
       ("btn-light-fg", "btn-light-bg", 4.5, "surface"), ("btn-light-fg", "btn-light-hover-bg", 4.5, "surface")]
    + [("code-fg", "surface", 4.5, "surface"), ("mark-fg", "bg-mark", 4.5, "surface"), ("mark1-fg", "bg-mark", 4.5, "surface"),
       ("required", "surface", 4.5, "surface"), ("tab-head-fg", "tab-head-bg", 4.5, "surface"),
       ("tab-active-fg", "tab-head-bg", 4.5, "surface"), ("text", "note-bg", 4.5, "surface")]
    + [("text", "calc-bg", 4.5, "surface"), ("text", "calc-key-bg", 4.5, "surface"),
       ("text", "calc-key-active-bg", 4.5, "surface"), ("calc-key-hover-fg", "calc-key-hover-bg", 4.5, "surface"),
       ("on-accent", "primary", 4.5, "surface")]  # the "=" key of the quick calculator
    + [(fg, bg, 4.5, "surface") for fg, bg in (
        ("qmd-pre-text", "qmd-pre-bg"), ("qmd-quote-text", "qmd-quote-bg"), ("qmd-copy-color", "qmd-copy-bg"),
        ("qmd-copy-ok-color", "qmd-copy-bg"), ("qmd-copy-fail-color", "qmd-copy-bg"))]
)


def _pair_cases():
    for theme in ("light", "dark"):
        for fg, bg, minimum, base in PAIRS:
            yield pytest.param(theme, fg, bg, minimum, base, id=f"{theme}:{fg}-on-{bg}")


@pytest.mark.parametrize("theme,fg,bg,minimum,base", list(_pair_cases()))
def test_token_pair_contrast(blocks, theme, fg, bg, minimum, base):
    tokens = {k.replace("--q-", "--q-", 1): v for k, v in blocks[theme].items()}
    tokens = {**tokens, **{f"--{k[2:]}": v for k, v in tokens.items()}}  # allow qmd-* names without the q- prefix
    base_c = _resolve(tokens, base)
    bg_c = _resolve(tokens, bg, base_c)
    fg_c = _resolve(tokens, fg, bg_c)
    ratio = _contrast(fg_c, bg_c)
    assert ratio >= minimum, f"{theme}: {fg} on {bg} is {ratio:.2f}:1, WCAG AA needs {minimum}:1"


def test_no_new_hard_coded_colours():
    offenders = []
    for fname, selector, prop, value in _literal_colours():
        if any(fname == f and frag in selector and prop == p for f, frag, p in ALLOWED_LITERALS):
            continue
        offenders.append(f"{fname}: {selector[:70]} {{ {prop}: {value[:60]} }}")
    assert not offenders, ("hard-coded colours found; use a --q-* token (variables-common.scss) or, if the colour must be "
                           "fixed in every theme, add it to ALLOWED_LITERALS with a reason:\n  " + "\n  ".join(offenders))
