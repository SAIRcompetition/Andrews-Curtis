def red(w):
    o=[]
    for a in w:
        if o and o[-1]==-a: o.pop()
        else: o.append(a)
    return tuple(o)
def inv(w): return tuple(-a for a in reversed(w))
def show(w): return ''.join({1:'x',-1:'X',2:'y',-2:'Y'}[a] for a in w) or '1'
GENS=[1,-1,2,-2]

PROTO=['r0<-r0^-1','r1<-r1^-1','r0<-r0.r1','r1<-r1.r0',
       'r0<-x r0 X','r0<-X r0 x','r0<-y r0 Y','r0<-Y r0 y',
       'r1<-x r1 X','r1<-X r1 x','r1<-y r1 Y','r1<-Y r1 y']
PROD =['r0<-r0^-1','r1<-r1^-1','r0<-r0.r1','r0<-r0.r1^-1','r1<-r1.r0','r1<-r1.r0^-1',
       'r0<-x r0 X','r0<-X r0 x','r0<-y r0 Y','r0<-Y r0 y',
       'r1<-x r1 X','r1<-X r1 x','r1<-y r1 Y','r1<-Y r1 y']

def ap_proto(s,m):
    r0,r1=s
    if m==0: return (inv(r0),r1)
    if m==1: return (r0,inv(r1))
    if m==2: return (red(r0+r1),r1)
    if m==3: return (r0,red(r1+r0))
    i=(m-4)>>2; g=GENS[(m-4)&3]; r=red((g,)+s[i]+(-g,))
    return (r,r1) if i==0 else (r0,r)
def ap_prod(s,m):
    r0,r1=s
    if m==0: return (inv(r0),r1)
    if m==1: return (r0,inv(r1))
    if m==2: return (red(r0+r1),r1)
    if m==3: return (red(r0+inv(r1)),r1)
    if m==4: return (r0,red(r1+r0))
    if m==5: return (r0,red(r1+inv(r0)))
    if m<10: g=GENS[m-6]; return (red((g,)+r0+(-g,)),r1)
    g=GENS[m-10]; return (r0,red((g,)+r1+(-g,)))

print("="*74)
print("A) The same ID means a different move in the two specs")
print("="*74)
print(f"{'id':>3} | {'prototype (12-move)':<22} | {'production ac-r2-v1 (14-move)':<24} | same?")
print("-"*74)
for i in range(14):
    a = PROTO[i] if i<12 else '(absent)'
    print(f"{i:>3} | {a:<22} | {PROD[i]:<24} | {'YES' if i<12 and PROTO[i]==PROD[i] else 'NO'}")

print()
print("="*74)
print("B) What happens if a prototype path is fed to the production verifier as-is")
print("="*74)
n,wv=1,(-2,)                       # MS(1, y^-1)
start=(red((-1,2,1,-2,-2)), red((1,)+inv(wv)))   # prototype convention r1 = x w^-1
path=[0,7,1,2,7,0,3]               # the recorded path for this instance in the dataset
print(f"Instance MS(1, y^-1), initial state under the prototype convention = ({show(start[0])} , {show(start[1])})")
print(f"recorded path = {path}\n")

for label,fn,p in [("(1) replay with prototype semantics (correct)", ap_proto, path),
                   ("(2) fed to the production verifier as-is (wrong)", ap_prod, path),
                   ("(3) remapped, then fed to the production verifier", ap_prod, [{0:0,1:1,2:2,3:4,4:6,5:7,6:8,7:9,8:10,9:11,10:12,11:13}[m] for m in path])]:
    s=start; trace=[]
    for m in p:
        s=fn(s,m); trace.append(f"{m}:({show(s[0])},{show(s[1])})")
    tag = "reached (x,y) OK" if s==((1,),(2,)) else ("loose trivial ~" if len(s[0])==1 and len(s[1])==1 and abs(s[0][0])!=abs(s[1][0]) else "**NOT trivial** x")
    print(f"{label}\n   path {p}\n   {' -> '.join(trace)}\n   endpoint ({show(s[0])},{show(s[1])})  {tag}\n")

print("="*74)
print("C) r1 convention: x^-1 w  vs  x w^-1")
print("="*74)
print(f"{'w':<20} | {'reqs r1 = x^-1 w':<18} | {'prototype r1 = x w^-1':<20} | moves apart")
print("-"*74)
for w in [(2,), (-2,), (2,1,-2), (-1,-2,1,-2)]:
    A=red((-1,)+w); B=red((1,)+inv(w))
    # A --move1--> inv(A) --move10--> x inv(A) X
    step1=inv(A); step2=red((1,)+step1+(-1,))
    ok = (step2==B)
    print(f"{show(w):<20} | {show(A):<18} | {show(B):<20} | {'2 (move 1 -> move 10) OK' if ok else 'MISMATCH'}")
print()
print("Derivation: (x^-1 w)^-1 = w^-1 x, then conjugate by x: x (w^-1 x) x^-1 = x w^-1  OK")
print("Note (x^-1 w)^-1 = w^-1 x  !=  x w^-1, so the two are NOT inverses of each other.")
