"""Desenha o gap de consumo por OP (medido no dosador x backflush do ERP).

Uso:
    python scripts/grafico_gap.py

Gera docs/gap-por-op.svg.
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
W, H, ESQ, TOPO, BASE = 720, 320, 50, 60, 270


def main():
    erp = pd.read_csv(RAIZ / "dados" / "erp_consumo_op.csv")
    grav = pd.read_csv(RAIZ / "dados" / "gravimetrico_op.csv")
    fechadas = erp[erp["Status"] == "FECHADA"]
    kg_erp = fechadas[fechadas["Unidade"] == "kg"].groupby("OP")["Qtd_Emitida"].sum()
    kg_med = grav.groupby("OP")["Kg_Medido"].sum()
    gap = ((kg_med / kg_erp - 1) * 100).dropna().sort_index()
    media = (kg_med[gap.index].sum() / kg_erp[gap.index].sum() - 1) * 100

    y_max = 14
    def y(v):
        return BASE - v / y_max * (BASE - TOPO)

    passo = (W - ESQ - 20) / len(gap)
    larg = passo * 0.62
    el = [f'<rect width="{W}" height="{H}" fill="#fff"/>',
          f'<text x="{ESQ - 20}" y="26" font-size="15">Consumo medido no dosador acima do registrado no ERP, por OP</text>',
          f'<text x="{ESQ - 20}" y="45" font-size="11" fill="#666">Base sintética. O ERP lança o consumo por backflush (peças apontadas x ficha técnica).</text>']
    for v in range(0, y_max + 1, 4):
        el.append(f'<line x1="{ESQ}" y1="{y(v):.0f}" x2="{W - 20}" y2="{y(v):.0f}" stroke="#e5e5e5"/>')
        el.append(f'<text x="{ESQ - 8}" y="{y(v) + 4:.0f}" text-anchor="end" fill="#666">{v}%</text>')
    for i, (op, v) in enumerate(gap.items()):
        x = ESQ + passo * i + (passo - larg) / 2
        el.append(f'<rect x="{x:.0f}" y="{y(v):.0f}" width="{larg:.0f}" height="{BASE - y(v):.0f}" fill="#2f5d8a"/>')
        el.append(f'<text x="{x + larg / 2:.0f}" y="{BASE + 14}" text-anchor="middle" font-size="9" fill="#666">{str(op)[-3:]}</text>')
    el.append(f'<line x1="{ESQ}" y1="{y(media):.0f}" x2="{W - 20}" y2="{y(media):.0f}" stroke="#c8553d" stroke-dasharray="5 4"/>')
    el.append(f'<text x="{W - 22}" y="{TOPO - 2}" text-anchor="end" fill="#c8553d">- - '
              f'média ponderada {media:.1f}%</text>'.replace(f"{media:.1f}", f"{media:.1f}".replace(".", ",")))
    el.append(f'<line x1="{ESQ}" y1="{BASE}" x2="{W - 20}" y2="{BASE}" stroke="#333"/>')
    el.append(f'<text x="{(W + ESQ) / 2:.0f}" y="{BASE + 32}" text-anchor="middle" fill="#666">OP (final do número)</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12" fill="#222">\n' + "\n".join(el) + "\n</svg>\n")
    (RAIZ / "docs" / "gap-por-op.svg").write_text(svg, encoding="utf-8")
    print("docs/gap-por-op.svg")


if __name__ == "__main__":
    main()
