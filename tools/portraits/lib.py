import cv2,numpy as np
from PIL import Image
def load(p):return np.array(Image.open(p).convert('RGBA'))
def gray(rgba):
    rgb=rgba[...,:3].astype(float);a=rgba[...,3:4]/255.
    return cv2.cvtColor((rgb*a+128*(1-a)).astype(np.uint8),cv2.COLOR_RGB2GRAY)
def panels(path):
    s=load(path);H,W=s.shape[:2];hh=H//2+ (1 if H%2 else 0)
    # boundary: find the empty separator row/col near the middle
    boxes=[(0,0,W//2,H//2),(W//2,0,W,H//2),(0,H//2,W//2,H),(W//2,H//2,W,H)]
    return [(s[y0:y1,x0:x1],(x0,y0)) for x0,y0,x1,y1 in boxes]
