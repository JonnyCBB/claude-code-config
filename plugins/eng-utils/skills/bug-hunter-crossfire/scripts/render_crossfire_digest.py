#!/usr/bin/env python3
"""Validate a Crossfire run record and render the self-contained HTML digest.

    python3 render_crossfire_digest.py --out digest.html < run.json

Exit 0: the record held and the digest was written.
Exit 1: the record was refused. stderr names the contradiction and NOTHING was written.

--out exists because `> digest.html` truncates the target before python starts, so a
refused re-render leaves a 0-byte file where a good digest was - and section 9 opens
that path in a browser. With --out the file is written once, after validation passes.
Omit it and the digest goes to stdout, which is what the tests use.

This script exists because prose was tried for the same job and produced a different
schema four times running, and because label collisions were hit twice while
hand-building the equivalent figure. It owns two things an orchestrator that authored
the findings cannot own: the reader-facing vocabulary, and the checks that the evidence
a finding claims is actually in the record.
"""

import html
import json
import sys

# ---------------------------------------------------------------------------
# Reader-facing vocabulary. Static here, never in the record: a per-run copy
# drifts from the code that sets the labels, and no internal state name is
# allowed to reach the reader.
# ---------------------------------------------------------------------------

EDGE_STATES = {
    "examined_finding": ("Examined - something to look at", "#b3261e", "none"),
    "examined_clean": ("Examined - nothing found", "#1f6f3f", "none"),
    "enumerated_not_examined": ("Found, not examined", "#6b5b00", "7 4"),
    "enumerated_unmeasurable": ("Found, no figures available", "#5a5a66", "2 4"),
}

HANDLINGS = {
    "fails_closed": "Fails closed",
    "fails_open": "Fails open",
    "absent": "No degraded-path handling found",
    "looks_handled": "Looks handled (screen only, not read)",
    "other": "Other",
}

OUTCOMES = {
    "outlier": "Outlier against its peers",
    "differs_from_sample": "Differs from a sample of its peers",
    "split": "No conclusion - the peers are split",
    "shared_default": "Possible shared default across every peer",
}

DEPTHS = {"read": "read in full", "screen": "screened only"}

BANDS = ["Read closely", "Worth a look", "Skim", "Not triaged"]

SMALL_COHORT = 3
LARGE_COHORT = 40

# Keys that would put a person's name beside the word "bug". The originating
# question was who is responsible for a system; blame for a line is a different
# thing and stays banned.
AUTHORSHIP_KEYS = {
    "author", "authors", "author_email", "authored_by", "blame", "blamed_on",
    "committer", "commit_author", "created_by", "git_author", "last_modified_by",
    "owner_email", "reported_by",
}

INTENT_VERDICTS = {"VIOLATION_SUPPORTED", "INTENDED_SUPPORTED", "AMBIGUOUS"}


class Refused(Exception):
    pass


def refuse(message):
    raise Refused(message)


def e(value):
    """Escape for HTML text and attribute context. Cohort notes quote other teams'
    source, so every string in the record is untrusted."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def walk_for_authorship(node, path="record"):
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in AUTHORSHIP_KEYS:
                refuse(f"{path}.{key} records authorship; Crossfire names teams, never people")
            walk_for_authorship(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            walk_for_authorship(value, f"{path}[{index}]")


def validate(record):
    if not isinstance(record, dict):
        refuse("the record must be a JSON object")

    walk_for_authorship(record)

    for key in ("run_id", "focus", "cost", "edges", "findings"):
        if key not in record:
            refuse(f"the record has no {key}")

    if not (record.get("run_id") or "").strip():
        refuse("run_id is empty; the digest has no sentinel to identify it by")

    focus = record["focus"]
    if not focus.get("component"):
        refuse("focus.component is empty; the run has no subject")
    if not focus.get("team"):
        refuse(f"focus.team is empty for {focus.get('component')}; every component names its owning team")

    if "metric_source" not in focus or not isinstance(focus["metric_source"], bool):
        refuse(
            "focus.metric_source must be true or false: whether the operator supplied metric "
            "exports for this run. Without it the digest cannot say whether a metric lookup "
            "was possible at all"
        )
    if "metric_alias" not in focus:
        refuse(
            "focus.metric_alias is absent. Record the alias, or null when the metric uses the "
            "component name - a missing key renders as 'checked, no alias found', which is a claim "
            "about a lookup nobody can see happened. A metric_alias outside focus is not read"
        )
    alias = focus["metric_alias"]
    if not focus["metric_source"] and alias is not None:
        refuse(
            "focus.metric_alias is set but focus.metric_source is false. An alias can only be "
            "resolved against a metric source; record null"
        )
    if alias is not None and alias == focus["component"]:
        refuse(
            "focus.metric_alias equals the component name. Record null when the metric uses the "
            "component name; an alias written where none exists hides that the lookup never ran"
        )

    for key, kind, shape in (
        ("focus", dict, "an object"),
        ("cost", dict, "an object"),
        ("edges", list, "a list"),
        ("findings", list, "a list"),
    ):
        if not isinstance(record[key], kind):
            refuse(f"{key} must be {shape}, not {type(record[key]).__name__}")

    cost = record["cost"]
    for key in ("edges_enumerated", "edges_screened", "edges_read", "agents_projected",
                "agents_spawned"):
        if cost.get(key) is not None and not isinstance(cost[key], int):
            refuse(
                f"cost.{key} must be a whole number, not {type(cost[key]).__name__}; every figure "
                "in the cost line is counted, never described"
            )
        if cost.get(key) is None:
            refuse(
                f"cost.{key} is missing. Every number in the cost line must be supplied: an absent "
                "one either renders as a blank in the sentence or takes another field's value, and "
                "both read as a figure somebody measured"
            )

    edges = record["edges"]
    uncovered = record.get("uncovered") or []
    findings = record["findings"]

    if not edges and not uncovered:
        refuse("the record carries nothing: no edges and no declaration of what could not be checked")

    if not isinstance(uncovered, list):
        refuse(f"uncovered must be a list, not {type(uncovered).__name__}")

    seen_edge_ids = set()
    for edge in edges:
        if not isinstance(edge, dict):
            refuse(f"every entry in edges must be an object, not {type(edge).__name__}")
        edge_id = edge.get("edge_id")
        if not edge_id:
            refuse("an edge has no edge_id")
        if edge_id in seen_edge_ids:
            refuse(f"duplicate edge_id {edge_id}")
        seen_edge_ids.add(edge_id)

        if edge.get("state") not in EDGE_STATES:
            refuse(f"unknown edge state {edge.get('state')!r} on {edge_id}")
        if not (edge.get("state_reason") or "").strip():
            refuse(
                f"{edge_id} has no state_reason. An edge with nothing found and an edge nobody "
                "looked at must not read alike"
            )
        for side in ("caller", "callee"):
            if not edge.get(side):
                refuse(f"{edge_id} does not name its {side}")
            if not isinstance(edge[side], str):
                refuse(
                    f"{edge_id}.{side} must be the component's name as a plain string, not "
                    f"{type(edge[side]).__name__}. The team rides alongside it as {side}_team; "
                    "only an uncovered component is an object"
                )
            if not (edge.get(f"{side}_team") or "").strip():
                refuse(f"{edge_id}: {edge[side]} has no owning team on this edge")
        if edge.get("caller") == edge.get("callee"):
            refuse(f"{edge_id} has the same component on both ends; that is not a boundary")

    # Section 4 calls this arithmetic the check that scope has not silently grown, so
    # it has to be arithmetic rather than three numbers written from memory.
    enumerated = cost["edges_enumerated"]
    screened = cost["edges_screened"]
    read_count = cost["edges_read"]
    if enumerated != len(edges):
        refuse(
            f"cost.edges_enumerated is {enumerated} and the record carries {len(edges)} edges; "
            "every enumerated edge appears with a state or the coverage is a claim"
        )
    if not (read_count <= screened <= len(edges)):
        refuse(
            f"cost says {read_count} read of {screened} screened of {len(edges)} edges, which "
            "cannot all be true"
        )
    examined = [e for e in edges if e["state"] in ("examined_finding", "examined_clean")]
    if read_count != len(examined):
        refuse(
            f"cost.edges_read is {read_count} and {len(examined)} edges carry an examined state; "
            "the cost line would contradict the coverage table under it"
        )

    for entry in uncovered:
        components_listed = entry.get("components")
        if not components_listed:
            refuse("an uncovered entry names no components, so it declares nothing")
        for item in components_listed:
            if not isinstance(item, dict):
                refuse(
                    "an uncovered component must be {component, team}; a bare name has nowhere "
                    "to carry the owning team every component in the digest needs"
                )
            if not (item.get("component") or "").strip():
                refuse("an uncovered component has no name")
            if not (item.get("team") or "").strip():
                refuse(f"the uncovered component {item['component']} has no owning team")
        if not (entry.get("why") or "").strip():
            names = ", ".join(i["component"] for i in components_listed)
            refuse(f"the uncovered entry for {names} does not say why")

    edges_with_findings = {edge["edge_id"] for edge in edges if edge["state"] == "examined_finding"}
    edges_cited = set()
    edge_by_id = {edge["edge_id"]: edge for edge in edges}
    components = {edge[side] for edge in edges for side in ("caller", "callee")}

    seen_finding_ids = set()
    for finding in findings:
        finding_id = finding.get("finding_id")
        if not finding_id:
            refuse("a finding has no finding_id")
        if finding_id in seen_finding_ids:
            refuse(f"duplicate finding_id {finding_id}")
        seen_finding_ids.add(finding_id)
        validate_finding(
            finding, seen_edge_ids, edges_with_findings, edges_cited, edge_by_id, components
        )

    orphans = sorted(edges_with_findings - edges_cited)
    if orphans:
        refuse(
            f"{', '.join(orphans)} is marked as carrying a finding and no finding cites it"
        )

    return record


def validate_finding(finding, known_edge_ids, edges_with_findings, edges_cited, edge_by_id, components):
    finding_id = finding["finding_id"]
    edge_id = finding.get("edge_id")

    if edge_id not in known_edge_ids:
        refuse(f"{finding_id} cites edge {edge_id}, which is not in the record")
    if edge_id not in edges_with_findings:
        refuse(
            f"{finding_id} reports on {edge_id}, whose state does not say it carries a finding. "
            "The diagram and the findings would disagree"
        )
    edges_cited.add(edge_id)

    outcome = finding.get("cohort_outcome")
    if outcome not in OUTCOMES:
        refuse(f"{finding_id}: unknown cohort_outcome {outcome!r}")

    if not (finding.get("title") or "").strip():
        refuse(f"{finding_id} has no title; the digest has nothing to head the finding with")

    if not (finding.get("inferred_contract") or "").strip():
        refuse(f"{finding_id} states no inferred contract; the contract is the evidence")

    population = finding.get("cohort_population") or {}
    total = population.get("callers_total")
    examined = population.get("callers_examined")
    if not isinstance(total, int) or not isinstance(examined, int):
        refuse(f"{finding_id}: cohort_population must give integer callers_total and callers_examined")

    if total < 1 or examined < 1:
        refuse(f"{finding_id}: cohort_population counts must be positive, got {total}/{examined}")
    if examined > total:
        refuse(
            f"{finding_id}: callers_examined {examined} exceeds callers_total {total}; the sample "
            "cannot be larger than the population"
        )

    cohort = finding.get("cohort") or []
    if not isinstance(cohort, list):
        refuse(
            f"{finding_id}.cohort must be the list of peers itself, not "
            f"{type(cohort).__name__}; there is no wrapper key around it"
        )
    for peer in cohort:
        if not isinstance(peer, dict):
            refuse(f"{finding_id}: every cohort row must be an object, not {type(peer).__name__}")

    for peer in cohort:
        if not peer.get("component"):
            refuse(f"{finding_id}: a cohort row has no component")
        if not (peer.get("team") or "").strip():
            refuse(f"{finding_id}: {peer['component']} in the cohort has no owning team")
        depth = peer.get("evidence_depth")
        if depth not in DEPTHS:
            refuse(f"{finding_id}: {peer['component']} has unknown evidence_depth {depth!r}")
        handling = peer.get("handling")
        if handling not in HANDLINGS:
            refuse(f"{finding_id}: {peer['component']} has unknown handling {handling!r}")
        if depth == "screen" and handling != "looks_handled":
            refuse(
                f"{finding_id}: {peer['component']} was screened only and the record states "
                f"'{handling}'. The screen routes; only a read may conclude"
            )
        if not (peer.get("evidence") or "").strip():
            refuse(f"{finding_id}: {peer['component']} carries no evidence pointer")

    # `callers_examined` counts callers READ. A screened peer may sit in the table - the
    # screen can promote one to "looks handled" - but it was not read, and the page must
    # not say it was. Counting the two together printed "7 callers read of 7" for a
    # cohort where four had been read.
    read_rows = [peer for peer in cohort if peer["evidence_depth"] == "read"]
    if len(read_rows) != examined:
        # Naming the key matters: four plausible spellings of `cohort` all produced this
        # refusal with an empty table, and the message described "the table" in English,
        # so an agent could not tell a misspelled key from a genuinely empty one.
        hint = (
            " The peer rows go in a key named exactly `cohort`, a list on the finding."
            if not cohort else ""
        )
        refuse(
            f"{finding_id}: cohort_population says {examined} callers examined and `cohort` "
            f"lists {len(read_rows)} read in full (of {len(cohort)} rows).{hint}"
        )

    names = [peer.get("component") for peer in cohort]
    if len(set(names)) != len(names):
        refuse(
            f"{finding_id}: a component appears more than once in the cohort table, so the "
            "population is double-counted"
        )

    edge = edge_by_id[edge_id]
    if cohort and edge["caller"] not in names:
        refuse(
            f"{finding_id}: the edge's own caller {edge['caller']} is absent from its cohort "
            "table, so the table is not about this edge"
        )

    outlier = finding.get("outlier_component")

    if outcome == "outlier":
        outlier_row = next((peer for peer in cohort if peer["component"] == outlier), None)
        if outlier_row is not None and outlier_row["evidence_depth"] != "read":
            refuse(
                f"{finding_id} names {outlier} as the outlier on a screen alone; a screened "
                "peer may be promoted to looks-handled but never named as the one that differs"
            )
        if outlier is not None and outlier != edge["caller"]:
            refuse(
                f"{finding_id} is about the edge from {edge['caller']} and names {outlier} as the "
                "outlier; the digest would blame a service that is not on the edge"
            )
        if examined < SMALL_COHORT:
            refuse(
                f"{finding_id} claims an outlier against fewer than 3 examined callers. "
                "Neither peer comparison nor a documented contract is available for that edge"
            )
        if total > LARGE_COHORT:
            refuse(
                f"{finding_id}: {total} callers is past {LARGE_COHORT}, so the finding must be "
                "worded as differs_from_sample against a stated sample, not as outlier status"
            )
        if not outlier:
            refuse(f"{finding_id} is an outlier finding and names no outlier component")
        handlings = {peer["handling"] for peer in cohort}
        if len(handlings) == 1:
            refuse(
                f"{finding_id} names an outlier while every caller in the table handles the "
                f"degraded path the same way ({sorted(handlings)[0]}). A population that agrees "
                "with itself has no outlier in it - that is a shared_default. If the difference "
                "is real but the five handling values cannot express it, record the outlier as "
                "'other' and say what differs in its note"
            )
        if outlier_row is not None and outlier_row["handling"] in {
            peer["handling"] for peer in cohort if peer["component"] != outlier
        } and len(handlings) > 1:
            refuse(
                f"{finding_id} names {outlier} as the outlier, and another caller in the table "
                "handles the degraded path exactly as it does; the reader would see the claim "
                "contradicted one line below it"
            )

    if outcome == "differs_from_sample":
        if total <= LARGE_COHORT:
            refuse(
                f"{finding_id}: sample wording is for populations past {LARGE_COHORT} callers and "
                f"this one has {total}; compare the peers instead"
            )
        if examined < SMALL_COHORT:
            refuse(
                f"{finding_id}: a sample of {examined} is not a sample; at least "
                f"{SMALL_COHORT} peers must be read as corroboration"
            )
        if not (finding.get("primary_evidence") or "").strip():
            refuse(
                f"{finding_id}: a sampled cohort needs primary_evidence - the callee's published "
                "contract or a maintained test - with the sample as corroboration"
            )
        if not (population.get("selection") or "").strip():
            refuse(f"{finding_id}: cohort_population.selection must state how the sample was drawn")

    if outcome == "shared_default" and outlier:
        refuse(
            f"{finding_id} is a shared_default and names {outlier} as an outlier. The evidence is "
            "one judgement about a pattern, not a population disagreeing"
        )

    if outcome == "split" and outlier:
        refuse(f"{finding_id} is a split cohort and names an outlier; a split states no conclusion")

    if outcome == "split":
        camps = {peer["handling"] for peer in cohort}
        if len(camps) < 2:
            refuse(f"{finding_id} is a split cohort with one handling in the table; show both camps")

    band = finding.get("band")
    if band not in BANDS:
        refuse(f"{finding_id}: band must be one of {BANDS}, got {band!r}")
    if band != "Not triaged" and not (finding.get("band_reason") or "").strip():
        refuse(f"{finding_id} is banded {band} with no band_reason")

    intent = finding.get("intent_verdict")
    if not isinstance(intent, dict) or not intent.get("verdict"):
        refuse(
            f"{finding_id} has no intent verdict. A candidate is reported only after a blind "
            "verifier has independently assessed whether the behaviour is intended"
        )
    if intent["verdict"] not in INTENT_VERDICTS:
        refuse(
            f"{finding_id}: intent verdict {intent['verdict']!r} is outside the verifier's "
            f"vocabulary {sorted(INTENT_VERDICTS)}; free text renders as a verdict that was reached"
        )
    if not (intent.get("evidence_trail") or "").strip():
        refuse(f"{finding_id}: the intent verdict carries no evidence trail, and it appears in full or not at all")

    exposure = finding.get("exposure")
    if not isinstance(exposure, dict):
        refuse(f"{finding_id} has no exposure block")
    share = exposure.get("share")
    if share is None:
        if not (exposure.get("why_not") or "").strip():
            refuse(f"{finding_id}: exposure has neither a figure nor a reason there is none")
    else:
        if not isinstance(share, dict):
            refuse(
                f"{finding_id}: share is {type(share).__name__}, not a dict. A string or bare number "
                "is real data in a form the renderer cannot use"
            )
        missing = [k for k in ("numerator", "denominator", "unit", "of") if k not in share]
        if missing:
            refuse(f"{finding_id}: share is missing {', '.join(missing)}")
        if not (share.get("of") or "").strip():
            refuse(f"{finding_id}: share.of is empty, so the figure does not say which question it answers")
        numerator, denominator = share["numerator"], share["denominator"]
        if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
            refuse(f"{finding_id}: share numerator and denominator must be numbers")
        if denominator <= 0:
            refuse(f"{finding_id}: share denominator is {denominator}; a share needs something to be a share of")
        if not 0 <= numerator <= denominator:
            refuse(
                f"{finding_id}: share numerator {numerator} is not within 0 and its denominator "
                f"{denominator}, so the percentage would be impossible"
            )

    site = finding.get("defect_site") or {}
    if site.get("component") and site["component"] not in components | set(names):
        refuse(
            f"{finding_id}: the defect site names {site['component']}, which appears on no edge "
            "and in no cohort table"
        )


# ---------------------------------------------------------------------------
# The diagram
# ---------------------------------------------------------------------------


def node_label(component, team, tier):
    tier_text = f"tier {tier}" if tier is not None else "tier unknown"
    return component, f"{team} - {tier_text}"


def render_svg(record):
    """A layered layout: the peer column on the left, the shared component on the right.
    The shape is bounded, so no graph-layout algorithm is needed - and a general one is
    what produced the label collisions this replaces."""
    focus = record["focus"]["component"]
    edges = record["edges"]

    if not edges:
        return (
            '<svg viewBox="0 0 640 80" width="640" height="80" role="img" '
            'aria-label="No edges were enumerated for this run.">'
            '<text x="16" y="44" font-family="system-ui,sans-serif" font-size="14" fill="#444">'
            "No edges were enumerated. See what could not be checked, below.</text></svg>"
        )

    peers = []
    for edge in edges:
        other, team, tier = (
            (edge["callee"], edge["callee_team"], edge.get("callee_tier"))
            if edge["caller"] == focus
            else (edge["caller"], edge["caller_team"], edge.get("caller_tier"))
        )
        peers.append((other, team, tier, edge))

    # Every label sits below its own box and every connector is a straight line to the
    # single focus node. Nothing is written along a line and no two connectors share a
    # segment, so there is nothing for a label to collide with. Orthogonal routing was
    # tried and put the state label straight through the vertical run.
    row_height = 78
    top = 24
    height = top + row_height * len(peers) + 40
    width = 880
    peer_x, focus_x = 24, 600
    box_w, box_h = 260, 40
    # Tall enough that each edge lands on its own row rather than on one pixel.
    focus_h = max(box_h, min(14 * len(peers), 260))
    focus_y = top + (row_height * len(peers)) // 2 - focus_h // 2

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" '
        f'aria-label="Call edges between {e(focus)} and its peers, with the state of each.">',
        '<style>.n{font-family:system-ui,sans-serif;font-size:13px;fill:#111}'
        '.s{font-family:system-ui,sans-serif;font-size:11px;fill:#555}'
        '.m{font-family:system-ui,sans-serif;font-size:10px;fill:#444}</style>',
        "<defs>"
        + "".join(
            f'<marker id="a{index}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{colour}"/></marker>'
            for index, (_, colour, _) in enumerate(EDGE_STATES.values())
        )
        + "</defs>",
    ]

    focus_team = record["focus"]["team"]
    focus_tier = record["focus"].get("tier")
    name, sub = node_label(focus, focus_team, focus_tier)
    parts.append(
        f'<rect x="{focus_x}" y="{focus_y}" width="{box_w}" height="{focus_h}" rx="6" '
        f'fill="#f2f2f7" stroke="#333" stroke-width="2"/>'
        f'<text class="n" x="{focus_x + 10}" y="{focus_y + focus_h // 2 - 3}">{e(name)}</text>'
        f'<text class="s" x="{focus_x + 10}" y="{focus_y + focus_h // 2 + 12}">{e(sub)}</text>'
    )

    state_index = {name: i for i, name in enumerate(EDGE_STATES)}
    for index, (other, team, tier, edge) in enumerate(peers):
        y = top + index * row_height
        label, colour, dash = EDGE_STATES[edge["state"]]
        marker = f'a{state_index[edge["state"]]}'
        # The arrow points at the callee, which is what the data says and what a reader
        # must not have to infer.
        focus_is_caller = edge["caller"] == focus
        name, sub = node_label(other, team, tier)
        parts.append(
            f'<rect x="{peer_x}" y="{y}" width="{box_w}" height="{box_h}" rx="6" '
            f'fill="#fff" stroke="#888"/>'
            f'<text class="n" x="{peer_x + 10}" y="{y + 17}">{e(name)}</text>'
            f'<text class="s" x="{peer_x + 10}" y="{y + 32}">{e(sub)}</text>'
        )
        x1, x2 = peer_x + box_w, focus_x
        y1 = y + box_h // 2
        span = focus_h - 12
        step = span / (len(peers) - 1) if len(peers) > 1 else 0
        y2 = int(focus_y + 6 + index * step)
        arrow = (
            f'marker-start="url(#{marker})"' if focus_is_caller
            else f'marker-end="url(#{marker})"'
        )
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="2" stroke-dasharray="{dash}" {arrow}>'
            f'<title>{e(edge["caller"])} calls {e(edge["callee"])}. '
            f'{e(label)}: {e(edge["state_reason"])}</title></line>'
        )
        method = edge.get("method")
        label_y = y + box_h + 13
        if method:
            parts.append(f'<text class="m" x="{peer_x + 10}" y="{label_y}">{e(method)}</text>')
            label_y += 13
        parts.append(f'<text class="m" x="{peer_x + 10}" y="{label_y}">{e(label)}</text>')

    # Fixed slots, not text-width arithmetic: a slot per state keeps the legend inside
    # the viewBox whatever the labels say. Marked `lg` so the layout test can tell a
    # legend label from one that would sit across a connector.
    legend_y = height - 22
    slot = (width - 24) // len(EDGE_STATES)
    for index, (label, colour, dash) in enumerate(EDGE_STATES.values()):
        x = 12 + index * slot
        parts.append(
            f'<line x1="{x}" y1="{legend_y}" x2="{x + 22}" y2="{legend_y}" stroke="{colour}" '
            f'stroke-width="2" stroke-dasharray="{dash}"/>'
            f'<text class="m lg" x="{x + 28}" y="{legend_y + 4}">{e(label)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

CSS = """
:root{color-scheme:light}
body{font-family:system-ui,-apple-system,sans-serif;line-height:1.5;color:#111;
     max-width:1000px;margin:0 auto;padding:24px 20px 64px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:18px;margin:32px 0 8px;border-bottom:1px solid #ddd;padding-bottom:4px}
h3{font-size:15px;margin:20px 0 4px}
.sub{color:#555;font-size:13px;margin:0 0 20px}
table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:13px}
th,td{border:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f6f6f8;font-weight:600}
.finding{border:1px solid #ccc;border-left:4px solid #b3261e;border-radius:6px;
         padding:12px 16px;margin:16px 0;background:#fff}
.finding.noconclusion{border-left-color:#6b5b00}
.finding.shared{border-left-color:#5a5a66}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;
      background:#eee;margin-right:6px}
.contract{background:#f6f6f8;border-left:3px solid #888;padding:8px 12px;margin:8px 0;font-size:14px}
.note{color:#555;font-size:12px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.empty{color:#555;font-style:italic}
footer{margin-top:40px;color:#666;font-size:12px;border-top:1px solid #ddd;padding-top:12px}
"""


def render_share(share):
    if share is None:
        return None
    num, den = share["numerator"], share["denominator"]
    try:
        pct = f"{(float(num) / float(den)) * 100:.2f}%"
    except (TypeError, ValueError, ZeroDivisionError):
        pct = "not computable"
    return (
        f'<p><strong>How much of it there is:</strong> {e(pct)} '
        f'({e(num)} of {e(den)} {e(share["unit"])})<br>'
        f'<span class="note">That percentage answers one question and only that one: '
        f'{e(share["of"])}.</span></p>'
    )


def render_cohort_table(cohort):
    rows = [
        "<table><thead><tr><th>Caller</th><th>Owning team</th>"
        "<th>How it handles the degraded path</th><th>How closely we looked</th>"
        "<th>Where we saw it</th></tr></thead><tbody>"
    ]
    for peer in cohort:
        rows.append(
            f"<tr><td>{e(peer['component'])}</td><td>{e(peer['team'])}</td>"
            f"<td>{e(HANDLINGS[peer['handling']])}"
            + (f'<br><span class="note">{e(peer["note"])}</span>' if peer.get("note") else "")
            + f"</td><td>{e(DEPTHS[peer['evidence_depth']])}</td>"
            f'<td class="mono">{e(peer["evidence"])}</td></tr>'
        )
    rows.append("</tbody></table>")
    return "".join(rows)


def render_finding(finding, edge_by_id):
    outcome = finding["cohort_outcome"]
    edge = edge_by_id[finding["edge_id"]]
    css_class = {
        "split": "finding noconclusion",
        "shared_default": "finding shared",
    }.get(outcome, "finding")

    population = finding["cohort_population"]
    parts = [
        f'<div class="{css_class}">',
        f'<h3>{e(finding["title"])}</h3>',
        f'<p><span class="pill">{e(OUTCOMES[outcome])}</span>'
        f'<span class="pill">How hard to look: {e(finding["band"])}</span></p>',
        f'<p><strong>Between:</strong> {e(edge["caller"])} ({e(edge["caller_team"])}) '
        f'calling {e(edge["callee"])} ({e(edge["callee_team"])})'
        + (f' - {e(edge["interface"])}.{e(edge["method"])}' if edge.get("method") else "")
        + "</p>",
        f'<div class="contract"><strong>What its peers do:</strong> {e(finding["inferred_contract"])}</div>',
    ]

    if outcome == "outlier":
        screened = len(finding["cohort"]) - population["callers_examined"]
        also = f", and {screened} screened but not read" if screened else ""
        parts.append(
            f'<p><strong>The one that differs:</strong> {e(finding["outlier_component"])}, '
            f'out of {population["callers_examined"]} callers read in full{also}, of '
            f'{population["callers_total"]} that call this service.</p>'
        )
    elif outcome == "differs_from_sample":
        parts.append(
            f'<p><strong>Against a sample, not the whole population.</strong> This service has '
            f'{population["callers_total"]} callers, too many to compare exhaustively, so '
            f'{population["callers_examined"]} were read as corroboration. '
            f'{e(population.get("selection", ""))}</p>'
            f'<p><strong>The primary evidence is the callee&#39;s own statement:</strong> '
            f'{e(finding["primary_evidence"])}</p>'
        )
    elif outcome == "shared_default":
        parts.append(
            "<p><strong>This is a shared default, not an outlier.</strong> Every caller examined "
            "does the same thing, so nothing here is out of line with its peers. It is on the page "
            "because the shared behaviour itself looks risky - which is one judgement about a "
            "pattern, not a population disagreeing.</p>"
        )
    elif outcome == "split":
        parts.append(
            "<p><strong>No conclusion.</strong> The callers are split between two handlings, so "
            "neither camp is presented as the finding. Both are in the table below.</p>"
        )

    if finding.get("observed_symptom"):
        parts.append(f'<p><strong>What it does:</strong> {e(finding["observed_symptom"])}</p>')

    site = finding.get("defect_site") or {}
    if site.get("path"):
        location = f'{site.get("component","")} {site["path"]}'
        if site.get("line"):
            location += f':{site["line"]}'
        link = site.get("permalink")
        rendered = (
            f'<a href="{e(link)}">{e(location)}</a>' if link else f'{e(location)} '
            f'<span class="note">(no permalink resolved)</span>'
        )
        parts.append(f'<p><strong>Where in the code:</strong> <span class="mono">{rendered}</span></p>')

    parts.append("<p><strong>Every caller we looked at:</strong></p>")
    parts.append(render_cohort_table(finding["cohort"]))

    intent = finding["intent_verdict"]
    verdict_text = {
        "VIOLATION_SUPPORTED": "the evidence points to this not being intended",
        "INTENDED_SUPPORTED": "the evidence points to this being intended",
        "AMBIGUOUS": "the evidence does not settle whether this is intended",
    }.get(intent["verdict"], intent["verdict"])
    parts.append(
        f"<p><strong>Was it meant to be like this?</strong> A separate investigator, told only what "
        f"the code does and never that anyone thought it was a bug, found that {e(verdict_text)}.<br>"
        f'<span class="note">{e(intent["evidence_trail"])}</span></p>'
    )

    share_html = render_share(finding["exposure"].get("share"))
    if share_html:
        parts.append(share_html)
    else:
        parts.append(
            f'<p><strong>How much of it there is:</strong> not measured. '
            f'<span class="note">{e(finding["exposure"]["why_not"])}</span></p>'
        )

    if finding.get("band_reason"):
        parts.append(f'<p class="note">Banded {e(finding["band"])}: {e(finding["band_reason"])}</p>')

    parts.append("</div>")
    return "".join(parts)


def render(record):
    focus = record["focus"]
    edges = record["edges"]
    findings = record["findings"]
    edge_by_id = {edge["edge_id"]: edge for edge in edges}
    cost = record["cost"]

    head = [
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        f"<title>Crossfire - {e(focus['component'])} - {e(record['run_id'])}</title>",
        f"<style>{CSS}</style></head><body>",
        f"<h1>What sits between {e(focus['component'])} and the services on the other side of it</h1>",
        f'<p class="sub">Run {e(record["run_id"])}, {e(record.get("generated_at", ""))}. '
        f'{e(focus["component"])} is owned by {e(focus["team"])}'
        + (f', tier {e(focus["tier"])}' if focus.get("tier") is not None else "")
        + ". This run read how each service on a shared call handles the path where that call "
        "goes wrong, and looked for one that handles it unlike the rest.</p>",
    ]

    body = ["<h2>The picture</h2>", render_svg(record)]

    if not focus["metric_source"]:
        body.append(
            '<p class="note">No metric source was supplied for this run, so no metric alias was '
            "resolved, edges come from code alone, and no exposure figure below is measured.</p>"
        )
    elif focus.get("metric_alias"):
        body.append(
            f'<p class="note">The metrics call {e(focus["component"])} '
            f'<span class="mono">{e(focus["metric_alias"])}</span>. That alias was resolved for '
            "this run, so the figures below are this service&#39;s and not another&#39;s.</p>"
        )
    else:
        body.append(
            f'<p class="note">The metrics use {e(focus["component"])}&#39;s own name, checked for '
            "this run. Saying so matters: silence here would read the same as never having "
            "looked, and about one component in twenty is labelled differently.</p>"
        )

    body.append("<h2>What we found</h2>")
    if not findings:
        read_edges = [edge for edge in edges if edge["state"] == "examined_clean"]
        if read_edges:
            body.append(
                '<p class="empty">Nothing. Every edge read below matched what its peers do. '
                "This is a result, not an absence of one - the edges read are named in the "
                "coverage table.</p>"
            )
        else:
            body.append(
                '<p class="empty">Nothing, and nothing was read. No edge in this run reached a '
                "full reading, so this is not a clean result - it is an unfinished one. What was "
                "found and not examined is named in the coverage table below.</p>"
            )
    else:
        order = {band: index for index, band in enumerate(BANDS)}
        for finding in sorted(findings, key=lambda f: (order[f["band"]], f["finding_id"])):
            body.append(render_finding(finding, edge_by_id))

    body.append("<h2>What was looked at, and what was not</h2>")
    body.append(
        "<table><thead><tr><th>Calling service</th><th>Service it calls</th><th>Method</th>"
        "<th>State</th><th>Why</th></tr></thead><tbody>"
    )
    for edge in edges:
        label, _, _ = EDGE_STATES[edge["state"]]
        body.append(
            f'<tr><td>{e(edge["caller"])}<br><span class="note">{e(edge["caller_team"])}</span></td>'
            f'<td>{e(edge["callee"])}<br><span class="note">{e(edge["callee_team"])}</span></td>'
            f'<td class="mono">{e(edge.get("method") or "-")}</td>'
            f'<td>{e(label)}</td><td>{e(edge["state_reason"])}</td></tr>'
        )
    body.append("</tbody></table>")

    uncovered = record.get("uncovered") or []
    if uncovered:
        body.append("<h2>What this run cannot see at all</h2>")
        body.append("<ul>")
        for item in uncovered:
            components = ", ".join(
                f'{e(i["component"])} <span class="note">({e(i["team"])})</span>'
                for i in item.get("components", [])
            )
            body.append(f"<li><strong>{components}</strong> - {e(item.get('why', ''))}</li>")
        body.append("</ul>")

    body.append("<h2>What the run cost</h2>")
    body.append(
        f"<p>{e(cost.get('edges_enumerated'))} call edges found, "
        f"{e(cost.get('edges_screened'))} screened, {e(cost.get('edges_read'))} read in full. "
        f"{e(cost.get('agents_projected'))} agents projected before dispatch, "
        f"{e(cost['agents_spawned'])} actually spawned.</p>"
    )
    if cost.get("bound_applied"):
        body.append(
            f'<p><strong>This run was bounded.</strong> {e(cost["bound_applied"])} '
            "A bounded run is not a complete one.</p>"
        )

    foot = [
        "<footer>Nothing left this machine. No pull request, ticket, Slack message or page was "
        "created by this run, and no state was kept for a future one.</footer></body></html>"
    ]
    return "".join(head + body + foot)


def main(argv):
    out_path = None
    if "--out" in argv:
        index = argv.index("--out")
        if index + 1 >= len(argv):
            print("crossfire: --out needs a path", file=sys.stderr)
            return 1
        out_path = argv[index + 1]

    raw = sys.stdin.read()
    if not raw.strip():
        print("crossfire: no input on stdin. Nothing was read and nothing was checked.", file=sys.stderr)
        return 1
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"crossfire: the run record is not valid json: {exc}", file=sys.stderr)
        return 1
    try:
        validate(record)
    except Refused as exc:
        print(f"crossfire: refused - {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - see below
        # A traceback is not a refusal. This skill promises that exit 1 names the
        # contradiction, and a reader cannot act on a KeyError. Reaching here means a
        # record shape got past validation that validation should have named, so say
        # that rather than printing a stack trace and calling it a refusal.
        print(
            f"crossfire: internal error while checking the record ({type(exc).__name__}: {exc}). "
            "This is a defect in the checker, not a verdict on the record.",
            file=sys.stderr,
        )
        return 1
    try:
        page = render(record)
    except Exception as exc:  # noqa: BLE001
        print(
            f"crossfire: internal error while rendering ({type(exc).__name__}: {exc}). "
            "Nothing was written.",
            file=sys.stderr,
        )
        return 1
    if out_path:
        # Written only here, so a refusal above cannot have touched it.
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(page)
        print(f"crossfire: wrote {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
