"""Clean, low-barrier schematic of S-type multistar orbital geometry."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "slide0_system_geometry_schematic.png"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "savefig.dpi": 300})

def glow(ax, x, y, color, r):
    for scale, alpha in [(3,.04),(2.2,.08),(1.5,.18),(1,1)]:
        ax.scatter(x, y, s=(r*scale)**2*55, color=color, alpha=alpha, edgecolors="none", zorder=5)

def base(ax):
    ax.set_facecolor("#071526"); ax.set_xlim(-3.2,14); ax.set_ylim(-4,4); ax.set_aspect("equal"); ax.axis("off")
    rng=np.random.default_rng(12); ax.scatter(rng.uniform(-3.2,14,75),rng.uniform(-4,4,75),s=rng.uniform(1,7,75),color="#9bb4d1",alpha=.22,edgecolors="none")

def label(ax,x,y,text,dy=-.72): ax.text(x,y+dy,text,color="#f5f7fb",ha="center",va="top",fontsize=12,weight="bold",zorder=9)

def distance(ax,x0,x1,y,text,color):
    ax.annotate("",xy=(x0,y),xytext=(x1,y),arrowprops=dict(arrowstyle="<->",color=color,lw=1.4))
    ax.text((x0+x1)/2,y+.22,text,color=color,ha="center",va="bottom",fontsize=11,bbox=dict(boxstyle="round,pad=.22",fc="#102840",ec=color,alpha=.95))

def draw_left(ax):
    base(ax); t=np.linspace(0,2*np.pi,600); ax.plot(np.cos(t),np.sin(t),color="#65d8ff",lw=2.3)
    glow(ax,0,0,"#ffd166",.42); label(ax,0,0,"Host Star A")
    px,py=.72,.70; glow(ax,px,py,"#76ddff",.12); ax.annotate("Planet",xy=(px,py),xytext=(1.85,1.70),color="#b9f2ff",fontsize=12,weight="bold",arrowprops=dict(arrowstyle="->",color="#76ddff",lw=1.2))
    ax.text(-.35,1.35,"Planet's orbit: 1 Earth–Sun distance",color="#8ee8ff",ha="center",fontsize=10)
    cx=12; ax.plot([.7,3],[0,0],color="#6e88a5",lw=1.4,ls=(0,(4,5))); ax.plot([3.35,10.4],[0,0],color="#6e88a5",lw=1.4,ls=(0,(4,5))); ax.plot([10.75,11.5],[0,0],color="#6e88a5",lw=1.4,ls=(0,(4,5)))
    ax.text(3.18,.13,"//",color="#d7e2ef",fontsize=16,ha="center"); ax.text(10.58,.13,"//",color="#d7e2ef",fontsize=16,ha="center")
    distance(ax,.9,11.4,-.95,"D = 1000 Earth–Sun distances","#d7e2ef"); glow(ax,cx,0,"#ff9f68",.48); label(ax,cx,0,"Companion Star B",dy=-.75)
    ax.text(5.9,-2.65,"The companion is about 1000 times farther away\nthan the planet's orbit is wide.",color="#c6d5e5",ha="center",fontsize=12)
    ax.text(5.4,3.45,"A. Real S-Type Systems: R ≈ 0.001",color="#70dcff",ha="center",fontsize=17,weight="bold"); ax.text(5.4,2.95,"Quiet geometry: the planet feels one dominant star.",color="#f5f7fb",ha="center",fontsize=13,weight="bold")

def draw_right(ax):
    base(ax)
    # Re-center the narrower lower schematic in its panel.
    ax.set_xlim(-4.0, 10.0)
    t=np.linspace(0,2*np.pi,600); ax.plot(np.cos(t),np.sin(t),color="#62d7ff",lw=2,ls=":",alpha=.65); glow(ax,0,0,"#ffd166",.42); label(ax,0,0,"Host Star A")
    px,py=.72,.70; glow(ax,px,py,"#76ddff",.12); ax.annotate("Planet",xy=(px,py),xytext=(1.85,1.70),color="#b9f2ff",fontsize=12,weight="bold",arrowprops=dict(arrowstyle="->",color="#76ddff",lw=1.2)); ax.text(-.35,1.35,"Original orbit: 1 Earth–Sun distance",color="#8ee8ff",ha="center",fontsize=10)
    cx=6; ax.plot([.7,cx-.55],[0,0],color="#e07070",lw=1.3,ls=(0,(3,4))); distance(ax,.9,cx-.55,-.95,"D ≈ 6 Earth–Sun distances","#ffd2d2"); glow(ax,cx,0,"#ff6b6b",.5); label(ax,cx,0,"Companion Star B",dy=-.75)
    radius=1+.2*np.sin(3*t+.4)+.1*np.sin(7*t); x,y=radius*np.cos(t),radius*np.sin(t); ax.plot(x,y,color="#ff6b6b",lw=2.6,ls=(0,(5,3))); ax.annotate("orbit is strongly\nshaken",xy=(x[160],y[160]),xytext=(2.15,2),color="#ffb2a8",fontsize=11,ha="center",arrowprops=dict(arrowstyle="->",color="#ff8c82",lw=1.5))
    ax.text(3,-2.65,"A nearby companion can repeatedly disturb\nthe planet's path over time.",color="#f1c5c5",ha="center",fontsize=12); ax.text(3,3.45,"B. Illustrative Unstable Region: R ≥ 0.1",color="#ff8f8f",ha="center",fontsize=17,weight="bold"); ax.text(3,2.95,"Active perturbation: two stars strongly compete.",color="#f5f7fb",ha="center",fontsize=13,weight="bold")

def main():
    fig,axes=plt.subplots(2,1,figsize=(14,12),facecolor="#071526"); draw_left(axes[0]); draw_right(axes[1]); fig.tight_layout(pad=1.2); fig.savefig(OUTPUT,dpi=300,bbox_inches="tight",facecolor=fig.get_facecolor()); plt.close(fig); print(f"Saved: {OUTPUT}")

if __name__ == "__main__": main()
