"""Gera a base sintética do estudo.

Imita o que existe na planta: o ERP registra o consumo de cada ordem de produção
(OP) por backflush, multiplicando as peças apontadas pela ficha técnica, e o
dosador gravimétrico pesa o que realmente entrou na máquina, por componente.
Todos os números são fictícios.

Uso:
    python scripts/gerar_dados_sinteticos.py

Gera em dados/:
    erp_consumo_op.csv        grão: OP x linha da ficha técnica (lado ERP)
    gravimetrico_op.csv       grão: OP x componente dosado (lado medido)
    pigmento_horario.csv      grão: hora (percentual de pigmento dosado)
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEMENTE = 7
PASTA = Path(__file__).resolve().parents[1] / "dados"
SETPOINT_PIGMENTO = 0.05   # receita: 5% de masterbatch sobre a massa dosada

PRODUTOS = {
    # produto: (peso líquido g/peça, galha g/peça na ficha, galha física g/peça, ciclo s)
    "PRD-A01": (182.0, 14.0, 21.0, 30),
    "PRD-B07": (410.0, 22.0, 36.0, 55),
    "PRD-C12": (96.0, 9.0, 13.0, 24),
}
# linhas da ficha técnica além da resina e do pigmento (consumidas por peça)
OUTRAS_LINHAS = [("ETQ-001", "Etiqueta", "un", 1 / 50), ("EMB-010", "Caixa", "un", 1 / 200),
                 ("HM-INJ", "Hora-máquina", "h", None)]


def gerar(rng):
    erp, grav = [], []
    inicio = pd.Timestamp("2026-07-09")
    for i in range(16):
        op = 330100 + i * 7
        produto = rng.choice(list(PRODUTOS))
        peso, galha_ficha, galha_fisica, ciclo = PRODUTOS[produto]
        planejado = int(rng.choice([2000, 3000, 5000, 8000]))
        apontado = int(planejado * rng.uniform(0.95, 1.08))
        abertura = inicio + pd.Timedelta(days=int(i * 1.6))
        status = "FECHADA"
        if i == 15:
            status = "EM_EXECUCAO"

        # lado ERP: backflush = apontado x ficha, a mesma razão em todas as linhas
        kg_ficha = (peso + galha_ficha) / 1000
        razao = apontado / planejado
        linhas = [("MP-PP01", "PP natural", "kg", kg_ficha * (1 - SETPOINT_PIGMENTO)),
                  ("MB-PRT01", "Masterbatch preto", "kg", kg_ficha * SETPOINT_PIGMENTO)]
        for cod, desc, un, por_peca in OUTRAS_LINHAS:
            linhas.append((cod, desc, un, por_peca if por_peca else ciclo / 3600))
        for cod, desc, un, por_peca in linhas:
            erp.append({"OP": op, "Produto": produto, "Abertura": abertura.date(), "Status": status,
                        "Item": cod, "Descricao": desc, "Unidade": un,
                        "Qtd_Planejada": round(planejado * por_peca, 4),
                        "Qtd_Emitida": round(planejado * por_peca * razao, 4),
                        "Tipo_Emissao": "Backflush",
                        "Pecas_Planejadas": planejado, "Pecas_Apontadas": apontado})

        # lado medido: o que entrou na máquina. A galha física é bem maior que a da
        # ficha, e parte das peças produzidas não chega a ser apontada.
        nao_apontadas = rng.normal(160, 15)
        kg_medido = ((apontado + nao_apontadas) * (peso + galha_fisica) / 1000) * rng.uniform(0.985, 1.0)
        pct_real = SETPOINT_PIGMENTO + rng.normal(0, 0.000004)
        duracao_h = (apontado + nao_apontadas) * ciclo / 3600 * rng.uniform(1.03, 1.12)
        for comp, frac in [("Componente 1 - PP natural", 1 - pct_real), ("Componente 2 - Masterbatch", pct_real)]:
            grav.append({"OP": op, "Componente": comp, "Kg_Medido": round(kg_medido * frac, 3),
                         "Inicio": (abertura + pd.Timedelta(hours=6)).isoformat(),
                         "Horas_Dosando": round(duracao_h, 2)})

    # ruído típico de uma base de medição: OPs de teste digitadas no painel
    for op_teste in (111111, 333333):
        grav.append({"OP": op_teste, "Componente": "Componente 1 - PP natural", "Kg_Medido": round(rng.uniform(0.2, 3), 3),
                     "Inicio": "2026-07-15T08:00:00", "Horas_Dosando": 0.02})

    horas = pd.date_range("2026-08-05 00:00", periods=24 * 28, freq="h")
    pigmento = pd.DataFrame({"Hora": horas,
                             "Pct_Pigmento": np.round(SETPOINT_PIGMENTO * 100 + rng.normal(0.0, 0.0012, len(horas)), 4),
                             "Kg_Dosado": np.round(rng.normal(28, 4, len(horas)), 2)})
    return pd.DataFrame(erp), pd.DataFrame(grav), pigmento


def main():
    rng = np.random.default_rng(SEMENTE)
    erp, grav, pig = gerar(rng)
    PASTA.mkdir(exist_ok=True)
    erp.to_csv(PASTA / "erp_consumo_op.csv", index=False)
    grav.to_csv(PASTA / "gravimetrico_op.csv", index=False)
    pig.to_csv(PASTA / "pigmento_horario.csv", index=False)
    print(f"erp_consumo_op.csv:   {len(erp)} linhas")
    print(f"gravimetrico_op.csv:  {len(grav)} linhas")
    print(f"pigmento_horario.csv: {len(pig)} linhas")


if __name__ == "__main__":
    main()
