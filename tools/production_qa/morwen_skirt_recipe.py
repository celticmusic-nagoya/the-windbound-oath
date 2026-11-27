import hashlib, math, struct, sys, zlib
from pathlib import Path
N=512
COLORS=((129,52,150),(163,73,191),(68,27,95),(231,169,153))
LAYERS=((1,0,.50,.40,.52),(1,1,.50,.37,.30),(2,0,.235,.075,.66),(2,1,.24,.085,.63),(2,0,.735,.045,.48),(2,1,.74,.055,.45),(3,0,.49,.018,.82),(3,1,.46,.016,.77),(3,1,.55,.016,.77))
factors=[[min(1,max(0,(w/2+1/N-abs((i/N-c+.5)%1-.5))*N))*a for i in range(N)] for _,_,c,w,a in LAYERS]
wave=[math.sin(2*math.pi*128*i/N) for i in range(N)]
rows=[]
for y in range(N):
    row=bytearray()
    for x in range(N):
        rgb=list(COLORS[0])
        for (col,axis,*_),factor in zip(LAYERS,factors):
            q=factor[y if axis else x]
            rgb=[v*(1-q)+t*q for v,t in zip(rgb,COLORS[col])]
        row.extend([max(0,min(255,round(v+wave[x]*wave[y]*1.8))) for v in rgb]+[255])
    rows.append(bytes(row)*2)
digest=hashlib.sha256(b''.join(rows)).hexdigest()
assert digest=='cdebf9c8f521085d9dc389f41c719d2b2d2a9e1c64ec49f3f4b58af66e2d36ff', digest
def chunk(tag,data):
    return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1024,512,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r for r in rows),9))+chunk(b'IEND',b'')
with Path(sys.argv[1]).open('xb') as f: f.write(png)
print(digest,hashlib.sha256(png).hexdigest())
