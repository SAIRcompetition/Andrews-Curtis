"""Training-set conversion regression (D-2 = prototype convention r1 = x w^-1).
Convert the 424 12-move paths embedded in reference/index.html to ac-r2-v1
and verify every endpoint lands exactly on the ordered target T = (x, y)."""
import json
import pathlib
SRC = pathlib.Path(__file__).resolve().parents[2] / "reference" / "index.html"
line = [l for l in open(SRC).read().split("\n") if l.startswith("const DATA")][0]
items = json.loads(line[len("const DATA = "):].rstrip(";"))["items"]

def red(w):
    o = []
    for a in w:
        if o and o[-1] == -a: o.pop()
        else: o.append(a)
    return tuple(o)
def inv(w): return tuple(-a for a in reversed(w))

GENS = [1, -1, 2, -2]
def ap(s, m):                                   # the 14 atomic moves of ac-r2-v1
    r0, r1 = s
    if m == 0: return (inv(r0), r1)
    if m == 1: return (r0, inv(r1))
    if m == 2: return (red(r0 + r1), r1)
    if m == 3: return (red(r0 + inv(r1)), r1)
    if m == 4: return (r0, red(r1 + r0))
    if m == 5: return (r0, red(r1 + inv(r0)))
    if m < 10: g = GENS[m - 6];  return (red((g,) + r0 + (-g,)), r1)
    g = GENS[m - 10];            return (r0, red((g,) + r1 + (-g,)))

REMAP = {0:0, 1:1, 2:2, 3:4, 4:6, 5:7, 6:8, 7:9, 8:10, 9:11, 10:12, 11:13}
CANON = {((1,),(2,)): [],        ((1,),(-2,)): [1],
         ((-1,),(2,)): [0],      ((-1,),(-2,)): [0,1],
         ((-2,),(1,)): [2,5,2,8],((2,),(-1,)): [3,4,3,10],
         ((-2,),(-1,)): [2,0,4,3],((2,),(1,)): [0,2,5,2,8]}
T = ((1,), (2,))

def ms(n, wv):                                  # D-2: r1 = x w^-1
    return (red(tuple([-1] + [2]*n + [1] + [-2]*(n+1))), red((1,) + inv(tuple(wv))))

ok = fail = 0
lens, peaks, works, olens = [], [], [], []
for it in items:
    p = it.get("path")
    if not p: continue
    s = ms(it["n"], it["wv"])
    mid = [REMAP[m] for m in p]
    for m in mid: s = ap(s, m)
    path = mid + CANON[s]                       # canonicalize to the exact ordered target
    s = ms(it["n"], it["wv"]); peak = len(s[0]) + len(s[1]); work = peak
    for m in path:
        s = ap(s, m); tot = len(s[0]) + len(s[1])
        peak = max(peak, tot); work += tot
    if s == T:
        ok += 1; lens.append(len(path)); peaks.append(peak); works.append(work); olens.append(len(p))
    else:
        fail += 1
def st(a): a = sorted(a); return a[0], a[len(a)//2], a[-1], sum(a)/len(a)
print("D-2 = prototype convention  r1 = x w^-1   |  target = exact ordered (x, y)")
print(f"  converted OK {ok} / failed {fail}")
print("  {:<28} {:>5} {:>7} {:>6} {:>8}".format("", "min", "median", "max", "mean"))
print("  {:<28} {:>5} {:>7} {:>6} {:>8.1f}".format("original 12-move length", *st(olens)))
print("  {:<28} {:>5} {:>7} {:>6} {:>8.1f}".format("ac-r2-v1 length", *st(lens)))
print("  {:<28} {:>5} {:>7} {:>6} {:>8.1f}".format("peak total relator length", *st(peaks)))
print("  {:<28} {:>5} {:>7} {:>6} {:>8.1f}".format("work = sum of per-step totals", *st(works)))
