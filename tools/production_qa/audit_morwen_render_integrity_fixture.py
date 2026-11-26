import ast, hashlib, io, pathlib, struct, zlib, warnings
from PIL import Image, PngImagePlugin
source=pathlib.Path(__file__).with_name('preserve_blender_transfer.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='7dc0acb55903e563de3f853cee4b714243906336'
module=ast.parse(source)
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='png_ok')
namespace={'struct':struct,'zlib':zlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact-main-png_ok>','exec'),namespace)
old=namespace['png_ok']
def decoded(raw):
    if not old(raw): raise ValueError('invalid PNG framing')
    # Qualify only non-interlaced RGB/RGBA 8/16-bit output. Reject unsupported layouts.
    w,h,depth,ctype,compression,filter_method,interlace=struct.unpack_from('>IIBBBBB',raw,16)
    if (depth not in (8,16) or ctype not in (2,6) or (compression,filter_method,interlace)!=(0,0,0)):
        raise ValueError('unsupported render PNG layout')
    rowbytes=1+w*(3 if ctype==2 else 4)*(depth//8)
    expected=h*rowbytes; offset=8; parts=[]
    while offset+12<=len(raw):
        n,kind=struct.unpack_from('>I4s',raw,offset)
        if kind==b'IDAT': parts.append(raw[offset+8:offset+8+n])
        offset+=12+n
    dec=zlib.decompressobj(); pixels=dec.decompress(b''.join(parts),expected+1)
    if len(pixels)!=expected or not dec.eof or dec.unused_data or dec.unconsumed_tail or any(pixels[i]>4 for i in range(0,expected,rowbytes)):
        raise ValueError('incomplete or invalid PNG scanlines')
    with warnings.catch_warnings():
        warnings.simplefilter('error',Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as im:
            assert im.format=='PNG' and im.size==(1024,1024) and getattr(im,'n_frames',1)==1
            im.verify()
        with Image.open(io.BytesIO(raw)) as im:
            im.load(); rgba=im.convert('RGBA')
            return hashlib.sha256(rgba.tobytes()).hexdigest()
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
def manual(data,ihdr=None):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr or struct.pack('>IIBBBBB',1024,1024,8,2,0,0,0))+chunk(b'IDAT',data)+chunk(b'IEND',b'')
def sample(color, note=''):
    out=io.BytesIO(); meta=PngImagePlugin.PngInfo(); meta.add_text('test',note)
    Image.new('RGB',(1024,1024),color).save(out,format='PNG',pnginfo=meta); return out.getvalue()
a=sample('red','a'); b=sample('red','b'); c=sample('blue','c')
cases=[('valid RGB',a,True,True),('truncated',a[:-1],False,False),('CRC-correct invalid zlib',manual(b'not-zlib'),True,False),('CRC-correct empty IDAT',manual(b''),True,False),('valid zlib too few scanlines',manual(zlib.compress(b'\0'*3073)),True,False),('invalid color type',manual(zlib.compress(b'\0'*3073),struct.pack('>IIBBBBB',1024,1024,8,7,0,0,0)),True,False)]
for label,raw,expected_old,expected_new in cases:
    got_old=old(raw)
    try: decoded(raw); got_new=True
    except (ValueError,OSError,AssertionError,SyntaxError,zlib.error): got_new=False
    assert (got_old,got_new)==(expected_old,expected_new),(label,got_old,got_new)
    print(f'{label}: current={got_old} decoded={got_new}')
assert hashlib.sha256(a).digest()!=hashlib.sha256(b).digest() and decoded(a)==decoded(b)
print('metadata-only duplicate: byte hashes different / decoded pixel hash equal')
assert decoded(a)!=decoded(c)
print('distinct pixel image: decoded hashes different')
print('8/8 expected outcomes; 5 observed gaps (4 invalid PNG accepted, 1 metadata-only duplicate)')
