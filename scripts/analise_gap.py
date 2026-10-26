"""Compara o consumo do ERP (backflush) com o consumo medido no dosador.

Responde, na ordem em que o estudo respondeu:

1. Quais OPs podem entrar na conta (base saneada antes de qualquer número).
2. O ERP mede consumo ou calcula? Se a razão emitido/planejado é a mesma em
   todas as linhas da ficha, é backflush: ninguém pesou nada.
3. O desvio é de mistura ou de volume? Compara o gap da resina com o do pigmento.
4. Quão preciso é o dosador? Percentual de pigmento hora a hora contra o setpoint.
5. Qual métrica usar para o gap? Percentual, kg ou peças não apontadas.

Uso:
    python scripts/analise_gap.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PASTA = Path(__file__).resolve().parents[1] / "dados"
MIN_CONSUMO_KG = 1.0       # abaixo disso é teste ou parada, não produção
SETPOINT = 5.0             # % de masterbatch na receita


def ic95(serie):
    n = len(serie)
    m = serie.mean()
    h = stats.t.ppf(0.975, n - 1) * serie.std(ddof=1) / np.sqrt(n)
    return m, m - h, m + h


def main():
    erp = pd.read_csv(PASTA / "erp_consumo_op.csv")
    grav = pd.read_csv(PASTA / "gravimetrico_op.csv")
    pig = pd.read_csv(PASTA / "pigmento_horario.csv")

    # 1) base saneada
    medido = grav.groupby("OP")["Kg_Medido"].sum()
    status = erp.groupby("OP")["Status"].first()
    classe = pd.Series("VALIDA", index=medido.index)
    classe[~classe.index.isin(status.index)] = "EXCLUIR (OP inexistente no ERP)"
    classe[medido < MIN_CONSUMO_KG] = "EXCLUIR (teste ou parada)"
    classe[classe.index.isin(status[status == "EM_EXECUCAO"].index)] = "AGUARDAR (OP em execução)"
    print("1) Classificação das OPs medidas")
    print(classe.value_counts().to_string(), "\n")
    validas = classe[classe == "VALIDA"].index

    # 2) backflush: razão emitido/planejado por linha da ficha
    erp["Razao"] = erp["Qtd_Emitida"] / erp["Qtd_Planejada"]
    disp = erp[erp["OP"].isin(validas)].groupby("OP")["Razao"].agg(["min", "max"])
    disp["Amplitude"] = disp["max"] - disp["min"]
    print("2) Razão emitido/planejado dentro de cada OP (resina, pigmento, etiqueta, caixa, hora-máquina)")
    print(f"   maior amplitude entre linhas da mesma OP: {disp['Amplitude'].max():.6f}")
    print("   -> a razão é a mesma em todas as linhas: o ERP multiplica peças apontadas pela ficha.\n")

    # 3) gap por componente
    kg_erp = erp[erp["Unidade"] == "kg"].pivot_table(index="OP", columns="Item", values="Qtd_Emitida", aggfunc="sum")
    kg_med = grav.pivot_table(index="OP", columns="Componente", values="Kg_Medido", aggfunc="sum")
    base = pd.DataFrame({
        "ERP_kg": kg_erp.sum(axis=1),
        "Medido_kg": kg_med.sum(axis=1),
        "Gap_MP_%": (kg_med["Componente 1 - PP natural"] / kg_erp["MP-PP01"] - 1) * 100,
        "Gap_Pigmento_%": (kg_med["Componente 2 - Masterbatch"] / kg_erp["MB-PRT01"] - 1) * 100,
        "Pigmento_medido_%": kg_med["Componente 2 - Masterbatch"] / kg_med.sum(axis=1) * 100,
    }).loc[validas]
    base["Gap_kg"] = base["Medido_kg"] - base["ERP_kg"]
    base["Gap_%"] = (base["Medido_kg"] / base["ERP_kg"] - 1) * 100
    ficha = erp[erp["Unidade"] == "kg"].groupby("OP").apply(
        lambda g: g["Qtd_Planejada"].sum() / g["Pecas_Planejadas"].iloc[0], include_groups=False)
    base["Pecas_equivalentes"] = base["Gap_kg"] / ficha.loc[validas]
    print("3) Gap por componente (OPs válidas)")
    print(base[["ERP_kg", "Medido_kg", "Gap_MP_%", "Gap_Pigmento_%", "Pigmento_medido_%"]].round(4).to_string())
    print(f"   diferença máxima entre gap da resina e gap do pigmento: "
          f"{(base['Gap_MP_%'] - base['Gap_Pigmento_%']).abs().max():.3f} p.p.")
    print("   -> gap igual nos dois componentes: o desvio é de volume total, não de mistura.\n")

    # 4) precisão do dosador
    print("4) Pigmento dosado hora a hora (setpoint 5,00%)")
    print(f"   média {pig['Pct_Pigmento'].mean():.4f}% | mínimo {pig['Pct_Pigmento'].min():.4f}% | "
          f"máximo {pig['Pct_Pigmento'].max():.4f}% | maior desvio {(pig['Pct_Pigmento'] - SETPOINT).abs().max():.4f} p.p.\n")

    # 5) qual métrica usar
    print("5) Estabilidade das métricas de gap (IC 95%, t de Student)")
    linhas = []
    for nome, col in [("Gap (%)", "Gap_%"), ("Gap (kg)", "Gap_kg"), ("Peças equivalentes", "Pecas_equivalentes")]:
        m, lo, hi = ic95(base[col])
        linhas.append({"Métrica": nome, "Média": m, "IC inferior": lo, "IC superior": hi,
                       "CV %": base[col].std(ddof=1) / m * 100})
    print(pd.DataFrame(linhas).round(2).to_string(index=False))
    print("   -> o percentual depende do tamanho da OP; peças equivalentes é a métrica mais estável.")


if __name__ == "__main__":
    main()
