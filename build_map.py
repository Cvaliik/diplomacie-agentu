"""build_map.py

Jednorazovy generator mapy uzemi pro web (BUILD.md cast 7). Web mapu jen obarvuje.

Z npc.json vezme souradnice a adjacency a vygeneruje:
  web/map.json        uzemi {id, polygon, capital_xy}, namorni trasy, obrys pevniny
  web/map.svg         kontrolni obrazek
  web/map_seeds.json  posunute polohy hlavnich mest (npc.json se nemeni)

Postup (ciste Python, bez numpy):
  1. Graf adjacency neni rovinny (Kalvera, Velmora, Ilme, Aurelie a Meridia sousedi kazdy s kazdym),
     proto se z nej odebere co nejmene hran a zbytek se nakresli bez krizeni; uzly se posunou jen
     tolik, kolik je treba. Odebrane hrany se kresli jako namorni trasy mezi hlavnimi mesty.
  2. Uzemi statu je okoli jeho "hvezdy": hlavni mesto a jeho cast kazde hrany k sousedovi
     (vetsi lid, vetsi cast hrany). Sousede tak maji spolecnou hranici vzdy.
  3. Ve stenach kresby se ctyrmi a vice staty vznikne jezero, aby se protilehle staty nedotkly;
     pobrezi je vzdalenost od kostry se sumem. Souradnice bunek jsou deformovane fraktalnim sumem,
     hranice proto nevypadaji jako Voronoi.

    python build_map.py
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent
W, H = 1000, 700
STEP = 4
SEED = 20260916
SHORT = {"A": "Kalvera", "B": "Ostrogard"}


# --------------------------------------------------------------------------
# sum
# --------------------------------------------------------------------------

def _hash(ix, iy, s):
    n = (ix * 374761393 + iy * 668265263 + s * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def _vnoise(x, y, s):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, s), _hash(ix + 1, iy, s)
    c, d = _hash(ix, iy + 1, s), _hash(ix + 1, iy + 1, s)
    top = a + (b - a) * ux
    return top + ((c + (d - c) * ux) - top) * uy


def fbm(x, y, s, octaves=5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * (_vnoise(x * freq, y * freq, s + 17 * o) - 0.5)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


# --------------------------------------------------------------------------
# geometrie
# --------------------------------------------------------------------------

def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def crosses(p1, p2, p3, p4):
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


# --------------------------------------------------------------------------
# svet a rovinna kresba
# --------------------------------------------------------------------------

def load_world():
    npc = json.loads((ROOT / "npc.json").read_text(encoding="utf-8"))
    nodes = {}
    for pid in ("A", "B"):
        p = npc["players"][pid]
        nodes[pid] = {"name": SHORT[pid], "full": p["name"], "x0": p["x"], "y0": p["y"],
                      "pop": {"A": 230, "B": 210}[pid], "kind": "player"}
    for n in npc["npc"]:
        nodes[n["id"]] = {"name": n["name"], "full": n["name"], "x0": n["x"], "y0": n["y"],
                          "pop": n["pop"], "kind": n.get("kind", "normal")}
    edges = set()
    for a, bs in npc["adjacency"].items():
        for b in bs:
            edges.add(tuple(sorted((a, b))))
    return nodes, edges


def crossing_count(pos, edges):
    cnt = 0
    for (a, b), (c, d) in itertools.combinations(list(edges), 2):
        if len({a, b, c, d}) == 4 and crosses(pos[a], pos[b], pos[c], pos[d]):
            cnt += 1
    return cnt


def crowding(pos, edges, min_gap=38.0):
    """Trest za uzel prilis blizko ciziho uzlu nebo hrany (uzemi by byla tenka)."""
    pen = 0.0
    for a, b in itertools.combinations(list(pos), 2):
        d = math.dist(pos[a], pos[b])
        if d < 2 * min_gap:
            pen += 2 * min_gap - d
    for n in pos:
        for a, b in edges:
            if n in (a, b):
                continue
            d = seg_dist(pos[n][0], pos[n][1], pos[a][0], pos[a][1], pos[b][0], pos[b][1])
            if d < min_gap:
                pen += min_gap - d
    return pen


def planar_layout(nodes, edges, rng, iters, coastal=()):
    """Posune uzly tak, aby se hrany nekrizily a uzly v `coastal` lezely na vnejsim obrysu (pobrezi).
    Vraci (pozice, pocet krizeni, pocet vnitrozemskych koncu tras, posun)."""
    pos = {k: [float(v["x0"]), float(v["y0"])] for k, v in nodes.items()}

    def inland(p):
        outer, _ = faces(p, edges)
        return sum(1 for k in coastal if k not in outer)

    def cost(p):
        drift = sum(math.hypot(p[k][0] - nodes[k]["x0"], p[k][1] - nodes[k]["y0"]) for k in p)
        cr = crossing_count(p, edges)
        land = inland(p) if (cr == 0 and coastal) else len(coastal)
        return 1000 * cr + 400 * land + 3 * crowding(p, edges) + 0.3 * drift

    cur = cost(pos)
    ids = list(pos)
    for it in range(iters):
        k = rng.choice(ids)
        old = list(pos[k])
        st = 70 * (1 - it / iters) + 6
        pos[k][0] = min(W - 70, max(70, pos[k][0] + rng.gauss(0, st)))
        pos[k][1] = min(H - 70, max(70, pos[k][1] + rng.gauss(0, st)))
        if (k == "A" and pos[k][0] > 260) or (k == "B" and pos[k][0] < 740):
            pos[k] = old
            continue
        c = cost(pos)
        if c <= cur:
            cur = c
        else:
            pos[k] = old
    drift = sum(math.hypot(pos[k][0] - nodes[k]["x0"], pos[k][1] - nodes[k]["y0"]) for k in pos)
    cr = crossing_count(pos, edges)
    return pos, cr, (inland(pos) if cr == 0 else len(coastal)), drift


def choose_removed(nodes, edges, rng):
    """Nejmensi mnozina odebranych hran s kresbou bez krizeni, kde oba konce kazde trasy maji pobrezi.

    Graf adjacency obsahuje uplny graf na peti uzlech (Kalvera, Velmora, Ilme, Aurelie, Meridia),
    proto se odebira z jeho hran; trasa po mori potrebuje, aby oba jeji konce lezely na pobrezi.
    """
    k5 = ["A", "N1", "N8", "N11", "N13"]
    cands = [e for e in (tuple(sorted(q)) for q in itertools.combinations(k5, 2)) if e in edges]
    options = [{e} for e in cands] + [set(q) for q in itertools.combinations(cands, 2)]
    best = None
    for rem in options:
        coastal = sorted({n for e in rem for n in e})
        pos, cr, inland, drift = planar_layout(nodes, edges - rem, random.Random(rng.random()), 2500, coastal)
        label = " a ".join("%s-%s" % e for e in sorted(rem))
        print("   bez %s: krizeni %d, vnitrozemskych koncu %d, posun %.0f" % (label, cr, inland, drift), flush=True)
        if cr == 0 and inland == 0 and (best is None or (len(rem), drift) < (len(best[0]), best[2])):
            best = (rem, pos, drift)
    return best


def faces(pos, edges):
    """Steny rovinne kresby (seznamy uzlu). Vnejsi stena ma nejvetsi plochu."""
    nbr = {k: [] for k in pos}
    for a, b in edges:
        nbr[a].append(b)
        nbr[b].append(a)
    for k in nbr:
        nbr[k].sort(key=lambda m: math.atan2(pos[m][1] - pos[k][1], pos[m][0] - pos[k][0]))
    used = set()
    out = []
    for a, b in edges:
        for u, v in ((a, b), (b, a)):
            if (u, v) in used:
                continue
            face, cu, cv = [], u, v
            while (cu, cv) not in used:
                used.add((cu, cv))
                face.append(cu)
                lst = nbr[cv]
                w = lst[(lst.index(cu) - 1) % len(lst)]
                cu, cv = cv, w
            out.append(face)

    def area(f):
        return 0.5 * sum(pos[f[i]][0] * pos[f[(i + 1) % len(f)]][1] - pos[f[(i + 1) % len(f)]][0] * pos[f[i]][1]
                         for i in range(len(f)))
    out.sort(key=lambda f: abs(area(f)), reverse=True)
    return out[0], out[1:]


# --------------------------------------------------------------------------
# rastr uzemi
# --------------------------------------------------------------------------

WATER, HIGHLAND, SHORE = -1, -2, -3     # more a jezera, vysocina bez vlastnika, neobydleny breh jezera


def blocker_faces(pos, inner):
    """Steny se ctyrmi a vice staty; nejjiznejsi je vysocina, ostatni jezera."""
    fs = [[pos[n] for n in f] for f in inner if len(f) >= 4]
    if not fs:
        return []
    cy = [sum(q[1] for q in f) / len(f) for f in fs]
    south = cy.index(max(cy))
    return [(f, "vysocina" if k == south else "jezero") for k, f in enumerate(fs)]


def rasterize(nodes, pos, edges, outer, inner, warp, coast_base, cut_outer=False):
    ids = list(nodes)
    idx = {k: i for i, k in enumerate(ids)}
    segs = []
    for a, b in edges:
        pa, pb = nodes[a]["pop"], nodes[b]["pop"]
        t = min(0.72, max(0.28, pa ** 1.6 / (pa ** 1.6 + pb ** 1.6)))
        mx = pos[a][0] + (pos[b][0] - pos[a][0]) * t
        my = pos[a][1] + (pos[b][1] - pos[a][1]) * t
        segs.append((idx[a], pos[a][0], pos[a][1], mx, my))
        segs.append((idx[b], pos[b][0], pos[b][1], mx, my))
    reach = [coast_base + 4.2 * math.sqrt(nodes[k]["pop"]) for k in ids]
    blockers = blocker_faces(pos, inner)
    outer_poly = [pos[n] for n in outer]
    caps = [tuple(pos[k]) for k in ids]
    nx, ny = W // STEP, H // STEP
    lab = [WATER] * (nx * ny)
    for j in range(3, ny - 3):
        for i in range(3, nx - 3):
            x, y = (i + 0.5) * STEP, (j + 0.5) * STEP
            wx = x + warp * fbm(x / 150.0, y / 150.0, 3) + 0.35 * warp * fbm(x / 38.0, y / 38.0, 21)
            wy = y + warp * fbm(x / 150.0 + 31.7, y / 150.0 + 11.3, 5) + 0.35 * warp * fbm(x / 38.0 + 7.1, y / 38.0 + 3.3, 23)
            best, owner = 1e18, -1
            for o, ax, ay, bx, by in segs:
                d = seg_dist(wx, wy, ax, ay, bx, by)
                if d < best:
                    best, owner = d, o
            coast = reach[owner] + 46.0 * fbm(x / 110.0, y / 110.0, 9)
            value = owner if best <= coast else WATER
            inland_water = value == WATER
            edge_d = min(x, y, W - x, H - y)
            near_cap = min(math.hypot(x - cx, y - cy) for cx, cy in caps) < 45.0
            if not near_cap and edge_d < 58.0 + 260.0 * fbm(x / 210.0 + 5.5, y / 210.0 + 2.2, 29) + 24.0 * fbm(x / 35.0, y / 35.0, 31):
                value = WATER
                inland_water = False
            if value != WATER or inland_water:
                for poly, kind in blockers:
                    if point_in_poly(wx, wy, poly):
                        dmin = min(seg_dist(wx, wy, *poly[k], *poly[(k + 1) % len(poly)]) for k in range(len(poly)))
                        block = 30.0 + 34.0 * fbm(x / 70.0, y / 70.0, 13) + 10.0 * fbm(x / 20.0, y / 20.0, 15)
                        if dmin > block:
                            if kind == "vysocina":
                                value = HIGHLAND
                            elif dmin > block + 26.0 + 14.0 * fbm(x / 30.0, y / 30.0, 17):
                                value = WATER       # mensi jezero
                            else:
                                value = SHORE       # neobydleny breh kolem jezera
                        elif inland_water:
                            value = owner      # voda uvnitr steny u brehu je pevnina statu
                        break
            if cut_outer and value >= 0 and best > 0.8 * coast and not point_in_poly(wx, wy, outer_poly):
                value = WATER
            lab[j * nx + i] = value
    return cleanup(lab, nx, ny, len(ids)), nx, ny


def cleanup(lab, nx, ny, n):
    """Kazde uzemi drzi jen nejvetsi souvislou cast; odtrzene kousky se stanou vodou."""
    seen = [False] * len(lab)
    comps = {r: [] for r in range(n)}
    for s0 in range(len(lab)):
        r = lab[s0]
        if r < 0 or seen[s0]:
            continue
        stack, comp = [s0], []
        seen[s0] = True
        while stack:
            c = stack.pop()
            comp.append(c)
            ci, cj = c % nx, c // nx
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = ci + di, cj + dj
                if 0 <= ii < nx and 0 <= jj < ny:
                    q = jj * nx + ii
                    if not seen[q] and lab[q] == r:
                        seen[q] = True
                        stack.append(q)
        comps[r].append(comp)
    for r, cs in comps.items():
        cs.sort(key=len, reverse=True)
        for comp in cs[1:]:
            for c in comp:
                lab[c] = -1
    return lab


def borders(lab, nx, ny, min_len):
    cnt = {}
    for j in range(ny):
        for i in range(nx):
            a = lab[j * nx + i]
            if a < 0:
                continue
            for di, dj in ((1, 0), (0, 1)):
                ii, jj = i + di, j + dj
                if ii < nx and jj < ny:
                    b = lab[jj * nx + ii]
                    if b >= 0 and b != a:
                        key = (min(a, b), max(a, b))
                        cnt[key] = cnt.get(key, 0) + 1
    return {k for k, v in cnt.items() if v >= min_len}


# --------------------------------------------------------------------------
# polygony
# --------------------------------------------------------------------------

def trace_loops(lab, nx, ny, target):
    def inside(i, j):
        if not (0 <= i < nx and 0 <= j < ny):
            return False
        v = lab[j * nx + i]
        return v != WATER if target is None else v == target
    edges = {}
    for j in range(ny):
        for i in range(nx):
            if not inside(i, j):
                continue
            if not inside(i, j - 1):
                edges.setdefault((i, j), []).append((i + 1, j))
            if not inside(i + 1, j):
                edges.setdefault((i + 1, j), []).append((i + 1, j + 1))
            if not inside(i, j + 1):
                edges.setdefault((i + 1, j + 1), []).append((i, j + 1))
            if not inside(i - 1, j):
                edges.setdefault((i, j + 1), []).append((i, j))
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur = [start], start
        while True:
            outs = edges.get(cur)
            if not outs:
                break
            nxt = outs.pop()
            if not outs:
                del edges[cur]
            loop.append(nxt)
            cur = nxt
            if cur == start:
                break
        if len(loop) > 6:
            loops.append([(p[0] * STEP, p[1] * STEP) for p in loop[:-1]])
    return loops


def smooth(loop, window=2, passes=2):
    """Klouzavy prumer po jednotkovych krocich rastru; sdilena hranice vyjde u obou statu stejne."""
    pts = list(loop)
    n = len(pts)
    if n < 2 * window + 1:
        return [[round(x, 1), round(y, 1)] for x, y in pts]
    for _ in range(passes):
        new = []
        for k in range(n):
            sx = sy = 0.0
            for d in range(-window, window + 1):
                q = pts[(k + d) % n]
                sx += q[0]
                sy += q[1]
            new.append((sx / (2 * window + 1), sy / (2 * window + 1)))
        pts = new
    return [[round(x, 1), round(y, 1)] for x, y in pts[::2]]


def path_d(rings):
    return " ".join("M" + " L".join("%s,%s" % (x, y) for x, y in r) + " Z" for r in rings)


# --------------------------------------------------------------------------
# hlavni beh
# --------------------------------------------------------------------------

def water_distance(lab, nx, ny):
    """Vzdalenost vodni bunky od pevniny (v bunkach), BFS."""
    INF = 10 ** 9
    dist = [INF] * len(lab)
    queue = []
    for c, v in enumerate(lab):
        if v != WATER:
            dist[c] = 0
            queue.append(c)
    head = 0
    while head < len(queue):
        c = queue[head]
        head += 1
        ci, cj = c % nx, c // nx
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = ci + di, cj + dj
            if 0 <= ii < nx and 0 <= jj < ny:
                q = jj * nx + ii
                if dist[q] > dist[c] + 1:
                    dist[q] = dist[c] + 1
                    queue.append(q)
    return dist


def outer_sea(lab, nx, ny):
    """Vodni bunky spojene s okrajem platna (bez vnitrozemskych jezer)."""
    sea = [False] * len(lab)
    stack = [c for c in range(len(lab)) if lab[c] == WATER and (c % nx in (0, nx - 1) or c // nx in (0, ny - 1))]
    for c in stack:
        sea[c] = True
    while stack:
        c = stack.pop()
        ci, cj = c % nx, c // nx
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = ci + di, cj + dj
            if 0 <= ii < nx and 0 <= jj < ny:
                q = jj * nx + ii
                if not sea[q] and lab[q] == WATER:
                    sea[q] = True
                    stack.append(q)
    return sea


def sea_route(lab, nx, ny, sea, wdist, a, b, cap_a, cap_b):
    """Nejlevnejsi cesta z hlavniho mesta a do b: jen pres vlastni uzemi obou a vnejsi more, s odstupem od brehu."""
    import heapq
    start = int(cap_a[1] // STEP) * nx + int(cap_a[0] // STEP)
    goal = int(cap_b[1] // STEP) * nx + int(cap_b[0] // STEP)
    best = {start: 0.0}
    prev = {}
    heap = [(0.0, start)]
    while heap:
        d, c = heapq.heappop(heap)
        if c == goal:
            break
        if d > best.get(c, 1e18):
            continue
        ci, cj = c % nx, c // nx
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ii, jj = ci + di, cj + dj
            if not (0 <= ii < nx and 0 <= jj < ny):
                continue
            q = jj * nx + ii
            v = lab[q]
            if v == WATER:
                if not sea[q]:
                    continue
                step = 1.0 + 6.0 / (1.0 + wdist[q]) + 0.8 * max(0, wdist[q] - 4)   # kousek od brehu
            elif v in (a, b):
                step = 3.0                                 # vlastni uzemi jen k pobrezi
            else:
                continue                                   # cizi uzemi nikdy
            nd = d + step * (1.414 if di and dj else 1.0)
            if nd < best.get(q, 1e18):
                best[q] = nd
                prev[q] = c
                heapq.heappush(heap, (nd, q))
    if goal not in prev:
        return None
    cells = [goal]
    while cells[-1] != start:
        cells.append(prev[cells[-1]])
    cells.reverse()
    pts = [((c % nx + 0.5) * STEP, (c // nx + 0.5) * STEP) for c in cells]
    pts[0], pts[-1] = tuple(cap_a), tuple(cap_b)
    # vyhlazeni (konce drzi)
    for _ in range(3):
        pts = [pts[0]] + [((pts[k - 1][0] + pts[k][0] + pts[k + 1][0]) / 3, (pts[k - 1][1] + pts[k][1] + pts[k + 1][1]) / 3)
                          for k in range(1, len(pts) - 1)] + [pts[-1]]
    pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
    mid = len(pts) // 2
    ang = math.degrees(math.atan2(pts[mid + 1][1] - pts[mid - 1][1], pts[mid + 1][0] - pts[mid - 1][0])) if 0 < mid < len(pts) - 1 else 0.0
    return {"from": a, "to": b, "path": [[round(x, 1), round(y, 1)] for x, y in pts],
            "ship": [round(pts[mid][0], 1), round(pts[mid][1], 1), round(ang, 1)]}


def centroid(lab, nx, value, restrict=None):
    cells = [c for c, v in enumerate(lab) if v == value and (restrict is None or restrict(c))]
    if not cells:
        return None
    return [round(sum((c % nx + 0.5) * STEP for c in cells) / len(cells), 1),
            round(sum((c // nx + 0.5) * STEP for c in cells) / len(cells), 1)]


PAPER, SEA, INK, GOLD = "#efe8da", "#d9e0e2", "#2a2825", "#b8902a"
SHIP = "M-7,0 L7,0 L4,3.5 L-4,3.5 Z M0,0 L0,-8 L5,-2 Z"


def render_svg(regions, land, lakes, highlands, shores, routes, nodes):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H),
           '<defs><pattern id="srafy" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
           '<line x1="0" y1="0" x2="0" y2="7" stroke="%s" stroke-width="0.8" opacity="0.55"/></pattern></defs>' % INK,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SEA),
           '<path d="%s" fill="%s" fill-rule="evenodd"/>' % (path_d(land), PAPER)]
    for r in regions:
        fallen = nodes[r["id"]]["kind"] == "fallen"
        out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" fill-rule="evenodd"/>' % (
            path_d(r["polygon"]), PAPER, GOLD if fallen else INK, "2.5" if fallen else "0.9"))
    for h in highlands:
        out.append('<path d="%s" fill="url(#srafy)" stroke="%s" stroke-width="0.9" fill-rule="evenodd"/>' % (path_d(h["polygon"]), INK))
    for sh in shores:
        out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.9" fill-rule="evenodd"/>' % (path_d(sh["polygon"]), PAPER, INK))
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8" fill-rule="evenodd"/>' % (path_d(land), INK))
    for rt in routes:
        d = "M" + " L".join("%s,%s" % tuple(q) for q in rt["path"])
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.2" stroke-dasharray="1 5" stroke-linecap="round"/>' % (d, INK))
        x, y, a = rt["ship"]
        out.append('<path d="%s" transform="translate(%s,%s) rotate(%s)" fill="%s"/>' % (SHIP, x, y, a if -90 <= a <= 90 else a - 180, INK))
    for r in regions:
        x, y = r["capital_xy"]
        out.append('<circle cx="%s" cy="%s" r="3.5" fill="%s"/>' % (x, y, INK))
        out.append('<text x="%s" y="%s" font-family="Georgia, serif" font-size="15" font-variant="small-caps" '
                   'letter-spacing="0.5" fill="%s">%s</text>' % (x + 7, y + 5, INK, nodes[r["id"]]["name"]))
    for item in lakes + highlands:
        if item.get("name") and item.get("label_xy"):
            x, y = item["label_xy"]
            out.append('<text x="%s" y="%s" font-family="Georgia, serif" font-size="13" font-style="italic" '
                       'text-anchor="middle" fill="%s">%s</text>' % (x, y, INK, item["name"]))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rng = random.Random(SEED)
    nodes, edges = load_world()
    ids = list(nodes)
    print("hran v adjacency: %d, krizeni v puvodnich souradnicich: %d" % (
        len(edges), crossing_count({k: (v["x0"], v["y0"]) for k, v in nodes.items()}, edges)))
    seeds_path = ROOT / "web" / "map_seeds.json"
    if "--reuse" in sys.argv and seeds_path.exists():
        saved = json.loads(seeds_path.read_text(encoding="utf-8"))
        pos = {k: [saved["uzly"][k]["x"], saved["uzly"][k]["y"]] for k in ids}
        removed = {tuple(e) for e in saved["odebrane_hrany"]}
        print("1. rovinna kresba z web/map_seeds.json (--reuse)")
    else:
        print("1. rovinna kresba (konce namornich tras na pobrezi)")
        removed, pos, drift = choose_removed(nodes, edges, rng)
    kept = edges - removed
    outer, inner = faces(pos, kept)
    print("   odebrano %s, sten %d, blokovacich %d" % (sorted(removed), len(inner), len(blocker_faces(pos, inner))))

    print("2. rastr uzemi")
    result = None
    for warp, cut in ((34.0, False), (34.0, True), (24.0, True), (14.0, True), (6.0, True)):
        lab, nx, ny = rasterize(nodes, pos, kept, outer, inner, warp, coast_base=38.0, cut_outer=cut)
        got = {tuple(sorted((ids[a], ids[b]))) for a, b in borders(lab, nx, ny, 5)}
        missing, extra = kept - got, got - kept
        print("   deformace %.0f, orez obrysem %s: chybi %d, navic %d" % (
            warp, "ano" if cut else "ne", len(missing), len(extra)), flush=True)
        if result is None or len(missing) + 2 * len(extra) < len(result[3]) + 2 * len(result[4]):
            result = (lab, nx, ny, missing, extra, warp)
        if not missing and not extra:
            break
    lab, nx, ny, missing, extra, warp = result

    print("3. namorni trasy")
    sea = outer_sea(lab, nx, ny)
    wdist = water_distance(lab, nx, ny)
    idx = {k: i for i, k in enumerate(ids)}
    routes, failed = [], []
    for a, b in sorted(removed | missing):
        rt = sea_route(lab, nx, ny, sea, wdist, idx[a], idx[b], pos[a], pos[b])
        if rt is None:
            failed.append((a, b))
            continue
        rt["from"], rt["to"] = a, b
        routes.append(rt)

    regions = []
    for i, k in enumerate(ids):
        rings = sorted((smooth(l) for l in trace_loops(lab, nx, ny, i)), key=len, reverse=True)
        regions.append({"id": k, "name": nodes[k]["full"], "polygon": rings,
                        "capital_xy": [round(pos[k][0], 1), round(pos[k][1], 1)],
                        "cells": sum(1 for v in lab if v == i)})
    land = [smooth(l) for l in trace_loops(lab, nx, ny, None)]
    highlands, lakes, shores = [], [], []
    hl = [smooth(l) for l in trace_loops(lab, nx, ny, HIGHLAND)]
    if hl:
        highlands.append({"name": "Pustá vysočina", "polygon": hl, "label_xy": centroid(lab, nx, HIGHLAND)})
    sh = [smooth(l) for l in trace_loops(lab, nx, ny, SHORE)]
    if sh:
        shores.append({"polygon": sh})
        # jezero = voda obklopena neobydlenym brehem (ne vnejsi more)
        def lake_cell(c):
            ci, cj = c % nx, c // nx
            return (not sea[c]) and any(0 <= ci + di < nx and 0 <= cj + dj < ny and lab[(cj + dj) * nx + ci + di] == SHORE
                                        for di in range(-3, 4) for dj in range(-3, 4))
        lake_xy = centroid(lab, nx, WATER, restrict=lake_cell)
        lakes.append({"name": "Ardanské jezero", "label_xy": lake_xy})

    web = ROOT / "web"
    web.mkdir(exist_ok=True)
    (web / "map.json").write_text(json.dumps({
        "width": W, "height": H,
        "regions": [{k: v for k, v in r.items() if k != "cells"} for r in regions],
        "land": land, "highlands": highlands, "shores": shores, "lakes": lakes,
        "sea_routes": routes,
    }, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (web / "map_seeds.json").write_text(json.dumps({
        "odebrane_hrany": sorted(list(e) for e in removed),
        "uzly": {k: {"x": round(pos[k][0], 3), "y": round(pos[k][1], 3),
                     "posun": round(math.hypot(pos[k][0] - nodes[k]["x0"], pos[k][1] - nodes[k]["y0"]), 1)}
                 for k in ids}}, ensure_ascii=False, indent=1), encoding="utf-8")
    (web / "map.svg").write_text(render_svg(regions, land, lakes, highlands, shores, routes, nodes), encoding="utf-8")

    print()
    print("REPORT SOUSEDSTVÍ")
    n_routes = len(removed | missing)
    print("  hran v adjacency: %d, pozemní hranice sedí: %d, námořní trasy: %d, přebývá: %d (deformace hranic %.0f)" % (
        len(edges), len(edges) - n_routes, n_routes, len(extra), warp))
    for rt in routes:
        a, b = rt["from"], rt["to"]
        why = "nerovinná pětice" if tuple(sorted((a, b))) in removed else "hranice se na rastru nevešla"
        print("  námořní trasa po moři: %s (%s) - %s (%s), %d bodů, důvod: %s" % (
            a, nodes[a]["name"], b, nodes[b]["name"], len(rt["path"]), why))
    for a, b in failed:
        print("  TRASA NENALEZENA: %s - %s" % (a, b))
    for a, b in sorted(extra):
        print("  přebývá: %s (%s) - %s (%s)" % (a, nodes[a]["name"], b, nodes[b]["name"]))
    print("  vysočina: %s, jezero: %s" % ("ano" if highlands else "ne", "ano" if lakes else "ne"))
    total = sum(r["cells"] for r in regions) or 1
    pops = sum(v["pop"] for v in nodes.values())
    print("  plocha / lid (%): " + ", ".join("%s %.0f/%.0f" % (
        nodes[r["id"]]["name"], 100 * r["cells"] / total, 100 * nodes[r["id"]]["pop"] / pops) for r in regions))
    print("  posun hlavních měst (px): " + ", ".join("%s %.0f" % (nodes[k]["name"], math.hypot(
        pos[k][0] - nodes[k]["x0"], pos[k][1] - nodes[k]["y0"])) for k in ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
