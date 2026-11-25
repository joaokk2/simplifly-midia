import sys, os, subprocess, audio, json, re
c, style, drop, cta, dur = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
FPS=30
audio.build(dur, drop=drop, transitions=[drop,cta], slams=[0,drop+.3], cta=cta+.1, out=f'mus_{c}.wav', style=style)
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',f'mus_{c}.wav','-i',f'{c}.wav','-filter_complex',
 f'[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={dur},asplit=2[vo1][vo2];[0:a]volume=0.5[mu];[mu][vo1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[md];[md][vo2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-2.5:LRA=9,alimiter=limit=0.72:level=false[out]',
 '-map','[out]','-ar','48000',f'mst_{c}.wav'],check=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.goto('file://'+os.path.abspath('reel.html')+f'?v=n&c={c}&render'); pg.evaluate('window.READY')
    N=int(pg.evaluate('window.DUR')*FPS)
    ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-i',f'mst_{c}.wav','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',f'raw_{c}.mp4'],stdin=subprocess.PIPE)
    for i in range(N):
        pg.evaluate(f'render({i/FPS})'); ff.stdin.write(pg.screenshot(type='jpeg',quality=93))
    ff.stdin.close(); ff.wait(); b.close()
o=subprocess.run(['ffmpeg','-nostats','-i',f'raw_{c}.mp4','-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
I=float(re.findall(r'I:\s+(-?[\d.]+) LUFS',o)[-1]); g=-14.0-I
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',f'raw_{c}.mp4','-c:v','copy','-af',f'volume={g:.2f}dB','-c:a','aac','-b:a','192k','-movflags','+faststart',f'n_{c}.mp4'],check=True)
print('ok',c,I,g)
