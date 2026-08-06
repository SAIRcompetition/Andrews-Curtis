import json, collections, random, pathlib
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
    return (red([-1]+[2]*n+[1]+[-2]*(n+1)), red([1]+list(inv(tuple(wv)))))
GENS=[1,-1,2,-2]
def ap(s,m):
    r0,r1=s
    if m==0: return (inv(r0),r1)
    if m==1: return (r0,inv(r1))
    if m==2: return (red(r0+r1),r1)
    if m==3: return (red(r0+inv(r1)),r1)
    if m==4: return (r0,red(r1+r0))
    if m==5: return (r0,red(r1+inv(r0)))
    if m<10: g=GENS[m-6]; return (red((g,)+r0+(-g,)),r1)
    g=GENS[m-10]; return (r0,red((g,)+r1+(-g,)))
INVM={0:0,1:1,2:3,3:2,4:5,5:4,6:7,7:6,8:9,9:8,10:11,11:10,12:13,13:12}

# --- swap identity: is (b,a) reachable from (a,b) for random words? ---
print("=== swap (r0,r1)->(r1,r0) derivable from the 14 moves? ===")
random.seed(7)
def rnd(L):
    w=[]
    while len(w)<L:
        g=random.choice([1,-1,2,-2])
        if w and w[-1]==-g: continue
        w.append(g)
    return tuple(w)
def bibfs(a,b,cap_nodes=400000,maxlen=40):
    if a==b: return 0
    F={a:0}; B={b:0}; qf=deque([a]); qb=deque([b]); n=0
    while qf and qb and n<cap_nodes:
        q,S,O=(qf,F,B) if len(qf)<=len(qb) else (qb,B,F)
        for _ in range(len(q)):
            s=q.popleft(); n+=1
            for m in range(14):
                t=ap(s,m)
                if len(t[0])+len(t[1])>maxlen: continue
                if t in S: continue
                S[t]=S[s]+1
                if t in O: return S[t]+O[t]
                q.append(t)
        if n>=cap_nodes: break
    return None
for L in (2,3,4):
    a,b=rnd(L),rnd(L)
    d=bibfs((a,b),(b,a),maxlen=4*L+14)
    print(f"  a={a} b={b} -> swap distance = {d}")

# --- do same-class open instances connect by short atomic bridges? ---
print()
print("=== bridge search inside reported AC classes (external `cls` labels) ===")
uns=[i for i in items if i["status"]!="trivial"]
byc=collections.defaultdict(list)
for i in uns: byc[i["cls"]].append(i)
for cname in ["14_1","13_1","15_1","16_1"]:
    grp=byc[cname]
    a,b=grp[0],grp[1]
    sa,sb=ms(a["n"],a["wv"]), ms(b["n"],b["wv"])
    la,lb=len(sa[0])+len(sa[1]), len(sb[0])+len(sb[1])
    d=bibfs(sa,sb,cap_nodes=250000,maxlen=max(la,lb)+8)
    print(f"  class {cname} (size {len(grp)}): MS({a['n']},{a['w']}) [len {la}] <-> MS({b['n']},{b['w']}) [len {lb}]  bridge = {d}")

# --- cls leading number vs actual initial length ---
print()
print("=== `cls` leading number vs actual initial total relator length ===")
import re
c=collections.Counter()
for i in uns:
    L0=int(re.match(r'(\d+)_',i["cls"]).group(1))
    act=len(ms(i["n"],i["wv"])[0])+len(ms(i["n"],i["wv"])[1])
    c["cls<act" if L0<act else ("cls=act" if L0==act else "cls>act")]+=1
print(" ",dict(c))
