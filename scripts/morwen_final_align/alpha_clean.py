"""Alpha-only clean-up of a received RGBA master: alpha <= 12 -> 0 and detached specks (< 600 px pieces
not joined to the figure) -> 0. RGB of visible pixels is untouched. Usage: python3 alpha_clean.py IN OUT"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
a = np.asarray(Image.open(sys.argv[1]).convert("RGBA")).copy(); A = a[..., 3]
A[A <= 12] = 0
lab, n = ndi.label(A > 0, structure=np.ones((3, 3)))
sz = np.bincount(lab.ravel()); sz[0] = 0; main = sz.argmax()
A[(lab != main) & (lab > 0) & (sz[lab] < 600)] = 0
a[A == 0, :3] = 0
Image.fromarray(a, "RGBA").save(sys.argv[2], optimize=True)
print("alpha changed px", int((np.asarray(Image.open(sys.argv[1]).convert("RGBA"))[..., 3] != A).sum()))
