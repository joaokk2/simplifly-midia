import sherpa_onnx, numpy as np, sys
from scipy.io import wavfile
from scipy.signal import resample_poly
m='sherpa-onnx-whisper-small/'
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m+'small-encoder.int8.onnx',decoder=m+'small-decoder.int8.onnx',tokens=m+'small-tokens.txt',language='pt',task='transcribe')
sr,x=wavfile.read(sys.argv[1]); x=x.astype(np.float32)/32768
if x.ndim>1: x=x.mean(1)
x=resample_poly(x,16000,sr).astype(np.float32)
segs=[tuple(map(float,s.split('-'))) for s in sys.argv[2:]]
for a,b in segs:
    seg=np.concatenate([np.zeros(3200,np.float32),x[int(a*16000):int(b*16000)],np.zeros(3200,np.float32)])
    st=rec.create_stream(); st.accept_waveform(16000,seg); rec.decode_stream(st); print(f'{a:.2f}-{b:.2f}', st.result.text)
