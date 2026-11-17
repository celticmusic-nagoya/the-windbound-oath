import ctypes,sys,time
x=ctypes.CDLL('libX11.so.6');t=ctypes.CDLL('libXtst.so.6')
x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p
x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong
x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_uint
x.XFlush.argtypes=[ctypes.c_void_p]
t.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
t.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
t.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
d=x.XOpenDisplay(b':99');assert d

def key(k,down):
 code=x.XKeysymToKeycode(d,x.XStringToKeysym(k.encode()));assert code,k
 t.XTestFakeKeyEvent(d,code,down,0);x.XFlush(d)

def move(a,b):t.XTestFakeMotionEvent(d,-1,int(a),int(b),0);x.XFlush(d)
def click(a,b):
 move(a,b);t.XTestFakeButtonEvent(d,1,1,0);t.XTestFakeButtonEvent(d,1,0,0);x.XFlush(d)

op=sys.argv[1]
if op=='click':click(*sys.argv[2:4])
if op=='hotkey':
 for k in sys.argv[2:]:key(k,1)
 for k in reversed(sys.argv[2:]):key(k,0)
if op=='type':
 mapping={'/':'slash','.':'period',"'":'apostrophe','(':'9',')':'0','_':'minus',':':'semicolon',',':'comma','=':'equal','[':'bracketleft',']':'bracketright',' ':'space','-':'minus'}
 for c in sys.argv[2]:
  shift=c.isupper() or c in '()_:'
  if shift:key('Shift_L',1)
  k=mapping.get(c,c.lower());key(k,1);key(k,0)
  if shift:key('Shift_L',0)
  time.sleep(.012)
if op=='drag':
 coords=list(map(int,sys.argv[2:]));move(coords[0],coords[1]);t.XTestFakeButtonEvent(d,1,1,0)
 for a,b in zip(coords[2::2],coords[3::2]):move(a,b);time.sleep(.1)
 t.XTestFakeButtonEvent(d,1,0,0);x.XFlush(d)
x.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int];x.XSync(d,0)
time.sleep(.2)
