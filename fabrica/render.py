"""Fábrica ATIVYA: renderiza carrosséis (JPG 1080x1350) e Reels (MP4 1080x1920 com batida)
na identidade visual oficial (preto #080808 + dourado #EDDCA8 + logo).

Uso:  python3 fabrica/render.py lote.json
Saída: conteudos/carrosseis/<nome>-NN.jpg  e  conteudos/reels/<nome>.mp4

Formato do lote.json:
{
 "carrosseis": [ {"nome": "c9", "slides": [BLOCO, ...]} ],      # 2 a 10 slides
 "reels":      [ {"nome": "reel16", "bpm": 140, "cenas": [BLOCO, ...]} ]
}
BLOCOS (texto entre *asteriscos* fica dourado):
 {"tipo":"T","titulo":"...","tam":100,"sub":"...","kicker":"..."}          título grande
 {"tipo":"L","titulo":"...","itens":[["título","texto"],...],"tam":64}     lista em cartões
 {"tipo":"P","titulo":"...","prompt":"...","nota":"..."}                   caixa de prompt
 {"tipo":"VS","area":"...","sem":"...","com":"..."}                        sem IA x com IA
 {"tipo":"CTA","titulo":"...","linhas":["...","..."]}                      chamada final (carrossel)
 {"tipo":"RCTA","extra":"..."}                                             "Comenta GUIA" final (Reel)
 {"tipo":"COLL"}                                                           capas da Coleção + preço
Cada bloco aceita "dur" (segundos) nos Reels; sem isso a duração vem do tamanho do texto.
"""
import base64, json, os, re, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BG, FG, MUTED, ACC = "#080808", "#F4EFE2", "#8C8676", "#EDDCA8"
LOGO = "data:image/png;base64," + base64.b64encode(open(f"{HERE}/logo.png", "rb").read()).decode()

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:var(--w);height:var(--h);background:{BG};color:{FG};font-family:'Inter Display','Inter',sans-serif;overflow:hidden;position:relative}}
.glow{{position:absolute;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,{ACC}14 0%,transparent 65%);right:-300px;top:-300px}}
.wrap{{position:absolute;inset:0;padding:90px 84px;display:flex;flex-direction:column}}
.brand img{{height:30px;display:block}}
.tag{{display:inline-block;font-weight:600;font-size:24px;letter-spacing:.22em;text-transform:uppercase;color:{ACC};border:2px solid {ACC};padding:10px 18px;border-radius:6px}}
h1{{font-weight:700;line-height:1.02;letter-spacing:-.015em}}
p{{font-weight:400;color:#CFC8B6;line-height:1.3}}
.hl{{color:{ACC}}}
.foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:26px;color:{MUTED}}}
.card{{background:#111110;border:1px solid {ACC}40;border-radius:18px;padding:34px 38px;margin-top:26px}}
.card h3{{font-weight:700;font-size:44px;margin-bottom:10px}}
.card p{{font-size:32px}}
.strike{{text-decoration:line-through;text-decoration-color:{ACC};text-decoration-thickness:5px;color:{MUTED}}}
"""
BRAND = f"<div class='brand'><img src='{LOGO}'></div>"

def page(body, w, h):
    return f"<html><head><meta charset='utf-8'><style>:root{{--w:{w}px;--h:{h}px}}{CSS}</style></head><body><div class='glow'></div><div class='wrap'>{body}</div></body></html>"
def hl(t): return re.sub(r"\*(.+?)\*", r"<span class='hl'>\1</span>", t or "")
def center(x): return f"<div style='margin:auto;display:flex;flex-direction:column;align-items:center;text-align:center'>{x}</div>"
def cover(vol, title, sub):
    return (f"<div style='width:300px;height:420px;border-radius:14px;background:linear-gradient(160deg,#16150F,#080808);border:2px solid {ACC};padding:26px;display:flex;flex-direction:column;box-shadow:0 30px 80px rgba(0,0,0,.6)'>"
            f"<img src='{LOGO}' style='height:16px;align-self:flex-start'><div style='margin-top:auto;font-weight:800;font-size:20px;color:{ACC}'>VOL. {vol}</div>"
            f"<div style='font-weight:700;font-size:34px;line-height:1.05;margin-top:8px'>{title}</div><div style='font-size:18px;color:#CFC8B6;margin-top:10px'>{sub}</div></div>")

def bloco(b, reel):
    t = b["tipo"]
    if t == "T":
        k = f"<span class='tag' style='align-self:flex-start;margin-bottom:40px'>{b['kicker']}</span>" if b.get("kicker") else ""
        s = f"<p style='font-size:40px;margin-top:40px'>{hl(b['sub'])}</p>" if b.get("sub") else ""
        return f"{BRAND}<div style='margin:auto 0;display:flex;flex-direction:column'>{k}<h1 style='font-size:{b.get('tam', 110 if reel else 90)}px'>{hl(b['titulo'])}</h1>{s}</div>"
    if t == "L":
        cards = "".join(f"<div class='card'><h3>{hl(h)}</h3>" + (f"<p>{hl(p)}</p>" if p else "") + "</div>" for h, p in b["itens"])
        return f"{BRAND}<div style='margin:auto 0'><h1 style='font-size:{b.get('tam', 64)}px;margin-bottom:10px'>{hl(b.get('titulo',''))}</h1>{cards}</div>"
    if t == "P":
        n = f"<p style='font-size:34px;margin-top:40px'>{hl(b['nota'])}</p>" if b.get("nota") else ""
        return (f"{BRAND}<div style='margin:auto 0'><h1 style='font-size:68px'>{hl(b['titulo'])}</h1>"
                f"<div class='card' style='border-color:{ACC}'><p style='font-size:38px;color:{FG};font-family:monospace;line-height:1.4'>\"{b['prompt']}\"</p></div>{n}</div>")
    if t == "VS":
        return (f"{BRAND}<div style='margin:auto 0'><span class='tag'>{b['area']}</span>"
                f"<div class='card' style='margin-top:40px'><p style='font-size:26px;letter-spacing:.2em;color:{MUTED}'>SEM IA</p><h3 style='color:{MUTED};margin-top:12px'>{b['sem']}</h3></div>"
                f"<div class='card' style='border-color:{ACC}'><p style='font-size:26px;letter-spacing:.2em;color:{ACC}'>COM IA</p><h3 style='margin-top:12px'>{b['com']}</h3></div></div>")
    if t == "CTA":
        ls = "".join(f"<p style='font-size:36px;margin-top:22px'>{hl(l)}</p>" for l in b.get("linhas", []))
        return f"{BRAND}<div style='margin:auto 0'><h1 style='font-size:92px'>{hl(b['titulo'])}</h1><div style='margin-top:40px'>{ls}</div></div>"
    if t == "RCTA":
        return (f"{BRAND}<div style='margin:auto 0'><h1 style='font-size:130px'>Comenta<br><span class='hl'>GUIA</span></h1>"
                f"<p style='font-size:50px;margin-top:40px'>e eu te mando 10 prompts grátis.</p><p style='font-size:40px;margin-top:60px;color:{MUTED}'>{b.get('extra','')}</p></div>"
                f"<div class='foot'><span>@metodoativya</span><span>metodoativya.com.br</span></div>")
    if t == "COLL":
        trio = ("<div style='display:flex'>" + cover(1, "IA na prática em 7 dias", "Uma tarefa por dia").replace("box-shadow", "transform:rotate(-8deg);box-shadow")
                + cover(2, "WhatsApp, objeções e negociação", "Scripts prontos").replace("box-shadow", "margin:0 -40px;z-index:2;position:relative;box-shadow")
                + cover(3, "100 prompts para negócios", "Prontos para copiar").replace("box-shadow", "transform:rotate(8deg);box-shadow") + "</div>")
        return BRAND + center(trio + "<h1 style='font-size:84px;margin-top:70px'>Coleção ATIVYA</h1>"
                              f"<p style='font-size:44px;margin-top:20px'><span class='strike'>R$ 59,70</span>  <b style='color:{FG};font-size:64px'>R$ 49,90</b></p>"
                              f"<p style='font-size:36px;margin-top:16px;color:{MUTED}'>3 e-books · garantia de 7 dias</p>")
    raise ValueError(f"tipo desconhecido: {t}")

def dur_for(b, last):
    if "dur" in b: return float(b["dur"])
    if last: return 2.6
    txt = " ".join(str(v) for k, v in b.items() if k not in ("tipo", "tam"))
    return round(min(3.0, max(1.3, 0.8 + 0.25 * len(re.sub(r"[\[\]\"',]", " ", txt).split()))), 2)

def encode(scene_dir, durs, out_mp4, bpm):
    inputs, filt = [], ""
    for i, d in enumerate(durs):
        inputs += ["-loop", "1", "-framerate", "30", "-t", str(d), "-i", f"{scene_dir}/s{i+1:02d}.png"]
        filt += (f"[{i}:v]scale=1188:2112,zoompan=z='min(zoom+0.0009,1.06)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
                 f"trim=duration={d},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.12[v{i}];")
    filt += "".join(f"[v{i}]" for i in range(len(durs))) + f"concat=n={len(durs)}:v=1:a=0[v]"
    tmp = out_mp4 + ".v.mp4"; wav = out_mp4 + ".wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", filt, "-map", "[v]", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", tmp], check=True)
    total = sum(durs)
    subprocess.run([sys.executable, f"{HERE}/beat.py", str(total), wav, str(bpm), "phonk"], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    os.remove(tmp); os.remove(wav)
    return total

def main(spec_path):
    spec = json.load(open(spec_path))
    cdir, rdir, tmpd = f"{ROOT}/conteudos/carrosseis", f"{ROOT}/conteudos/reels", f"{ROOT}/.tmp_cenas"
    os.makedirs(cdir, exist_ok=True); os.makedirs(rdir, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        def snap(html, path, w, h, jpeg):
            pg = br.new_page(viewport={"width": w, "height": h}); pg.set_content(html); pg.wait_for_timeout(80)
            pg.screenshot(path=path, type="jpeg", quality=92) if jpeg else pg.screenshot(path=path); pg.close()
        for c in spec.get("carrosseis", []):
            n = len(c["slides"]); assert 2 <= n <= 10, c["nome"]
            for i, b in enumerate(c["slides"], 1):
                foot = f"<div class='foot'><span>@metodoativya</span><span>{i}/{n} →</span></div>"
                snap(page(bloco(b, False) + foot, 1080, 1350), f"{cdir}/{c['nome']}-{i:02d}.jpg", 1080, 1350, True)
            print(f"carrossel {c['nome']}: {n} slides")
        scenes = {}
        for r in spec.get("reels", []):
            d = f"{tmpd}/{r['nome']}"; os.makedirs(d, exist_ok=True)
            for i, b in enumerate(r["cenas"], 1):
                snap(page(bloco(b, True), 1080, 1920), f"{d}/s{i:02d}.png", 1080, 1920, False)
            scenes[r["nome"]] = [dur_for(b, i == len(r["cenas"]) - 1) for i, b in enumerate(r["cenas"])]
        br.close()
    for r in spec.get("reels", []):
        total = encode(f"{tmpd}/{r['nome']}", scenes[r["nome"]], f"{rdir}/{r['nome']}.mp4", r.get("bpm", 140))
        print(f"reel {r['nome']}: {total:.1f}s")
    subprocess.run(["rm", "-rf", tmpd])

if __name__ == "__main__":
    main(sys.argv[1])
