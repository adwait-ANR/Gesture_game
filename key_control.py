# key_control.py
# Strong key injection using win32 API on Windows, fallback to pynput.
import sys
import threading
import time

USE_WIN32 = False
try:
    if sys.platform.startswith('win'):
        import win32api, win32con
        USE_WIN32 = True
except Exception:
    USE_WIN32 = False

# Provide unified API: press_hold(key), release_hold(key), start_repeat(key), stop_repeat(key)
repeat_threads = {}
repeat_stop_flags = {}
REPEAT_INTERVAL = 0.03  # 30 ms

def _repeat_thread_win(vk):
    while not repeat_stop_flags.get(vk, True) == True:
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(REPEAT_INTERVAL)

def _repeat_thread_pyn(keyboard, key):
    while not repeat_stop_flags.get(key, True) == True:
        keyboard.press(key)
        keyboard.release(key)
        time.sleep(REPEAT_INTERVAL)

if USE_WIN32:
    def press_hold(vk):
        try:
            win32api.keybd_event(vk, 0, 0, 0)
        except:
            pass

    def release_hold(vk):
        try:
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except:
            pass

    def start_repeat(vk):
        if vk in repeat_threads:
            return
        repeat_stop_flags[vk] = False
        t = threading.Thread(target=_repeat_thread_win, args=(vk,), daemon=True)
        repeat_threads[vk] = t
        t.start()

    def stop_repeat(vk):
        if vk in repeat_stop_flags:
            repeat_stop_flags[vk] = True
            repeat_threads.pop(vk, None)
else:
    # fallback to pynput
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
    except Exception:
        keyboard = None
    print("the win is not working")

    def press_hold(key):
        try:
            if keyboard: keyboard.press(key)
        except:
            pass

    def release_hold(key):
        try:
            if keyboard: keyboard.release(key)
        except:
            pass

    def start_repeat(key):
        if key in repeat_threads:
            return
        repeat_stop_flags[key] = False
        t = threading.Thread(target=_repeat_thread_pyn, args=(keyboard, key), daemon=True)
        repeat_threads[key] = t
        t.start()

    def stop_repeat(key):
        if key in repeat_stop_flags:
            repeat_stop_flags[key] = True
            repeat_threads.pop(key, None)
