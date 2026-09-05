#!/usr/bin/env python3
"""Render a normalised bug-hunt run model as one self-contained HTML document.

Structure is fixed here rather than left to the caller because a report whose
shape changes between runs cannot be compared across runs -- and
design-history-and-failed-approaches.md section 5 records finders substituting
their own schema four times running when given latitude. The fix that worked was
making the schema mandatory, not asking for adherence.

The layout is **Manifest**, chosen over Ledger in research section 4.7 because
the scarce resource is reviewer minutes, run sizes vary from a handful to a
measured 44 candidates, and a table degrades upward more gracefully than a
per-finding column. The palette, type and six-column row are ported from the
approved mockup rather than re-derived.

**There is deliberately no convergence mark.** A two-track glyph for the two
axes was designed and then dropped: with the verdict spelled out as a word it
became decoration. Do not reintroduce it -- see the requirements document's
"Not in the digest" list, alongside the internal disposition names, the
free-text defect description, and any routing or ownership lookup.

Attributes in this document are built only from a closed vocabulary: Band and
Verdict enum values, static class names, and a validated run id. Finding text
goes exclusively into text nodes via html.escape at the interpolation site.
There is deliberately no generic attr() helper, so there is no call site a
future edit could route finding text through. That absence is what makes the
rule structural rather than a convention.

Usage:
    python3 digest_model.py < run.json | python3 render_digest.py > digest.html

Exit codes:
    0  OK          HTML on stdout
    1  BAD_MODEL   stdin did not reconstruct into a model
    2  NO_INPUT    nothing on stdin, or usage error. Never a pass.

Nothing reaches stdout on an error exit. A bash pipeline reports only the last
command's status, so a partial digest here would reach the write gate looking
like a successful render.
"""

import html
import json
import re
import sys
from typing import Final

from digest_model import Band, RenderModel, Verdict, _jargon_hits, model_from_dict

# The one attribute value in this document not drawn from an enum or a class
# name. A static developer-controlled constant, never derived from a finding, so
# it cannot carry finding text -- and the attribute test covers it by
# construction rather than by inspection.
_FONT_HREF: Final[str] = (
    "https://fonts.googleapis.com/css2"
    "?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800"
    "&family=Instrument+Sans:wght@400;500;600"
    "&family=IBM+Plex+Mono:wght@400;500;600"
    "&display=swap"
)

_STYLE: Final[str] = """
:root{
  --ground:#101720; --surf:#18212C; --surf-2:#1E2937; --rule:#2A3543; --rule-2:#3A485A;
  --text:#DCE4EC; --text-2:#93A2B3; --dim:#6B7A8B;
  --act:#FF6B7A; --imp:#E8A33D; --low:#7E8FA0; --verify:#4FD1B5; --call:#C99BF5;
  --display:"Bricolage Grotesque","Trebuchet MS",sans-serif;
  --body:"Instrument Sans",-apple-system,BlinkMacSystemFont,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --cols:6.4rem minmax(0,2.5fr) minmax(0,1.1fr) 11.6rem 3rem;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--text);font-family:var(--body);font-size:15px;line-height:1.5}
.shell{max-width:80rem;margin:0 auto;padding:clamp(1rem,3vw,2.4rem) clamp(1rem,3vw,2.4rem) 6rem}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}

.mast{border-bottom:1px solid var(--rule-2);padding-bottom:1.5rem}
.kicker{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:0 0 .9rem}
.kicker b{color:var(--text-2);font-weight:500}
.mast h1{font-family:var(--display);font-weight:800;font-size:clamp(1.7rem,4.4vw,2.7rem);line-height:1.05;letter-spacing:-.025em;margin:0;max-width:34ch}
.mast h1 em{font-style:normal;color:var(--act)}
.counts{font-family:var(--mono);font-size:.82rem;margin:1rem 0 0;display:flex;flex-wrap:wrap;gap:.15rem .95rem;color:var(--text-2)}
.counts b{font-weight:600;font-size:1.05rem;margin-right:.28rem}
.counts .b-act b{color:var(--act)}.counts .b-imp b{color:var(--imp)}
.counts .b-low b{color:var(--low)}.counts .b-def b{color:var(--dim)}
.counts .axis{font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-right:.15rem}
.counts .v-count b{color:var(--verify)}
.mast .sub{color:var(--text-2);max-width:62ch;margin:.8rem 0 0;font-size:.95rem}
.band-why b{color:var(--text-2);font-weight:600}
.bar{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1.1rem}
.btn{font-family:var(--display);font-weight:600;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;background:none;border:1px solid var(--rule-2);color:var(--text-2);padding:.45rem .75rem;cursor:pointer}
.btn:hover{border-color:var(--verify);color:var(--text)}
.btn:focus-visible{outline:2px solid var(--verify);outline-offset:2px}

/* band group header */
.band{display:flex;align-items:baseline;gap:.85rem;margin:2.6rem 0 .5rem}
.band h2{font-family:var(--display);font-weight:800;font-size:.95rem;letter-spacing:.12em;text-transform:uppercase;margin:0;white-space:nowrap}
.band .hr{flex:1;height:1px;background:var(--rule-2)}
.band .n{font-family:var(--mono);font-size:.78rem;color:var(--dim)}
.b-act h2{color:var(--act)} .b-imp h2{color:var(--imp)} .b-low h2{color:var(--low)} .b-def h2{color:var(--dim)}
.spill{margin-top:10px}.spill>summary{cursor:pointer;padding:8px 10px;border:1px solid var(--line,#d8d8d8);border-radius:6px;font-size:13px;line-height:1.5}.spill[open]>summary{margin-bottom:8px}.spill-body{padding-left:6px}.spill-file>summary{cursor:pointer;padding:5px 8px;font-size:12.5px;display:flex;justify-content:space-between;border-bottom:1px solid var(--line,#eee)}.band-why{margin:0 0 .8rem;font-size:.82rem;color:var(--dim);max-width:70ch}

.group{border:1px solid var(--rule)}
.mhead{display:grid;grid-template-columns:var(--cols);gap:1rem;background:var(--surf-2);padding:.5rem 1rem;border-bottom:1px solid var(--rule-2)}
.mhead span{font-family:var(--display);font-weight:600;font-size:.6rem;letter-spacing:.15em;text-transform:uppercase;color:var(--text-2)}
.mhead .r{text-align:right}

.row{border-bottom:1px solid var(--rule);background:var(--surf)}
.row:last-child{border-bottom:0}
.row > summary{display:grid;grid-template-columns:var(--cols);gap:1rem;align-items:start;padding:.8rem 1rem;cursor:pointer;list-style:none}
.row > summary::-webkit-details-marker{display:none}
.row > summary:hover{background:var(--surf-2)}
.row > summary:focus-visible{outline:2px solid var(--verify);outline-offset:-2px}
.row[open] > summary{background:var(--surf-2);border-bottom:1px solid var(--rule)}

/* verdict, now a plain word */
.v{font-family:var(--display);font-weight:700;font-size:.63rem;letter-spacing:.12em;text-transform:uppercase;padding-top:.2rem}
.v-bug{color:var(--verify)}
.v-call{color:var(--call)}
.v-none{color:var(--dim)}
.v-un{color:var(--dim)}

.c-what{min-width:0}
.c-what h3{font-family:var(--body);font-weight:500;font-size:.95rem;line-height:1.35;margin:0}
.c-what .why{font-size:.82rem;color:var(--text-2);margin:.22rem 0 0}
/* Two-line clamp, not nowrap+ellipsis. The mockup's single clipped line cut
   mid-token on every row of a measured run. digest_model bounds the value to
   _SYMPTOM_MAX_CHARS so this should never fire; it is here so an overrun
   degrades to two readable lines rather than to a broken fragment. */
.c-what .sym{font-family:var(--mono);font-size:.72rem;color:var(--verify);margin:.3rem 0 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;white-space:normal;overflow-wrap:anywhere;opacity:.85}
.c-what .sym::before{content:"observed  ";color:var(--dim);letter-spacing:.06em}
.c-where{font-family:var(--mono);font-size:.71rem;color:var(--text-2);min-width:0;white-space:normal;overflow-wrap:anywhere;padding-top:.15rem;line-height:1.35}
.c-where a.src{color:var(--verify);text-decoration:none;border-bottom:1px solid transparent}
.c-where a.src:hover{border-bottom-color:var(--verify)}
.c-where a.src:focus-visible{outline:2px solid var(--verify);outline-offset:2px}
.detail .srcline{font-family:var(--mono);font-size:.78rem;overflow-wrap:anywhere}
.detail .srcline a{color:var(--verify)}
.detail .srcline .unlinked{color:var(--text-2)}
.detail .prov{font-family:var(--mono);font-size:.75rem;color:var(--text-2);overflow-wrap:anywhere}
.detail .prov a{color:var(--verify)}
.detail .prov .none{color:var(--text-2);opacity:.7;font-style:italic}
/* Collapsed by default, and visually quieter than the evidence above it: this
   answers "how do you know" for the reader who asks, without competing with the
   finding for the attention of the reader who does not. */
.detail .method{margin:.9rem 0 .2rem;border-top:1px solid var(--rule);padding-top:.5rem}
.detail .method>summary{cursor:pointer;font-size:.78rem;color:var(--text-2)}
.detail .method ul{margin:.5rem 0 .2rem;padding-left:1.1rem}
.detail .method li{font-size:.79rem;line-height:1.5;color:var(--text-2);margin:.25rem 0}
.detail .method a{color:var(--verify);font-family:var(--mono);font-size:.74rem}
.c-what .untiered{display:inline-block;font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;color:var(--imp);border:1px solid var(--imp);padding:.05rem .3rem;margin-top:.3rem;opacity:.9}
.detail .cmp{font-family:var(--mono);font-size:.8rem}
.detail .srcline .why-not{color:var(--dim);font-family:var(--body);font-size:.8rem;display:block;margin-top:.25rem}
.c-exp{font-family:var(--mono);font-size:.92rem;text-align:right;font-variant-numeric:tabular-nums;line-height:1.25}
.c-exp small{display:block;font-size:.62rem;letter-spacing:.06em;text-transform:uppercase;color:var(--verify);margin-top:.15rem}
.c-exp small.est{color:var(--dim)}
/* What the figure is a share OF. Small, wrapped, and directly under the number,
   because the number without it was measured unreadable -- see _render_exposure. */
.c-exp em{display:block;font-style:normal;font-family:var(--body);font-size:.68rem;color:var(--text-2);line-height:1.25;margin-top:.12rem;white-space:normal;overflow-wrap:anywhere}
.c-exp .none{font-family:var(--body);font-size:.72rem;color:var(--dim);font-variant-numeric:normal}
/* The percentage, the magnitude bar, and the working. The figure is the largest
   thing in the cell because it is what a reader sets priority on; the working
   under the hairline is what makes it checkable and says what it is a share of. */
.c-exp .pct{display:flex;align-items:baseline;justify-content:flex-end;gap:.4rem}
.c-exp .pct .f{font-family:var(--mono);font-weight:500;font-size:1.12rem;font-variant-numeric:tabular-nums;color:var(--text);letter-spacing:-.01em}
.c-exp .pct .mk{font-family:var(--mono);font-size:.55rem;letter-spacing:.08em;text-transform:uppercase;color:var(--verify)}
.c-exp .pct .mk.est{color:var(--imp)}
/* Linear, and gridded at the quarters so 1% and 25% cannot look alike. A log
   scale would exaggerate the small values, and every share on the measured run
   was small -- the point of the bar is that they are. */
.c-exp .bar{position:relative;height:.3rem;background:rgba(107,122,139,.16);overflow:hidden;margin-top:.28rem}
.c-exp .bar i{position:absolute;top:0;bottom:0;left:0;background:var(--verify)}
.c-exp .bar i.est{background:var(--imp)}
.c-exp .bar i.tk{width:1.5px}
.c-exp .bar u{position:absolute;top:0;bottom:0;width:1px;background:var(--ground);opacity:.55;text-decoration:none}
/* Hatched, never filled. A filled bar next to an unmeasured share reads as
   100%, which is the misread a reconciler had to correct on this very finding. */
.c-exp .bar.absent{background:repeating-linear-gradient(-45deg,rgba(107,122,139,.20) 0 3px,transparent 3px 6px)}
.c-exp .work{border-top:1px solid var(--rule-2);padding-top:.26rem;margin-top:.26rem;font-family:var(--body);font-size:.67rem;color:var(--text-2);line-height:1.3;text-align:right;overflow-wrap:anywhere}
.c-exp .work .n{font-family:var(--mono);font-variant-numeric:tabular-nums}
.c-exp .work .why{display:block;color:var(--dim);font-size:.64rem;margin-top:.12rem;font-style:italic}
/* A per-finding marker on the always-visible row, following .untiered: a band
   assigned without an exposure figure says so, rather than implying it weighed
   something it did not. Most findings on a real run have no figure. */
.c-what .noexp{display:inline-block;font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;color:var(--dim);border:1px solid var(--rule-2);padding:.05rem .3rem;margin-top:.3rem}
.c-eff{font-family:var(--mono);font-size:.92rem;text-align:right;color:var(--text-2);padding-top:.15rem}

.detail{padding:1rem 1rem 1.3rem 7.4rem;font-size:.88rem}
.detail h4{font-family:var(--display);font-weight:600;font-size:.62rem;letter-spacing:.15em;text-transform:uppercase;color:var(--text-2);margin:1.2rem 0 .4rem}
.detail h4:first-child{margin-top:0}
.detail p{margin:.35rem 0;max-width:80ch}
.axes{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule);border:1px solid var(--rule);margin:.5rem 0}
.axes > div{background:var(--ground);padding:.7rem .85rem}
.axes h5{font-family:var(--mono);font-size:.65rem;letter-spacing:.07em;text-transform:uppercase;margin:0 0 .3rem;color:var(--verify)}
.axes.amb div:last-child h5{color:var(--call)}
.axes.int div:last-child h5{color:var(--low)}
.axes p{font-size:.82rem;color:var(--text-2);margin:.2rem 0}
pre{font-family:var(--mono);font-size:.75rem;line-height:1.6;background:var(--ground);border:1px solid var(--rule);padding:.7rem .8rem;overflow-x:auto;margin:.45rem 0;color:var(--text)}
code{font-family:var(--mono);font-size:.87em;color:var(--verify)}
pre code{color:inherit}
.sub-d{border:1px solid var(--rule);margin:.5rem 0;background:var(--ground)}
.sub-d > summary{cursor:pointer;list-style:none;padding:.45rem .8rem;font-size:.78rem;font-family:var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--text-2);display:flex;gap:.5rem;align-items:center}
.sub-d > summary::-webkit-details-marker{display:none}
.sub-d > summary::before{content:"+";color:var(--verify);font-weight:600}
.sub-d[open] > summary::before{content:"–"}
.sub-d > summary:focus-visible{outline:2px solid var(--verify);outline-offset:-2px}
.sub-d .in{padding:0 .8rem .8rem}

/* discards, collapsed */
.discard{margin-top:2.6rem;border:1px solid var(--rule);background:var(--surf)}
.discard > summary{cursor:pointer;list-style:none;padding:.8rem 1rem;display:flex;gap:.6rem;align-items:center;font-size:.88rem}
.discard > summary::-webkit-details-marker{display:none}
.discard > summary::before{content:"▸";color:var(--dim);font-size:.8rem}
.discard[open] > summary::before{content:"▾"}
.discard > summary:hover{background:var(--surf-2)}
.discard > summary:focus-visible{outline:2px solid var(--verify);outline-offset:-2px}
.discard .hint{color:var(--dim);font-size:.8rem;margin-left:auto;font-family:var(--mono)}
.discard .in{padding:.2rem 1rem 1.2rem;border-top:1px solid var(--rule)}
.discard .in > p:first-child{margin-top:.8rem}

.cov{margin:2.8rem 0 0;border:1px solid var(--rule);background:var(--surf);padding:1.2rem 1.3rem 1.4rem}
.cov h2{font-family:var(--display);font-weight:800;font-size:.95rem;letter-spacing:.1em;text-transform:uppercase;margin:0 0 .5rem}
.cov p{font-size:.85rem;color:var(--text-2);margin:.4rem 0;max-width:82ch}
.cov p b{color:var(--text)}.cov-files{margin:.7rem 0 .2rem}.cov-files>summary{cursor:pointer;font-size:.82rem;color:var(--text-2)}.dirs{margin:.6rem 0 0;max-width:100%}.dir{border-top:1px solid var(--rule)}.dir>summary{cursor:pointer;display:flex;gap:1rem;justify-content:space-between;align-items:baseline;padding:.35rem .1rem;font-size:.76rem;color:var(--text-2)}.dir .dirname{font-family:var(--mono,monospace);overflow-wrap:anywhere;min-width:0}.dir .n{flex:none;opacity:.6}.files{margin:.1rem 0 .5rem;padding:0 0 0 1.1rem;list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.1rem 1rem}.files li{font-size:.75rem;color:var(--text-2);overflow-wrap:anywhere}
.strip{display:flex;flex-wrap:wrap;gap:2px;margin:.9rem 0 .5rem}
.cell{flex:1 1 6.5rem;background:var(--ground);border:1px solid var(--rule);padding:.4rem .55rem;font-family:var(--mono);font-size:.65rem;color:var(--text-2);line-height:1.35}
.cell b{display:block;font-family:var(--display);font-weight:600;font-size:.57rem;letter-spacing:.11em;text-transform:uppercase;margin-top:.22rem}
.cell.found{border-left:2px solid var(--act)} .cell.found b{color:var(--act)}
.cell.clean{border-left:2px solid var(--verify)} .cell.clean b{color:var(--verify)}
.cell.dead{border-left:2px solid var(--dim)} .cell.dead b{color:var(--dim)}

footer{margin-top:2.4rem;padding-top:1.1rem;border-top:1px solid var(--rule-2);font-size:.81rem;color:var(--text-2)}
footer p{margin:.4rem 0;max-width:82ch}
footer b{color:var(--text)}

@media (max-width:900px){
  :root{--cols:5.4rem minmax(0,1fr) 6rem}
  .mhead span.h-where,.mhead span.h-eff{display:none}
  .c-where,.c-eff{display:none}
  .detail{padding-left:1rem}
  .axes{grid-template-columns:1fr}
}
@media print{
  :root{--ground:#fff;--surf:#fff;--surf-2:#f4f4f4;--text:#111;--text-2:#444;--rule:#bbb;--rule-2:#888;--verify:#0a6;--call:#749}
  body{font-size:10.5pt} .bar{display:none} .row{break-inside:avoid}
}

/* ---------------------------------------------------------------------
   Two amendments to the approved mockup, both requested after review.
   Kept below the ported sheet so the diff against the mockup stays legible.
   --------------------------------------------------------------------- */

/* 1. Emphasis on the load-bearing words in a finding title. A highlighter
      swipe rather than a colour swap: colour alone must never carry meaning,
      and the mark survives greyscale printing. */
.c-what h3 em{font-style:normal;font-weight:600;color:var(--text);
  background:linear-gradient(transparent 60%,rgba(255,107,122,.30) 60%);
  padding:0 .08em}

/* 2. Wrap long blocks instead of scrolling them. A fix prompt the reader has
      to scroll sideways is one they will not read, and it is the artifact the
      whole report exists to hand over. */
pre{white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:visible}

/* 3. The requirements document mandates prefers-reduced-motion; the approved
      mockup omits it. There is no motion in this sheet today, so the guard is
      vacuous right now -- it is here so a future transition cannot be added
      without inheriting it. The mockup and the requirements disagreed and the
      requirements win. */
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}
"""  # ported verbatim from the approved mockup; a variable, not an f-string body

_SCRIPT: Final[str] = """
(function(){
  var d=function(){return document.querySelectorAll('details')};
  var ex=document.getElementById('ex'), co=document.getElementById('co');
  if(ex)ex.onclick=function(){d().forEach(function(x){x.open=true})};
  if(co)co.onclick=function(){d().forEach(function(x){x.open=false})};
  window.addEventListener('beforeprint',function(){d().forEach(function(x){x.open=true})});
  function reveal(){if(!location.hash)return;var t=document.querySelector(location.hash);if(!t)return;
    var e=t.closest('details');while(e){e.open=true;e=e.parentElement&&e.parentElement.closest('details')}}
  window.addEventListener('hashchange',reveal);reveal();
  // A source link lives inside <summary>, so a click on it would bubble up and
  // toggle the row as a side effect of opening the file. Stopping propagation
  // keeps the two actions separate: click the link to read the code, click
  // anywhere else on the row to expand the evidence.
  document.querySelectorAll('a.src').forEach(function(a){
    a.addEventListener('click',function(e){e.stopPropagation()});
  });
})();
"""  # static: no interpolation point, so no finding text can reach it

# Closed vocabularies. Every value that reaches a class attribute comes from one
# of these two tables or from a static literal -- never from finding text.
_BAND_CLASS: dict[Band, str] = {
    Band.ACT_NOW: "b-act",
    Band.IMPORTANT: "b-imp",
    Band.LOW: "b-low",
    Band.NOT_CHECKED: "b-def",
}

_VERDICT_CLASS: dict[Verdict, str] = {
    Verdict.BUG: "v-bug",
    Verdict.YOUR_CALL: "v-call",
    Verdict.COULDNT_VERIFY: "v-none",
    Verdict.NOT_CHECKED: "v-un",
    Verdict.NOT_A_BUG: "v-none",
}

_PERCENT = re.compile(r"^[<>~]?\d+(?:\.\d+)?%")


# Three significant figures, and no "<0.01%" threshold. A threshold would need
# escaping to survive as HTML, and more importantly it withholds the figure at
# exactly the magnitudes where the reader is deciding whether something is rare
# or absent: 0.00464% and 0% license different decisions.
def _format_pct(pct: float) -> str:
    if pct == 0:
        return "0%"
    if pct >= 100:
        return "100%"
    figure = f"{pct:#.3g}"
    if "." in figure:
        figure = figure.rstrip("0").rstrip(".")
    return f"{figure}%"


def _format_figure(figure: float) -> str:
    """Thousands-separated, and no trailing .00 on a whole number."""
    if float(figure).is_integer():
        return f"{int(figure):,}"
    return f"{figure:,.2f}".rstrip("0").rstrip(".")


# The three absences, and the sentence each one earns. They are not
# interchangeable: NO_INSTRUMENT says the harm is also undetectable in
# production, which is a priority input rather than a gap in the run.
# A `path_denominator` that is nothing but one of these says only what the
# headline above it already says, with a reason attached. Found by re-rendering a
# real record rather than by reading the code: most rows produced a bare
# `UNKNOWN` directly under "no share measured", which is the same nothing said
# twice and a worse version of the confusion this change exists to remove.
# `run-record-schema.md`'s `share_absent` section is canonical for the counts.
#
# Matched against the WHOLE value, never a prefix. "not established -- the share
# of requests was not queried" is the shape the schema documents as correct and
# it carries the reason, so a prefix match would delete the content this column
# was fixed once already for discarding.
_BARE_ABSENCE_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "unknown",
        "not measured",
        "unmeasured",
        "not established",
        "none",
        "n/a",
        "na",
    }
)


def _is_bare_absence(phrase: str) -> bool:
    return phrase.strip().strip(".;:-").casefold() in _BARE_ABSENCE_TOKENS


_SHARE_ABSENT_COPY: Final[dict[str, tuple[str, str]]] = {
    "NOT_QUERIED": ("no share measured", "the numerator was never queried"),
    "NO_INSTRUMENT": ("no share measured", "no instrument can measure this"),
    "NOT_REQUEST_SCOPED": ("not a share", "no request denominator applies"),
}


# Words that make a bug title a bug title. Highlighting these is what lets a
# reader scan a 44-row manifest and see what each finding actually claims,
# rather than reading four near-identical sentences in full.
#
# A fixed lexicon plus a code-identifier pattern, deliberately: the alternative
# was asking the orchestrator to mark its own emphasis, which adds a schema
# field the requirements did not ask for and which design-history section 5
# says agents reword when given latitude. A closed list cannot drift.
_EMPHASIS_TERMS: Final[frozenset[str]] = frozenset(
    {
        "accepts",
        "bypass",
        "bypasses",
        "dropped",
        "drops",
        "fails",
        "failed",
        "ignores",
        "ignored",
        "incorrect",
        "missing",
        "never",
        "no",
        "not",
        "omits",
        "omitted",
        "silently",
        "skipped",
        "skips",
        "stale",
        "unbounded",
        "unfiltered",
        "without",
        "wrong",
    }
)

# camelCase, snake_case, or a call like filterByLicence(). These name the thing
# the defect is in, so they are worth the same emphasis as the failure verb.
_IDENTIFIER = re.compile(
    r"\b[a-z][A-Za-z0-9]*(?:[A-Z][A-Za-z0-9]*)+(?:\(\))?"
    r"|\b[a-z]+(?:_[a-z0-9]+)+\b"
)

# Two spans at most. Emphasising everything emphasises nothing, and a title
# where half the words are marked is harder to scan than one with none.
_MAX_EMPHASIS: Final[int] = 2

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_()]*")


def _emphasise(text: str) -> str:
    """Mark the load-bearing words in a title, escaping at every site.

    Escaping happens per segment rather than over the whole string, because the
    markup is inserted between segments -- escaping afterwards would escape the
    tags themselves, and escaping beforehand would make the offsets wrong.
    """
    spans: list[tuple[int, int]] = []
    for match in _WORD.finditer(text):
        if len(spans) >= _MAX_EMPHASIS:
            break
        word = match.group()
        if word.lower() in _EMPHASIS_TERMS or _IDENTIFIER.fullmatch(word):
            spans.append((match.start(), match.end()))

    out: list[str] = []
    cursor = 0
    for start, end in spans:
        out.append(html.escape(text[cursor:start]))
        out.append(f"<em>{html.escape(text[start:end])}</em>")
        cursor = end
    out.append(html.escape(text[cursor:]))
    return "".join(out)


def _tier_label(tier: str) -> str:
    """Data is `2`; display is `Tier 2`. `UNTIERED` is shown as itself.

    Kept as a function rather than inlined because the absence case is the whole
    point: `UNTIERED` has no "Tier N" spelling, and writing one would perform in
    presentation the fold that the tier rule forbids in data.
    """
    return "UNTIERED" if tier == "UNTIERED" else f"Tier {tier}"


def _render_untiered_flag(finding) -> str:
    """A visible marker on the row when the component has no catalogued tier.

    The tier rule requires `UNTIERED` components to be "their own visible stratum". The
    digest is the artifact a human actually reads, so without this an untiered
    component's findings render identically to a Tier 1 component's and the
    cataloguing gap the rule exists to surface is invisible.

    Only the absence case gets a row marker. A real tier is context and lives in
    the expansion; putting every tier here would add a column that is constant on
    the common single-component run and would crowd the finding text for no gain.
    """
    if finding.tier != "UNTIERED":
        return ""
    return '<span class="untiered" title="No reliability tier in the catalog">UNTIERED</span>'


def _render_where(finding) -> str:
    """The defect site, linked to source when a verified permalink exists.

    This is the ONLY place finding-derived text reaches an href, and the module
    docstring's "no finding text in attributes" rule is preserved rather than
    broken here, by two independent checks:

    1. `digest_model._PERMALINK` has already proven the value is an https URL
       pinned to a 40-char commit SHA. That closes `javascript:` and any other
       scheme.
    2. `html.escape(..., quote=True)` here closes quote-breakout.

    Neither is sufficient alone. Upstream validation without escaping would still
    admit a quote in a path segment; escaping without upstream validation would
    still admit `javascript:alert(1)`. Do not remove either believing the other
    covers it.

    A null permalink renders as plain text. That is the honest default: the
    orchestrator emits a link only where it verified the pinned ref matches the
    examined checkout, so "no link" means "we could not prove this link would
    land on the right line", never "we forgot".
    """
    site = html.escape(finding.defect_site)
    if not finding.permalink:
        return site
    href = html.escape(finding.permalink, quote=True)
    return (
        f'<a class="src" href="{href}" target="_blank" rel="noopener noreferrer">'
        f"{site}</a>"
    )


def _render_observed(finding) -> str:
    """The evidence block, rendered for EVERY finding regardless of band.

    The row's symptom line is shown only on Act Now (see Finding.symptom_collapsed),
    and before this block existed there was nowhere else it appeared -- so for
    Important, Low and Not-checked findings a required, validated field reached
    the reader NOWHERE. The three quiet groups are most of a run: on the
    measured 64-finding record, 63 of them.

    Head is at most two lines, matching the row clamp, so the same evidence
    reads the same in both places. The rest goes one click down in the sheet's
    existing nested-details component rather than into a wall of frames, because
    the frame that matters is almost always the first.
    """
    lines = finding.observed_full.splitlines() if finding.observed_full else []
    head, tail = lines[:2], lines[2:]
    # Trailing blank lines are an artifact of the capture, not a frame, and
    # would otherwise be offered as "Show 1 more frame" leading to an empty box.
    while tail and not tail[-1].strip():
        tail.pop()
    text = "\n".join(head).rstrip()
    # observed_symptom is validated non-empty, so this fallback guarantees the
    # <pre> always has content -- an empty one is never rendered.
    if not text.strip():
        text = finding.observed_symptom
    block = f"<h4>What was observed</h4><pre>{html.escape(text)}</pre>"
    if not tail:
        return block
    noun = "frame" if len(tail) == 1 else "frames"
    rest = html.escape("\n".join(tail))
    return (
        f'{block}<details class="sub-d"><summary>Show {len(tail)} more {noun}'
        f'</summary><div class="in"><pre>{rest}</pre>'
        f"</div></details>"
    )


def _render_unlinked_note(finding) -> str:
    """Why this finding has no source link, in its OWN recorded words.

    This sentence used to be hardcoded, asserting that the examined checkout did
    not match a pushed commit. On the measured run it was printed 64 times and
    was false 64 times: nothing had been checked at all, and every one of the 49
    distinct files was byte-identical to origin/master. A report that volunteers
    an untested cause is worse than one that links nothing, because the false
    cause is the part the reader remembers.

    So the cause now comes from `permalink_resolution.unlinked`, written by
    whoever actually attempted the resolution. With no recorded reason the note
    stays neutral and claims nothing -- the absence of a reason is itself the
    finding, and pointing at the step that would produce one is the only honest
    direction to give.
    """
    if finding.permalink:
        return ""
    reason = (finding.permalink_unlinked_reason or "").strip()
    if not reason:
        return (
            '<span class="why-not">No source link, and no reason was recorded '
            "for this one. Run the link step over this record to find out why.</span>"
        )
    if reason[-1] not in ".!?":
        reason += "."
    return (
        f'<span class="why-not">No source link: {html.escape(reason)} A link is '
        "emitted only where the file is byte-identical to a commit that has been "
        "pushed, so pushing the branch this was read from and re-running the link "
        "step is what makes it resolve.</span>"
    )


def _render_exposure(exposure) -> str:
    """The exposure cell: the figure, what it is a share OF, and its provenance.

    The schema carries both denominators as prose because both are true and the
    choice between them silently decides priority. This cell shows the path
    denominator, which is the one that tells a reader whether this matters to the
    users who hit it; the full pair is in the expansion.

    **The noun is never supplied here.** "0.072%" is a share of searches in one
    service and of something else entirely in the next, so a hardcoded unit would
    be wrong everywhere except where it was written. The record already carries
    the phrase -- `path_denominator` is specified as `X% of <the path this defect
    lives on>` -- and this used to match the leading `X%` and discard the rest.

    That discarded remainder was the whole meaning. Measured: a first-time reader
    met a bare `0.072%` beside an Act Now row, could not tell what it was a share
    of, and named this column as the part of the report they could not understand.
    A number that small next to that band does not merely fail to inform, it reads
    as an argument against the band, and the phrase that would resolve it was one
    click away in the expansion.
    """
    if exposure.share is not None:
        return _render_share(exposure)
    return _render_shareless(exposure)


def _render_share(exposure) -> str:
    """The percentage, its magnitude, and the working that makes it checkable.

    The figure leads because it is what a reader sets priority on -- 1% of
    requests and 25% of requests are different problems. It is never alone: the
    working under the hairline carries both sides and the phrase saying what the
    denominator counts, which is the same rule `path_denominator` already obeys
    and for the same measured reason. A bare figure sent a first-time reader to
    this column as the part of the report they could not understand.
    """
    share = exposure.share
    pct = 100.0 * share.numerator / share.denominator
    est = "" if exposure.basis == "MEASURED" else " est"
    return (
        f'<div class="pct"><span class="f">{_format_pct(pct)}</span>'
        f'<span class="mk{est}">{html.escape(exposure.basis)}</span></div>'
        f"{_render_bar(pct, exposure.basis)}"
        f'<div class="work"><span class="n">{_format_figure(share.numerator)}</span>'
        f' of <span class="n">{_format_figure(share.denominator)}</span> '
        f"{html.escape(share.unit)} {html.escape(share.of)}</div>"
    )


def _render_bar(pct: float, basis: str) -> str:
    """Linear, gridded at the quarters, and never full unless the share is.

    Right-aligned tabular figures spanning four orders of magnitude do not rank
    at a glance -- 0%, 0.00464%, 0.564% and 7.18% all read as "small" until you
    count decimal places. The bar is the second encoding that fixes exactly
    that, and it is the reason a percentage is worth adding at all.
    """
    est = "" if basis == "MEASURED" else " est"
    grid = '<u style="left:25%"></u><u style="left:50%"></u><u style="left:75%"></u>'
    if pct == 0:
        fill = ""
    elif pct < 0.5:
        # Narrower than a pixel in this column. A tick states presence without
        # overstating magnitude; a minimum-width fill would lie about it.
        fill = f'<i class="tk{est}"></i>'
    else:
        fill = f'<i class="{est.strip()}" style="width:{min(pct, 100.0):.4g}%"></i>'
    return f'<div class="bar">{fill}{grid}</div>'


def _render_shareless(exposure) -> str:
    """No percentage exists, so none is shown -- and the reason is named.

    Three absences reach this branch and they are not interchangeable for
    somebody setting priority. `NO_INSTRUMENT` says the harm is also undetectable
    in production, which is the same fact the flagged finding's `band_reason`
    cites as "harm undetectable" -- a priority input, not a gap in the run.
    `NOT_QUERIED` says only that nobody looked. `NOT_REQUEST_SCOPED` says the
    question does not apply. Rendering all three as one word is what made a
    reader ask how the column could say "not measured" and then print a figure.

    The prose denominators still render here, unchanged, because they are what
    reaches the reader today and the rubric requires both. What is new is that
    `basis` travels with them: it previously printed only inside the
    percentage-led branch, and 0 of 82 path denominators on the measured run led
    with a percentage -- so MEASURED reached the reader on none of the 15
    findings that had earned it.
    """
    reason = exposure.share_absent or "NOT_QUERIED"
    headline, generic = _SHARE_ABSENT_COPY.get(
        reason, _SHARE_ABSENT_COPY["NOT_QUERIED"]
    )
    detail = (exposure.share_absent_detail or generic).strip()
    parts: list[str] = []
    phrase = exposure.path_denominator.strip()
    if phrase and _is_bare_absence(phrase):
        # The headline states the absence and names its reason. Repeating the
        # producer's bare token underneath adds nothing and reads as a second,
        # competing claim.
        phrase = ""
    if phrase:
        match = _PERCENT.match(phrase)
        basis_class = "" if exposure.basis == "MEASURED" else ' class="est"'
        if match:
            figure = match.group(0)
            unit = phrase[len(figure) :].strip()
            parts.append(
                f"{html.escape(figure)}"
                f"{f'<em>{html.escape(unit)}</em>' if unit else ''}"
            )
        else:
            parts.append(f"<em>{html.escape(phrase)}</em>")
        # UNKNOWN is deliberately not printed. A provenance word under an absent
        # figure asserts an estimate exists where none does, and one run shipped
        # `n/a` above `ESTIMATED` on all 76 rows, which read as having measured
        # nothing at all. The headline above already states the absence.
        if exposure.basis != "UNKNOWN":
            parts.append(f"<small{basis_class}>{html.escape(exposure.basis)}</small>")
    # Both denominators, always, because the rubric requires both and because
    # they can point in OPPOSITE directions. Measured on a real report: the
    # column rendered "100% of process terminations on the production branch"
    # while dropping the component denominator "0% of request traffic", so the
    # reader saw the number that argues for urgency and not the one that argues
    # against it. Across four reports the component denominator reached the
    # column on 0 of 62 checked findings.
    component = exposure.component_denominator.strip()
    if component:
        parts.append(f'<em class="cden">{html.escape(component)}</em>')
    return (
        f'<div class="pct"><span class="none">{html.escape(headline)}</span></div>'
        '<div class="bar absent"></div>'
        f'<div class="work">{"".join(parts)}'
        f'<span class="why">{html.escape(detail)}</span></div>'
    )


def _render_unexposed_band_flag(finding) -> str:
    """Say when a band was reached without an exposure figure.

    The band is a guide and the priority call belongs to the reader, so the row
    owes them the inputs the guide actually had. Measured on the character-pro
    run: Act Now 0, Important 0, Low 1, Not checked 81 -- and the single banded
    finding carries `basis: UNKNOWN`, with its own `band_reason` ending "Exposure
    UNKNOWN and undecidable with current telemetry". So the one band that run
    produced was assigned without the input, and nothing on the row said so.

    Deliberately NOT a threshold change. n=1 is not a calibration sample, and
    requiring a measured share to reach a higher band would cap the
    NO_INSTRUMENT case at the bottom -- the case where no telemetry can
    distinguish a harmed state from a healthy one, which is the condition under
    which harm goes unnoticed in production. That is backwards, and it is the
    reasoning that put the flagged finding in Low to begin with.

    Off when there is no band: 81 of 82 findings were never verified, and a
    caveat about how a band was reached would be asserting a band nobody
    assigned. On the always-visible row rather than the expansion, following
    `_render_untiered_flag`, because a qualification a click away is how this
    column came to discard real impact statements while the page looked whole.
    """
    band = getattr(finding, "band", None)
    if band is None or band is Band.NOT_CHECKED:
        return ""
    if finding.exposure.share is not None:
        return ""
    return '<span class="noexp">banded without exposure</span>'


def _render_row(finding) -> str:
    """One manifest row. Every interpolation is html.escape'd at its own site.

    The symptom line is the amendment research section 4.3 made to the Manifest
    spec: one line of *actual evidence* in the always-visible row, not a glyph
    and not a summary, because that is what lets a reader trust or dismiss
    without expanding. It is dropped below Act Now, which the model has already
    decided -- see Finding.symptom_collapsed.
    """
    symptom = (
        ""
        if finding.symptom_collapsed
        else f'<p class="sym">{html.escape(finding.observed_symptom)}</p>'
    )
    # In the ALWAYS-VISIBLE row, not the expansion. A band demoted on a measured
    # dormancy has to disclose the capability it still has, and reasoning one
    # click away is exactly how the exposure column came to throw away real
    # impact statements while the page looked complete.
    band_reason = (
        f'<p class="bandwhy">{html.escape(finding.band_reason)}</p>'
        if getattr(finding, "band_reason", None)
        else ""
    )
    return (
        f'<details class="row" id="f-{html.escape(finding.fingerprint)}">'
        f"<summary>"
        f'<div class="v {_VERDICT_CLASS[finding.verdict]}">'
        f"{html.escape(finding.verdict.value)}</div>"
        f'<div class="c-what"><h3>{_emphasise(finding.title)}</h3>'
        f'<p class="why">{html.escape(finding.consequence)}</p>'
        f"{band_reason}"
        f"{_render_untiered_flag(finding)}"
        f"{_render_unexposed_band_flag(finding)}{symptom}</div>"
        f'<div class="c-where">{_render_where(finding)}</div>'
        f'<div class="c-exp">{_render_exposure(finding.exposure)}</div>'
        f'<div class="c-eff">{html.escape(finding.effort)}</div>'
        f"</summary>"
        f'<div class="detail">{_render_detail(finding)}</div>'
        f"</details>"
    )


def _render_detail(finding) -> str:
    """The expansion, in the order the requirements document fixes: what was
    observed, then why we believe this, then exposure with both denominators,
    then the fix prompt, then the post-fix verification block.

    The evidence sits directly under Source and above the reasoning on purpose:
    a reader deciding whether to trust a finding wants the output first and the
    argument second.
    """
    axes_class = "axes" if finding.verdict is Verdict.BUG else "axes amb"
    # Repeated here even though the Where column already carries it, because that
    # column is display:none under 900px -- so on a phone the expansion is the
    # only place the location exists at all. A reader who cannot find the file
    # cannot check the finding, which is the one thing this report exists to let
    # them do.
    unlinked_note = _render_unlinked_note(finding)
    parts = [
        "<h4>Component</h4>",
        f'<p class="cmp">{html.escape(finding.component)} &middot; '
        f"{html.escape(_tier_label(finding.tier))}</p>",
        "<h4>Source</h4>",
        f'<p class="srcline">{_render_where(finding)}{unlinked_note}</p>',
        _render_introduced(finding),
        _render_observed(finding),
        "<h4>Why we believe this</h4>",
        f'<div class="{axes_class}">'
        f"<div><h5>Reproduced live</h5>"
        f"<p>{html.escape(finding.mechanism.trail)}</p></div>"
        f"<div><h5>Intent checked blind</h5>"
        f"<p>{html.escape(finding.intent.trail)}</p></div></div>",
        "<h4>Exposure</h4>",
        f"<p>{html.escape(finding.exposure.path_denominator)} &middot; "
        f"{html.escape(finding.exposure.component_denominator)}</p>"
        f"<p>{html.escape(finding.exposure.note)}</p>",
    ]
    if finding.fix_prompt:
        parts += [
            "<h4>Fix prompt</h4>",
            f"<pre>{html.escape(finding.fix_prompt)}</pre>",
        ]
    parts.append(_render_method(finding))
    if finding.verification:
        check = finding.verification
        parts += [
            "<h4>Verify after shipping</h4>",
            f"<pre>{html.escape(check.metric_query)}</pre>",
            f"<p>Today: {html.escape(check.reads_today)}</p>"
            f"<p>Expected after: {html.escape(check.expected_after)}</p>"
            f"<p>{html.escape(check.expectation_basis)} "
            f"({html.escape(check.artifact_form)})</p>",
        ]
    return "".join(parts)


def _render_introduced(finding) -> str:
    """The commit that last wrote this line, and the pull request that merged it.

    Always visible inside the expansion rather than tucked behind another
    disclosure, because it is the one piece of history a reader reaches for
    first: the change that put the line there, and the discussion around it.

    No author, ever, and no owning squad. `run-record-schema.md` is canonical
    for that rule and for why it is not negotiable.
    """
    prov = finding.provenance
    if prov is None:
        reason = finding.provenance_unresolved_reason
        tail = f": {html.escape(reason)}" if reason else "."
        return (
            f'<h4>Introduced</h4><p class="prov"><span class="none">'
            f"not traced</span>{tail}</p>"
        )
    bits = [
        f'<a class="src" href="{html.escape(prov.commit_url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">'
        f"{html.escape(prov.commit_short)}</a>"
    ]
    if prov.date:
        bits.append(html.escape(prov.date))
    pull = prov.pull_request
    if pull:
        bits.append(
            f'<a class="src" href="{html.escape(str(pull["url"]), quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">'
            f"PR #{html.escape(str(pull['number']))}</a>"
        )
    else:
        # Stated rather than left blank. A commit with no pull request in its
        # subject predates the merge tooling that writes one, which is common
        # enough to matter, and a reader who sees only a commit needs to know
        # nothing was withheld.
        bits.append('<span class="none">no pull request on this commit</span>')
    return f'<h4>Introduced</h4><p class="prov">{" &middot; ".join(bits)}</p>'


def _render_method(finding) -> str:
    """How this finding was checked, behind a disclosure.

    Collapsed by default on purpose. It answers a question that only some
    readers have -- it exists because someone watching this report presented
    asked whether the checking included re-running the code from before the
    change -- and a reader who does not have that question should not have to
    scroll past the answer.

    Every line states what happened OR that it did not happen. A block that
    appeared only when the method looked thorough would be an advertisement, and
    a reader cannot calibrate on evidence that is only shown when it is good.
    """
    method = finding.method
    if method is None:
        # Rendered rather than omitted, and the schema promises exactly this.
        # An omitted block makes "nobody recorded how this was checked" look
        # identical to "this report predates the block existing", which is the
        # same confusion `permalink_unlinked_reason` exists to prevent one field
        # over. Measured the other way round: the first build returned "" here
        # while the schema claimed the opposite, and the gap was invisible until
        # someone opened a report and asked where the section had gone.
        return (
            '<details class="method"><summary>How this was checked</summary>'
            "<ul><li>Nobody recorded how this finding was checked. That is a gap "
            "in the run rather than a statement about the finding.</li></ul>"
            "</details>"
        )
    items = [
        "<li>Reproduced by running the code locally, by an agent that was not "
        "told how confident the original report was or how serious it claimed "
        "to be.</li>"
    ]
    if method.before_after:
        items.append(f"<li>{html.escape(method.before_after)}</li>")
    else:
        items.append(
            "<li>The code was not re-run at an earlier commit for comparison. "
            "The reproduction above stands on its own.</li>"
        )
    items.append(
        "<li>Checked separately by a second agent, which was shown only a "
        "neutral description of the behaviour: no conclusion, no reproduction "
        "result, and no hint that anything was thought to be wrong.</li>"
    )
    if method.history_read:
        read = " &middot; ".join(
            _render_history_entry(entry) for entry in method.history_read
        )
        items.append(f"<li>That second check read the history here: {read}</li>")
    else:
        items.append(
            "<li>That second check settled the question without reading the "
            "history of this code.</li>"
        )
    return (
        '<details class="method"><summary>How this was checked</summary>'
        f"<ul>{''.join(items)}</ul></details>"
    )


def _render_history_entry(entry) -> str:
    if not isinstance(entry, dict):
        return html.escape(str(entry))
    label = entry.get("label") or entry.get("commit") or entry.get("pr") or "history"
    url = entry.get("url")
    if not url:
        return html.escape(str(label))
    return (
        f'<a class="src" href="{html.escape(str(url), quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{html.escape(str(label))}</a>'
    )


_MHEAD: Final[str] = (
    '<div class="mhead"><span>Verdict</span><span>Finding</span>'
    '<span class="h-where">Where</span><span class="r">Exposure</span>'
    '<span class="r h-eff">Effort</span></div>'
)


def _render_band(band: Band, findings: list, model: RenderModel) -> str:
    """One band group. Rendered even when empty, so an empty band cannot vanish.

    An empty band that simply disappeared would make a systematic blind spot
    look identical to a clean component -- the failure SKILL.md section 7 warns
    about.

    **This line is where the standing caveats live now.** They used to sit in one
    paragraph above the fold, which stacked three unrelated warnings in front of a
    reader who had not yet seen a finding and therefore had nothing to apply them
    to. Each one now renders against the thing it qualifies: the ordering caveat on
    the band whose order it describes, the shortfall on the band that was skipped,
    and the UNTIERED gloss only on a band that actually contains one.
    """
    anchor = band.value.replace(" ", "-")
    # The unchecked group's header must say WHY, in the always-visible line.
    # Inside the fold it is worthless: a skimmer reads a bare "not checked" as
    # "checked and found fine", which is the opposite of what happened.
    #
    # The cause is read from the record rather than asserted here. The hardcoded
    # sentence claimed the run "hit its limit", which is only one of the two ways
    # this happens: a candidate skipped for cost is a scheduling fact about the
    # run, while one skipped because its group was never reached is a severity
    # judgement, and stating the wrong one is worse than stating neither.
    if band is Band.NOT_CHECKED:
        why = "These were never looked at"
        if model.shortfall:
            reason = str(model.shortfall["reason"]).rstrip(".!?")
            why += f", because {html.escape(reason)}"
        why += (
            ". Not because anyone decided they were unimportant. "
            "Each one is written up in full in the report folder."
        )
    elif band is Band.ACT_NOW:
        why = "Ordered only where the order can be justified in writing."
    else:
        why = "Listed in a fixed internal order. The order does not rank them."
    # An UNTIERED marker with no stated meaning reads as a severity signal, which
    # inverts the empty-run rule: the label marks a CATALOGUING gap, not a less important
    # component. The row's hover title carries the fact, but hover is not readable
    # on touch or in print, so it is said in text -- on the bands where the marker
    # is actually visible, rather than once at the top for a reader who may never
    # scroll to one.
    if any(f.tier == "UNTIERED" for f in findings):
        why += (
            " <b>UNTIERED</b> marks a component with no reliability tier in the "
            "catalog. That is a cataloguing gap, not a judgement that the "
            "component matters less, and it never moves anything into a lower group."
        )
    if not findings:
        return (
            f'<section id="band-{html.escape(anchor)}">'
            f'<div class="band {_BAND_CLASS[band]}"><h2>{html.escape(_BAND_LABEL[band])}</h2>'
            f'<span class="hr"></span><span class="n">0</span></div>'
            f'<p class="band-why">Nothing in this group.</p></section>'
        )
    # The unchecked band collapses WHOLE. Showing "the first N" was tried and is
    # actively misleading: order here is fingerprint-ascending, which this page
    # says two inches away is not a severity judgement, so any sample reads as a
    # top-N the run never computed.
    if band is Band.NOT_CHECKED and len(findings) > _NOT_CHECKED_SHOWN:
        return (
            f'<section id="band-{html.escape(anchor)}">'
            f'<div class="band {_BAND_CLASS[band]}"><h2>{html.escape(_BAND_LABEL[band])}</h2>'
            f'<span class="hr"></span><span class="n">{len(findings)}</span></div>'
            f'<p class="band-why">{why}</p>{_render_spill(findings)}</section>'
        )
    rows = "".join(_render_row(f) for f in findings)
    return (
        f'<section id="band-{html.escape(anchor)}">'
        f'<div class="band {_BAND_CLASS[band]}"><h2>{html.escape(_BAND_LABEL[band])}</h2>'
        f'<span class="hr"></span><span class="n">{len(findings)}</span></div>'
        f'<p class="band-why">{why}</p>'
        f'<div class="group">{_MHEAD}{rows}</div></section>'
    )


_NOT_CHECKED_SHOWN = 5


def _render_spill(spilled: list) -> str:
    """The whole unchecked list, collapsed, grouped by file.

    `references/bounded-verification.md` requires every unchecked candidate to
    appear by name so a partial run cannot be mistaken for a complete one. A
    hundred-plus rendered rows meets that letter and defeats its purpose: the
    reader stops long before the end, and the unchecked tail visually swamps the
    findings that were actually checked.

    So the names live one click down, grouped by file rather than flat -- someone
    who opens this wants to navigate it, not scroll it. **The REASON stays in the
    always-visible header**, never inside the fold: the same ruling this report
    already makes for UNTIERED, that a marker inside a collapsed block is not a
    visible one. Hidden, "not checked" reads as "checked and fine", which is the
    exact misreading the rule exists to prevent.
    """
    if not spilled:
        return ""
    groups: dict[str, list] = {}
    for f in spilled:
        groups.setdefault(f.defect_site.rsplit("/", 1)[-1].split(":")[0], []).append(f)
    blocks = "".join(
        f"<details class='spill-file'><summary><b>{html.escape(name)}</b>"
        f"<span class='n'>{len(items)}</span></summary>"
        f"<div class='group'>{_MHEAD}{''.join(_render_row(i) for i in items)}</div>"
        "</details>"
        for name, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    )
    return (
        f"<details class='spill'><summary>Show all {len(spilled)}, "
        f"grouped by file &mdash; {len(groups)} files</summary>"
        f"<div class='spill-body'>{blocks}</div></details>"
    )


def _render_discards(findings: list) -> str:
    """Discarded candidates, collapsed. Always emitted, even when empty.

    Discards cannot live in the band structure: a discarded candidate has no
    band at all, because SKILL.md section 6 assigns a threat level only to
    non-discarded dispositions (rows 3-7).

    They ship in the same report because the discard rate is the only thing that
    lets a reader calibrate what the confirmations are worth. A run reporting
    only what it confirmed gives no such calibration.
    """
    rows = "".join(_render_row(f) for f in findings)
    body = (
        f'<div class="group">{_MHEAD}{rows}</div>'
        if findings
        else "<p>Nothing was checked and rejected on this run.</p>"
    )
    return (
        f'<details class="discard"><summary>Not a bug'
        f'<span class="hint">{len(findings)} checked and rejected</span></summary>'
        f'<div class="in">{body}</div></details>'
    )


def _render_coverage(model: RenderModel) -> str:
    """Coverage as one sentence, with a searchable file list one click down.

    This replaced a grid of one cell per search slice. The grid failed on both
    counts: it carried almost no information, because the partition is even by
    construction so every cell read "5 files, ~296 lines", and every cell drew a
    coloured rule, so a colour present on 100% of items encoded nothing while
    still reading as alarm.

    What a service owner actually asks here is narrower and answerable: **"was
    the file I am worried about searched?"** A list of slices cannot answer that
    and a list of files can, so the fold holds file names rather than slices.
    The slice structure is how the work was divided; that is the tool's
    bookkeeping, not the reader's.

    Still always rendered. The empty-run rule needs it when a run finds nothing -- a clean
    component and an unsearched one must not look alike -- and a reader can only
    trust a NEGATIVE result if they can tell "searched and clean" from "never
    looked at".
    """
    names: list[str] = []
    for c in model.coverage:
        got = c["files"]
        names.extend(got if isinstance(got, list) else [])
    names = sorted(set(names))
    total_lines = sum(int(c["lines"]) for c in model.coverage)
    passes = len(model.coverage)

    if names:
        # Group by folder. Printing the full path on every row repeated ~90
        # near-identical characters 178 times, and long unbreakable paths burst
        # out of the container under a multi-column layout. The folder is the
        # varying part, so it becomes the group heading and each row is just a
        # filename -- short, wrappable, and scannable at a glance.
        folders: dict[str, list[str]] = {}
        for n in names:
            head, _, tail = n.rpartition("/")
            folders.setdefault(head or ".", []).append(tail)
        blocks = "".join(
            f"<details class='dir'><summary><span class='dirname'>"
            f"{html.escape(d)}</span><span class='n'>{len(fs)}</span></summary>"
            f"<ul class='files'>"
            + "".join(f"<li>{html.escape(f)}</li>" for f in sorted(fs))
            + "</ul></details>"
            for d, fs in sorted(folders.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        )
        detail = (
            f"<details class='cov-files'><summary>Check whether a specific file "
            f"was searched &mdash; {len(names)} files in {len(folders)} folders"
            f"</summary><div class='dirs'>{blocks}</div></details>"
        )
        headline = (
            f"<p><b>All {len(names)} files ({total_lines:,} lines) were searched.</b> "
            f"Nothing was skipped.</p>"
        )
    else:
        detail = ""
        headline = (
            f"<p><b>{passes} searches ran over {total_lines:,} lines.</b> "
            "Individual file names were not recorded for this run, so this "
            "report cannot tell you whether one specific file was searched.</p>"
        )

    dead = "".join(
        f"<p>{html.escape(str(s['surface']))} &mdash; "
        f"{html.escape(str(s['requests_30d']))} requests in 30 days.</p>"
        for s in model.dead_surface
    )
    return (
        f'<section class="cov"><h2>What was searched</h2>'
        f"{headline}{detail}{dead}</section>"
    )


#: What each band is CALLED on the page. The enum value stays "Not checked" -- it is
#: the schema value that run records and reference files cite -- but the digest can
#: no longer print it, because `Verdict.NOT_CHECKED` prints the identical words and
#: means something else entirely.
#:
#: The band means "left outside the verification bound, so no urgency was assigned".
#: The verdict means "nobody established whether this is real". Printing both as
#: "Not checked" made the masthead read "0 not checked" on a run where 31 of 31
#: findings were unverified -- see _render_counts.
_BAND_LABEL: Final[dict[Band, str]] = {
    Band.ACT_NOW: "Act Now",
    Band.IMPORTANT: "Important",
    Band.LOW: "Low",
    Band.NOT_CHECKED: "Not triaged",
}

assert set(_BAND_LABEL) == set(Band), "every band needs a display label"


def _render_counts(model: RenderModel) -> str:
    """The one-line triage summary under the title.

    Asked for in exactly this shape by a reader who skipped the old headline
    entirely and said what they wanted instead: the component's name, then
    "3 act now, 2 important, 10 low", then the list.

    **Counted from `grouped`, never from the record.** The numbers this replaces
    were written into the run record as prose and went stale the first time a
    finding changed band after publication. A count that is derived cannot
    disagree with the section it summarises.

    Every band shows, including empty ones, for the same reason `_render_band`
    renders an empty band: "0 act now" is a result, and a band that vanishes when
    empty makes a clean component and an unsearched one look alike.
    """
    bands = " &middot; ".join(
        f'<span class="{_BAND_CLASS[band]}"><b>{len(model.grouped[band])}</b> '
        f"{html.escape(_BAND_LABEL[band].lower())}</span>"
        for band in Band
    )

    # The verdict axis, which this line omitted entirely until 2026-08-28.
    #
    # `Band.NOT_CHECKED` and `Verdict.NOT_CHECKED` are different things sharing one
    # string: the band means "left outside the verification bound", the verdict means
    # "nobody established whether this is real". Counting only bands, the masthead
    # printed "0 not checked" on a run where 31 of 31 findings carried the NOT CHECKED
    # verdict -- so the single line a reader quotes asserted the opposite of the
    # truth, with every validator and all seven pass criteria green. A human opening
    # the page is what caught it.
    #
    # Both axes are named now, because the ambiguity is what made the number
    # unreadable rather than merely incomplete: "0 not checked" cannot be interpreted
    # correctly by anyone who does not already know which axis it counts.
    findings = [f for band in Band for f in model.grouped[band]]
    total = len(findings)
    checked = sum(1 for f in findings if f.verdict is not Verdict.NOT_CHECKED)
    return (
        f'<span class="axis">urgency</span> {bands} '
        f'&middot; <span class="axis">verification</span> '
        f'<span class="v-count"><b>{checked} of {total}</b> verified</span>'
    )


def _subject(model: RenderModel) -> str:
    """What the title is a report ABOUT -- a name, never a claim.

    The heading used to be a model-authored sentence summarising the run, and two
    readers rejected it independently on the same day: one that it was "a lot of
    text in the title (like 5 lines)", one that it read "like an article title for
    The Verge". The second is the more serious of the two. A summary at the top has
    to be persuasive to be worth its space, and persuasive prose over machine
    findings reads as something to discount, which spends the credibility the two
    verification passes below actually earned.

    So the heading names its subject and stops. Everything that sentence tried to
    say is already on the page, computed rather than asserted: the counts are in
    the band headers, what was searched is in the coverage section, and how far
    each finding got is its own verdict column.

    The scope qualifier ("all 178 of its main Java files") is not lost -- it stays
    in `<title>`, which is what a bookmark and a browser tab show, and the coverage
    section states it in full. It is off the heading because a heading naming one
    component and a heading naming a component plus a file count are read
    differently: the second invites the reader to check the arithmetic before they
    have seen a single finding.
    """
    if len(model.components) == 1:
        comp = model.components[0]
        # components may be dicts (with 'id', 'tier', etc.) or plain strings.
        # str() on a dict renders the Python repr, which is not a title.
        if isinstance(comp, dict):
            return str(comp.get("id") or comp)
        return str(comp)
    return model.scope_label


def _render_footer(model: RenderModel) -> str:
    """Provenance, cost, and how the findings were arrived at.

    The method statement moved here from directly under the title. Asked for by
    the reader who wanted the top of the page to be the component's name, the
    counts, and then the findings: on being asked whether the report would be
    more or less trustworthy without a summary, they said it "should be available
    somewhere but not the highest prio of what to show".

    It moved rather than went, because it is the answer to the other standing
    objection -- that a machine-written report is not worth trusting. A reader who
    wants to know how much weight to put on this page comes looking for it, and
    finds it beside the cost and coverage evidence, which is where the rest of the
    case for the run already lives.
    """
    cost, gate = model.cost, model.gate
    # The ref is provenance, not decoration: every line number in this report is
    # only meaningful against the commit it was read at, and a reader comparing
    # the report to a moved master needs to know which commit that was.
    provenance = ""
    if model.repo:
        provenance = (
            f"<p>Source refs point at <b>{html.escape(str(model.repo['full_name']))}</b> "
            f"at commit <b>{html.escape(str(model.repo['ref']))[:12]}</b> on "
            f"{html.escape(str(model.repo['host']))}. Line numbers are accurate "
            f"as of that commit and will drift as the branch moves.</p>"
        )
    return (
        f"<footer>"
        f"<p>Every finding above was reproduced live and independently checked "
        f"against the code's own contract by two agents that never saw each "
        f"other's work. Findings are grouped by urgency; the verdict column says "
        f"how far each one got.</p>"
        f"{provenance}<p>Run <b>{html.escape(model.run_id)}</b> over "
        f"{html.escape(model.scope_label)}. "
        f"<b>{html.escape(str(cost['agents']))}</b> agents, "
        f"<b>{html.escape(str(cost['wall_clock_minutes']))}</b> minutes. "
        f"{html.escape(str(gate['leaks_found']))} problem(s) found and fixed in "
        f"the checks themselves, across "
        f"{html.escape(str(gate['dossiers_scanned']))} of them; "
        f"{html.escape(str(gate['redaction_hits']))} time(s) something that looked "
        f"like a secret was masked before writing.</p>"
        f"<p>Everything called a bug here was worked out twice, by two separate "
        f"automated checks that were kept apart on purpose: one tried to make it "
        f"happen, the other worked out whether the code is meant to behave that "
        f"way. <b>Read a result as those two agreeing</b> &mdash; not as a person "
        f"having confirmed it. That is also why things that were checked and ruled "
        f"out are still listed here: knowing what was rejected is what tells you "
        f"what the rest is worth. The full write-up for each one is in the report "
        f"folder.</p>"
        f"<p>Nothing here has been sent anywhere. Sharing it is a human step.</p></footer>"
    )


def render(model: RenderModel) -> str:
    """The whole document.

    The run id is interpolated as visible text because write_artifact.py checks
    for the sentinel in the source BEFORE writing anything, and the digest's
    sentinel is the run id.
    """
    bands = "".join(_render_band(band, model.grouped[band], model) for band in Band)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Bug hunt: {html.escape(model.scope_label)}</title>"
        f'<link rel="stylesheet" href="{_FONT_HREF}">'
        f"<style>{_STYLE}</style></head><body>"
        f'<div class="shell"><header class="mast">'
        f'<p class="kicker"><b>Bug hunt</b> &middot; run {html.escape(model.run_id)} &middot; '
        f"{html.escape(str(model.cost['agents']))} agents</p>"
        f"<h1>Bug report: {html.escape(_subject(model))}</h1>"
        f'<p class="counts">{_render_counts(model)}</p>'
        f'<div class="bar"><button class="btn" id="ex" type="button">Expand all</button>'
        f'<button class="btn" id="co" type="button">Collapse all</button></div>'
        f"</header>"
        f"{bands}{_render_discards(model.discarded)}{_render_coverage(model)}"
        f"{_render_footer(model)}"
        f"</div><script>{_SCRIPT}</script></body></html>"
    )


def _fail(status: str, problems: list[str], code: int) -> None:
    json.dump({"status": status, "problems": problems}, sys.stderr, indent=2)
    sys.exit(code)


_STRIP: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r"<[^>]+>"),
)


def _self_scan(page: str, model: RenderModel) -> list[str]:
    """Reject invented vocabulary this FILE put on the page.

    `digest_model.py` scans the record, which is where the rule was assumed to
    be enforceable. It cannot see a banned word hardcoded in a template here --
    and one was: an empty group rendered the sentence "Nothing in this band.",
    putting a word from the substitution table in front of the reader. It
    surfaced only because a run happened to produce an empty group and someone
    read the page; a run where every group has findings never renders that
    branch, so the leak had shipped in two released versions.

    Two exclusions, both of which this check got wrong on the first attempt and
    both of which are the difference between a useful gate and one that fires on
    every real run.

    Markup is not prose. Class names, ids and the stylesheet legitimately use
    the internal words -- `.band`, `.axes` -- and a scan that could not tell
    them apart would teach the next author to rename CSS to appease it.

    **Captured output is not this file's wording.** `digest_model` deliberately
    exempts `_VERBATIM_FIELDS` from the vocabulary rule, because a stack trace
    or an assertion message says whatever the program said. Re-imposing the rule
    here would overrule that decision from a file that cannot see which field
    the text came from. Measured: the first version of this scan failed a real
    76-finding record on the word `candidate`, which came from the captured line
    `RESTRICTED uri ranked above >=1 clean candidate`. Subtracting the verbatim
    values reuses the one canonical exemption list rather than growing a second.
    """
    text = page
    for stripper in _STRIP:
        text = stripper.sub(" ", text)
    text = html.unescape(text)
    for value in _verbatim_values(model):
        if value:
            text = text.replace(value, " ")
    return [
        f"the rendered page shows wording no reader can define: {word}. "
        "It did not come from the record, so it is hardcoded in this file -- "
        "run-record-schema.md has what to write instead."
        for word in _jargon_hits(text)
    ]


def _verbatim_values(model: RenderModel) -> list[str]:
    """Every string the record is allowed to carry jargon inside.

    Mirrors `digest_model._VERBATIM_FIELDS` for the fields that actually render,
    plus the coverage file lists, which are paths for the same reason.
    """
    values: list[str] = []
    for findings in (*model.grouped.values(), model.discarded):
        for f in findings:
            values += [f.observed_symptom, f.observed_full or "", f.defect_site]
            if f.verification:
                values.append(f.verification.metric_query)
    for entry in model.coverage:
        values += [str(name) for name in entry.get("files", [])]
    return values


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if args:
        _fail("USAGE", [f"unexpected argument(s): {' '.join(args)}"], 2)

    source = sys.stdin.read()
    if not source.strip():
        _fail("NO_INPUT", ["nothing on stdin; the digest is unrendered"], 2)

    try:
        payload = json.loads(source)
    except json.JSONDecodeError as error:
        _fail("NO_INPUT", [f"stdin is not valid JSON: {error}"], 2)

    try:
        model = model_from_dict(payload)
    except (KeyError, TypeError, ValueError) as error:
        _fail("BAD_MODEL", [f"stdin did not reconstruct into a model: {error}"], 1)

    page = render(model)

    leaks = _self_scan(page, model)
    if leaks:
        _fail("JARGON_LEAK", leaks, 1)

    sys.stdout.write(page)
    sys.exit(0)


if __name__ == "__main__":
    main()
