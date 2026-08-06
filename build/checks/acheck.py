import json, re, collections, pathlib
from collections import deque

SRC = pathlib.Path(__file__).resolve().parents[2] / "reference" / "index.html"
line=[l for l in open(SRC).read().split("\n") if l.startswith("const DATA")][0]
items=json.loads(line[len("const DATA = "):].rstrip(";"))["items"]

def red(w):
    o=[]
    for a in w:
        if o and o[-1]==-a: o.pop()
        else: o.append(a)
    return tuple(o)
def inv(w): return tuple(-a for a in reversed(w))
def ms(n,wv):
    r0=[-1]+[2]*n+[1]+[-2]*(n+1)
    return (red(r0), red([1]+list(inv(tuple(wv)))))

# ---- PRODUCTION 14-move spec (proposed ac-r2-v1) ----
# 0: r0<-r0^-1        1: r1<-r1^-1
# 2: r0<-r0*r1        3: r0<-r0*r1^-1     4: r1<-r1*r0     5: r1<-r1*r0^-1
# 6..9:  r0 <- g r0 g^-1 for g in x,x^-1,y,y^-1
# 10..13: r1 <- g r1 g^-1 for g in x,x^-1,y,y^-1
GENS=[1,-1,2,-2]
def apply14(s,m):
    r0,r1=s
    if m==0: return (inv(r0),r1)
    if m==1: return (r0,inv(r1))
    if m==2: return (red(r0+r1),r1)
    if m==3: return (red(r0+inv(r1)),r1)
    if m==4: return (r0,red(r1+r0))
    if m==5: return (r0,red(r1+inv(r0)))
    if 6<=m<=9:
        g=GENS[m-6]; return (red((g,)+r0+(-g,)),r1)
    if 10<=m<=13:
        g=GENS[m-10]; return (r0,red((g,)+r1+(-g,)))
    raise ValueError(m)

# ---- PROTOTYPE 12-move spec (reference/index.html) ----
def apply12(s,m):
    r0,r1=s
    if m==0: return (inv(r0),r1)
    if m==1: return (r0,inv(r1))
    if m==2: return (red(r0+r1),r1)
    if m==3: return (r0,red(r1+r0))
    i=(m-4)>>2; g=GENS[(m-4)&3]
    r=red((g,)+s[i]+(-g,))
    return (r,r1) if i==0 else (r0,r)

TARGET=((1,),(2,))
def loose_trivial(s):
    return len(s[0])==1 and len(s[1])==1 and abs(s[0][0])!=abs(s[1][0])

# ---- Q1: BFS cost from each "loose trivial" state to exact (x,y) under 14 moves ----
starts=[]
for a in (1,-1,2,-2):
    for b in (1,-1,2,-2):
        if abs(a)!=abs(b): starts.append(((a,),(b,)))
print("=== Q1: cost to canonicalize loose-trivial -> exact ((x),(y)) under 14 moves ===")
def bfs(start,goal,apply,nmoves,cap=12,maxlen=30):
    if start==goal: return 0,[]
    seen={start}; q=deque([(start,[])])
    while q:
        s,p=q.popleft()
        if len(p)>=cap: continue
        for m in range(nmoves):
            t=apply(s,m)
            if len(t[0])+len(t[1])>maxlen: continue
            if t in seen: continue
            if t==goal: return len(p)+1,p+[m]
            seen.add(t); q.append((t,p+[m]))
    return None,None
costs={}
for st in starts:
    c,p=bfs(st,TARGET,apply14,14)
    costs[st]=c
    print(f"  {st} -> exact target: {c} moves   path={p}")
print("  max canonicalization cost:", max(costs.values()))

# ---- Q2: replay the 424 recorded paths under the 12-move spec, then measure extra cost ----
print()
print("=== Q2: replay 424 recorded prototype paths ===")
ok=0; bad=0; exact=0; extra=collections.Counter(); lens=[]
peaks=[]
for it in items:
    p=it.get("path")
    if not p: continue
    s=ms(it["n"],it["wv"]); peak=len(s[0])+len(s[1])
    for m in p:
        s=apply12(s,m); peak=max(peak,len(s[0])+len(s[1]))
    if loose_trivial(s):
        ok+=1; lens.append(len(p)); peaks.append(peak)
        if s==TARGET: exact+=1
        else: extra[costs[s]]+=1
    else: bad+=1
print(f"  replayed OK (loose trivial): {ok}   failed: {bad}")
print(f"  already exactly ((x),(y)): {exact}")
print(f"  need extra canonicalization moves: {dict(sorted(extra.items()))}")
lens.sort(); peaks.sort()
print(f"  path length under 12-move metric: min={lens[0]} med={lens[len(lens)//2]} max={lens[-1]} mean={sum(lens)/len(lens):.1f}")
print(f"  peak total relator length: min={peaks[0]} med={peaks[len(peaks)//2]} max={peaks[-1]}")

# ---- Q3: how many of the 1190 have NO public replayable certificate ----
print()
print("=== Q3: certificate coverage of MS-1190 ===")
c=collections.Counter()
for it in items:
    c[(it["status"], bool(it.get("path")))]+=1
for k,v in sorted(c.items()): print("  status=%-9s has_path=%-5s : %d"%(k[0],k[1],v))
