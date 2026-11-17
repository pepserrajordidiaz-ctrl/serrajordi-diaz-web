# Site geometry from the on-site measurements (Nov 2026), anchored on the Cadastre façade and side directions.
import math, json
A=(-5.01,6.30); Bc=(4.11,7.65)
def sub(p,q): return (p[0]-q[0],p[1]-q[1])
def add(p,q): return (p[0]+q[0],p[1]+q[1])
def sc(p,k): return (p[0]*k,p[1]*k)
def unit(p): L=math.hypot(*p); return (p[0]/L,p[1]/L)
def dot(p,q): return p[0]*q[0]+p[1]*q[1]
f=unit(sub(Bc,A)); d=(f[1],-f[0])
B=add(A,sc(f,9.20))
W1=add(A,sc(unit(sub((-4.17,1.91),A)),5.90))
Wj1=add(W1,(-0.68,-0.13)); W2=add(W1,(-1.05,-0.21))
W3=add(W2,sc(unit(sub((-2.61,-6.60),(-5.22,1.70))),7.10))
E1=add(B,sc(unit(sub((6.52,-5.61),Bc)),9.70))
E2=add(E1,sc(f,-3.00)); E3=add(E2,sc(d,2.70)); E4=add(E1,sc(d,2.70))
site=[A,W1,Wj1,W2,W3,E3,E2,E1,B]
def area(P): return abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))))/2
loc=lambda p:(round(dot(sub(p,A),f),3),round(dot(sub(p,A),d),3))
G={"site":[[round(x,3) for x in p] for p in site],"eat":[[round(x,3) for x in p] for p in (E1,E2,E3,E4)],
   "area":round(area(site),1),"eat_area":round(area([E1,E2,E3,E4]),2),"back":round(math.hypot(*sub(E3,W3)),2),
   "local":{k:loc(v) for k,v in dict(A=A,W1=W1,Wj1=Wj1,W2=W2,W3=W3,E3=E3,E2=E2,E1=E1,B=B,E4=E4).items()}}
if __name__=="__main__": print(json.dumps(G,indent=1))
