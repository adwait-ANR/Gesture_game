import cv2

def draw_stick_figure(frame,lm,h,w):
    connections=[(11,12),(11,23),(12,24),(23,24),
                 (11,13),(13,15),(12,14),(14,16),
                 (23,25),(25,27),(24,26),(26,28)]
    for a,b in connections:
        ax,ay=int(lm[a].x*w),int(lm[a].y*h)
        bx,by=int(lm[b].x*w),int(lm[b].y*h)
        cv2.line(frame,(ax,ay),(bx,by),(0,255,255),2)
    return frame

def draw_hip_thresholds(frame,logic,cfg):
    if logic.baseline_hip is None: return frame
    h,w=frame.shape[:2]
    base=int(logic.baseline_hip)
    top=base-cfg.HIP_MARGIN
    bottom=base+cfg.HIP_MARGIN
    cv2.line(frame,(0,base),(w,base),(0,0,255),3)
    cv2.putText(frame,"BASELINE",(10,base-10),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
    cv2.line(frame,(0,top),(w,top),(255,0,0),2)
    cv2.putText(frame,"Jump Zone",(10,top-8),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,0),2)
    cv2.line(frame,(0,bottom),(w,bottom),(255,0,0),2)
    cv2.putText(frame,"Sit Zone",(10,bottom+20),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,0),2)
    return frame
