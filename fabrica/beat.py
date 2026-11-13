import numpy as np, wave, sys
sr=44100; bpm=float(sys.argv[3]) if len(sys.argv)>3 else 140
dur=float(sys.argv[1]); out=sys.argv[2]; style=sys.argv[4] if len(sys.argv)>4 else "phonk"
n=int(sr*dur); mix=np.zeros(n); beat=60/bpm; step=beat/4
rng=np.random.default_rng(7)
def add(sig,t,g=1.0):
    i=int(t*sr); j=min(n,i+len(sig))
    if i<n: mix[i:j]+=g*sig[:j-i]
def kick():
    t=np.arange(int(.35*sr))/sr; f=45+160*np.exp(-t*35)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t*7)
def clap():
    t=np.arange(int(.22*sr))/sr; nz=rng.standard_normal(len(t))
    env=np.exp(-t*22)+.5*np.exp(-((t-.012)*300)**2)
    return np.convolve(nz,[1,-.9],'same')*env*.55
def hat(o=False):
    t=np.arange(int((.18 if o else .05)*sr))/sr; nz=np.diff(rng.standard_normal(len(t)+1))
    return nz*np.exp(-t*(18 if o else 90))*.18
def bell(freq,l=.3):
    t=np.arange(int(l*sr))/sr
    s=np.sin(2*np.pi*freq*t)+.6*np.sin(2*np.pi*freq*1.48*t)+.3*np.sin(2*np.pi*freq*2.0*t)
    return np.tanh(2*s)*np.exp(-t*9)*.22
def bass808(freq,l):
    t=np.arange(int(l*sr))/sr; f=freq*(1+.5*np.exp(-t*30))
    return np.tanh(2.2*np.sin(2*np.pi*np.cumsum(f)/sr))*np.minimum(1,np.exp(-(t-l*.7).clip(0)*12))*.5
# progression (Phrygian-ish dark): root notes
roots=[55.0,55.0,58.27,51.91]   # A1 A1 Bb1 Ab1
mel=[440,523.25,466.16,440,349.23,440,392,349.23]  # cowbell melody
bars=int(dur/(beat*4))+1
intro=beat*4 if style=="phonk" else 0
for b in range(bars):
    t0=b*beat*4; r=roots[b%4]
    for s in range(16):
        t=t0+s*step
        if t>=dur: break
        drums = t>=intro
        if drums and s in (0,6,10) : add(kick(),t,.95)
        if drums and s in (4,12): add(clap(),t,.8)
        if drums: add(hat(s%8==6), t, 1 if s%2==0 else .6)
        if drums and s==14 and b%2==1: [add(hat(),t+k*step/3,.7) for k in range(3)]
        if s%2==0: add(bell(mel[(s//2+b)%8]*(1 if b%4<2 else 1.06)), t, .9 if drums else .6)
    if t0>=intro: add(bass808(r,beat*1.5),t0,1); add(bass808(r,beat),t0+beat*2.5,.9)
# sidechain-ish pump & master
mix=np.tanh(mix*1.3); 
fade=int(1.0*sr); mix[-fade:]*=np.linspace(1,0,fade)
mix=mix/np.max(np.abs(mix))*.89
d=(mix*32767).astype(np.int16); st=np.repeat(d[:,None],2,1)
w=wave.open(out,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes()); w.close()
