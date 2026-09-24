"""
Desenha as figuras da Etapa 2 (arquitetura e modelo conceitual) em PNG.

Uso:  python desenhar_diagramas.py <pasta_saida>
"""
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA_FONTES = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
PRETO, CINZA, BRANCO = (0, 0, 0), (232, 232, 232), (255, 255, 255)


def fonte(tamanho, estilo=""):
    arquivo = {"": "arial.ttf", "b": "arialbd.ttf", "i": "ariali.ttf"}[estilo]
    return ImageFont.truetype(str(PASTA_FONTES / arquivo), tamanho)


def medir(d, texto, f):
    x0, y0, x1, y1 = d.multiline_textbbox((0, 0), texto, font=f, align="center", spacing=8)
    return x1 - x0, y1 - y0, x0, y0


def texto_centrado(d, cx, cy, texto, f):
    w, h, x0, y0 = medir(d, texto, f)
    d.multiline_text((cx - w / 2 - x0, cy - h / 2 - y0), texto, font=f, fill=PRETO, align="center", spacing=8)


def caixa(d, cx, cy, w, h, titulo, detalhe=""):
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=CINZA, outline=PRETO, width=3)
    ft, fd = fonte(30, "b"), fonte(26)
    th = medir(d, titulo, ft)[1]
    if not detalhe:
        texto_centrado(d, cx, cy, titulo, ft)
        return
    dh = medir(d, detalhe, fd)[1]
    total = th + 18 + dh
    texto_centrado(d, cx, cy - total / 2 + th / 2, titulo, ft)
    texto_centrado(d, cx, cy + total / 2 - dh / 2, detalhe, fd)


def linha_tracejada(d, p0, p1, largura=3, traco=18, vao=12):
    comp = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / comp, (p1[1] - p0[1]) / comp
    pos = 0.0
    while pos < comp:
        fim = min(pos + traco, comp)
        d.line([(p0[0] + ux * pos, p0[1] + uy * pos), (p0[0] + ux * fim, p0[1] + uy * fim)], fill=PRETO, width=largura)
        pos += traco + vao


def seta(d, p0, p1, tracejada=False):
    if tracejada:
        linha_tracejada(d, p0, p1)
    else:
        d.line([p0, p1], fill=PRETO, width=4)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ponta = [p1] + [(p1[0] - 26 * math.cos(ang + s * 0.45), p1[1] - 26 * math.sin(ang + s * 0.45)) for s in (1, -1)]
    d.polygon(ponta, fill=PRETO)


def arquitetura(saida):
    img = Image.new("RGB", (2450, 900), BRANCO)
    d = ImageDraw.Draw(img)

    for a, b in [((560, 40), (2400, 40)), ((2400, 40), (2400, 860)), ((2400, 860), (560, 860)), ((560, 860), (560, 40))]:
        linha_tracejada(d, a, b)
    d.text((590, 60), "Nuvem AWS", font=fonte(30, "b"), fill=PRETO)

    caixa(d, 260, 600, 400, 520, "Origens de dados\n(simuladas)",
          "Meta Ads\nCRM\nPlanilhas comerciais")
    caixa(d, 1480, 220, 1700, 160, "Orquestração — Apache Airflow",
          "Docker Compose numa Amazon EC2 t4g.small ligada sob demanda: dispara ingestão,\n"
          "carga e transformação, um dia de referência por execução")

    linha_y, w, h = 600, 380, 240
    etapas = [
        (790, "Ingestão", "Python (pandas, boto3)\nem contêiner Docker"),
        (1240, "Amazon S3", "camada bruta:\narquivos por fonte\ne data de referência"),
        (1690, "Carga e\ntransformação", "Python + SQL"),
        (2150, "Amazon RDS", "PostgreSQL\nstaging → dw\n(modelo estrela)"),
    ]
    for cx, titulo, detalhe in etapas:
        caixa(d, cx, linha_y, w, h, titulo, detalhe)

    seta(d, (460, linha_y), (790 - w / 2, linha_y))
    for (cx_a, *_), (cx_b, *_) in zip(etapas, etapas[1:]):
        seta(d, (cx_a + w / 2, linha_y), (cx_b - w / 2, linha_y))
    for cx in (790, 1690):
        seta(d, (cx, 300), (cx, linha_y - h / 2), tracejada=True)

    img.save(saida, dpi=(200, 200))


ENTIDADES = {
    "Campanha": (280, 170), "Investimento diário": (280, 560),
    "Oportunidade": (900, 170), "Colaborador": (900, 560), "Meta mensal": (900, 950),
    "Plano": (1520, 170),
}
RELACOES = [  # (entidade A, entidade B, cardinalidade no lado A, no lado B, verbo)
    ("Campanha", "Investimento diário", "1", "N", "registra"),
    ("Campanha", "Oportunidade", "0..1", "N", "origina"),
    ("Oportunidade", "Colaborador", "N", "1", "atendida por"),
    ("Colaborador", "Meta mensal", "1", "N", "recebe"),
    ("Plano", "Oportunidade", "1", "0..N", "contratado em"),
]
CAIXA_W, CAIXA_H = 380, 110


def borda(centro, alvo):
    dx, dy = alvo[0] - centro[0], alvo[1] - centro[1]
    t = min((CAIXA_W / 2) / abs(dx) if dx else math.inf, (CAIXA_H / 2) / abs(dy) if dy else math.inf)
    return centro[0] + dx * t, centro[1] + dy * t


def modelo_conceitual(saida):
    img = Image.new("RGB", (1810, 1060), BRANCO)
    d = ImageDraw.Draw(img)
    fc, fv = fonte(28, "b"), fonte(26, "i")

    rotulos = []  # (x, y, texto, fonte, com fundo branco)
    for a, b, card_a, card_b, verbo in RELACOES:
        pa, pb = borda(ENTIDADES[a], ENTIDADES[b]), borda(ENTIDADES[b], ENTIDADES[a])
        d.line([pa, pb], fill=PRETO, width=3)
        comp = math.dist(pa, pb)
        ux, uy = (pb[0] - pa[0]) / comp, (pb[1] - pa[1]) / comp
        nx, ny = uy, -ux  # perpendicular, para fora das caixas
        for (px, py), sentido, card in ((pa, 1, card_a), (pb, -1, card_b)):
            rotulos.append((px + sentido * ux * 45 + nx * 28, py + sentido * uy * 45 + ny * 28, card, fc, False))
        rotulos.append(((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, verbo, fv, True))

    for nome, (cx, cy) in ENTIDADES.items():
        caixa(d, cx, cy, CAIXA_W, CAIXA_H, nome)

    for x, y, texto, f, fundo in rotulos:
        if fundo:
            w, h, _, _ = medir(d, texto, f)
            d.rectangle([x - w / 2 - 10, y - h / 2 - 8, x + w / 2 + 10, y + h / 2 + 8], fill=BRANCO)
        texto_centrado(d, x, y, texto, f)

    img.save(saida, dpi=(200, 200))


if __name__ == "__main__":
    pasta = Path(sys.argv[1])
    pasta.mkdir(parents=True, exist_ok=True)
    arquitetura(pasta / "arquitetura.png")
    modelo_conceitual(pasta / "modelo_conceitual.png")
    print("ok")
