"""Caso de investimento: ganho recorrente do dosador gravimétrico.

Duas alavancas, as duas sobre o masterbatch (pigmento), que é o item caro:

B1  Evitar a sobredosagem que o dosador volumétrico exige por segurança.
B2  Reduzir o percentual da receita, porque a precisão dispensa a margem.

Ponto de método: a massa da peça não muda. Cada kg de masterbatch que deixa de
entrar é substituído por um kg de resina, então o ganho vale a DIFERENÇA de
preço entre os dois, não o preço cheio do masterbatch.

Todas as premissas abaixo são ilustrativas. Edite e rode de novo.

Uso:
    python scripts/caso_financeiro.py
"""
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "dados"

PREMISSAS = {
    "preco_masterbatch_rs_kg": 18.00,
    "preco_resina_rs_kg": 9.00,
    "sobredosagem_evitada": 0.10,      # B1: 10% a mais de pigmento no volumétrico
    "reducao_setpoint_pp": 0.5,        # B2: receita de 5,00% para 4,50%
    "maquinas": 6,
    "capex_por_maquina_rs": 42_000.0,
    "tma": 0.15,
    "anos": 5,
}


def br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def vpl(taxa, fluxos):
    return sum(f / (1 + taxa) ** t for t, f in enumerate(fluxos))


def tir(fluxos, lo=-0.99, hi=10.0):
    for _ in range(200):
        meio = (lo + hi) / 2
        if vpl(meio, fluxos) > 0:
            lo = meio
        else:
            hi = meio
    return meio


def main():
    p = PREMISSAS
    pig = pd.read_csv(PASTA / "pigmento_horario.csv", parse_dates=["Hora"])
    dias = (pig["Hora"].max() - pig["Hora"].min()).total_seconds() / 86400 + 1 / 24
    kg_total_ano = pig["Kg_Dosado"].sum() * 365 / dias
    kg_mb_ano = kg_total_ano * pig["Pct_Pigmento"].mean() / 100
    diferencial = p["preco_masterbatch_rs_kg"] - p["preco_resina_rs_kg"]

    b1_kg = kg_mb_ano * p["sobredosagem_evitada"]
    b2_kg = kg_total_ano * p["reducao_setpoint_pp"] / 100
    ganho_maquina = (b1_kg + b2_kg) * diferencial
    ganho_frota = ganho_maquina * p["maquinas"]
    investimento = p["capex_por_maquina_rs"] * p["maquinas"]
    fluxos = [-investimento] + [ganho_frota] * p["anos"]
    anuidade = sum(1 / (1 + p["tma"]) ** t for t in range(1, p["anos"] + 1))
    teto_capex = ganho_maquina * anuidade

    print("Base medida, anualizada (1 máquina)")
    print(f"  massa dosada:       {br(kg_total_ano)} kg/ano")
    print(f"  masterbatch:        {br(kg_mb_ano)} kg/ano")
    print(f"  diferencial MB-PP:  R$ {br(diferencial, 2)}/kg\n")

    print("Alavancas por máquina/ano")
    print(f"  B1 sobredosagem evitada ({p['sobredosagem_evitada']:.0%}): {br(b1_kg)} kg -> R$ {br(b1_kg * diferencial)}")
    print(f"  B2 setpoint -{br(p['reducao_setpoint_pp'], 2)} p.p.:         {br(b2_kg)} kg -> R$ {br(b2_kg * diferencial)}\n")

    print("Caso da frota")
    print(f"  investimento:       R$ {br(investimento)} ({p['maquinas']} máquinas)")
    print(f"  ganho anual:        R$ {br(ganho_frota)}")
    print(f"  payback:            {investimento / ganho_frota * 12:.0f} meses")
    print(f"  VPL {p['anos']} anos @ {p['tma']:.0%}:   R$ {br(vpl(p['tma'], fluxos))}")
    print(f"  TIR:                {tir(fluxos):.0%} a.a.")
    print(f"  teto de CAPEX:      R$ {br(teto_capex)} por máquina (VPL zero)")
    print(f"  margem de segurança: {br(teto_capex / p['capex_por_maquina_rs'], 1)}x o preço cotado\n")

    print("Sensibilidade de B1 (1 máquina)")
    for s in (0.03, 0.05, 0.10, 0.20):
        print(f"  {s:>4.0%} de sobredosagem -> {br(kg_mb_ano * s)} kg -> R$ {br(kg_mb_ano * s * diferencial)}")


if __name__ == "__main__":
    main()
