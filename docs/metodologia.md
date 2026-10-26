# Metodologia

## De onde vem cada número

| Fonte | O que entrega | Como entrou no estudo |
|---|---|---|
| Dosador gravimétrico | peso dosado de cada componente, coletado por OPC-UA em um banco de série temporal | consumo medido por OP e percentual de pigmento hora a hora |
| MES de injeção | número da OP escrito no dosador quando a ordem começa | liga a pesagem à ordem certa |
| ERP | ficha técnica, quantidade planejada e emitida por linha, tipo de emissão | consumo registrado por OP |

## Etapas

1. **Sanear a base.** Classificar cada janela de dosagem e cada OP antes de qualquer conta. Na base real, a primeira execução encontrou OPs de teste, uma OP aberta meses antes da dosagem e OPs medidas que o ERP ainda não tinha sincronizado.
2. **Provar o backflush.** Comparar a razão emitido/planejado entre as linhas da ficha. Razão constante em itens tão diferentes é a assinatura do backflush, e o campo de tipo de emissão do ERP confirmou.
3. **Separar volume de mistura.** Calcular o gap por componente. Gap igual na resina e no pigmento, com o percentual de pigmento batendo com a receita, mostra que o dosador acerta a mistura.
4. **Escolher a métrica.** Comparar a estabilidade do gap em percentual, em kg e em peças equivalentes. Com poucas OPs, a métrica errada gera um intervalo de confiança que cruza zero.
5. **Precificar.** Valorar o pigmento poupado pelo diferencial de preço contra a resina, porque a massa da peça não muda.
6. **Montar o caso.** Payback, VPL, TIR e o teto de CAPEX que ainda dá VPL zero, para mostrar a folga do caso em relação ao preço cotado.

## Cuidados que mudaram o resultado

- **Confundidores.** Duas OPs com o mesmo gap em peças pareciam indicar perda fixa por troca de OP. Elas diferiam em tamanho, molde, perda declarada e tipo de emissão ao mesmo tempo. A conclusão só vale com várias OPs do mesmo produto em tamanhos diferentes.
- **Valoração.** Usar o preço cheio do pigmento em vez do diferencial superestimava o ganho.
- **Escopo.** A galha (canal de alimentação) faz parte do processo e já é paga pelo cliente. O excesso de galha física sobre a ficha foi documentado, mas não entrou como ganho.
