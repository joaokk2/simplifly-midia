import sys, os, subprocess
from playwright.sync_api import sync_playwright
v = sys.argv[1]; FPS = 30
subprocess.run(['python3', 'audio.py', v], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'mix{v}.wav', '-af',
                'loudnorm=I=-14:TP=-2.5:LRA=9,alimiter=limit=0.72:level=false', '-ar', '48000', f'master{v}.wav'], check=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto('file://' + os.path.abspath('reel.html') + f'?v={v}&render'); pg.evaluate('window.READY')
    dur = pg.evaluate('window.DUR'); N = int(dur * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                           '-i', f'master{v}.wav', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', f'trial{v}.mp4'], stdin=subprocess.PIPE)
    for i in range(N):
        pg.evaluate(f'render({i / FPS})')
        ff.stdin.write(pg.screenshot(type='jpeg', quality=93))
    ff.stdin.close(); ff.wait(); b.close()
print('ok', v)
