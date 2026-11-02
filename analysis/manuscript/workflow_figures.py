"""Draw the six Section 6.2 workflow figures in one shared style.

Each panel is a row of component boxes joined by blue arrows. An O box below a
row node records results; a C+L box below the row marks a return path drawn
as an orange dashed arrow. Icons come from figures/workflow_icons/.
Run from the repository root: python figures/workflow_figures.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ICONS = HERE / "workflow_icons"

S = 4  # render scale; one panel unit is S pixels
FONT = "C:/Windows/Fonts/segoeui.ttf"
LABEL_FONT = ImageFont.truetype(FONT, 16 * S)
SMALL_FONT = ImageFont.truetype(FONT, 13 * S)
CAPTION_FONT = ImageFont.truetype(FONT, 21 * S)
BRACKET_FONT = ImageFont.truetype(FONT, 17 * S)

INK = (0, 0, 0)
BLUE = (67, 168, 249)
ORANGE = (240, 140, 0)
PANEL_EDGE = (60, 100, 150)
PANEL_FILL = (252, 254, 253)
STYLE = {  # fill, edge
    "C": ((240, 239, 253), (207, 198, 242)),
    "LLM": ((239, 255, 245), (191, 232, 207)),
    "T": ((240, 247, 255), (191, 221, 247)),
    "E": ((240, 247, 255), (191, 221, 247)),
    "V": ((254, 250, 240), (245, 227, 163)),
    "O": ((254, 250, 240), (245, 227, 163)),
    "CL": ((240, 239, 253), (207, 198, 242)),
    "G": ((240, 247, 255), (191, 221, 247)),
}

# Panels of one figure sit side by side in a single row. A two-panel figure uses
# wider panels so that every figure has the same total width.
ROW_WIDTH = 1428 * S
PANEL_W, PANEL_H = 472 * S, 296 * S
NODE_W, NODE_H = 88 * S, 120 * S
ARROW_GAP = 13 * S  # fixed space between row nodes; node width absorbs the rest
NODE_W_MAX = 150 * S
ROW_Y = 40 * S  # leaves room above the row for the Lifecycle bracket and Governance box
LOW_W, LOW_H = 124 * S, 84 * S
LOW_Y = 200 * S
CAPTION_H = 36 * S
SIDE_MARGIN = 11 * S  # nodes are spread evenly between the side margins
G_W = 136 * S


def icon(name: str, size: int) -> Image.Image:
    image = Image.open(ICONS / f"{name}.png").convert("RGBA")
    scale = size / max(image.size)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)


def rounded(draw, box, style, radius=12 * S, width=2 * S):
    fill, edge = STYLE[style]
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=edge, width=width)


def centred_text(draw, cx, top, lines, font, fill=INK, spacing=2 * S):
    y = top
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text((cx - w / 2, y), line, font=font, fill=fill)
        y += font.size + spacing


def dashed(draw, points, colour, width, dash=9 * S, gap=6 * S):
    """Draw a dashed polyline through a dense list of points."""
    on, left = True, dash
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while pos < seg:
            step = min(left, seg - pos)
            if on:
                t0, t1 = pos / seg, (pos + step) / seg
                draw.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                           (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=colour, width=width)
            pos += step
            left -= step
            if left <= 0:
                on = not on
                left = dash if on else gap


def head(draw, tip, angle, colour, size=9 * S):
    a1, a2 = angle + math.radians(150), angle - math.radians(150)
    draw.polygon([tip, (tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1)),
                  (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2))], fill=colour)


def curve(p0, p1, bend):
    """Quadratic Bezier from p0 to p1 bulging by `bend` pixels."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / length * bend, my + dx / length * bend
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])
            for t in [i / 40 for i in range(41)]]


def elbow(p0, p1, control):
    """Quadratic Bezier from p0 to p1 through one control point."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * control[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * control[1] + t * t * p1[1])
            for t in [i / 40 for i in range(41)]]


def return_arrow(draw, p0, p1, control):
    """Orange dashed arrow; the head follows the final direction of the curve."""
    points = elbow(p0, p1, control)
    dashed(draw, points[:-2], ORANGE, 3 * S)
    (xa, ya), (xb, yb) = points[-4], points[-1]
    head(draw, (xb, yb), math.atan2(yb - ya, xb - xa), ORANGE, 11 * S)


def fitted_font(draw, lines, width):
    """Largest label font, down to 12 units, at which every line fits the box width."""
    size = LABEL_FONT.size
    while size > 12 * S and max(draw.textlength(line, font=ImageFont.truetype(FONT, size)) for line in lines) > width:
        size -= S // 2
    return LABEL_FONT if size == LABEL_FONT.size else ImageFont.truetype(FONT, size)


def node_box(draw, canvas, box, style, icon_name, label, tag):
    rounded(draw, box, style)
    x0, y0, x1, y1 = box
    ic = icon(icon_name, 42 * S)
    canvas.alpha_composite(ic, (round((x0 + x1 - ic.width) / 2), round(y0 + 7 * S)))
    lines = label.split("\n") + [f"[{tag}]"]
    font = fitted_font(draw, lines, (x1 - x0) - 6 * S)
    text_h = len(lines) * (font.size + 2 * S)
    top = y0 + 54 * S + max(0, (y1 - y0 - 58 * S - text_h) / 2)
    centred_text(draw, (x0 + x1) / 2, top, lines, font)


def rounded_outline(box, r):
    """Points along a rounded rectangle, for drawing dashed borders."""
    x0, y0, x1, y1 = box
    return ([(x0 + r, y0), (x1 - r, y0)] + curve((x1 - r, y0), (x1, y0 + r), -r * 0.4)
            + [(x1, y1 - r)] + curve((x1, y1 - r), (x1 - r, y1), -r * 0.4)
            + [(x0 + r, y1)] + curve((x0 + r, y1), (x0, y1 - r), -r * 0.4)
            + [(x0, y0 + r)] + curve((x0, y0 + r), (x0 + r, y0), -r * 0.4))


def low_box(draw, canvas, box, style, icon_name, label, tag, optional=False):
    if optional:  # dashed border: the component appears in only some systems of this form
        fill, edge = STYLE[style]
        draw.rounded_rectangle(box, radius=12 * S, fill=fill)
        dashed(draw, rounded_outline(box, 12 * S), edge, 2 * S, dash=6 * S, gap=4 * S)
    else:
        rounded(draw, box, style)
    x0, y0, x1, y1 = box
    ic = icon(icon_name, 30 * S)
    canvas.alpha_composite(ic, (round((x0 + x1 - ic.width) / 2), round(y0 + 6 * S)))
    lines = [label, f"[{tag}]"]
    centred_text(draw, (x0 + x1) / 2, y0 + 40 * S, lines, fitted_font(draw, lines, LOW_W - 8 * S))


def panel(spec: dict) -> Image.Image:
    canvas = Image.new("RGBA", (PANEL_W, PANEL_H + CAPTION_H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    # dotted panel frame
    frame = (6 * S, 6 * S, PANEL_W - 6 * S, PANEL_H - 6 * S)
    draw.rounded_rectangle(frame, radius=22 * S, fill=PANEL_FILL)
    x0, y0, x1, y1 = frame
    r = 22 * S
    outline = ([(x0 + r, y0), (x1 - r, y0)] + curve((x1 - r, y0), (x1, y0 + r), -r * 0.4)
               + [(x1, y1 - r)] + curve((x1, y1 - r), (x1 - r, y1), -r * 0.4)
               + [(x0 + r, y1)] + curve((x0 + r, y1), (x0, y1 - r), -r * 0.4)
               + [(x0, y0 + r)] + curve((x0, y0 + r), (x0 + r, y0), -r * 0.4))
    dashed(draw, outline, PANEL_EDGE, 4 * S, dash=6 * S, gap=4 * S)

    nodes = spec["row"]
    n = len(nodes)
    avail = PANEL_W - 2 * SIDE_MARGIN
    node_w = min(NODE_W_MAX, (avail - (n - 1) * ARROW_GAP) / n)
    gap = (avail - n * node_w) / max(n - 1, 1)
    total = n * node_w + (n - 1) * gap
    start = (PANEL_W - total) / 2
    boxes = []
    for i, (style, icon_name, label, tag) in enumerate(nodes):
        bx = start + i * (node_w + gap)
        box = (bx, ROW_Y, bx + node_w, ROW_Y + NODE_H)
        boxes.append(box)
        node_box(draw, canvas, box, style, icon_name, label, tag)
        if i:
            ax0, ax1, ay = boxes[i - 1][2] + 1 * S, bx - 2 * S, ROW_Y + NODE_H / 2
            draw.line([(ax0, ay), (ax1 - 6 * S, ay)], fill=BLUE, width=3 * S)
            head(draw, (ax1, ay), 0, BLUE, 8 * S)

    # Lifecycle bracket over the row: every workflow step is sequenced by L.
    l_y = ROW_Y - 9 * S
    l_x0 = boxes[0][0]
    l_x1 = (PANEL_W - 16 * S - G_W - 8 * S) if "govern" in spec else boxes[-1][2]
    l_colour = STYLE["CL"][1]
    draw.line([(l_x0, l_y), (l_x1, l_y)], fill=l_colour, width=2 * S)
    for x in (l_x0, l_x1):
        draw.line([(x, l_y), (x, ROW_Y - 3 * S)], fill=l_colour, width=2 * S)
    draw.text((l_x0 + 4 * S, l_y - BRACKET_FONT.size - 3 * S), "Lifecycle [L]",
              font=BRACKET_FONT, fill=INK)

    def below(index, width):
        cx = (boxes[index][0] + boxes[index][2]) / 2
        cx = min(max(cx, 14 * S + width / 2), PANEL_W - 14 * S - width / 2)
        return cx

    if "store" in spec:
        index, icon_name, label = spec["store"]
        cx = below(index, LOW_W)
        if "loop" in spec:  # leave room on the left for the C+L box
            cx = min(cx + 34 * S, PANEL_W - 14 * S - LOW_W / 2)
        box = (cx - LOW_W / 2, LOW_Y, cx + LOW_W / 2, LOW_Y + LOW_H)
        low_box(draw, canvas, box, "O", icon_name, label, "O", optional=not spec.get("o_core", False))
        sx = (boxes[index][0] + boxes[index][2]) / 2
        tip = (cx, LOW_Y - 3 * S)
        start_pt = (sx, ROW_Y + NODE_H + 4 * S)
        angle = math.atan2(tip[1] - start_pt[1], tip[0] - start_pt[0])
        # the shaft stops inside the head along the same direction, so the two stay aligned
        shaft_end = (tip[0] - 7 * S * math.cos(angle), tip[1] - 7 * S * math.sin(angle))
        draw.line([start_pt, shaft_end], fill=BLUE, width=3 * S)
        head(draw, tip, angle, BLUE, 10 * S)
        store_box = box
    else:
        store_box = None

    if "loop" in spec:
        source, target, icon_name, label = spec["loop"]
        tx = (boxes[target][0] + boxes[target][2]) / 2
        sxc = (boxes[source][0] + boxes[source][2]) / 2
        cx = store_box[0] - LOW_W / 2 - 0.1 * PANEL_W if store_box else (tx + sxc) / 2
        cx = max(cx, 14 * S + LOW_W / 2)
        box = (cx - LOW_W / 2, LOW_Y, cx + LOW_W / 2, LOW_Y + LOW_H)
        low_box(draw, canvas, box, "CL", icon_name, label, spec.get("loop_tag", "C+L"))
        # source node -> right side of the C+L box. The control point is mirrored
        # across the chord, so the arc bulges downwards: it leaves the source heading
        # down and arrives pointing left into the box.
        src = boxes[source]
        p0 = (src[0] + 14 * S, src[3] + 4 * S)
        p1 = (box[2] + 4 * S, LOW_Y + LOW_H * 0.3)
        c = (p1[0], p0[1] + 10 * S)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        t = ((c[0] - p0[0]) * dx + (c[1] - p0[1]) * dy) / (dx * dx + dy * dy)
        foot = (p0[0] + t * dx, p0[1] + t * dy)
        return_arrow(draw, p0, p1, (2 * foot[0] - c[0], 2 * foot[1] - c[1]))
        # C+L box -> target node: leaves the top of the box, arrives pointing up
        q1 = (tx, ROW_Y + NODE_H + 6 * S)
        top = LOW_Y - 3 * S
        if box[0] + 12 * S <= tx <= box[2] - 12 * S:
            qx = max(box[0] + 18 * S, min(tx, p1[0] - 40 * S))  # keep clear of the incoming arrow
            return_arrow(draw, (qx, top), q1, (qx, (top + q1[1]) / 2))
        elif tx < box[0]:
            q0 = (box[0] + 22 * S, top)
            return_arrow(draw, q0, q1, (q1[0], q0[1]))
        else:
            q0 = (box[2] - 22 * S, top)
            return_arrow(draw, q0, q1, (q1[0], q0[1]))

    if "govern" in spec:
        index, label = spec["govern"]
        gw, gh = G_W, 26 * S
        gx1 = PANEL_W - 16 * S
        gbox = (gx1 - gw, 10 * S, gx1, 10 * S + gh)
        rounded(draw, gbox, "G", radius=8 * S)
        ic = icon("shield", 22 * S)
        canvas.alpha_composite(ic, (round(gbox[0] + 6 * S), round(gbox[1] + 4 * S)))
        draw.text((gbox[0] + 32 * S, gbox[1] + 6 * S), "Governance [G]", font=SMALL_FONT, fill=INK)
        tx = (boxes[index][0] + boxes[index][2]) / 2
        dashed(draw, [(gbox[0] - 2 * S, gbox[1] + gh / 2), (tx, gbox[1] + gh / 2), (tx, ROW_Y - 2 * S)],
               PANEL_EDGE, 2 * S, dash=3 * S, gap=4 * S)
        # label sits right of the vertical connector, clear of the Lifecycle bracket label
        draw.text((tx - draw.textlength(label, font=SMALL_FONT) - 6 * S, gbox[1] + gh / 2 - SMALL_FONT.size - 1 * S), label, font=SMALL_FONT, fill=INK)

    w = draw.textlength(spec["caption"], font=CAPTION_FONT)
    draw.text(((PANEL_W - w) / 2, PANEL_H + 6 * S), spec["caption"], font=CAPTION_FONT, fill=(0, 0, 0))
    return canvas


def figure(name: str, panels: list[dict]) -> None:
    global PANEL_W
    base = PANEL_W
    gap = 6 * S
    PANEL_W = (ROW_WIDTH - gap * (len(panels) - 1)) // len(panels)
    images = [panel(spec) for spec in panels]
    PANEL_W = base
    out = Image.new("RGB", (ROW_WIDTH, images[0].height), "white")
    x = 0
    for image in images:
        out.paste(image, (x, 0), image)
        x += image.width + gap
    out.save(HERE / f"workflow_{name}.png", dpi=(300, 300))
    print("written", f"workflow_{name}.png", out.size)


R = {  # reusable row nodes: (style, icon, label, tag)
    "llm": lambda label: ("LLM", "brain", label, "LLM"),
    "tools": lambda label: ("T", "tools", label, "T"),
    "exec": lambda label: ("E", "terminal", label, "E"),
    "verify": lambda label: ("V", "verify", label, "V"),
    "ctx": lambda label, tag="C": ("C", "document", label, tag),
}

# "o_core": every example system cited for the form documents Observability, so its O box is
# drawn solid; otherwise the O box is dashed because only some systems of the form record it.
FIGURES = {
    "unit_test": [
        {"caption": "(a) Context-guided test generation",
         "row": [("T", "document", "Source\ninformation", "T"), ("C", "search", "Select\ncontext", "C"),
                 R["llm"]("Generate\ntest"), R["exec"]("Execute"), R["verify"]("Verify")],
         "store": (4, "database", "Store result")},
        {"caption": "(b) Failure-guided test repair",
         "row": [R["ctx"]("Context"), R["llm"]("Generate"), R["tools"]("Tools"), R["exec"]("Execute"),
                 R["verify"]("Verify")],
         "store": (4, "error", "Store error"), "loop": (4, 1, "retry", "Retry test")},
        {"caption": "(c) Adequacy-guided test-suite expansion",
         "row": [R["ctx"]("Target"), R["llm"]("Generate"), R["tools"]("Tools"), R["exec"]("Execute"),
                 R["verify"]("Verify")],
         "store": (4, "gap", "Store gap"), "loop": (4, 0, "target", "Next target")},
    ],
    "oracle": [
        {"caption": "(a) Check-guided assertion refinement", "o_core": True,
         "row": [R["ctx"]("Test\ncontext"), R["llm"]("Generate\nassertion"), R["tools"]("Compile\nor analyse"),
                 R["exec"]("Run\ntest"), R["verify"]("Check\nassertion")],
         "store": (4, "error", "Store error"), "loop": (4, 1, "retry", "Refine assertion")},
        {"caption": "(b) Relation- or property-based checking",
         "row": [R["ctx"]("Target"), R["llm"]("Derive\nrelation"), ("T", "gear", "Prepare\nfollow-up", "T"),
                 R["exec"]("Execute\npaired cases"), R["verify"]("Check\nrelation")],
         "store": (4, "violation", "Store violation")},
    ],
    "system_test_input": [
        {"caption": "(a) Validity-guided repair", "o_core": True,
         "row": [R["ctx"]("Program\ncontext"), R["llm"]("Generate\ninput"), R["tools"]("Build\nor check"),
                 R["exec"]("Run\ntarget"), R["verify"]("Check\nvalidity")],
         "store": (4, "error", "Store error"), "loop": (4, 1, "retry", "Repair input")},
        {"caption": "(b) State-checked interaction", "o_core": True,
         "row": [("C", "window", "Current\nstate", "C"), R["llm"]("Select\naction"), R["tools"]("Execute\naction"),
                 R["exec"]("Run\napplication"), R["verify"]("Check\nstate")],
         "store": (4, "database", "Store state"), "loop": (4, 1, "retry", "Recover / replan"),
         "loop_tag": "L"},  # the examples route the check result through L only
        {"caption": "(c) History-guided exploration", "o_core": True,
         "row": [("C", "database", "Testing\nhistory", "C"), R["llm"]("Choose\ntarget"), R["tools"]("Test\ntools"),
                 R["exec"]("Execute\ntest"), R["verify"]("Check\noutcome")],
         "store": (4, "database", "Store history"), "loop": (4, 0, "chart", "Guide exploration")},
    ],
    "bug_analysis": [
        {"caption": "(a) Program-evidence-based analysis",
         "row": [("T", "document", "Code and\nspecs", "T"), ("C", "search", "Select\nevidence", "C"),
                 R["llm"]("Extract\nsemantics"), R["verify"]("Check\nevidence")],
         "store": (3, "database", "Store finding")},
        {"caption": "(b) Executable-evidence validation",
         "row": [R["ctx"]("Defect\ncontext"), R["llm"]("Generate\ntest"), R["tools"]("Test or\nreplay tools"),
                 R["exec"]("Execute\nversions"), R["verify"]("Compare\nbehaviour")],
         "store": (4, "database", "Store evidence"), "loop": (4, 1, "retry", "Refine test")},
    ],
    "debugging": [
        {"caption": "(a) Tool-feedback-guided investigation", "o_core": True,
         "row": [R["ctx"]("Failure\ncontext"), R["llm"]("Choose\nquery"), R["tools"]("Diagnostic\ntools"),
                 ("C", "document", "Update\ncontext", "C")],
         "store": (3, "database", "Store response"), "loop": (3, 1, "retry", "Next query")},
        {"caption": "(b) Recorded-failure interpretation",
         "row": [R["ctx"]("Failure\nrecord"), R["llm"]("Interpret\nrecord"), ("T", "search", "Check or\nanalyse", "T/V")],
         "store": (2, "database", "Store evidence"), "loop": (2, 1, "chart", "Further search")},
        {"caption": "(c) Execution-guided program transformation",
         "row": [R["ctx"]("Program\ncontext"), R["llm"]("Transform\nvariant"), ("E", "terminal", "Build\nor run", "T/E"),
                 R["verify"]("Check\nproperty")],
         "store": (3, "database", "Store result"), "loop": (3, 1, "retry", "Next variant")},
    ],
    "program_repair": [
        {"caption": "(a) Context-guided patch screening",
         "row": [("T", "search", "Retrieve\ncontext", "T"), R["ctx"]("Combine\ncontext"), R["llm"]("Generate\npatches"),
                 R["exec"]("Run\ntests"), R["verify"]("Select\npatch")],
         "store": (4, "database", "Store patch")},
        {"caption": "(b) Test-guided patch regeneration",
         "row": [R["ctx"]("Bug, test\ncontext"), R["llm"]("Generate\npatch"), R["tools"]("Apply\npatch"),
                 R["exec"]("Run\ntests"), R["verify"]("Check\nresult")],
         "store": (4, "error", "Store feedback"), "loop": (4, 1, "retry", "Next candidate")},
        {"caption": "(c) Tool-guided repair orchestration", "o_core": True,
         "row": [R["ctx"]("Working\nstate"), R["llm"]("Choose\naction"), R["tools"]("Invoke\ntools"),
                 R["exec"]("Execute\n(optional)"), R["verify"]("Check\noutcome")],
         "store": (4, "database", "Store state"), "loop": (4, 1, "chart", "Next action"),
         "govern": (2, "constrains tools")},
    ],
}

if __name__ == "__main__":
    for figure_name, specs in FIGURES.items():
        figure(figure_name, specs)
