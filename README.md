# Mídia do Instagram da ATIVYA (@metodoativya)

Branch separado do app principal. Tudo aqui é usado pelas publicações automáticas.

- `conteudos/carrosseis/<nome>-NN.jpg` e `conteudos/reels/<nome>.mp4` — mídia na identidade oficial (preto #080808 + dourado #EDDCA8).
- `fila/reels.json` — fila dos Reels automáticos (publicados 2x por dia, na ordem; já publicados são pulados pela 1ª linha da legenda).
- `fila/carrosseis.json` — fila dos carrosséis (1 por dia).
- `fila/reels-manuais.json` — Reels para o dono postar pelo app com áudio em alta (1 por dia).
- `fabrica/render.py` — gera novos carrosséis e Reels a partir de um lote JSON (ver instruções no topo do arquivo).
- `fabrica/lotes/` — lotes já gerados (histórico).

Mídia servida via jsDelivr: `https://cdn.jsdelivr.net/gh/flaviobernardessilva/github-amd6ctab@<commit>/conteudos/...`
