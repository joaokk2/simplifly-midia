import os, subprocess
from playwright.sync_api import sync_playwright
FPS=30
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.abspath('reel.html')+'?v=5&render'); pg.evaluate('window.READY')
    N=int(pg.evaluate('window.DUR')*FPS)
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-i','master5.wav','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','andre2.mp4'],stdin=subprocess.PIPE)
    for i in range(N):
        pg.evaluate(f'render({i/FPS})'); ff.stdin.write(pg.screenshot(type='jpeg',quality=93))
    ff.stdin.close(); ff.wait(); b.close()
