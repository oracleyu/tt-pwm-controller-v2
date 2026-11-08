"""Plot actual external-pin VCD values; no expected waveforms are synthesized."""
from pathlib import Path
import os
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
scopes=[];symbols={};events={};t=0;header=True
for line in (root/'reports/wave-rtl.vcd').read_text().splitlines():
    a=line.split()
    if not a:continue
    if header:
        if a[0]=='$scope':scopes.append(a[2])
        elif a[0]=='$upscope':scopes.pop()
        elif a[0]=='$var':symbols['.'.join(scopes+[a[4]])]=a[3];events.setdefault(a[3],[])
        elif a[0]=='$enddefinitions':header=False
    elif a[0].startswith('#'):t=int(a[0][1:])
    elif a[0][0] in 'bB' and len(a)>1:events.setdefault(a[1],[]).append((t,a[0][1:]))
    elif a[0][0] in '01xz':events.setdefault(a[0][1:],[]).append((t,a[0][0]))
def trace(name,bit):
    x=[];y=[]
    for time,value in events[symbols[name]]:
        if any(c in value.lower() for c in 'xz'):continue
        if time>100e6:break
        x.append(time/1e6);y.append((int(value,2)>>bit)&1)
    if x[-1]<100:x.append(100);y.append(y[-1])
    return x,y
signals=[('tb.ui_in',1,'CS_n','#636b78'),('tb.ui_in',0,'SPI SCK','#df8736'),
         ('tb.ui_in',2,'MOSI','#49a187'),('tb.uo_out',2,'MISO','#7959b8'),
         ('tb.uo_out',3,'Pending','#b0842b'),('tb.uo_out',0,'PWM left','#287bc1'),
         ('tb.uo_out',1,'PWM right','#945cc4')]
fig,axs=plt.subplots(7,1,figsize=(14,8),sharex=True,layout='constrained')
for ax,(name,bit,label,color) in zip(axs,signals):
    x,y=trace(name,bit);ax.step(x,y,where='post',lw=1.15,color=color)
    ax.set_ylabel(label,rotation=0,ha='right',va='center');ax.set_ylim(-.15,1.15);ax.set_yticks([0,1]);ax.grid(alpha=.15)
    ax.spines[['top','right']].set_visible(False)
axs[-1].set_xlim(0,100);axs[-1].set_xlabel('Time (us); actual RTL simulation, 50 MHz system clock')
fig.suptitle('V2: SPI status / atomic configuration / registered 25% and 75% PWM')
fig.savefig(root/'reports/waveform.png',dpi=160);fig.savefig(root/'reports/waveform.svg')
# A detailed view of the first enabled PWM period, also from the same VCD.
x,y=trace('tb.uo_out',4);start=next(a for a,b in zip(x,y) if b)
fig2,ax2=plt.subplots(3,1,figsize=(12,4.5),sharex=True,layout='constrained')
for ax,(name,bit,label,color) in zip(ax2,[('tb.uo_out',0,'PWM left (25%)','#287bc1'),('tb.uo_out',1,'PWM right (75%)','#945cc4'),('tb.uo_out',7,'Period pulse','#df8736')]):
    a,b=trace(name,bit);ax.step(a,b,where='post',color=color,lw=1.6);ax.set_ylabel(label,rotation=0,ha='right',va='center');ax.set_ylim(-.15,1.15);ax.set_yticks([0,1]);ax.grid(alpha=.15)
ax2[-1].set_xlim(start-.5,min(start+24,100));ax2[-1].set_xlabel('Time (us)')
fig2.suptitle('Actual V2 PWM output after the first committed configuration (N=2)')
fig2.savefig(root/'reports/waveform-pwm.png',dpi=170)
print('Saved actual SPI/PWM and PWM-detail waveform previews.')
