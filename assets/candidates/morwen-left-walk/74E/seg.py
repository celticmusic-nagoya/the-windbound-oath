import numpy as np, cv2
LINES = None
def classify(img, lines):
    f = img.astype(int)
    mx = f.max(2); mn = f.min(2)
    nonwhite = ~((mn > 215) & ((mx - mn) < 35))
    fg = nonwhite & ~lines
    fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    # bridge the removed grid lines (<=3 px) inside the body
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    fg &= ~(lines & ~cv2.dilate((nonwhite & ~lines).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
    big = [k for k in range(1, n) if st[k, cv2.CC_STAT_AREA] >= 150]
    body = np.isin(lab, big) if big else fg
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(int); H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    top = body & (H >= 3) & (H <= 15) & (S > 130) & (V > 150)
    hair = body & (V < 90)
    shorts = body & (S < 45) & (V >= 90)
    skin = body & ~top & ~hair & ~shorts
    return dict(body=body, skin=skin, top=top, shorts=shorts, hair=hair)
