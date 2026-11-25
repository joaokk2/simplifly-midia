import sys, os, subprocess, audio
c, style = sys.argv[1], sys.argv[2]
FPS=30; out=f'{c}.mp4'
audio.build(12.0, drop=5.6, transitions=[5.6,9.2], slams=[0,.5,1.0,6.0,9.6], cta=9.4, out=f'mix_{c}.wav', style=style)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f'mix_{c}.wav','-af','loudnorm=I=-14:TP=-2.5:LRA=9,alimiter=limit=0.72:level=false','-ar','48000',f'm_{c}.wav'],check=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.abspath('reel.html')+f'?v=g&c={c}&render'); pg.evaluate('window.READY')
    N=int(pg.evaluate('window.DUR')*FPS)
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-i',f'm_{c}.wav','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],stdin=subprocess.PIPE)
    for i in range(N):
        pg.evaluate(f'render({i/FPS})'); ff.stdin.write(pg.screenshot(type='jpeg',quality=93))
    ff.stdin.close(); ff.wait(); b.close()
print('ok',c)
