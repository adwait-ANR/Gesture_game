def ema(value, prev, alpha):
    if prev is None: return value
    return alpha*value + (1-alpha)*prev

def median_baseline_from_landmarks(samples,w,h):
    if len(samples)<5: return None,None
    hips=[]
    centers=[]
    for lm in samples:
        lh=lm[23].y*h; rh=lm[24].y*h
        hips.append((lh+rh)/2)
        lsh=lm[11].x*w; rsh=lm[12].x*w
        centers.append((lsh+rsh)/2)
    hips.sort(); centers.sort()
    return hips[len(hips)//2], centers[len(centers)//2]
