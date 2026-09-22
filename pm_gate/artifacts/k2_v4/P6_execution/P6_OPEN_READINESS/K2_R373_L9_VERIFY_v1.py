import re,collections
t=open('k2_v4_8L.l9.kicad_pcb').read()
NECK=(93.0,44.0,112.0,58.0)
inN=lambda x,y: 93-1e-9<=x<=112+1e-9 and 44-1e-9<=y<=58+1e-9
def blocks(text,key):
    out=[];pat='('+key;i=0
    while True:
        i=text.find(pat,i)
        if i<0: break
        k=i;dd=0;ins=False
        while k<len(text):
            c=text[k]
            if ins:
                if c=='"': ins=False
            elif c=='"': ins=True
            elif c=='(': dd+=1
            elif c==')':
                dd-=1
                if dd==0: break
            k+=1
        out.append(text[i:k+1]); i=k+1
    return out
NETS=['DS320_STRAP_B_ADDR1_7-0','DS320_STRAP_B_ADDR0_15-8','I2C1_SDA','PERSTA#']
cnt=collections.Counter(); vc=collections.Counter(); tot=0
for b in blocks(t,'segment'):
    lay=re.search(r'\(layer "([^"]+)"\)',b).group(1)
    net=re.search(r'\(net "([^"]*)"\)',b).group(1)
    m=re.search(r'\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)',b)
    x1,y1,x2,y2=map(float,m.groups())
    if lay=='In5.Cu' and (inN(x1,y1) or inN(x2,y2)): cnt[net]+=1; tot+=1
for b in blocks(t,'via'):
    m=re.search(r'\(at ([\d.-]+) ([\d.-]+)\)',b)
    if not m: continue
    x,y=float(m.group(1)),float(m.group(2))
    nm=re.search(r'\(net "([^"]*)"\)',b)
    if nm and inN(x,y): vc[nm.group(1)]+=1
print('l9  In5 in-neck segs (4 nets):',{n:cnt.get(n,0) for n in NETS})
print('l9  in-neck vias  (4 nets):',{n:vc.get(n,0) for n in NETS})
print('l9  total in-neck In5 segs (all nets):',tot)
d=0;ins=False
for c in t:
    if ins:
        if c=='"': ins=False
    elif c=='"': ins=True
    elif c=='(': d+=1
    elif c==')': d-=1
print('paren balance:',d,' segments:',t.count('(segment'),' vias:',t.count('(via'))
