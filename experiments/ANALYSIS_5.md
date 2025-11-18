# Reunião 18/11

## Teste de relevância estatística

- Para cada padrão encontrado, agora, antes filtrar pela semelhança (jaccard), testamos pela relevância (os 100 primeiros)
- Para cada padrão, com um dado suporte `s`, buscamos 10k subgrupos no dataset de validação com esse mesmo suporte e a mesma proporção de classes.
    - Primeiro, o AUC do padrão e do modelo são recalculados no dataset de validação
    - Depois, para cada subgrupo, o AUC é calculado
    - Para cada diff de AUC_sg - AUC_modelo, se o diff for maior ou igual que o AUC_sg_obs - AUC_modelo, ou seja, (AUC_ag > AUC_sg_obs), então incrementemos um counter
    - No final da avaliação dos 10k subgrupos, o p-valor será igual a porcentagem dos subugrpos com diff maior ou igual do que o diff observado
- Entretanto, esses 100 p-valores devem ser ajustados por causa da taxa de falsos positivos (False Discovery Rate - FDR)
   - Em estudos com muitos testes, a chance de obter um falso positivo aumenta a cada teste realizado (falso positivo = hipótese nula é rejeitada => padrão é relevante)
- Depois do reajuste, os padrões filtrados (máximo 100) passam pelo filtro de similaridade e os top-k são retornados.


### Problemas com dados sintéticos

- O método aqui utilizado, Benjamini/Hochberg (ou o Benjamini/Yekutieli) corrigem o valor p com base nos valores obtidos em todos os testes. Se os 100 testes tiverem valores p altos, então o valor p baixo (menor que 0.05) será muito provavelmente tratado como irrelevante, pois irá se ajustar com base nos outros casos


- Portanto, nos dados sintéticos, sugiro não basear se no resultado final da valição estatística para dizer se o padrão foi encontrado, e sim somente pelo filtro de similaridade de jaccard.

- Se o noise for 0, então muito provável que somente exista no dataset os padrões injetados, então o FDR não corrige muito o valor p, mas com noise 0.5 e 1, mais padrões irrerelevantes são encontrados, e assim, o valores p pequenos são corrigidos.

Exemplo:

- Dataset 1k, tamanho padrão 20, 5k de iterações

- **Noise 0**

```
ALL PATTERNS
================
  Pattern 0: Quality=1.4094, ROC-AUC=0.7000, Support=20, Pattern={'D'}
  Pattern 1: Quality=1.2845, ROC-AUC=0.7000, Support=20, Pattern={'C'}{'D'}
  Pattern 2: Quality=0.8427, ROC-AUC=0.8000, Support=20, Pattern={'B'}
  Pattern 3: Quality=0.5588, ROC-AUC=0.9000, Support=20, Pattern={'A'}
================================================================================

================
APPLYING STATISTICAL VALIDATION
================

 Pattern 0
    Support=20, Class balance={0.0: 10, 1.0: 10}. Pattern AUC=0.7000, p-value=0.000400

 Pattern 1
    Support=20, Class balance={0.0: 10, 1.0: 10}. Pattern AUC=0.7000, p-value=0.000600

 Pattern 2
    Support=20, Class balance={1.0: 10, 0.0: 10}. Pattern AUC=0.8000, p-value=0.010599

 Pattern 3
    Support=20, Class balance={0.0: 10, 1.0: 10}. Pattern AUC=0.9000, p-value=0.171183

 Applying FDR correction
  Pattern 0: AUC diff=0.2504, p=0.000400, adj_p=0.001200 --> SIGNIFICANT
  Pattern 1: AUC diff=0.2504, p=0.000600, adj_p=0.001200 --> SIGNIFICANT
  Pattern 2: AUC diff=0.1504, p=0.010599, adj_p=0.014132 --> SIGNIFICANT
  Pattern 3: AUC diff=0.0504, p=0.171183, adj_p=0.171183 --> NOT SIGNIFICANT

 Found 3 significant patterns out of 4 tested.
  Validation completed in 26.96 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=1.4094, ROC-AUC=0.7000, Support=20, Pattern={'D'}
  Pattern 1: Quality=1.2845, ROC-AUC=0.7000, Support=20, Pattern={'C'}{'D'}
  Pattern 2: Quality=0.8427, ROC-AUC=0.8000, Support=20, Pattern={'B'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=1.4094, ROC-AUC=0.7000, Support=20, Pattern={'D'}
  Pattern 1: Quality=0.8427, ROC-AUC=0.8000, Support=20, Pattern={'B'}
================================================================================

Quality: 1.4093946160348323, Extent: 20, ROCAUC: 0.7, Pattern: {'D'}
Quality: 0.8426570161951887, Extent: 20, ROCAUC: 0.7999999999999999, Pattern: {'B'}
```

- **Noise 1:**

```
================
ALL PATTERNS
================
  Pattern 0: Quality=1.4180, ROC-AUC=0.7000, Support=20, Pattern={'D'}
  Pattern 1: Quality=0.8478, ROC-AUC=0.8000, Support=20, Pattern={'B'}
  Pattern 2: Quality=0.3125, ROC-AUC=0.9395, Support=608, Pattern={'Z'}{'X'}{'Z'}
  Pattern 3: Quality=0.2444, ROC-AUC=0.9325, Support=382, Pattern={'Y'}{'Y'}{'V'}{'Z'}
  Pattern 4: Quality=0.2368, ROC-AUC=0.9361, Support=387, Pattern={'W'}{'V'}{'Z'}{'V'}
  Pattern 5: Quality=0.2364, ROC-AUC=0.9362, Support=383, Pattern={'Z'}{'Y'}{'X'}{'V'}
  Pattern 6: Quality=0.2357, ROC-AUC=0.9365, Support=371, Pattern={'Y'}{'Z'}{'X'}{'Z'}
  Pattern 7: Quality=0.2333, ROC-AUC=0.9381, Support=396, Pattern={'V'}{'Z'}{'X'}{'V'}
  Pattern 8: Quality=0.2332, ROC-AUC=0.9380, Support=379, Pattern={'Y'}{'Y'}{'Z'}{'Z'}
  ....

 Pattern 118: Quality=0.1001, ROC-AUC=0.9408, Support=74, Pattern={'Z'}{'W'}{'W'}{'V'}{'Z'}{'Z'}

================
APPLYING STATISTICAL VALIDATION
================

 Pattern 0
    Support=20, Class balance={1.0: 10, 0.0: 10}. Pattern AUC=0.7000, p-value=0.000400

 Pattern 1
    Support=20, Class balance={1.0: 10, 0.0: 10}. Pattern AUC=0.8000, p-value=0.008699

 Pattern 2
    Support=608, Class balance={0.0: 311, 1.0: 297}. Pattern AUC=0.9471, p-value=0.183082

 Pattern 3
    Support=381, Class balance={0.0: 195, 1.0: 186}. Pattern AUC=0.9521, p-value=0.522748

 ....

  Applying FDR correction
  Pattern 0: AUC diff=0.2516, p=0.000400, adj_p=0.039996 --> SIGNIFICANT
  Pattern 1: AUC diff=0.1516, p=0.008699, adj_p=0.217478 --> NOT SIGNIFICANT
  Pattern 2: AUC diff=0.0045, p=0.183082, adj_p=0.428562 --> NOT SIGNIFICANT
  Pattern 3: AUC diff=-0.0006, p=0.522748, adj_p=0.631744 --> NOT SIGNIFICANT
  Pattern 4: AUC diff=-0.0058, p=0.770623, adj_p=0.813287 --> NOT SIGNIFICANT
  Pattern 5: AUC diff=0.0157, p=0.023798, adj_p=0.264418 --> NOT SIGNIFICANT
  Pattern 6: AUC diff=0.0114, p=0.070993, adj_p=0.322695 --> NOT SIGNIFICANT
  Pattern 7: AUC diff=0.0056, p=0.242176, adj_p=0.497066 --> NOT SIGNIFICANT
  Pattern 8: AUC diff=0.0113, p=0.070493, adj_p=0.322695 --> NOT SIGNIFICANT

 ...

Found 1 significant patterns out of 100 tested.
Validation completed in 1960.56 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=1.4180, ROC-AUC=0.7000, Support=20, Pattern={'D'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=1.4180, ROC-AUC=0.7000, Support=20, Pattern={'D'}
================================================================================
```

## Experimentos com dataset sintéticos

Cada arquivo abaixo terá 3 variações, com noise 0, 0.5 e 1, e possivelmente com sequências de tamanho 8-15 também.

Os datasets já criados (fora os "l_4") têm sequências de tamanho 15-30. Antes, os experimentos estavam sendo realizados com tamanho de 8-15. Foi notado uma queda de performance com sequências mais longas.

- config/d_1k__q_5%__l_4.json
- config/d_1k__q_5%.json
- config/d_1k__q_20__l_4.json
- config/d_1k__q_20.json
- config/d_5k__q_1%__l_4.json
- config/d_5k__q_1%.json
- config/d_5k__q_5%__l_4.json
- config/d_5k__q_5%.json
- config/d_5k__q_20__l_4.json
- config/d_5k__q_20.json
- config/d_10k__q_0.5%__l_4.json
- config/d_10k__q_0.5%.json
- config/d_10k__q_1%__l_4.json
- config/d_10k__q_1%.json
- config/d_10k__q_5%__l_4.json
- config/d_10k__q_5%.json
- config/d_10k__q_20__l_4.json
- config/d_10k__q_20.json
- config/d_20k__q_0.1%__l_4.json
- config/d_20k__q_0.1%.json
- config/d_20k__q_0.5%__l_4.json
- config/d_20k__q_0.5%.json
- config/d_20k__q_1%__l_4.json
- config/d_20k__q_1%.json
- config/d_20k__q_5%__l_4.json
- config/d_20k__q_5%.json
- config/d_20k__q_20__l_4.json
- config/d_20k__q_20.json
- config/d_50k__q_0.1%__l_4.json
- config/d_50k__q_0.1%.json
- config/d_50k__q_0.5%__l_4.json
- config/d_50k__q_0.5%.json
- config/d_50k__q_1%__l_4.json
- config/d_50k__q_1%.json
- config/d_50k__q_5%__l_4.json
- config/d_50k__q_5%.json
- config/d_50k__q_20__l_4.json
- config/d_50k__q_20.json

## Experimentos com dataset reais

Treinei um LSTM para alguns datasets do artigo Anytime..., vários padrões longos são encontrados, e com qualide e suporte bons, portanto, ficam no topo. Entretanto, a interpretabilidade deles é baixa, assim, adicionei um parâmetro de max-size dos padrões.

### Exemplo efeito max size (dataset 'emm_context')

<details>
  <summary>Sem max size</summary>
 
`ipython3 -c "from mctsextent.main import get_patterns;get_patterns(filename='emm_context', time_budget=2000, top_k=10, theta=0.5, iterations_limit=1000)"`


```
================
ALL PATTERNS
================
  Pattern 0: Quality=2.2467, ROC-AUC=0.7000, Support=25, Pattern={'23'}{'29'}{'46'}{'47'}{'52'}{'51'}{'51'}{'51'}{'53'}
  Pattern 1: Quality=2.1865, ROC-AUC=0.6950, Support=30, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 2: Quality=2.1342, ROC-AUC=0.7160, Support=30, Pattern={'29'}{'46'}{'47'}{'46'}{'51'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 3: Quality=2.1064, ROC-AUC=0.6852, Support=21, Pattern={'1'}{'13'}{'18'}{'19'}{'23'}{'46'}{'47'}{'52'}{'51'}{'52'}{'51'}{'54'}{'54'}{'54'}{'53'}
  Pattern 4: Quality=2.0328, ROC-AUC=0.7000, Support=25, Pattern={'1'}{'8'}{'18'}{'19'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 5: Quality=1.7576, ROC-AUC=0.7329, Support=37, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 6: Quality=1.7266, ROC-AUC=0.7059, Support=21, Pattern={'1'}{'8'}{'18'}{'19'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 7: Quality=1.6835, ROC-AUC=0.7314, Support=33, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 8: Quality=1.6443, ROC-AUC=0.7507, Support=38, Pattern={'13'}{'18'}{'18'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 9: Quality=1.6173, ROC-AUC=0.7222, Support=27, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 10: Quality=1.5474, ROC-AUC=0.7507, Support=38, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 11: Quality=1.5466, ROC-AUC=0.7212, Support=21, Pattern={'8'}{'13'}{'17'}{'19'}{'23'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 12: Quality=1.5091, ROC-AUC=0.7091, Support=21, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 13: Quality=1.4983, ROC-AUC=0.7212, Support=21, Pattern={'8'}{'13'}{'18'}{'17'}{'19'}{'23'}{'25'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 14: Quality=1.4979, ROC-AUC=0.7500, Support=26, Pattern={'1'}{'46'}{'47'}{'46'}{'51'}{'52'}{'51'}{'51'}{'53'}
  Pattern 15: Quality=1.4660, ROC-AUC=0.7547, Support=40, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 16: Quality=1.3430, ROC-AUC=0.7604, Support=32, Pattern={'1'}{'13'}{'18'}{'19'}{'23'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'54'}{'54'}{'53'}
  Pattern 17: Quality=1.2222, ROC-AUC=0.7741, Support=42, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 18: Quality=1.1720, ROC-AUC=0.7923, Support=41, Pattern={'8'}{'16'}{'17'}{'46'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 19: Quality=1.1602, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'52'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 20: Quality=1.1478, ROC-AUC=0.7759, Support=36, Pattern={'8'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 21: Quality=1.1373, ROC-AUC=0.7411, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 22: Quality=1.1207, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 23: Quality=1.1022, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 24: Quality=1.0958, ROC-AUC=0.7417, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 25: Quality=1.0646, ROC-AUC=0.7901, Support=45, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 26: Quality=1.0545, ROC-AUC=0.8161, Support=48, Pattern={'29'}{'46'}{'51'}{'52'}{'51'}{'51'}{'54'}
  Pattern 27: Quality=1.0242, ROC-AUC=0.7714, Support=24, Pattern={'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 28: Quality=1.0225, ROC-AUC=0.7820, Support=34, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'25'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 29: Quality=1.0126, ROC-AUC=0.7792, Support=38, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 30: Quality=1.0084, ROC-AUC=0.7950, Support=33, Pattern={'13'}{'19'}{'23'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}{'54'}
  Pattern 31: Quality=0.9962, ROC-AUC=0.7815, Support=31, Pattern={'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 32: Quality=0.9641, ROC-AUC=0.8020, Support=47, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 33: Quality=0.9479, ROC-AUC=0.7815, Support=31, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 34: Quality=0.9369, ROC-AUC=0.7643, Support=27, Pattern={'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 35: Quality=0.9211, ROC-AUC=0.7643, Support=27, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 36: Quality=0.9075, ROC-AUC=0.8279, Support=54, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'54'}{'54'}{'53'}
  Pattern 37: Quality=0.8751, ROC-AUC=0.8223, Support=47, Pattern={'8'}{'17'}{'46'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 38: Quality=0.8717, ROC-AUC=0.7756, Support=25, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 39: Quality=0.8709, ROC-AUC=0.8304, Support=48, Pattern={'17'}{'46'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 40: Quality=0.8693, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}
  Pattern 41: Quality=0.8693, ROC-AUC=0.8214, Support=37, Pattern={'29'}{'46'}{'47'}{'51'}{'51'}{'54'}{'54'}
  Pattern 42: Quality=0.8654, ROC-AUC=0.8219, Support=53, Pattern={'13'}{'18'}{'19'}{'23'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 43: Quality=0.8474, ROC-AUC=0.7692, Support=24, Pattern={'1'}{'8'}{'18'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 44: Quality=0.8463, ROC-AUC=0.8083, Support=38, Pattern={'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}{'53'}{'54'}
  Pattern 45: Quality=0.8283, ROC-AUC=0.8279, Support=54, Pattern={'17'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}{'53'}{'54'}
  Pattern 46: Quality=0.8283, ROC-AUC=0.8279, Support=54, Pattern={'19'}{'24'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 47: Quality=0.8110, ROC-AUC=0.7756, Support=25, Pattern={'1'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 48: Quality=0.7935, ROC-AUC=0.8279, Support=54, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 49: Quality=0.7822, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'23'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}{'54'}
  Pattern 50: Quality=0.7819, ROC-AUC=0.8487, Support=59, Pattern={'24'}{'29'}{'46'}{'51'}{'53'}{'53'}
  Pattern 51: Quality=0.7791, ROC-AUC=0.8254, Support=37, Pattern={'23'}{'29'}{'47'}{'46'}{'52'}{'52'}{'52'}{'54'}
  Pattern 52: Quality=0.7781, ROC-AUC=0.8382, Support=60, Pattern={'13'}{'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}
  Pattern 53: Quality=0.7752, ROC-AUC=0.8219, Support=53, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 54: Quality=0.7690, ROC-AUC=0.8111, Support=37, Pattern={'8'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'51'}{'54'}{'53'}{'53'}{'53'}
  Pattern 55: Quality=0.7615, ROC-AUC=0.8537, Support=66, Pattern={'19'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 56: Quality=0.7606, ROC-AUC=0.8105, Support=44, Pattern={'8'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}{'53'}
  Pattern 57: Quality=0.7469, ROC-AUC=0.8296, Support=47, Pattern={'1'}{'19'}{'23'}{'24'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 58: Quality=0.7459, ROC-AUC=0.8674, Support=69, Pattern={'29'}{'46'}{'51'}{'51'}
  Pattern 59: Quality=0.7444, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'24'}{'46'}{'47'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 60: Quality=0.7444, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'23'}{'29'}{'46'}{'47'}{'46'}{'51'}{'51'}{'53'}{'54'}
  Pattern 61: Quality=0.7397, ROC-AUC=0.8242, Support=43, Pattern={'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 62: Quality=0.7382, ROC-AUC=0.8000, Support=31, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 63: Quality=0.7338, ROC-AUC=0.7967, Support=27, Pattern={'8'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'54'}
  Pattern 64: Quality=0.7320, ROC-AUC=0.8971, Support=46, Pattern={'40'}
  Pattern 65: Quality=0.7307, ROC-AUC=0.8487, Support=59, Pattern={'23'}{'29'}{'46'}{'51'}{'54'}{'54'}{'53'}
  Pattern 66: Quality=0.7307, ROC-AUC=0.8487, Support=59, Pattern={'24'}{'29'}{'46'}{'52'}{'51'}{'53'}{'53'}
  Pattern 67: Quality=0.7104, ROC-AUC=0.8537, Support=66, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 68: Quality=0.7104, ROC-AUC=0.8537, Support=66, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'54'}{'53'}
  Pattern 69: Quality=0.7077, ROC-AUC=0.7909, Support=32, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 70: Quality=0.6850, ROC-AUC=0.8487, Support=59, Pattern={'17'}{'19'}{'23'}{'46'}{'51'}{'54'}{'53'}{'53'}
  Pattern 71: Quality=0.6770, ROC-AUC=0.8279, Support=54, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 72: Quality=0.6669, ROC-AUC=0.8699, Support=73, Pattern={'23'}{'51'}{'51'}{'51'}{'53'}
  Pattern 73: Quality=0.6646, ROC-AUC=0.8537, Support=66, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 74: Quality=0.6605, ROC-AUC=0.8103, Support=34, Pattern={'8'}{'18'}{'18'}{'23'}{'24'}{'24'}{'27'}{'29'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 75: Quality=0.6556, ROC-AUC=0.8370, Support=37, Pattern={'8'}{'46'}{'47'}{'52'}{'51'}{'51'}{'52'}{'53'}
  Pattern 76: Quality=0.6533, ROC-AUC=0.8997, Support=80, Pattern={'23'}{'46'}
  Pattern 77: Quality=0.6459, ROC-AUC=0.8914, Support=47, Pattern={'19'}{'47'}
  Pattern 78: Quality=0.6446, ROC-AUC=0.7917, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 79: Quality=0.6423, ROC-AUC=0.8512, Support=64, Pattern={'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 80: Quality=0.6401, ROC-AUC=0.8638, Support=77, Pattern={'23'}{'29'}{'51'}{'51'}{'54'}{'54'}{'53'}
  Pattern 81: Quality=0.6400, ROC-AUC=0.8026, Support=31, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}
  Pattern 82: Quality=0.6378, ROC-AUC=0.8669, Support=72, Pattern={'8'}{'23'}{'51'}{'51'}{'51'}{'53'}
  Pattern 83: Quality=0.6367, ROC-AUC=0.8566, Support=58, Pattern={'46'}{'51'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 84: Quality=0.6291, ROC-AUC=0.8000, Support=32, Pattern={'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 85: Quality=0.6262, ROC-AUC=0.8333, Support=53, Pattern={'18'}{'19'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}
  Pattern 86: Quality=0.6255, ROC-AUC=0.8611, Support=66, Pattern={'23'}{'29'}{'46'}{'52'}{'52'}{'52'}{'54'}
  Pattern 87: Quality=0.6255, ROC-AUC=0.8611, Support=66, Pattern={'19'}{'23'}{'46'}{'52'}{'52'}{'51'}{'54'}
  Pattern 88: Quality=0.6227, ROC-AUC=0.8317, Support=50, Pattern={'8'}{'13'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 89: Quality=0.6209, ROC-AUC=0.8674, Support=69, Pattern={'29'}{'46'}{'51'}{'52'}{'51'}{'54'}
  Pattern 90: Quality=0.6209, ROC-AUC=0.8510, Support=45, Pattern={'29'}{'46'}{'52'}{'54'}{'53'}{'53'}{'53'}
  Pattern 91: Quality=0.6200, ROC-AUC=0.9303, Support=136, Pattern={'23'}
  Pattern 92: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'46'}
  Pattern 93: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'29'}{'46'}
  Pattern 94: Quality=0.6183, ROC-AUC=0.8978, Support=110, Pattern={'29'}{'51'}{'51'}
  Pattern 95: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'29'}
  Pattern 96: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'19'}
  Pattern 97: Quality=0.6119, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'53'}
  Pattern 98: Quality=0.6090, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}
  Pattern 99: Quality=0.6071, ROC-AUC=0.8971, Support=46, Pattern={'29'}{'40'}
  Pattern 100: Quality=0.6062, ROC-AUC=0.9241, Support=53, Pattern={'47'}
  Pattern 101: Quality=0.6029, ROC-AUC=0.8468, Support=49, Pattern={'13'}{'19'}{'23'}{'27'}{'29'}{'51'}{'51'}{'52'}{'53'}
  Pattern 102: Quality=0.5999, ROC-AUC=0.8333, Support=53, Pattern={'1'}{'18'}{'17'}{'23'}{'29'}{'46'}{'52'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 103: Quality=0.5988, ROC-AUC=0.8457, Support=63, Pattern={'1'}{'17'}{'19'}{'23'}{'29'}{'46'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 104: Quality=0.5953, ROC-AUC=0.8565, Support=67, Pattern={'29'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 105: Quality=0.5944, ROC-AUC=0.8638, Support=77, Pattern={'19'}{'23'}{'51'}{'52'}{'52'}{'53'}{'53'}{'54'}
  Pattern 106: Quality=0.5943, ROC-AUC=0.8673, Support=62, Pattern={'19'}{'23'}{'29'}{'46'}{'53'}{'53'}
  Pattern 107: Quality=0.5920, ROC-AUC=0.8733, Support=44, Pattern={'23'}{'46'}{'47'}{'51'}
  Pattern 108: Quality=0.5819, ROC-AUC=0.8978, Support=86, Pattern={'51'}{'51'}{'51'}
  Pattern 109: Quality=0.5808, ROC-AUC=0.8547, Support=60, Pattern={'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'53'}{'53'}{'54'}
  Pattern 110: Quality=0.5782, ROC-AUC=0.8786, Support=73, Pattern={'19'}{'23'}{'46'}{'51'}{'53'}
  Pattern 111: Quality=0.5762, ROC-AUC=0.7941, Support=25, Pattern={'1'}{'8'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 112: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'29'}{'46'}{'53'}
  Pattern 113: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'23'}{'29'}{'46'}
  Pattern 114: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'23'}{'46'}
  Pattern 115: Quality=0.5750, ROC-AUC=0.8333, Support=53, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 116: Quality=0.5750, ROC-AUC=0.8333, Support=53, Pattern={'1'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 117: Quality=0.5750, ROC-AUC=0.8889, Support=21, Pattern={'40'}{'43'}
  Pattern 118: Quality=0.5717, ROC-AUC=0.8148, Support=33, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'18'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 119: Quality=0.5713, ROC-AUC=0.8272, Support=33, Pattern={'16'}{'17'}{'19'}{'23'}{'24'}{'46'}{'47'}{'46'}{'52'}{'53'}{'54'}{'54'}
  Pattern 120: Quality=0.5696, ROC-AUC=0.8321, Support=59, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 121: Quality=0.5688, ROC-AUC=0.8043, Support=29, Pattern={'1'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 122: Quality=0.5681, ROC-AUC=0.8493, Support=71, Pattern={'16'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 123: Quality=0.5654, ROC-AUC=0.8621, Support=55, Pattern={'8'}{'23'}{'51'}{'51'}{'51'}{'53'}{'53'}
  Pattern 124: Quality=0.5630, ROC-AUC=0.8462, Support=63, Pattern={'1'}{'13'}{'18'}{'18'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 125: Quality=0.5624, ROC-AUC=0.8557, Support=66, Pattern={'19'}{'23'}{'24'}{'29'}{'51'}{'51'}{'52'}{'52'}{'54'}{'53'}
  Pattern 126: Quality=0.5552, ROC-AUC=0.8760, Support=76, Pattern={'29'}{'51'}{'52'}{'51'}{'51'}{'54'}
  Pattern 127: Quality=0.5533, ROC-AUC=0.8304, Support=46, Pattern={'16'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 128: Quality=0.5527, ROC-AUC=0.8904, Support=46, Pattern={'23'}{'46'}{'47'}
  Pattern 129: Quality=0.5514, ROC-AUC=0.9352, Support=21, Pattern={'56'}
  Pattern 130: Quality=0.5473, ROC-AUC=0.7875, Support=21, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 131: Quality=0.5445, ROC-AUC=0.9213, Support=126, Pattern={'29'}{'51'}
  Pattern 132: Quality=0.5386, ROC-AUC=0.8278, Support=36, Pattern={'1'}{'8'}{'18'}{'19'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 133: Quality=0.5384, ROC-AUC=0.8611, Support=66, Pattern={'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'52'}{'51'}{'52'}
  Pattern 134: Quality=0.5376, ROC-AUC=0.8512, Support=64, Pattern={'18'}{'19'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 135: Quality=0.5354, ROC-AUC=0.9228, Support=127, Pattern={'23'}{'52'}
  Pattern 136: Quality=0.5354, ROC-AUC=0.8488, Support=69, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 137: Quality=0.5343, ROC-AUC=0.8903, Support=104, Pattern={'23'}{'51'}{'52'}{'51'}{'53'}
  Pattern 138: Quality=0.5335, ROC-AUC=0.9118, Support=50, Pattern={'47'}{'51'}
  Pattern 139: Quality=0.5319, ROC-AUC=0.9551, Support=128, Pattern={'46'}
  Pattern 140: Quality=0.5301, ROC-AUC=0.8321, Support=59, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 141: Quality=0.5298, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}{'54'}
  Pattern 142: Quality=0.5297, ROC-AUC=0.8419, Support=50, Pattern={'16'}{'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'51'}{'51'}{'53'}{'54'}
  Pattern 143: Quality=0.5284, ROC-AUC=0.9242, Support=130, Pattern={'29'}{'52'}
  Pattern 144: Quality=0.5221, ROC-AUC=0.9048, Support=82, Pattern={'24'}{'29'}{'46'}
  Pattern 145: Quality=0.5208, ROC-AUC=0.8743, Support=45, Pattern={'29'}{'47'}{'46'}{'51'}{'54'}
  Pattern 146: Quality=0.5202, ROC-AUC=0.8786, Support=73, Pattern={'23'}{'29'}{'46'}{'51'}{'54'}{'53'}
  Pattern 147: Quality=0.5202, ROC-AUC=0.8786, Support=73, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}{'53'}
  Pattern 148: Quality=0.5197, ROC-AUC=0.8621, Support=55, Pattern={'23'}{'29'}{'51'}{'51'}{'51'}{'53'}{'53'}{'54'}
  Pattern 149: Quality=0.5178, ROC-AUC=0.7863, Support=22, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 150: Quality=0.5157, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'53'}
  Pattern 151: Quality=0.5149, ROC-AUC=0.8860, Support=75, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}
  Pattern 152: Quality=0.5149, ROC-AUC=0.8860, Support=75, Pattern={'23'}{'29'}{'46'}{'51'}{'54'}
  Pattern 153: Quality=0.5100, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'53'}
  Pattern 154: Quality=0.5100, ROC-AUC=0.9275, Support=134, Pattern={'29'}{'53'}
  Pattern 155: Quality=0.5093, ROC-AUC=0.8683, Support=56, Pattern={'25'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 156: Quality=0.5092, ROC-AUC=0.9274, Support=130, Pattern={'16'}{'23'}
  Pattern 157: Quality=0.5076, ROC-AUC=0.8512, Support=64, Pattern={'18'}{'19'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 158: Quality=0.5044, ROC-AUC=0.8651, Support=78, Pattern={'1'}{'18'}{'19'}{'51'}{'52'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 159: Quality=0.5010, ROC-AUC=0.8810, Support=74, Pattern={'19'}{'23'}{'29'}{'46'}{'52'}{'53'}
  Pattern 160: Quality=0.4989, ROC-AUC=0.9296, Support=135, Pattern={'23'}{'29'}
  Pattern 161: Quality=0.4989, ROC-AUC=0.9296, Support=135, Pattern={'19'}{'23'}
  Pattern 162: Quality=0.4987, ROC-AUC=0.8877, Support=102, Pattern={'17'}{'29'}{'52'}{'51'}{'51'}{'53'}
  Pattern 163: Quality=0.4978, ROC-AUC=0.9199, Support=52, Pattern={'47'}{'52'}
  Pattern 164: Quality=0.4958, ROC-AUC=0.8481, Support=65, Pattern={'8'}{'18'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 165: Quality=0.4937, ROC-AUC=0.8881, Support=101, Pattern={'23'}{'29'}{'52'}{'51'}{'51'}{'53'}
  Pattern 166: Quality=0.4932, ROC-AUC=0.8947, Support=105, Pattern={'19'}{'23'}{'52'}{'51'}{'51'}
  Pattern 167: Quality=0.4932, ROC-AUC=0.8947, Support=105, Pattern={'23'}{'29'}{'52'}{'51'}{'51'}
  Pattern 168: Quality=0.4932, ROC-AUC=0.8503, Support=49, Pattern={'18'}{'18'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'53'}
  Pattern 169: Quality=0.4931, ROC-AUC=0.8913, Support=87, Pattern={'24'}{'29'}{'51'}{'53'}{'53'}
  Pattern 170: Quality=0.4919, ROC-AUC=0.8213, Support=43, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 171: Quality=0.4907, ROC-AUC=0.9313, Support=139, Pattern={'24'}{'29'}
  Pattern 172: Quality=0.4907, ROC-AUC=0.9313, Support=139, Pattern={'19'}{'29'}
  Pattern 173: Quality=0.4907, ROC-AUC=0.8222, Support=29, Pattern={'1'}{'13'}{'18'}{'18'}{'46'}{'49'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 174: Quality=0.4878, ROC-AUC=0.9199, Support=42, Pattern={'40'}{'45'}
  Pattern 175: Quality=0.4875, ROC-AUC=0.9325, Support=148, Pattern={'51'}{'51'}
  Pattern 176: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'23'}{'46'}{'52'}{'51'}{'54'}
  Pattern 177: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'23'}{'29'}{'46'}{'52'}{'52'}{'54'}
  Pattern 178: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'29'}{'46'}{'51'}{'54'}{'53'}
  Pattern 179: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'23'}{'46'}{'52'}{'52'}{'54'}
  Pattern 180: Quality=0.4865, ROC-AUC=0.8663, Support=67, Pattern={'8'}{'13'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'53'}
  Pattern 181: Quality=0.4865, ROC-AUC=0.8361, Support=49, Pattern={'8'}{'16'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'51'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 182: Quality=0.4858, ROC-AUC=0.7969, Support=20, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'40'}{'45'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 183: Quality=0.4840, ROC-AUC=0.8714, Support=57, Pattern={'25'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 184: Quality=0.4813, ROC-AUC=0.9241, Support=53, Pattern={'47'}{'46'}
  Pattern 185: Quality=0.4804, ROC-AUC=0.8638, Support=77, Pattern={'17'}{'18'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'53'}{'53'}{'54'}
  Pattern 186: Quality=0.4791, ROC-AUC=0.9162, Support=121, Pattern={'29'}{'51'}{'53'}
  Pattern 187: Quality=0.4785, ROC-AUC=0.8921, Support=83, Pattern={'52'}{'51'}{'51'}{'51'}{'54'}
  Pattern 188: Quality=0.4780, ROC-AUC=0.8898, Support=102, Pattern={'23'}{'29'}{'52'}{'52'}{'52'}{'54'}
  Pattern 189: Quality=0.4768, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'53'}
  Pattern 190: Quality=0.4755, ROC-AUC=0.8636, Support=75, Pattern={'8'}{'18'}{'23'}{'52'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 191: Quality=0.4754, ROC-AUC=0.8419, Support=50, Pattern={'16'}{'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 192: Quality=0.4735, ROC-AUC=0.8904, Support=46, Pattern={'23'}{'46'}{'47'}{'46'}
  Pattern 193: Quality=0.4735, ROC-AUC=0.8904, Support=46, Pattern={'24'}{'29'}{'46'}{'47'}
  Pattern 194: Quality=0.4714, ROC-AUC=0.8352, Support=43, Pattern={'1'}{'8'}{'18'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 195: Quality=0.4709, ROC-AUC=0.8528, Support=66, Pattern={'8'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 196: Quality=0.4688, ROC-AUC=0.9177, Support=121, Pattern={'23'}{'52'}{'52'}
  Pattern 197: Quality=0.4682, ROC-AUC=0.9178, Support=122, Pattern={'23'}{'52'}{'53'}
  Pattern 198: Quality=0.4681, ROC-AUC=0.9134, Support=86, Pattern={'24'}{'46'}{'53'}
  Pattern 199: Quality=0.4661, ROC-AUC=0.8304, Support=46, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 200: Quality=0.4661, ROC-AUC=0.9299, Support=64, Pattern={'23'}{'49'}
  Pattern 201: Quality=0.4606, ROC-AUC=0.8565, Support=67, Pattern={'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 202: Quality=0.4594, ROC-AUC=0.9193, Support=124, Pattern={'29'}{'51'}{'52'}
  Pattern 203: Quality=0.4591, ROC-AUC=0.8457, Support=50, Pattern={'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'29'}{'51'}{'52'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 204: Quality=0.4590, ROC-AUC=0.9195, Support=125, Pattern={'29'}{'52'}{'53'}
  Pattern 205: Quality=0.4582, ROC-AUC=0.8928, Support=46, Pattern={'24'}{'46'}{'47'}{'51'}
  Pattern 206: Quality=0.4571, ROC-AUC=0.8182, Support=35, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 207: Quality=0.4560, ROC-AUC=0.9197, Support=123, Pattern={'23'}{'29'}{'51'}
  Pattern 208: Quality=0.4529, ROC-AUC=0.8483, Support=49, Pattern={'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 209: Quality=0.4507, ROC-AUC=0.9164, Support=87, Pattern={'24'}{'46'}{'51'}
  Pattern 210: Quality=0.4497, ROC-AUC=0.9209, Support=125, Pattern={'23'}{'52'}{'54'}
  Pattern 211: Quality=0.4476, ROC-AUC=0.8781, Support=95, Pattern={'8'}{'13'}{'16'}{'17'}{'29'}{'52'}{'51'}{'51'}{'53'}
  Pattern 212: Quality=0.4476, ROC-AUC=0.9213, Support=126, Pattern={'19'}{'29'}{'51'}
  Pattern 213: Quality=0.4463, ROC-AUC=0.8294, Support=36, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 214: Quality=0.4454, ROC-AUC=0.8848, Support=46, Pattern={'24'}{'47'}{'46'}{'51'}{'54'}
  Pattern 215: Quality=0.4451, ROC-AUC=0.8182, Support=34, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 216: Quality=0.4440, ROC-AUC=0.9218, Support=126, Pattern={'23'}{'29'}{'52'}
  Pattern 217: Quality=0.4419, ROC-AUC=0.8880, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'53'}{'54'}
  Pattern 218: Quality=0.4406, ROC-AUC=0.8886, Support=103, Pattern={'23'}{'29'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 219: Quality=0.4405, ROC-AUC=0.8621, Support=55, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'51'}{'51'}{'53'}{'53'}{'54'}
  Pattern 220: Quality=0.4403, ROC-AUC=0.8905, Support=86, Pattern={'23'}{'29'}{'51'}{'53'}{'53'}{'54'}
  Pattern 221: Quality=0.4377, ROC-AUC=0.8429, Support=39, Pattern={'8'}{'24'}{'25'}{'24'}{'29'}{'52'}{'52'}{'51'}{'52'}{'51'}{'53'}{'54'}{'54'}
  Pattern 222: Quality=0.4377, ROC-AUC=0.8429, Support=39, Pattern={'1'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'52'}{'52'}{'51'}{'54'}{'53'}{'53'}
  Pattern 223: Quality=0.4365, ROC-AUC=0.9306, Support=22, Pattern={'47'}{'47'}
  Pattern 224: Quality=0.4357, ROC-AUC=0.9231, Support=125, Pattern={'16'}{'23'}{'53'}
  Pattern 225: Quality=0.4354, ROC-AUC=0.8841, Support=100, Pattern={'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 226: Quality=0.4352, ROC-AUC=0.8913, Support=87, Pattern={'24'}{'29'}{'52'}{'51'}{'53'}{'53'}
  Pattern 227: Quality=0.4352, ROC-AUC=0.8913, Support=87, Pattern={'29'}{'52'}{'51'}{'53'}{'54'}{'53'}
  Pattern 228: Quality=0.4352, ROC-AUC=0.8913, Support=87, Pattern={'19'}{'29'}{'51'}{'53'}{'53'}{'54'}
  Pattern 229: Quality=0.4343, ROC-AUC=0.8952, Support=107, Pattern={'8'}{'19'}{'23'}{'29'}{'51'}{'51'}
  Pattern 230: Quality=0.4315, ROC-AUC=0.9242, Support=130, Pattern={'17'}{'29'}{'52'}
  Pattern 231: Quality=0.4315, ROC-AUC=0.9242, Support=130, Pattern={'19'}{'29'}{'52'}
  Pattern 232: Quality=0.4309, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'53'}
  Pattern 233: Quality=0.4299, ROC-AUC=0.9085, Support=93, Pattern={'18'}{'25'}{'29'}{'51'}
  Pattern 234: Quality=0.4298, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'29'}{'46'}{'52'}{'54'}
  Pattern 235: Quality=0.4296, ROC-AUC=0.9124, Support=123, Pattern={'51'}{'51'}{'52'}{'53'}
  Pattern 236: Quality=0.4285, ROC-AUC=0.9471, Support=166, Pattern={'24'}{'51'}
  Pattern 237: Quality=0.4279, ROC-AUC=0.8462, Support=50, Pattern={'8'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 238: Quality=0.4252, ROC-AUC=0.8903, Support=104, Pattern={'19'}{'23'}{'29'}{'51'}{'51'}{'53'}{'54'}
  Pattern 239: Quality=0.4220, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'53'}
  Pattern 240: Quality=0.4203, ROC-AUC=0.9223, Support=91, Pattern={'46'}{'51'}{'53'}
  Pattern 241: Quality=0.4201, ROC-AUC=0.8222, Support=29, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'18'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 242: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'19'}{'23'}{'53'}
  Pattern 243: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'53'}
  Pattern 244: Quality=0.4187, ROC-AUC=0.8746, Support=72, Pattern={'17'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'54'}{'54'}
  Pattern 245: Quality=0.4174, ROC-AUC=0.8538, Support=37, Pattern={'8'}{'13'}{'16'}{'17'}{'29'}{'40'}{'52'}{'51'}{'51'}{'53'}
  Pattern 246: Quality=0.4164, ROC-AUC=0.8912, Support=77, Pattern={'18'}{'19'}{'23'}{'29'}{'46'}{'53'}
  Pattern 247: Quality=0.4159, ROC-AUC=0.8733, Support=44, Pattern={'19'}{'46'}{'47'}{'52'}{'51'}{'52'}{'54'}
  Pattern 248: Quality=0.4158, ROC-AUC=0.8882, Support=44, Pattern={'17'}{'29'}{'40'}{'52'}{'51'}
  Pattern 249: Quality=0.4155, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'53'}
  Pattern 250: Quality=0.4154, ROC-AUC=0.9520, Support=180, Pattern={'24'}{'53'}
  Pattern 251: Quality=0.4131, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'29'}{'53'}
  Pattern 252: Quality=0.4127, ROC-AUC=0.8295, Support=35, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'54'}{'54'}{'53'}{'54'}{'53'}
  Pattern 253: Quality=0.4123, ROC-AUC=0.8654, Support=56, Pattern={'19'}{'29'}{'52'}{'51'}{'51'}{'52'}{'51'}{'54'}{'53'}{'53'}
  Pattern 254: Quality=0.4119, ROC-AUC=0.8915, Support=103, Pattern={'18'}{'19'}{'23'}{'29'}{'52'}{'52'}{'52'}
  Pattern 255: Quality=0.4117, ROC-AUC=0.9524, Support=123, Pattern={'46'}{'54'}
  Pattern 256: Quality=0.4117, ROC-AUC=0.8743, Support=45, Pattern={'23'}{'29'}{'47'}{'46'}{'52'}{'52'}{'54'}
  Pattern 257: Quality=0.4107, ROC-AUC=0.9542, Support=187, Pattern={'52'}{'52'}
  Pattern 258: Quality=0.4106, ROC-AUC=0.9530, Support=124, Pattern={'46'}{'52'}
  Pattern 259: Quality=0.4106, ROC-AUC=0.8304, Support=46, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 260: Quality=0.4104, ROC-AUC=0.9286, Support=142, Pattern={'51'}{'51'}{'52'}
  Pattern 261: Quality=0.4100, ROC-AUC=0.8880, Support=85, Pattern={'23'}{'29'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 262: Quality=0.4097, ROC-AUC=0.8429, Support=39, Pattern={'8'}{'24'}{'25'}{'24'}{'29'}{'52'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'54'}
  Pattern 263: Quality=0.4095, ROC-AUC=0.9549, Support=189, Pattern={'51'}{'54'}
  Pattern 264: Quality=0.4083, ROC-AUC=0.9555, Support=191, Pattern={'52'}{'51'}
  Pattern 265: Quality=0.4078, ROC-AUC=0.9558, Support=192, Pattern={'51'}{'52'}
  Pattern 266: Quality=0.4047, ROC-AUC=0.8381, Support=47, Pattern={'1'}{'8'}{'16'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 267: Quality=0.4044, ROC-AUC=0.8806, Support=73, Pattern={'1'}{'8'}{'46'}{'51'}{'52'}{'51'}{'52'}{'53'}
  Pattern 268: Quality=0.4041, ROC-AUC=0.8810, Support=74, Pattern={'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'53'}{'54'}
  Pattern 269: Quality=0.4035, ROC-AUC=0.8361, Support=49, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 270: Quality=0.4031, ROC-AUC=0.8462, Support=50, Pattern={'1'}{'8'}{'18'}{'17'}{'19'}{'23'}{'52'}{'51'}{'52'}{'51'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 271: Quality=0.4031, ROC-AUC=0.8462, Support=50, Pattern={'18'}{'17'}{'19'}{'23'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'54'}
  Pattern 272: Quality=0.4031, ROC-AUC=0.8056, Support=20, Pattern={'1'}{'8'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'46'}{'47'}{'46'}{'49'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 273: Quality=0.4027, ROC-AUC=0.9299, Support=142, Pattern={'52'}{'51'}{'51'}
  Pattern 274: Quality=0.4020, ROC-AUC=0.9296, Support=135, Pattern={'19'}{'23'}{'29'}
  Pattern 275: Quality=0.4018, ROC-AUC=0.8877, Support=102, Pattern={'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 276: Quality=0.4018, ROC-AUC=0.8894, Support=64, Pattern={'13'}{'19'}{'23'}{'27'}{'29'}{'53'}
  Pattern 277: Quality=0.3999, ROC-AUC=0.9162, Support=121, Pattern={'24'}{'29'}{'51'}{'53'}
  Pattern 278: Quality=0.3999, ROC-AUC=0.9162, Support=121, Pattern={'29'}{'51'}{'54'}{'54'}
  Pattern 279: Quality=0.3999, ROC-AUC=0.9162, Support=121, Pattern={'19'}{'29'}{'51'}{'53'}
  Pattern 280: Quality=0.3968, ROC-AUC=0.9173, Support=128, Pattern={'51'}{'52'}{'51'}{'53'}
  Pattern 281: Quality=0.3965, ROC-AUC=0.8936, Support=106, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}{'52'}{'54'}
  Pattern 282: Quality=0.3957, ROC-AUC=0.8936, Support=77, Pattern={'18'}{'18'}{'24'}{'46'}{'51'}{'53'}
  Pattern 283: Quality=0.3931, ROC-AUC=0.9172, Support=122, Pattern={'29'}{'52'}{'52'}{'54'}
  Pattern 284: Quality=0.3924, ROC-AUC=0.8705, Support=44, Pattern={'18'}{'29'}{'46'}{'47'}{'46'}{'52'}{'54'}{'53'}
  Pattern 285: Quality=0.3915, ROC-AUC=0.8295, Support=35, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}{'53'}
  Pattern 286: Quality=0.3909, ROC-AUC=0.8970, Support=90, Pattern={'19'}{'29'}{'52'}{'53'}{'54'}{'54'}
  Pattern 287: Quality=0.3906, ROC-AUC=0.9325, Support=148, Pattern={'51'}{'52'}{'51'}
  Pattern 288: Quality=0.3896, ROC-AUC=0.9177, Support=121, Pattern={'23'}{'24'}{'52'}{'52'}
  Pattern 289: Quality=0.3891, ROC-AUC=0.8844, Support=99, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 290: Quality=0.3891, ROC-AUC=0.8844, Support=99, Pattern={'18'}{'23'}{'29'}{'52'}{'51'}{'51'}{'52'}{'53'}{'54'}
  Pattern 291: Quality=0.3890, ROC-AUC=0.9178, Support=122, Pattern={'23'}{'29'}{'52'}{'53'}
  Pattern 292: Quality=0.3871, ROC-AUC=0.8703, Support=71, Pattern={'8'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 293: Quality=0.3869, ROC-AUC=0.8978, Support=92, Pattern={'51'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 294: Quality=0.3866, ROC-AUC=0.9059, Support=49, Pattern={'47'}{'46'}{'51'}{'54'}
  Pattern 295: Quality=0.3863, ROC-AUC=0.9234, Support=52, Pattern={'46'}{'47'}{'46'}
  Pattern 296: Quality=0.3856, ROC-AUC=0.8210, Support=27, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 297: Quality=0.3853, ROC-AUC=0.8636, Support=75, Pattern={'18'}{'17'}{'19'}{'23'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'54'}
  Pattern 298: Quality=0.3840, ROC-AUC=0.8241, Support=24, Pattern={'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 299: Quality=0.3831, ROC-AUC=0.9187, Support=122, Pattern={'19'}{'23'}{'52'}{'51'}
  Pattern 300: Quality=0.3831, ROC-AUC=0.9187, Support=122, Pattern={'23'}{'29'}{'51'}{'54'}
  Pattern 301: Quality=0.3831, ROC-AUC=0.9187, Support=122, Pattern={'23'}{'29'}{'52'}{'51'}
  Pattern 302: Quality=0.3823, ROC-AUC=0.8651, Support=64, Pattern={'13'}{'18'}{'18'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 303: Quality=0.3819, ROC-AUC=0.8786, Support=73, Pattern={'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'51'}{'53'}{'54'}
  Pattern 304: Quality=0.3809, ROC-AUC=0.8746, Support=72, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'46'}{'51'}{'54'}{'53'}{'54'}
  Pattern 305: Quality=0.3800, ROC-AUC=0.9058, Support=91, Pattern={'25'}{'29'}{'52'}{'51'}{'52'}
  Pattern 306: Quality=0.3799, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'53'}{'54'}
  Pattern 307: Quality=0.3798, ROC-AUC=0.9195, Support=125, Pattern={'19'}{'29'}{'52'}{'53'}
  Pattern 308: Quality=0.3790, ROC-AUC=0.9192, Support=121, Pattern={'13'}{'17'}{'23'}{'52'}
  Pattern 309: Quality=0.3778, ROC-AUC=0.8488, Support=69, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 310: Quality=0.3775, ROC-AUC=0.8805, Support=78, Pattern={'1'}{'19'}{'23'}{'24'}{'25'}{'29'}{'51'}{'51'}{'53'}
  Pattern 311: Quality=0.3770, ROC-AUC=0.8845, Support=59, Pattern={'18'}{'23'}{'29'}{'54'}{'54'}{'53'}{'53'}
  Pattern 312: Quality=0.3768, ROC-AUC=0.9197, Support=123, Pattern={'18'}{'23'}{'29'}{'51'}
  Pattern 313: Quality=0.3768, ROC-AUC=0.9197, Support=123, Pattern={'19'}{'23'}{'29'}{'51'}
  Pattern 314: Quality=0.3743, ROC-AUC=0.8822, Support=99, Pattern={'8'}{'19'}{'24'}{'29'}{'52'}{'51'}{'51'}{'52'}{'53'}{'54'}
  Pattern 315: Quality=0.3742, ROC-AUC=0.9203, Support=125, Pattern={'17'}{'29'}{'51'}{'54'}
  Pattern 316: Quality=0.3742, ROC-AUC=0.9203, Support=125, Pattern={'24'}{'29'}{'52'}{'51'}
  Pattern 317: Quality=0.3742, ROC-AUC=0.9203, Support=125, Pattern={'17'}{'29'}{'52'}{'51'}
  Pattern 318: Quality=0.3741, ROC-AUC=0.8866, Support=103, Pattern={'1'}{'18'}{'19'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 319: Quality=0.3733, ROC-AUC=0.8431, Support=38, Pattern={'1'}{'17'}{'18'}{'24'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 320: Quality=0.3695, ROC-AUC=0.9079, Support=95, Pattern={'19'}{'23'}{'29'}{'53'}{'53'}
  Pattern 321: Quality=0.3672, ROC-AUC=0.8780, Support=79, Pattern={'13'}{'18'}{'19'}{'23'}{'29'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 322: Quality=0.3672, ROC-AUC=0.8795, Support=98, Pattern={'8'}{'18'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'51'}{'52'}{'53'}
  Pattern 323: Quality=0.3648, ROC-AUC=0.9218, Support=126, Pattern={'23'}{'24'}{'29'}{'52'}
  Pattern 324: Quality=0.3631, ROC-AUC=0.8831, Support=98, Pattern={'13'}{'17'}{'19'}{'23'}{'29'}{'51'}{'51'}{'54'}{'53'}{'54'}
  Pattern 325: Quality=0.3603, ROC-AUC=0.8946, Support=63, Pattern={'1'}{'24'}{'25'}{'46'}{'53'}{'54'}
  Pattern 326: Quality=0.3590, ROC-AUC=0.8636, Support=75, Pattern={'1'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 327: Quality=0.3590, ROC-AUC=0.8636, Support=75, Pattern={'1'}{'8'}{'18'}{'17'}{'19'}{'23'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 328: Quality=0.3572, ROC-AUC=0.9098, Support=97, Pattern={'19'}{'29'}{'53'}{'53'}{'54'}
  Pattern 329: Quality=0.3546, ROC-AUC=0.8884, Support=82, Pattern={'1'}{'19'}{'23'}{'24'}{'25'}{'29'}{'51'}{'51'}
  Pattern 330: Quality=0.3535, ROC-AUC=0.8886, Support=103, Pattern={'19'}{'23'}{'24'}{'29'}{'51'}{'51'}{'52'}{'54'}{'53'}
  Pattern 331: Quality=0.3530, ROC-AUC=0.9348, Support=66, Pattern={'29'}{'46'}{'49'}
  Pattern 332: Quality=0.3523, ROC-AUC=0.9242, Support=130, Pattern={'17'}{'19'}{'29'}{'52'}
  Pattern 333: Quality=0.3523, ROC-AUC=0.8715, Support=74, Pattern={'18'}{'18'}{'19'}{'25'}{'24'}{'29'}{'52'}{'51'}{'51'}{'52'}{'53'}{'54'}
  Pattern 334: Quality=0.3515, ROC-AUC=0.9386, Support=104, Pattern={'46'}{'51'}{'54'}
  Pattern 335: Quality=0.3507, ROC-AUC=0.8936, Support=106, Pattern={'8'}{'18'}{'23'}{'29'}{'51'}{'52'}{'51'}{'54'}
  Pattern 336: Quality=0.3496, ROC-AUC=0.8650, Support=70, Pattern={'13'}{'16'}{'18'}{'18'}{'19'}{'25'}{'24'}{'29'}{'52'}{'51'}{'51'}{'52'}{'53'}{'54'}
  Pattern 337: Quality=0.3493, ROC-AUC=0.9206, Support=90, Pattern={'24'}{'46'}{'52'}{'54'}
  Pattern 338: Quality=0.3483, ROC-AUC=0.9421, Support=157, Pattern={'52'}{'52'}{'53'}
  Pattern 339: Quality=0.3483, ROC-AUC=0.9395, Support=105, Pattern={'46'}{'52'}{'51'}
  Pattern 340: Quality=0.3483, ROC-AUC=0.8817, Support=43, Pattern={'13'}{'17'}{'47'}{'46'}{'51'}{'54'}{'54'}
  Pattern 341: Quality=0.3467, ROC-AUC=0.8381, Support=47, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 342: Quality=0.3447, ROC-AUC=0.8603, Support=74, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 343: Quality=0.3441, ROC-AUC=0.9143, Support=118, Pattern={'23'}{'29'}{'52'}{'51'}{'53'}
  Pattern 344: Quality=0.3440, ROC-AUC=0.8697, Support=41, Pattern={'8'}{'16'}{'23'}{'24'}{'29'}{'46'}{'47'}{'46'}{'52'}
  Pattern 345: Quality=0.3435, ROC-AUC=0.9434, Support=158, Pattern={'24'}{'52'}{'52'}
  Pattern 346: Quality=0.3434, ROC-AUC=0.8905, Support=86, Pattern={'17'}{'19'}{'23'}{'24'}{'51'}{'53'}{'54'}{'53'}
  Pattern 347: Quality=0.3420, ROC-AUC=0.9152, Support=124, Pattern={'52'}{'52'}{'51'}{'54'}{'53'}
  Pattern 348: Quality=0.3411, ROC-AUC=0.9223, Support=91, Pattern={'46'}{'51'}{'53'}{'54'}
  Pattern 349: Quality=0.3408, ROC-AUC=0.9123, Support=40, Pattern={'24'}{'40'}{'45'}{'52'}
  Pattern 350: Quality=0.3399, ROC-AUC=0.8835, Support=59, Pattern={'8'}{'17'}{'24'}{'24'}{'46'}{'52'}{'54'}{'53'}
  Pattern 351: Quality=0.3399, ROC-AUC=0.8838, Support=45, Pattern={'24'}{'46'}{'47'}{'46'}{'51'}{'52'}{'54'}
  Pattern 352: Quality=0.3398, ROC-AUC=0.9445, Support=162, Pattern={'51'}{'52'}{'53'}
  Pattern 353: Quality=0.3398, ROC-AUC=0.8970, Support=90, Pattern={'8'}{'24'}{'29'}{'52'}{'54'}{'53'}{'53'}
  Pattern 354: Quality=0.3396, ROC-AUC=0.9306, Support=22, Pattern={'47'}{'47'}{'53'}
  Pattern 355: Quality=0.3396, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'54'}{'53'}
  Pattern 356: Quality=0.3396, ROC-AUC=0.9263, Support=131, Pattern={'19'}{'23'}{'29'}{'53'}
  Pattern 357: Quality=0.3393, ROC-AUC=0.9104, Support=84, Pattern={'24'}{'46'}{'51'}{'52'}{'54'}
  Pattern 358: Quality=0.3366, ROC-AUC=0.9155, Support=119, Pattern={'23'}{'24'}{'52'}{'52'}{'54'}
  Pattern 359: Quality=0.3366, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'51'}{'53'}{'54'}
  Pattern 360: Quality=0.3366, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'29'}{'51'}{'53'}
  Pattern 361: Quality=0.3357, ROC-AUC=0.9458, Support=163, Pattern={'24'}{'51'}{'54'}
  Pattern 362: Quality=0.3354, ROC-AUC=0.9459, Support=165, Pattern={'8'}{'51'}{'53'}
  Pattern 363: Quality=0.3340, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'54'}{'53'}
  Pattern 364: Quality=0.3340, ROC-AUC=0.9463, Support=166, Pattern={'17'}{'51'}{'53'}
  Pattern 365: Quality=0.3340, ROC-AUC=0.9463, Support=166, Pattern={'18'}{'51'}{'53'}
  Pattern 366: Quality=0.3339, ROC-AUC=0.9114, Support=85, Pattern={'1'}{'24'}{'46'}{'53'}{'54'}
  Pattern 367: Quality=0.3339, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'29'}{'53'}{'54'}
  Pattern 368: Quality=0.3330, ROC-AUC=0.9162, Support=121, Pattern={'19'}{'29'}{'51'}{'53'}{'54'}
  Pattern 369: Quality=0.3325, ROC-AUC=0.9276, Support=132, Pattern={'1'}{'16'}{'18'}{'19'}
  Pattern 370: Quality=0.3318, ROC-AUC=0.8869, Support=102, Pattern={'8'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'51'}{'52'}{'53'}
  Pattern 371: Quality=0.3312, ROC-AUC=0.8845, Support=59, Pattern={'1'}{'23'}{'29'}{'53'}{'54'}{'53'}{'54'}{'53'}
  Pattern 372: Quality=0.3309, ROC-AUC=0.8500, Support=26, Pattern={'13'}{'14'}{'17'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'52'}{'53'}
  Pattern 373: Quality=0.3292, ROC-AUC=0.8867, Support=100, Pattern={'1'}{'16'}{'18'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'54'}
  Pattern 374: Quality=0.3261, ROC-AUC=0.9172, Support=122, Pattern={'8'}{'29'}{'51'}{'52'}{'54'}
  Pattern 375: Quality=0.3251, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'53'}{'54'}
  Pattern 376: Quality=0.3248, ROC-AUC=0.9171, Support=119, Pattern={'13'}{'18'}{'23'}{'52'}{'54'}
  Pattern 377: Quality=0.3242, ROC-AUC=0.9258, Support=94, Pattern={'46'}{'52'}{'53'}{'54'}
  Pattern 378: Quality=0.3228, ROC-AUC=0.8880, Support=85, Pattern={'1'}{'17'}{'19'}{'23'}{'52'}{'52'}{'53'}{'54'}{'53'}
  Pattern 379: Quality=0.3221, ROC-AUC=0.9178, Support=122, Pattern={'19'}{'23'}{'29'}{'52'}{'53'}
  Pattern 380: Quality=0.3221, ROC-AUC=0.9178, Support=122, Pattern={'23'}{'29'}{'52'}{'54'}{'54'}
  Pattern 381: Quality=0.3221, ROC-AUC=0.9178, Support=122, Pattern={'23'}{'29'}{'52'}{'53'}{'54'}
  Pattern 382: Quality=0.3215, ROC-AUC=0.8841, Support=100, Pattern={'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 383: Quality=0.3207, ROC-AUC=0.8742, Support=92, Pattern={'16'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 384: Quality=0.3207, ROC-AUC=0.8742, Support=92, Pattern={'8'}{'16'}{'18'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 385: Quality=0.3199, ROC-AUC=0.9499, Support=119, Pattern={'46'}{'52'}{'54'}
  Pattern 386: Quality=0.3194, ROC-AUC=0.9517, Support=179, Pattern={'24'}{'52'}{'54'}
  Pattern 387: Quality=0.3185, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'53'}{'54'}
  Pattern 388: Quality=0.3185, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'54'}{'53'}
  Pattern 389: Quality=0.3182, ROC-AUC=0.9306, Support=138, Pattern={'1'}{'18'}{'19'}{'29'}
  Pattern 390: Quality=0.3177, ROC-AUC=0.9524, Support=181, Pattern={'8'}{'24'}{'52'}
  Pattern 391: Quality=0.3166, ROC-AUC=0.8844, Support=99, Pattern={'17'}{'19'}{'23'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 392: Quality=0.3159, ROC-AUC=0.9532, Support=184, Pattern={'52'}{'51'}{'54'}
  Pattern 393: Quality=0.3151, ROC-AUC=0.8767, Support=37, Pattern={'29'}{'46'}{'49'}{'51'}{'52'}{'51'}{'51'}{'54'}
  Pattern 394: Quality=0.3151, ROC-AUC=0.9536, Support=185, Pattern={'51'}{'52'}{'54'}
  Pattern 395: Quality=0.3144, ROC-AUC=0.8811, Support=97, Pattern={'16'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 396: Quality=0.3143, ROC-AUC=0.9234, Support=61, Pattern={'29'}{'46'}{'49'}{'51'}
  Pattern 397: Quality=0.3137, ROC-AUC=0.9530, Support=124, Pattern={'18'}{'46'}{'52'}
  Pattern 398: Quality=0.3137, ROC-AUC=0.9530, Support=124, Pattern={'17'}{'46'}{'52'}
  Pattern 399: Quality=0.3133, ROC-AUC=0.9193, Support=124, Pattern={'24'}{'29'}{'52'}{'51'}{'54'}
  Pattern 400: Quality=0.3129, ROC-AUC=0.9195, Support=125, Pattern={'19'}{'29'}{'52'}{'54'}{'53'}
  Pattern 401: Quality=0.3129, ROC-AUC=0.9195, Support=125, Pattern={'19'}{'29'}{'52'}{'53'}{'54'}
  Pattern 402: Quality=0.3117, ROC-AUC=0.9199, Support=42, Pattern={'18'}{'40'}{'45'}{'53'}
  Pattern 403: Quality=0.3104, ROC-AUC=0.8951, Support=90, Pattern={'24'}{'51'}{'52'}{'51'}{'54'}{'53'}{'53'}{'54'}
  Pattern 404: Quality=0.3104, ROC-AUC=0.8762, Support=76, Pattern={'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 405: Quality=0.3101, ROC-AUC=0.9562, Support=193, Pattern={'17'}{'24'}{'54'}
  Pattern 406: Quality=0.3082, ROC-AUC=0.8824, Support=46, Pattern={'17'}{'19'}{'23'}{'29'}{'47'}{'46'}{'52'}{'54'}
  Pattern 407: Quality=0.3069, ROC-AUC=0.9102, Support=56, Pattern={'46'}{'49'}{'51'}{'51'}{'53'}
  Pattern 408: Quality=0.3063, ROC-AUC=0.8380, Support=35, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'27'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 409: Quality=0.3050, ROC-AUC=0.8795, Support=98, Pattern={'8'}{'18'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 410: Quality=0.3035, ROC-AUC=0.9209, Support=125, Pattern={'18'}{'17'}{'23'}{'52'}{'54'}
  Pattern 411: Quality=0.3024, ROC-AUC=0.9064, Support=79, Pattern={'1'}{'16'}{'24'}{'46'}{'53'}{'54'}
  Pattern 412: Quality=0.3021, ROC-AUC=0.9119, Support=116, Pattern={'23'}{'29'}{'52'}{'51'}{'52'}{'53'}
  Pattern 413: Quality=0.3013, ROC-AUC=0.8702, Support=72, Pattern={'16'}{'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 414: Quality=0.3013, ROC-AUC=0.8910, Support=88, Pattern={'24'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 415: Quality=0.2983, ROC-AUC=0.8858, Support=66, Pattern={'1'}{'24'}{'24'}{'52'}{'52'}{'51'}{'54'}{'53'}{'53'}
  Pattern 416: Quality=0.2971, ROC-AUC=0.8869, Support=102, Pattern={'8'}{'17'}{'23'}{'24'}{'29'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 417: Quality=0.2939, ROC-AUC=0.9131, Support=117, Pattern={'23'}{'29'}{'51'}{'52'}{'54'}{'53'}
  Pattern 418: Quality=0.2939, ROC-AUC=0.9131, Support=117, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}{'53'}
  Pattern 419: Quality=0.2926, ROC-AUC=0.8333, Support=31, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'18'}{'17'}{'17'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'53'}{'54'}{'53'}{'54'}{'54'}
  Pattern 420: Quality=0.2912, ROC-AUC=0.9189, Support=89, Pattern={'46'}{'51'}{'52'}{'53'}{'54'}
  Pattern 421: Quality=0.2879, ROC-AUC=0.8877, Support=102, Pattern={'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 422: Quality=0.2826, ROC-AUC=0.9079, Support=116, Pattern={'17'}{'24'}{'52'}{'51'}{'52'}{'51'}{'53'}
  Pattern 423: Quality=0.2822, ROC-AUC=0.9355, Support=97, Pattern={'13'}{'46'}{'51'}{'54'}
  Pattern 424: Quality=0.2806, ROC-AUC=0.8910, Support=59, Pattern={'1'}{'16'}{'24'}{'25'}{'24'}{'46'}{'53'}{'54'}
  Pattern 425: Quality=0.2795, ROC-AUC=0.9365, Support=102, Pattern={'46'}{'51'}{'52'}{'54'}
  Pattern 426: Quality=0.2787, ROC-AUC=0.8404, Support=46, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 427: Quality=0.2786, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'29'}{'52'}{'52'}{'54'}
  Pattern 428: Quality=0.2776, ROC-AUC=0.8766, Support=57, Pattern={'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}{'54'}{'53'}{'53'}
  Pattern 429: Quality=0.2750, ROC-AUC=0.9152, Support=51, Pattern={'17'}{'47'}{'46'}{'52'}{'54'}
  Pattern 430: Quality=0.2739, ROC-AUC=0.9348, Support=66, Pattern={'29'}{'46'}{'49'}{'54'}
  Pattern 431: Quality=0.2739, ROC-AUC=0.9348, Support=66, Pattern={'19'}{'29'}{'46'}{'49'}
  Pattern 432: Quality=0.2727, ROC-AUC=0.9263, Support=131, Pattern={'18'}{'17'}{'23'}{'53'}{'54'}
  Pattern 433: Quality=0.2727, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'54'}{'53'}{'54'}
  Pattern 434: Quality=0.2715, ROC-AUC=0.9166, Support=120, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}{'54'}
  Pattern 435: Quality=0.2714, ROC-AUC=0.9094, Support=117, Pattern={'16'}{'17'}{'18'}{'52'}{'51'}{'51'}{'53'}
  Pattern 436: Quality=0.2703, ROC-AUC=0.9000, Support=91, Pattern={'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'53'}{'54'}
  Pattern 437: Quality=0.2693, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'53'}{'54'}{'53'}
  Pattern 438: Quality=0.2693, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'54'}{'53'}{'53'}
  Pattern 439: Quality=0.2679, ROC-AUC=0.9279, Support=141, Pattern={'17'}{'18'}{'51'}{'52'}{'52'}
  Pattern 440: Quality=0.2674, ROC-AUC=0.8553, Support=23, Pattern={'15'}{'18'}{'19'}{'29'}{'46'}{'47'}{'52'}{'52'}{'51'}{'51'}{'53'}
  Pattern 441: Quality=0.2668, ROC-AUC=0.9171, Support=119, Pattern={'13'}{'18'}{'17'}{'23'}{'52'}{'54'}
  Pattern 442: Quality=0.2668, ROC-AUC=0.9171, Support=119, Pattern={'8'}{'16'}{'23'}{'24'}{'29'}{'52'}
  Pattern 443: Quality=0.2647, ROC-AUC=0.9177, Support=121, Pattern={'8'}{'18'}{'23'}{'29'}{'51'}{'54'}
  Pattern 444: Quality=0.2642, ROC-AUC=0.8905, Support=86, Pattern={'1'}{'8'}{'18'}{'17'}{'19'}{'23'}{'51'}{'53'}{'53'}{'54'}
  Pattern 445: Quality=0.2642, ROC-AUC=0.8905, Support=86, Pattern={'8'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}{'53'}
  Pattern 446: Quality=0.2642, ROC-AUC=0.8905, Support=86, Pattern={'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}{'54'}{'53'}
  Pattern 447: Quality=0.2641, ROC-AUC=0.9178, Support=122, Pattern={'19'}{'23'}{'29'}{'52'}{'54'}{'53'}
  Pattern 448: Quality=0.2640, ROC-AUC=0.8807, Support=64, Pattern={'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 449: Quality=0.2622, ROC-AUC=0.9441, Support=161, Pattern={'52'}{'51'}{'54'}{'53'}
  Pattern 450: Quality=0.2619, ROC-AUC=0.9387, Support=67, Pattern={'24'}{'46'}{'49'}{'51'}
  Pattern 451: Quality=0.2616, ROC-AUC=0.9155, Support=41, Pattern={'16'}{'23'}{'40'}{'45'}{'53'}
  Pattern 452: Quality=0.2614, ROC-AUC=0.8551, Support=38, Pattern={'8'}{'16'}{'15'}{'18'}{'18'}{'17'}{'46'}{'49'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 453: Quality=0.2611, ROC-AUC=0.8784, Support=77, Pattern={'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'29'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 454: Quality=0.2605, ROC-AUC=0.8242, Support=20, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'27'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 455: Quality=0.2603, ROC-AUC=0.9079, Support=95, Pattern={'18'}{'17'}{'23'}{'54'}{'53'}{'53'}{'54'}
  Pattern 456: Quality=0.2603, ROC-AUC=0.9079, Support=95, Pattern={'8'}{'18'}{'19'}{'23'}{'29'}{'53'}{'53'}
  Pattern 457: Quality=0.2603, ROC-AUC=0.9079, Support=95, Pattern={'19'}{'23'}{'29'}{'53'}{'54'}{'53'}{'54'}
  Pattern 458: Quality=0.2599, ROC-AUC=0.9009, Support=89, Pattern={'13'}{'18'}{'23'}{'24'}{'29'}{'54'}{'54'}{'53'}
  Pattern 459: Quality=0.2598, ROC-AUC=0.9288, Support=134, Pattern={'18'}{'23'}{'24'}{'29'}{'54'}
  Pattern 460: Quality=0.2581, ROC-AUC=0.9187, Support=122, Pattern={'17'}{'19'}{'23'}{'29'}{'52'}{'51'}
  Pattern 461: Quality=0.2574, ROC-AUC=0.9212, Support=61, Pattern={'23'}{'29'}{'46'}{'49'}{'53'}
  Pattern 462: Quality=0.2565, ROC-AUC=0.9458, Support=163, Pattern={'18'}{'24'}{'51'}{'52'}
  Pattern 463: Quality=0.2529, ROC-AUC=0.8583, Support=50, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'54'}{'53'}{'54'}
  Pattern 464: Quality=0.2503, ROC-AUC=0.8880, Support=85, Pattern={'18'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}
  Pattern 465: Quality=0.2490, ROC-AUC=0.9023, Support=89, Pattern={'19'}{'23'}{'25'}{'24'}{'29'}{'52'}{'53'}{'54'}
  Pattern 466: Quality=0.2486, ROC-AUC=0.8978, Support=92, Pattern={'1'}{'18'}{'51'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 467: Quality=0.2481, ROC-AUC=0.9098, Support=97, Pattern={'17'}{'19'}{'24'}{'29'}{'54'}{'53'}{'53'}
  Pattern 468: Quality=0.2474, ROC-AUC=0.9234, Support=61, Pattern={'24'}{'29'}{'46'}{'49'}{'51'}
  Pattern 469: Quality=0.2471, ROC-AUC=0.9208, Support=127, Pattern={'18'}{'18'}{'19'}{'29'}{'52'}{'54'}
  Pattern 470: Quality=0.2461, ROC-AUC=0.8742, Support=92, Pattern={'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 471: Quality=0.2459, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'54'}{'53'}{'54'}
  Pattern 472: Quality=0.2459, ROC-AUC=0.9485, Support=140, Pattern={'54'}{'53'}{'54'}{'53'}
  Pattern 473: Quality=0.2454, ROC-AUC=0.8766, Support=57, Pattern={'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}{'54'}{'53'}{'54'}{'53'}
  Pattern 474: Quality=0.2437, ROC-AUC=0.8133, Support=20, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 475: Quality=0.2430, ROC-AUC=0.9505, Support=174, Pattern={'8'}{'16'}{'24'}{'52'}
  Pattern 476: Quality=0.2428, ROC-AUC=0.9131, Support=117, Pattern={'8'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}
  Pattern 477: Quality=0.2423, ROC-AUC=0.8780, Support=79, Pattern={'8'}{'13'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 478: Quality=0.2421, ROC-AUC=0.9492, Support=118, Pattern={'1'}{'46'}{'52'}{'54'}
  Pattern 479: Quality=0.2407, ROC-AUC=0.9499, Support=119, Pattern={'18'}{'46'}{'52'}{'54'}
  Pattern 480: Quality=0.2398, ROC-AUC=0.8882, Support=51, Pattern={'23'}{'29'}{'46'}{'49'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 481: Quality=0.2398, ROC-AUC=0.9519, Support=180, Pattern={'52'}{'51'}{'52'}{'54'}
  Pattern 482: Quality=0.2394, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'54'}{'53'}{'54'}
  Pattern 483: Quality=0.2371, ROC-AUC=0.8333, Support=31, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 484: Quality=0.2360, ROC-AUC=0.9536, Support=185, Pattern={'17'}{'51'}{'52'}{'54'}
  Pattern 485: Quality=0.2360, ROC-AUC=0.9536, Support=185, Pattern={'18'}{'51'}{'52'}{'54'}
  Pattern 486: Quality=0.2350, ROC-AUC=0.9143, Support=118, Pattern={'8'}{'17'}{'23'}{'29'}{'51'}{'54'}{'54'}
  Pattern 487: Quality=0.2344, ROC-AUC=0.8579, Support=54, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 488: Quality=0.2336, ROC-AUC=0.8603, Support=41, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 489: Quality=0.2331, ROC-AUC=0.9034, Support=54, Pattern={'29'}{'46'}{'49'}{'51'}{'52'}{'51'}{'54'}
  Pattern 490: Quality=0.2329, ROC-AUC=0.9152, Support=124, Pattern={'18'}{'17'}{'52'}{'51'}{'51'}{'54'}{'53'}
  Pattern 491: Quality=0.2322, ROC-AUC=0.9555, Support=191, Pattern={'17'}{'18'}{'51'}{'52'}
  Pattern 492: Quality=0.2320, ROC-AUC=0.9186, Support=85, Pattern={'13'}{'17'}{'46'}{'51'}{'54'}{'54'}
  Pattern 493: Quality=0.2317, ROC-AUC=0.9558, Support=192, Pattern={'18'}{'17'}{'51'}{'52'}
  Pattern 494: Quality=0.2315, ROC-AUC=0.8650, Support=70, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 495: Quality=0.2310, ROC-AUC=0.9151, Support=120, Pattern={'18'}{'19'}{'29'}{'52'}{'51'}{'54'}{'54'}
  Pattern 496: Quality=0.2310, ROC-AUC=0.9562, Support=195, Pattern={'17'}{'18'}{'53'}{'54'}
  Pattern 497: Quality=0.2288, ROC-AUC=0.8583, Support=29, Pattern={'18'}{'18'}{'23'}{'29'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'51'}{'54'}{'53'}
  Pattern 498: Quality=0.2260, ROC-AUC=0.8762, Support=76, Pattern={'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'51'}{'54'}{'53'}{'54'}
  Pattern 499: Quality=0.2259, ROC-AUC=0.8556, Support=37, Pattern={'8'}{'14'}{'17'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 500: Quality=0.2252, ROC-AUC=0.9332, Support=99, Pattern={'46'}{'52'}{'51'}{'52'}{'54'}
  Pattern 501: Quality=0.2248, ROC-AUC=0.9114, Support=85, Pattern={'1'}{'17'}{'46'}{'52'}{'52'}{'54'}{'53'}
  Pattern 502: Quality=0.2239, ROC-AUC=0.9162, Support=121, Pattern={'18'}{'19'}{'29'}{'51'}{'54'}{'53'}{'54'}
  Pattern 503: Quality=0.2233, ROC-AUC=0.8817, Support=43, Pattern={'13'}{'16'}{'18'}{'17'}{'47'}{'46'}{'51'}{'52'}{'54'}{'54'}
  Pattern 504: Quality=0.2218, ROC-AUC=0.9257, Support=138, Pattern={'18'}{'17'}{'51'}{'51'}{'52'}{'54'}
  Pattern 505: Quality=0.2208, ROC-AUC=0.9231, Support=106, Pattern={'24'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 506: Quality=0.2203, ROC-AUC=0.9166, Support=120, Pattern={'8'}{'18'}{'23'}{'29'}{'52'}{'51'}{'54'}
  Pattern 507: Quality=0.2203, ROC-AUC=0.9166, Support=120, Pattern={'1'}{'8'}{'17'}{'23'}{'24'}{'52'}{'52'}
  Pattern 508: Quality=0.2194, ROC-AUC=0.8631, Support=38, Pattern={'8'}{'18'}{'17'}{'18'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 509: Quality=0.2182, ROC-AUC=0.9379, Support=149, Pattern={'18'}{'18'}{'24'}{'51'}{'53'}
  Pattern 510: Quality=0.2179, ROC-AUC=0.9379, Support=148, Pattern={'18'}{'24'}{'51'}{'52'}{'53'}
  Pattern 511: Quality=0.2159, ROC-AUC=0.9123, Support=40, Pattern={'18'}{'19'}{'23'}{'40'}{'45'}{'51'}
  Pattern 512: Quality=0.2147, ROC-AUC=0.9263, Support=131, Pattern={'18'}{'17'}{'19'}{'23'}{'29'}{'53'}
  Pattern 513: Quality=0.2146, ROC-AUC=0.9079, Support=95, Pattern={'8'}{'18'}{'19'}{'23'}{'29'}{'54'}{'53'}{'53'}
  Pattern 514: Quality=0.2146, ROC-AUC=0.9079, Support=95, Pattern={'17'}{'19'}{'23'}{'24'}{'29'}{'53'}{'53'}{'54'}
  Pattern 515: Quality=0.2135, ROC-AUC=0.9177, Support=121, Pattern={'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}
  Pattern 516: Quality=0.2133, ROC-AUC=0.9267, Support=133, Pattern={'1'}{'18'}{'19'}{'29'}{'54'}{'54'}
  Pattern 517: Quality=0.2122, ROC-AUC=0.8571, Support=37, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'17'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 518: Quality=0.2090, ROC-AUC=0.8333, Support=20, Pattern={'1'}{'8'}{'17'}{'18'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 519: Quality=0.2090, ROC-AUC=0.9275, Support=134, Pattern={'17'}{'19'}{'29'}{'54'}{'53'}{'54'}
  Pattern 520: Quality=0.2059, ROC-AUC=0.9099, Support=61, Pattern={'14'}{'19'}{'23'}{'46'}{'52'}{'52'}{'54'}
  Pattern 521: Quality=0.2052, ROC-AUC=0.9119, Support=116, Pattern={'18'}{'23'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 522: Quality=0.2052, ROC-AUC=0.9119, Support=116, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 523: Quality=0.2052, ROC-AUC=0.9119, Support=116, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 524: Quality=0.2026, ROC-AUC=0.8742, Support=92, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 525: Quality=0.2023, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 526: Quality=0.2022, ROC-AUC=0.9421, Support=157, Pattern={'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 527: Quality=0.1999, ROC-AUC=0.8984, Support=88, Pattern={'18'}{'17'}{'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 528: Quality=0.1978, ROC-AUC=0.9077, Support=117, Pattern={'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 529: Quality=0.1956, ROC-AUC=0.9211, Support=129, Pattern={'18'}{'17'}{'24'}{'52'}{'51'}{'52'}{'51'}
  Pattern 530: Quality=0.1955, ROC-AUC=0.9017, Support=31, Pattern={'29'}{'40'}{'45'}{'52'}{'53'}{'53'}{'54'}
  Pattern 531: Quality=0.1954, ROC-AUC=0.9079, Support=116, Pattern={'18'}{'17'}{'24'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 532: Quality=0.1954, ROC-AUC=0.8506, Support=36, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'18'}{'17'}{'18'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 533: Quality=0.1953, ROC-AUC=0.9441, Support=161, Pattern={'17'}{'52'}{'51'}{'53'}{'54'}
  Pattern 534: Quality=0.1941, ROC-AUC=0.9444, Support=160, Pattern={'17'}{'24'}{'51'}{'52'}{'54'}
  Pattern 535: Quality=0.1937, ROC-AUC=0.9445, Support=162, Pattern={'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 536: Quality=0.1935, ROC-AUC=0.9306, Support=22, Pattern={'19'}{'47'}{'46'}{'47'}{'51'}
  Pattern 537: Quality=0.1935, ROC-AUC=0.9425, Support=112, Pattern={'8'}{'18'}{'24'}{'27'}{'53'}
  Pattern 538: Quality=0.1920, ROC-AUC=0.8650, Support=70, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 539: Quality=0.1900, ROC-AUC=0.9136, Support=65, Pattern={'14'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 540: Quality=0.1894, ROC-AUC=0.9089, Support=118, Pattern={'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 541: Quality=0.1892, ROC-AUC=0.9143, Support=118, Pattern={'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'54'}
  Pattern 542: Quality=0.1879, ROC-AUC=0.9463, Support=166, Pattern={'18'}{'17'}{'51'}{'54'}{'53'}
  Pattern 543: Quality=0.1879, ROC-AUC=0.8333, Support=31, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 544: Quality=0.1874, ROC-AUC=0.8773, Support=75, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 545: Quality=0.1873, ROC-AUC=0.8764, Support=41, Pattern={'1'}{'18'}{'19'}{'46'}{'49'}{'51'}{'52'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 546: Quality=0.1854, ROC-AUC=0.9074, Support=39, Pattern={'16'}{'23'}{'40'}{'45'}{'52'}{'54'}{'54'}
  Pattern 547: Quality=0.1853, ROC-AUC=0.9151, Support=120, Pattern={'17'}{'19'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 548: Quality=0.1837, ROC-AUC=0.9388, Support=35, Pattern={'15'}{'18'}{'17'}{'40'}{'45'}
  Pattern 549: Quality=0.1834, ROC-AUC=0.8946, Support=46, Pattern={'17'}{'19'}{'23'}{'46'}{'49'}{'51'}{'54'}{'53'}{'53'}
  Pattern 550: Quality=0.1832, ROC-AUC=0.9289, Support=92, Pattern={'24'}{'27'}{'52'}{'51'}{'52'}{'54'}
  Pattern 551: Quality=0.1803, ROC-AUC=0.9480, Support=139, Pattern={'17'}{'54'}{'53'}{'54'}{'53'}
  Pattern 552: Quality=0.1790, ROC-AUC=0.9485, Support=140, Pattern={'18'}{'54'}{'53'}{'53'}{'54'}
  Pattern 553: Quality=0.1789, ROC-AUC=0.8858, Support=84, Pattern={'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 554: Quality=0.1763, ROC-AUC=0.9341, Support=142, Pattern={'8'}{'24'}{'52'}{'51'}{'52'}{'53'}
  Pattern 555: Quality=0.1752, ROC-AUC=0.8506, Support=36, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 556: Quality=0.1752, ROC-AUC=0.9492, Support=118, Pattern={'1'}{'17'}{'46'}{'52'}{'54'}
  Pattern 557: Quality=0.1749, ROC-AUC=0.9272, Support=63, Pattern={'24'}{'29'}{'46'}{'49'}{'52'}{'54'}
  Pattern 558: Quality=0.1731, ROC-AUC=0.9412, Support=20, Pattern={'47'}{'46'}{'47'}{'49'}{'53'}
  Pattern 559: Quality=0.1708, ROC-AUC=0.8840, Support=63, Pattern={'8'}{'13'}{'16'}{'18'}{'19'}{'23'}{'25'}{'24'}{'29'}{'54'}{'53'}{'54'}{'53'}
  Pattern 560: Quality=0.1704, ROC-AUC=0.9137, Support=49, Pattern={'17'}{'23'}{'46'}{'49'}{'54'}{'53'}{'53'}
  Pattern 561: Quality=0.1697, ROC-AUC=0.8551, Support=38, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'49'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 562: Quality=0.1690, ROC-AUC=0.9536, Support=185, Pattern={'18'}{'17'}{'51'}{'52'}{'54'}
  Pattern 563: Quality=0.1687, ROC-AUC=0.9165, Support=59, Pattern={'23'}{'29'}{'46'}{'49'}{'52'}{'51'}{'54'}
  Pattern 564: Quality=0.1686, ROC-AUC=0.9510, Support=84, Pattern={'14'}{'46'}{'52'}{'52'}{'54'}
  Pattern 565: Quality=0.1683, ROC-AUC=0.9539, Support=186, Pattern={'1'}{'17'}{'52'}{'51'}{'52'}
  Pattern 566: Quality=0.1682, ROC-AUC=0.8562, Support=36, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 567: Quality=0.1682, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'17'}{'19'}{'23'}{'29'}{'54'}{'53'}
  Pattern 568: Quality=0.1682, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'18'}{'19'}{'23'}{'29'}{'54'}{'54'}
  Pattern 569: Quality=0.1682, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'17'}{'19'}{'23'}{'54'}{'53'}{'54'}
  Pattern 570: Quality=0.1682, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'54'}{'53'}
  Pattern 571: Quality=0.1682, ROC-AUC=0.9255, Support=130, Pattern={'17'}{'18'}{'19'}{'23'}{'29'}{'53'}{'54'}
  Pattern 572: Quality=0.1676, ROC-AUC=0.8780, Support=79, Pattern={'1'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 573: Quality=0.1676, ROC-AUC=0.8780, Support=79, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 574: Quality=0.1647, ROC-AUC=0.9350, Support=115, Pattern={'14'}{'52'}{'51'}{'51'}{'52'}{'54'}
  Pattern 575: Quality=0.1647, ROC-AUC=0.9123, Support=40, Pattern={'1'}{'18'}{'17'}{'40'}{'45'}{'52'}{'54'}
  Pattern 576: Quality=0.1638, ROC-AUC=0.9119, Support=116, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 577: Quality=0.1634, ROC-AUC=0.9177, Support=60, Pattern={'19'}{'29'}{'46'}{'49'}{'52'}{'53'}{'54'}
  Pattern 578: Quality=0.1634, ROC-AUC=0.9177, Support=60, Pattern={'19'}{'23'}{'29'}{'46'}{'49'}{'52'}{'54'}
  Pattern 579: Quality=0.1611, ROC-AUC=0.8726, Support=73, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 580: Quality=0.1609, ROC-AUC=0.8333, Support=21, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 581: Quality=0.1599, ROC-AUC=0.9379, Support=148, Pattern={'17'}{'24'}{'51'}{'52'}{'53'}{'54'}
  Pattern 582: Quality=0.1592, ROC-AUC=0.9128, Support=118, Pattern={'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 583: Quality=0.1577, ROC-AUC=0.8857, Support=32, Pattern={'15'}{'18'}{'17'}{'19'}{'29'}{'47'}{'46'}{'52'}{'51'}{'51'}
  Pattern 584: Quality=0.1556, ROC-AUC=0.9131, Support=117, Pattern={'17'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'53'}{'54'}
  Pattern 585: Quality=0.1556, ROC-AUC=0.9131, Support=117, Pattern={'1'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'53'}
  Pattern 586: Quality=0.1545, ROC-AUC=0.9020, Support=54, Pattern={'1'}{'8'}{'46'}{'49'}{'51'}{'52'}{'51'}{'52'}{'53'}
  Pattern 587: Quality=0.1531, ROC-AUC=0.9334, Support=65, Pattern={'46'}{'49'}{'51'}{'52'}{'53'}{'54'}
  Pattern 588: Quality=0.1487, ROC-AUC=0.9045, Support=114, Pattern={'8'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 589: Quality=0.1486, ROC-AUC=0.9395, Support=126, Pattern={'18'}{'18'}{'52'}{'54'}{'53'}{'53'}
  Pattern 590: Quality=0.1482, ROC-AUC=0.9237, Support=77, Pattern={'14'}{'25'}{'52'}{'51'}{'51'}{'52'}{'54'}
  Pattern 591: Quality=0.1477, ROC-AUC=0.9113, Support=94, Pattern={'8'}{'13'}{'19'}{'25'}{'24'}{'29'}{'54'}{'53'}{'54'}
  Pattern 592: Quality=0.1457, ROC-AUC=0.9402, Support=124, Pattern={'14'}{'17'}{'18'}{'51'}{'52'}{'52'}
  Pattern 593: Quality=0.1440, ROC-AUC=0.8854, Support=28, Pattern={'19'}{'23'}{'25'}{'24'}{'29'}{'40'}{'45'}{'52'}{'53'}{'54'}
  Pattern 594: Quality=0.1400, ROC-AUC=0.9044, Support=54, Pattern={'17'}{'18'}{'17'}{'19'}{'23'}{'29'}{'46'}{'51'}{'53'}
  Pattern 595: Quality=0.1396, ROC-AUC=0.9074, Support=39, Pattern={'13'}{'18'}{'17'}{'23'}{'40'}{'45'}{'52'}{'54'}
  Pattern 596: Quality=0.1389, ROC-AUC=0.8333, Support=25, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 597: Quality=0.1383, ROC-AUC=0.9234, Support=61, Pattern={'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'54'}
  Pattern 598: Quality=0.1373, ROC-AUC=0.9441, Support=161, Pattern={'17'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 599: Quality=0.1373, ROC-AUC=0.9441, Support=161, Pattern={'1'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 600: Quality=0.1373, ROC-AUC=0.9441, Support=161, Pattern={'18'}{'17'}{'52'}{'51'}{'54'}{'53'}
  Pattern 601: Quality=0.1366, ROC-AUC=0.8654, Support=40, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'23'}{'24'}{'46'}{'49'}{'52'}{'51'}{'52'}
  Pattern 602: Quality=0.1314, ROC-AUC=0.9118, Support=47, Pattern={'14'}{'25'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 603: Quality=0.1307, ROC-AUC=0.8558, Support=21, Pattern={'1'}{'13'}{'18'}{'23'}{'24'}{'40'}{'45'}{'51'}{'51'}{'52'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 604: Quality=0.1277, ROC-AUC=0.8858, Support=84, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 605: Quality=0.1275, ROC-AUC=0.9206, Support=90, Pattern={'8'}{'17'}{'18'}{'46'}{'51'}{'54'}{'53'}{'54'}
  Pattern 606: Quality=0.1247, ROC-AUC=0.8333, Support=21, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 607: Quality=0.1244, ROC-AUC=0.9300, Support=86, Pattern={'17'}{'17'}{'19'}{'23'}{'51'}{'54'}{'53'}
  Pattern 608: Quality=0.1236, ROC-AUC=0.9209, Support=87, Pattern={'8'}{'16'}{'18'}{'46'}{'52'}{'54'}{'53'}{'54'}
  Pattern 609: Quality=0.1224, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'54'}{'53'}{'54'}
  Pattern 610: Quality=0.1206, ROC-AUC=0.8478, Support=35, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 611: Quality=0.1203, ROC-AUC=0.9125, Support=114, Pattern={'1'}{'8'}{'16'}{'17'}{'18'}{'23'}{'24'}{'52'}{'51'}{'52'}
  Pattern 612: Quality=0.1190, ROC-AUC=0.9231, Support=37, Pattern={'14'}{'17'}{'18'}{'47'}{'51'}{'52'}{'52'}
  Pattern 613: Quality=0.1188, ROC-AUC=0.9099, Support=61, Pattern={'14'}{'18'}{'29'}{'46'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 614: Quality=0.1185, ROC-AUC=0.8550, Support=39, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 615: Quality=0.1178, ROC-AUC=0.9131, Support=117, Pattern={'18'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 616: Quality=0.1152, ROC-AUC=0.9517, Support=181, Pattern={'1'}{'18'}{'52'}{'54'}{'53'}{'54'}
  Pattern 617: Quality=0.1148, ROC-AUC=0.9519, Support=180, Pattern={'18'}{'17'}{'52'}{'51'}{'52'}{'54'}
  Pattern 618: Quality=0.1138, ROC-AUC=0.9009, Support=89, Pattern={'1'}{'13'}{'16'}{'18'}{'19'}{'23'}{'29'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 619: Quality=0.1137, ROC-AUC=0.9202, Support=128, Pattern={'1'}{'8'}{'18'}{'17'}{'24'}{'52'}{'51'}{'52'}{'51'}
  Pattern 620: Quality=0.1118, ROC-AUC=0.8873, Support=83, Pattern={'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 621: Quality=0.1108, ROC-AUC=0.8946, Support=46, Pattern={'1'}{'8'}{'18'}{'17'}{'19'}{'23'}{'49'}{'51'}{'53'}{'53'}{'54'}
  Pattern 622: Quality=0.1101, ROC-AUC=0.9509, Support=75, Pattern={'18'}{'46'}{'49'}{'51'}{'52'}{'54'}
  Pattern 623: Quality=0.1100, ROC-AUC=0.8625, Support=24, Pattern={'1'}{'14'}{'15'}{'18'}{'19'}{'23'}{'29'}{'47'}{'46'}{'52'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 624: Quality=0.1081, ROC-AUC=0.9535, Support=113, Pattern={'17'}{'17'}{'24'}{'52'}{'53'}{'54'}
  Pattern 625: Quality=0.1079, ROC-AUC=0.9551, Support=190, Pattern={'1'}{'13'}{'16'}{'54'}{'53'}{'54'}
  Pattern 626: Quality=0.1073, ROC-AUC=0.9098, Support=116, Pattern={'8'}{'18'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 627: Quality=0.1063, ROC-AUC=0.9185, Support=101, Pattern={'8'}{'13'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 628: Quality=0.1050, ROC-AUC=0.9547, Support=88, Pattern={'15'}{'17'}{'46'}{'52'}{'51'}{'52'}
  Pattern 629: Quality=0.1030, ROC-AUC=0.8984, Support=88, Pattern={'8'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 630: Quality=0.1004, ROC-AUC=0.9297, Support=40, Pattern={'23'}{'24'}{'47'}{'49'}{'52'}{'51'}{'54'}
  Pattern 631: Quality=0.0998, ROC-AUC=0.9107, Support=115, Pattern={'1'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 632: Quality=0.0998, ROC-AUC=0.9383, Support=115, Pattern={'14'}{'18'}{'17'}{'19'}{'23'}{'29'}{'53'}
  Pattern 633: Quality=0.0986, ROC-AUC=0.9221, Support=124, Pattern={'1'}{'13'}{'16'}{'19'}{'23'}{'29'}{'54'}{'53'}{'54'}
  Pattern 634: Quality=0.0984, ROC-AUC=0.9060, Support=109, Pattern={'16'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 635: Quality=0.0975, ROC-AUC=0.9395, Support=126, Pattern={'18'}{'18'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 636: Quality=0.0950, ROC-AUC=0.8631, Support=26, Pattern={'18'}{'18'}{'23'}{'24'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 637: Quality=0.0947, ROC-AUC=0.9234, Support=132, Pattern={'13'}{'16'}{'18'}{'17'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 638: Quality=0.0932, ROC-AUC=0.9407, Support=127, Pattern={'1'}{'8'}{'17'}{'52'}{'54'}{'53'}{'53'}
  Pattern 639: Quality=0.0881, ROC-AUC=0.9183, Support=76, Pattern={'13'}{'15'}{'18'}{'23'}{'24'}{'29'}{'54'}{'54'}{'53'}
  Pattern 640: Quality=0.0869, ROC-AUC=0.8833, Support=43, Pattern={'1'}{'8'}{'15'}{'17'}{'19'}{'23'}{'29'}{'46'}{'52'}{'52'}{'51'}{'52'}{'53'}{'53'}
  Pattern 641: Quality=0.0855, ROC-AUC=0.8718, Support=40, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 642: Quality=0.0843, ROC-AUC=0.9306, Support=22, Pattern={'18'}{'19'}{'29'}{'47'}{'46'}{'47'}{'51'}
  Pattern 643: Quality=0.0843, ROC-AUC=0.9306, Support=22, Pattern={'8'}{'19'}{'46'}{'47'}{'47'}{'54'}{'53'}
  Pattern 644: Quality=0.0840, ROC-AUC=0.8757, Support=41, Pattern={'8'}{'13'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 645: Quality=0.0833, ROC-AUC=0.9137, Support=49, Pattern={'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'54'}{'54'}{'53'}
  Pattern 646: Quality=0.0833, ROC-AUC=0.9137, Support=49, Pattern={'18'}{'17'}{'23'}{'46'}{'49'}{'54'}{'53'}{'53'}{'54'}
  Pattern 647: Quality=0.0806, ROC-AUC=0.9206, Support=36, Pattern={'17'}{'17'}{'19'}{'23'}{'40'}{'51'}{'54'}{'53'}
  Pattern 648: Quality=0.0794, ROC-AUC=0.8844, Support=43, Pattern={'1'}{'8'}{'13'}{'17'}{'19'}{'23'}{'29'}{'46'}{'49'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 649: Quality=0.0781, ROC-AUC=0.9379, Support=39, Pattern={'16'}{'17'}{'24'}{'47'}{'46'}{'49'}{'51'}
  Pattern 650: Quality=0.0775, ROC-AUC=0.9123, Support=40, Pattern={'18'}{'17'}{'19'}{'23'}{'40'}{'45'}{'51'}{'54'}{'54'}
  Pattern 651: Quality=0.0762, ROC-AUC=0.8889, Support=63, Pattern={'8'}{'14'}{'18'}{'19'}{'23'}{'24'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 652: Quality=0.0762, ROC-AUC=0.9315, Support=96, Pattern={'16'}{'18'}{'17'}{'25'}{'27'}{'52'}{'53'}{'54'}
  Pattern 653: Quality=0.0744, ROC-AUC=0.9023, Support=111, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 654: Quality=0.0731, ROC-AUC=0.8754, Support=38, Pattern={'13'}{'15'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 655: Quality=0.0726, ROC-AUC=0.8839, Support=40, Pattern={'8'}{'18'}{'19'}{'23'}{'24'}{'46'}{'49'}{'52'}{'52'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 656: Quality=0.0709, ROC-AUC=0.9009, Support=45, Pattern={'1'}{'16'}{'18'}{'23'}{'29'}{'46'}{'49'}{'54'}{'53'}{'54'}{'54'}
  Pattern 657: Quality=0.0695, ROC-AUC=0.9342, Support=110, Pattern={'13'}{'15'}{'18'}{'23'}{'24'}{'29'}{'54'}{'53'}
  Pattern 658: Quality=0.0676, ROC-AUC=0.9107, Support=115, Pattern={'8'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 659: Quality=0.0674, ROC-AUC=0.9504, Support=177, Pattern={'8'}{'18'}{'17'}{'18'}{'24'}{'54'}{'53'}
  Pattern 660: Quality=0.0655, ROC-AUC=0.9373, Support=147, Pattern={'1'}{'18'}{'24'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 661: Quality=0.0645, ROC-AUC=0.9515, Support=179, Pattern={'1'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}
  Pattern 662: Quality=0.0639, ROC-AUC=0.9045, Support=73, Pattern={'8'}{'17'}{'17'}{'23'}{'24'}{'29'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 663: Quality=0.0618, ROC-AUC=0.9371, Support=126, Pattern={'18'}{'18'}{'24'}{'24'}{'52'}{'54'}{'53'}{'54'}
  Pattern 664: Quality=0.0606, ROC-AUC=0.8833, Support=43, Pattern={'1'}{'8'}{'15'}{'17'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}
  Pattern 665: Quality=0.0601, ROC-AUC=0.8558, Support=21, Pattern={'1'}{'13'}{'16'}{'18'}{'17'}{'23'}{'24'}{'40'}{'45'}{'51'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 666: Quality=0.0601, ROC-AUC=0.9087, Support=66, Pattern={'15'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'51'}{'54'}{'53'}{'54'}
  Pattern 667: Quality=0.0588, ROC-AUC=0.9374, Support=120, Pattern={'8'}{'15'}{'18'}{'17'}{'51'}{'51'}{'52'}{'54'}
  Pattern 668: Quality=0.0585, ROC-AUC=0.9074, Support=110, Pattern={'1'}{'8'}{'16'}{'18'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 669: Quality=0.0584, ROC-AUC=0.9326, Support=64, Pattern={'17'}{'46'}{'49'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 670: Quality=0.0584, ROC-AUC=0.9088, Support=92, Pattern={'8'}{'13'}{'16'}{'18'}{'19'}{'23'}{'25'}{'24'}{'29'}{'54'}{'53'}{'54'}
  Pattern 671: Quality=0.0580, ROC-AUC=0.8706, Support=37, Pattern={'1'}{'13'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 672: Quality=0.0579, ROC-AUC=0.8542, Support=34, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 673: Quality=0.0578, ROC-AUC=0.9538, Support=144, Pattern={'1'}{'14'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 674: Quality=0.0572, ROC-AUC=0.8963, Support=83, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'51'}{'54'}{'53'}{'54'}
  Pattern 675: Quality=0.0570, ROC-AUC=0.8772, Support=43, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}
  Pattern 676: Quality=0.0533, ROC-AUC=0.9125, Support=114, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'23'}{'24'}{'52'}{'51'}{'52'}
  Pattern 677: Quality=0.0508, ROC-AUC=0.9081, Support=57, Pattern={'19'}{'23'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 678: Quality=0.0504, ROC-AUC=0.8707, Support=49, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 679: Quality=0.0503, ROC-AUC=0.9089, Support=114, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 680: Quality=0.0497, ROC-AUC=0.9009, Support=85, Pattern={'14'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 681: Quality=0.0488, ROC-AUC=0.8472, Support=22, Pattern={'8'}{'13'}{'15'}{'18'}{'17'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 682: Quality=0.0486, ROC-AUC=0.8661, Support=22, Pattern={'1'}{'18'}{'23'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 683: Quality=0.0485, ROC-AUC=0.8974, Support=68, Pattern={'14'}{'18'}{'17'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 684: Quality=0.0459, ROC-AUC=0.8840, Support=63, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 685: Quality=0.0449, ROC-AUC=0.9070, Support=71, Pattern={'1'}{'14'}{'15'}{'18'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 686: Quality=0.0445, ROC-AUC=0.9057, Support=87, Pattern={'14'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 687: Quality=0.0428, ROC-AUC=0.9306, Support=27, Pattern={'23'}{'29'}{'47'}{'46'}{'48'}{'52'}{'52'}{'54'}
  Pattern 688: Quality=0.0427, ROC-AUC=0.9079, Support=74, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'24'}{'27'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 689: Quality=0.0381, ROC-AUC=0.8552, Support=30, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 690: Quality=0.0377, ROC-AUC=0.8382, Support=21, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'18'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 691: Quality=0.0344, ROC-AUC=0.9244, Support=101, Pattern={'1'}{'14'}{'18'}{'19'}{'29'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 692: Quality=0.0330, ROC-AUC=0.8765, Support=36, Pattern={'1'}{'13'}{'14'}{'16'}{'18'}{'18'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 693: Quality=0.0324, ROC-AUC=0.8980, Support=62, Pattern={'14'}{'16'}{'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 694: Quality=0.0307, ROC-AUC=0.9094, Support=72, Pattern={'14'}{'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 695: Quality=0.0300, ROC-AUC=0.8827, Support=40, Pattern={'8'}{'13'}{'14'}{'15'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 696: Quality=0.0290, ROC-AUC=0.8500, Support=22, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'18'}{'19'}{'23'}{'24'}{'29'}{'40'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 697: Quality=0.0284, ROC-AUC=0.8979, Support=46, Pattern={'14'}{'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'53'}{'54'}{'53'}{'54'}{'53'}
  Pattern 698: Quality=0.0283, ROC-AUC=0.9039, Support=86, Pattern={'8'}{'15'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 699: Quality=0.0281, ROC-AUC=0.8631, Support=26, Pattern={'1'}{'8'}{'17'}{'18'}{'19'}{'24'}{'24'}{'29'}{'46'}{'49'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 700: Quality=0.0276, ROC-AUC=0.8846, Support=29, Pattern={'16'}{'18'}{'19'}{'23'}{'24'}{'29'}{'40'}{'52'}{'51'}{'52'}{'52'}{'53'}{'54'}{'53'}
  Pattern 701: Quality=0.0273, ROC-AUC=0.9002, Support=52, Pattern={'1'}{'8'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 702: Quality=0.0267, ROC-AUC=0.9231, Support=32, Pattern={'17'}{'17'}{'19'}{'47'}{'49'}{'51'}{'52'}{'53'}{'54'}
  Pattern 703: Quality=0.0265, ROC-AUC=0.8571, Support=28, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'17'}{'19'}{'23'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 704: Quality=0.0260, ROC-AUC=0.9309, Support=70, Pattern={'8'}{'15'}{'18'}{'17'}{'46'}{'51'}{'51'}{'52'}{'54'}
  Pattern 705: Quality=0.0257, ROC-AUC=0.8844, Support=35, Pattern={'15'}{'17'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 706: Quality=0.0254, ROC-AUC=0.9261, Support=101, Pattern={'1'}{'15'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'53'}
  Pattern 707: Quality=0.0236, ROC-AUC=0.9495, Support=172, Pattern={'8'}{'16'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}
  Pattern 708: Quality=0.0226, ROC-AUC=0.9499, Support=173, Pattern={'13'}{'16'}{'18'}{'17'}{'52'}{'51'}{'52'}{'54'}
  Pattern 709: Quality=0.0224, ROC-AUC=0.9483, Support=117, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'46'}{'52'}{'54'}
  Pattern 710: Quality=0.0214, ROC-AUC=0.8839, Support=40, Pattern={'8'}{'18'}{'19'}{'23'}{'24'}{'46'}{'49'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 711: Quality=0.0168, ROC-AUC=0.9484, Support=66, Pattern={'1'}{'17'}{'17'}{'25'}{'54'}{'53'}{'54'}{'53'}
  Pattern 712: Quality=0.0164, ROC-AUC=0.9220, Support=106, Pattern={'8'}{'18'}{'18'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 713: Quality=0.0161, ROC-AUC=0.9000, Support=46, Pattern={'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'51'}{'53'}{'54'}{'53'}
  Pattern 714: Quality=0.0142, ROC-AUC=0.8707, Support=49, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 715: Quality=0.0140, ROC-AUC=0.9060, Support=109, Pattern={'1'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 716: Quality=0.0127, ROC-AUC=0.9489, Support=43, Pattern={'18'}{'46'}{'47'}{'46'}{'49'}{'51'}{'52'}{'54'}
  Pattern 717: Quality=0.0123, ROC-AUC=0.9404, Support=155, Pattern={'8'}{'18'}{'18'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 718: Quality=0.0103, ROC-AUC=0.9395, Support=126, Pattern={'8'}{'18'}{'18'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 719: Quality=0.0103, ROC-AUC=0.8924, Support=78, Pattern={'8'}{'13'}{'14'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 720: Quality=0.0080, ROC-AUC=0.9275, Support=26, Pattern={'18'}{'46'}{'47'}{'46'}{'48'}{'49'}{'51'}{'52'}{'54'}
  Pattern 721: Quality=0.0077, ROC-AUC=0.9195, Support=38, Pattern={'14'}{'18'}{'19'}{'23'}{'24'}{'29'}{'47'}{'46'}{'51'}{'54'}
  Pattern 722: Quality=0.0074, ROC-AUC=0.9355, Support=64, Pattern={'1'}{'13'}{'15'}{'17'}{'18'}{'46'}{'49'}{'51'}{'52'}
  Pattern 723: Quality=0.0068, ROC-AUC=0.8995, Support=83, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 724: Quality=0.0067, ROC-AUC=0.9259, Support=21, Pattern={'23'}{'29'}{'47'}{'46'}{'48'}{'52'}{'52'}{'52'}{'54'}
  Pattern 725: Quality=0.0060, ROC-AUC=0.9037, Support=52, Pattern={'1'}{'8'}{'13'}{'15'}{'18'}{'17'}{'18'}{'46'}{'49'}{'51'}{'52'}{'51'}{'54'}
  Pattern 726: Quality=0.0054, ROC-AUC=0.8462, Support=22, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 727: Quality=0.0020, ROC-AUC=0.9153, Support=78, Pattern={'8'}{'18'}{'17'}{'18'}{'17'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 728: Quality=0.0003, ROC-AUC=0.8979, Support=46, Pattern={'1'}{'8'}{'14'}{'17'}{'23'}{'24'}{'29'}{'52'}{'51'}{'53'}{'54'}{'53'}{'54'}{'54'}
  Pattern 729: Quality=-0.0005, ROC-AUC=0.9325, Support=114, Pattern={'16'}{'17'}{'18'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 730: Quality=-0.0023, ROC-AUC=0.8845, Support=62, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 731: Quality=-0.0028, ROC-AUC=0.9306, Support=22, Pattern={'19'}{'23'}{'29'}{'46'}{'47'}{'47'}{'46'}{'54'}{'53'}
  Pattern 732: Quality=-0.0067, ROC-AUC=0.8958, Support=28, Pattern={'18'}{'23'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 733: Quality=-0.0068, ROC-AUC=0.8704, Support=21, Pattern={'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'47'}{'46'}{'52'}{'51'}{'52'}{'52'}{'53'}{'54'}{'54'}
  Pattern 734: Quality=-0.0082, ROC-AUC=0.9340, Support=112, Pattern={'1'}{'8'}{'14'}{'18'}{'17'}{'24'}{'52'}{'51'}{'52'}{'51'}
  Pattern 735: Quality=-0.0093, ROC-AUC=0.9261, Support=101, Pattern={'14'}{'17'}{'18'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 736: Quality=-0.0108, ROC-AUC=0.9060, Support=109, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 737: Quality=-0.0116, ROC-AUC=0.8571, Support=23, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 738: Quality=-0.0153, ROC-AUC=0.9062, Support=66, Pattern={'1'}{'15'}{'18'}{'17'}{'19'}{'23'}{'25'}{'29'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 739: Quality=-0.0158, ROC-AUC=0.8827, Support=40, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 740: Quality=-0.0174, ROC-AUC=0.9371, Support=126, Pattern={'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'52'}{'54'}{'53'}{'54'}
  Pattern 741: Quality=-0.0239, ROC-AUC=0.9280, Support=91, Pattern={'1'}{'8'}{'13'}{'16'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'54'}
  Pattern 742: Quality=-0.0247, ROC-AUC=0.8571, Support=28, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 743: Quality=-0.0262, ROC-AUC=0.8896, Support=29, Pattern={'8'}{'13'}{'18'}{'17'}{'18'}{'24'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 744: Quality=-0.0268, ROC-AUC=0.9177, Support=96, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'17'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 745: Quality=-0.0304, ROC-AUC=0.9043, Support=65, Pattern={'14'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 746: Quality=-0.0306, ROC-AUC=0.8946, Support=46, Pattern={'14'}{'16'}{'18'}{'17'}{'17'}{'19'}{'23'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 747: Quality=-0.0309, ROC-AUC=0.8722, Support=26, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}
  Pattern 748: Quality=-0.0320, ROC-AUC=0.9420, Support=155, Pattern={'1'}{'8'}{'13'}{'17'}{'18'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 749: Quality=-0.0325, ROC-AUC=0.9244, Support=101, Pattern={'1'}{'14'}{'15'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 750: Quality=-0.0333, ROC-AUC=0.9206, Support=36, Pattern={'8'}{'17'}{'17'}{'19'}{'23'}{'24'}{'40'}{'51'}{'52'}{'53'}{'54'}
  Pattern 751: Quality=-0.0334, ROC-AUC=0.9056, Support=36, Pattern={'19'}{'23'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 752: Quality=-0.0343, ROC-AUC=0.9060, Support=109, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 753: Quality=-0.0363, ROC-AUC=0.8900, Support=20, Pattern={'16'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'40'}{'45'}{'51'}{'53'}{'54'}{'53'}
  Pattern 754: Quality=-0.0401, ROC-AUC=0.8977, Support=62, Pattern={'14'}{'15'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 755: Quality=-0.0401, ROC-AUC=0.8845, Support=62, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 756: Quality=-0.0405, ROC-AUC=0.8701, Support=29, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 757: Quality=-0.0412, ROC-AUC=0.9200, Support=95, Pattern={'1'}{'14'}{'16'}{'15'}{'18'}{'19'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 758: Quality=-0.0414, ROC-AUC=0.8654, Support=21, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}
  Pattern 759: Quality=-0.0418, ROC-AUC=0.8889, Support=45, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'17'}{'23'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}
  Pattern 760: Quality=-0.0466, ROC-AUC=0.8767, Support=37, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'17'}{'18'}{'23'}{'24'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 761: Quality=-0.0484, ROC-AUC=0.9456, Support=126, Pattern={'1'}{'8'}{'14'}{'17'}{'24'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 762: Quality=-0.0498, ROC-AUC=0.8901, Support=45, Pattern={'14'}{'15'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}
  Pattern 763: Quality=-0.0504, ROC-AUC=0.8924, Support=78, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 764: Quality=-0.0510, ROC-AUC=0.8880, Support=40, Pattern={'1'}{'8'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'25'}{'24'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 765: Quality=-0.0545, ROC-AUC=0.8889, Support=48, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}
  Pattern 766: Quality=-0.0555, ROC-AUC=0.9495, Support=172, Pattern={'1'}{'8'}{'13'}{'16'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}
  Pattern 767: Quality=-0.0555, ROC-AUC=0.9495, Support=172, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}
  Pattern 768: Quality=-0.0560, ROC-AUC=0.8971, Support=32, Pattern={'1'}{'8'}{'17'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 769: Quality=-0.0560, ROC-AUC=0.9280, Support=91, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'54'}
  Pattern 770: Quality=-0.0565, ROC-AUC=0.9185, Support=101, Pattern={'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 771: Quality=-0.0568, ROC-AUC=0.9394, Support=150, Pattern={'1'}{'16'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 772: Quality=-0.0592, ROC-AUC=0.9181, Support=94, Pattern={'8'}{'13'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 773: Quality=-0.0608, ROC-AUC=0.8831, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 774: Quality=-0.0612, ROC-AUC=0.8730, Support=36, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 775: Quality=-0.0622, ROC-AUC=0.9395, Support=126, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 776: Quality=-0.0637, ROC-AUC=0.8910, Support=58, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 777: Quality=-0.0657, ROC-AUC=0.9265, Support=62, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 778: Quality=-0.0661, ROC-AUC=0.8968, Support=57, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 779: Quality=-0.0665, ROC-AUC=0.9192, Support=93, Pattern={'8'}{'13'}{'14'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 780: Quality=-0.0666, ROC-AUC=0.9512, Support=73, Pattern={'8'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'52'}{'54'}
  Pattern 781: Quality=-0.0680, ROC-AUC=0.9521, Support=75, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'18'}{'17'}{'46'}{'49'}{'52'}
  Pattern 782: Quality=-0.0683, ROC-AUC=0.8909, Support=64, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 783: Quality=-0.0685, ROC-AUC=0.8765, Support=36, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 784: Quality=-0.0702, ROC-AUC=0.8904, Support=46, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 785: Quality=-0.0703, ROC-AUC=0.8558, Support=21, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 786: Quality=-0.0709, ROC-AUC=0.8596, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'46'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 787: Quality=-0.0714, ROC-AUC=0.9553, Support=101, Pattern={'8'}{'13'}{'16'}{'15'}{'18'}{'24'}{'27'}{'54'}{'53'}{'54'}
  Pattern 788: Quality=-0.0717, ROC-AUC=0.8919, Support=66, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 789: Quality=-0.0722, ROC-AUC=0.8955, Support=32, Pattern={'1'}{'8'}{'15'}{'17'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'53'}{'53'}
  Pattern 790: Quality=-0.0754, ROC-AUC=0.9306, Support=22, Pattern={'8'}{'18'}{'19'}{'23'}{'29'}{'46'}{'47'}{'47'}{'46'}{'54'}{'53'}
  Pattern 791: Quality=-0.0781, ROC-AUC=0.8636, Support=27, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 792: Quality=-0.0816, ROC-AUC=0.8988, Support=45, Pattern={'1'}{'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'49'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 793: Quality=-0.0819, ROC-AUC=0.8831, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 794: Quality=-0.0830, ROC-AUC=0.9083, Support=63, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'53'}{'54'}{'53'}{'54'}
  Pattern 795: Quality=-0.0832, ROC-AUC=0.9456, Support=126, Pattern={'1'}{'8'}{'14'}{'15'}{'17'}{'24'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 796: Quality=-0.0844, ROC-AUC=0.8696, Support=30, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 797: Quality=-0.0851, ROC-AUC=0.8769, Support=41, Pattern={'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 798: Quality=-0.0873, ROC-AUC=0.9113, Support=36, Pattern={'8'}{'16'}{'18'}{'17'}{'18'}{'23'}{'24'}{'47'}{'49'}{'52'}{'51'}{'52'}{'54'}{'54'}
  Pattern 799: Quality=-0.0879, ROC-AUC=0.9237, Support=99, Pattern={'1'}{'8'}{'14'}{'15'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 800: Quality=-0.0904, ROC-AUC=0.9472, Support=100, Pattern={'1'}{'14'}{'16'}{'15'}{'17'}{'24'}{'52'}{'54'}{'54'}{'53'}{'54'}
  Pattern 801: Quality=-0.0912, ROC-AUC=0.8839, Support=23, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'18'}{'17'}{'24'}{'25'}{'24'}{'27'}{'46'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 802: Quality=-0.0921, ROC-AUC=0.8812, Support=38, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 803: Quality=-0.0929, ROC-AUC=0.9192, Support=93, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 804: Quality=-0.0930, ROC-AUC=0.8741, Support=24, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 805: Quality=-0.0937, ROC-AUC=0.8849, Support=45, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 806: Quality=-0.0952, ROC-AUC=0.8874, Support=44, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'17'}{'19'}{'23'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 807: Quality=-0.0968, ROC-AUC=0.8896, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'24'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 808: Quality=-0.0975, ROC-AUC=0.9000, Support=22, Pattern={'15'}{'17'}{'17'}{'19'}{'23'}{'29'}{'40'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 809: Quality=-0.1001, ROC-AUC=0.9310, Support=33, Pattern={'1'}{'8'}{'18'}{'17'}{'19'}{'23'}{'47'}{'49'}{'51'}{'53'}{'53'}{'54'}
  Pattern 810: Quality=-0.1015, ROC-AUC=0.8769, Support=41, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 811: Quality=-0.1035, ROC-AUC=0.8750, Support=30, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 812: Quality=-0.1052, ROC-AUC=0.9557, Support=148, Pattern={'1'}{'8'}{'14'}{'15'}{'17'}{'18'}{'24'}{'52'}{'54'}{'53'}{'54'}
  Pattern 813: Quality=-0.1064, ROC-AUC=0.9553, Support=96, Pattern={'13'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'24'}{'27'}{'54'}{'53'}
  Pattern 814: Quality=-0.1113, ROC-AUC=0.9232, Support=99, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 815: Quality=-0.1131, ROC-AUC=0.9034, Support=31, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'40'}{'45'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 816: Quality=-0.1155, ROC-AUC=0.8627, Support=23, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 817: Quality=-0.1162, ROC-AUC=0.9009, Support=45, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 818: Quality=-0.1182, ROC-AUC=0.9005, Support=43, Pattern={'1'}{'8'}{'13'}{'16'}{'15'}{'18'}{'17'}{'18'}{'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 819: Quality=-0.1185, ROC-AUC=0.9117, Support=90, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 820: Quality=-0.1189, ROC-AUC=0.9178, Support=54, Pattern={'1'}{'13'}{'15'}{'18'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 821: Quality=-0.1219, ROC-AUC=0.9254, Support=101, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}
  Pattern 822: Quality=-0.1224, ROC-AUC=0.8684, Support=25, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 823: Quality=-0.1226, ROC-AUC=0.9472, Support=100, Pattern={'8'}{'13'}{'14'}{'18'}{'17'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 824: Quality=-0.1226, ROC-AUC=0.9472, Support=100, Pattern={'14'}{'16'}{'15'}{'17'}{'18'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 825: Quality=-0.1264, ROC-AUC=0.8690, Support=25, Pattern={'1'}{'8'}{'14'}{'15'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 826: Quality=-0.1295, ROC-AUC=0.9177, Support=96, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 827: Quality=-0.1328, ROC-AUC=0.9052, Support=62, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 828: Quality=-0.1333, ROC-AUC=0.9111, Support=73, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 829: Quality=-0.1336, ROC-AUC=0.9512, Support=73, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'52'}{'54'}
  Pattern 830: Quality=-0.1336, ROC-AUC=0.9108, Support=71, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 831: Quality=-0.1336, ROC-AUC=0.8960, Support=60, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 832: Quality=-0.1361, ROC-AUC=0.9232, Support=99, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 833: Quality=-0.1395, ROC-AUC=0.9212, Support=78, Pattern={'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'18'}{'17'}{'19'}{'23'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 834: Quality=-0.1401, ROC-AUC=0.8800, Support=25, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 835: Quality=-0.1464, ROC-AUC=0.9286, Support=84, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'52'}{'51'}{'52'}{'51'}{'54'}
  Pattern 836: Quality=-0.1473, ROC-AUC=0.8959, Support=30, Pattern={'1'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 837: Quality=-0.1484, ROC-AUC=0.8874, Support=44, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 838: Quality=-0.1499, ROC-AUC=0.9375, Support=24, Pattern={'16'}{'15'}{'18'}{'17'}{'19'}{'23'}{'24'}{'40'}{'45'}{'51'}{'53'}{'54'}{'53'}
  Pattern 839: Quality=-0.1526, ROC-AUC=0.9472, Support=100, Pattern={'13'}{'14'}{'16'}{'15'}{'17'}{'18'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 840: Quality=-0.1529, ROC-AUC=0.9452, Support=65, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'17'}{'25'}{'24'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 841: Quality=-0.1548, ROC-AUC=0.9108, Support=71, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 842: Quality=-0.1571, ROC-AUC=0.8979, Support=46, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 843: Quality=-0.1578, ROC-AUC=0.8926, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'17'}{'23'}{'29'}{'40'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}
  Pattern 844: Quality=-0.1578, ROC-AUC=0.8800, Support=25, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 845: Quality=-0.1594, ROC-AUC=0.8704, Support=21, Pattern={'1'}{'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 846: Quality=-0.1596, ROC-AUC=0.9005, Support=43, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}
  Pattern 847: Quality=-0.1612, ROC-AUC=0.8718, Support=22, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 848: Quality=-0.1622, ROC-AUC=0.8864, Support=28, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'27'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 849: Quality=-0.1629, ROC-AUC=0.8741, Support=24, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 850: Quality=-0.1635, ROC-AUC=0.9512, Support=73, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'46'}{'52'}{'54'}
  Pattern 851: Quality=-0.1685, ROC-AUC=0.9417, Support=84, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 852: Quality=-0.1700, ROC-AUC=0.9211, Support=21, Pattern={'8'}{'13'}{'18'}{'23'}{'24'}{'29'}{'46'}{'47'}{'46'}{'48'}{'52'}{'52'}{'53'}{'54'}{'53'}
  Pattern 853: Quality=-0.1721, ROC-AUC=0.9341, Support=76, Pattern={'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 854: Quality=-0.1743, ROC-AUC=0.9127, Support=64, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 855: Quality=-0.1745, ROC-AUC=0.8929, Support=35, Pattern={'1'}{'8'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 856: Quality=-0.1768, ROC-AUC=0.8765, Support=27, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 857: Quality=-0.1806, ROC-AUC=0.9472, Support=100, Pattern={'1'}{'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 858: Quality=-0.1827, ROC-AUC=0.9375, Support=80, Pattern={'1'}{'8'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 859: Quality=-0.1827, ROC-AUC=0.9257, Support=82, Pattern={'1'}{'8'}{'14'}{'15'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 860: Quality=-0.1874, ROC-AUC=0.9125, Support=24, Pattern={'1'}{'16'}{'18'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'49'}{'52'}{'54'}{'53'}{'54'}{'54'}
  Pattern 861: Quality=-0.1922, ROC-AUC=0.8929, Support=35, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 862: Quality=-0.1935, ROC-AUC=0.8914, Support=32, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'27'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 863: Quality=-0.1956, ROC-AUC=0.9079, Support=23, Pattern={'8'}{'14'}{'18'}{'19'}{'23'}{'24'}{'46'}{'47'}{'49'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 864: Quality=-0.2025, ROC-AUC=0.9452, Support=95, Pattern={'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'24'}{'25'}{'24'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 865: Quality=-0.2035, ROC-AUC=0.9371, Support=24, Pattern={'1'}{'14'}{'15'}{'18'}{'23'}{'29'}{'40'}{'45'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 866: Quality=-0.2053, ROC-AUC=0.9466, Support=101, Pattern={'1'}{'8'}{'13'}{'14'}{'15'}{'18'}{'17'}{'18'}{'17'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 867: Quality=-0.2065, ROC-AUC=0.9212, Support=78, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 868: Quality=-0.2095, ROC-AUC=0.9495, Support=133, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 869: Quality=-0.2123, ROC-AUC=0.9497, Support=106, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'52'}{'54'}{'53'}{'54'}
  Pattern 870: Quality=-0.2170, ROC-AUC=0.9415, Support=94, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'24'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 871: Quality=-0.2223, ROC-AUC=0.8800, Support=25, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 872: Quality=-0.2285, ROC-AUC=0.9311, Support=83, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 873: Quality=-0.2477, ROC-AUC=0.9553, Support=96, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'27'}{'54'}{'53'}{'54'}
  Pattern 874: Quality=-0.2523, ROC-AUC=0.8810, Support=20, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 875: Quality=-0.2631, ROC-AUC=0.9501, Support=87, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'24'}{'25'}{'24'}{'27'}{'52'}{'54'}{'53'}{'54'}
  Pattern 876: Quality=-0.2634, ROC-AUC=0.8909, Support=21, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'40'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 877: Quality=-0.3911, ROC-AUC=0.9306, Support=24, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'40'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 878: Quality=-0.3936, ROC-AUC=0.9545, Support=24, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'47'}{'46'}{'49'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 879: Quality=-0.4296, ROC-AUC=0.9421, Support=22, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'40'}{'45'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
================================================================================

================
APPLYING STATISTICAL VALIDATION
================

 Pattern 0
    Support=25, Class balance={1.0: 20, 0.0: 5}. Pattern AUC=0.7000, p-value=0.000700

 Pattern 1
    Support=30, Class balance={1.0: 20, 0.0: 10}. Pattern AUC=0.6950, p-value=0.000200

 Pattern 2
    Support=30, Class balance={1.0: 27, 0.0: 3}. Pattern AUC=0.7160, p-value=0.006899

 Pattern 3
    Support=21, Class balance={1.0: 18, 0.0: 3}. Pattern AUC=0.6852, p-value=0.003500

 Pattern 4
    Support=25, Class balance={1.0: 20, 0.0: 5}. Pattern AUC=0.7000, p-value=0.000300

 Pattern 5
    Support=37, Class balance={1.0: 23, 0.0: 14}. Pattern AUC=0.7329, p-value=0.000100

 Pattern 6
    Support=21, Class balance={1.0: 17, 0.0: 4}. Pattern AUC=0.7059, p-value=0.001500

 Pattern 7
    Support=33, Class balance={1.0: 22, 0.0: 11}. Pattern AUC=0.7314, p-value=0.000100

 Pattern 8
    Support=38, Class balance={1.0: 23, 0.0: 15}. Pattern AUC=0.7507, p-value=0.000100

 Pattern 9
    Support=27, Class balance={1.0: 24, 0.0: 3}. Pattern AUC=0.7222, p-value=0.007999

 Pattern 10
    Support=38, Class balance={1.0: 23, 0.0: 15}. Pattern AUC=0.7507, p-value=0.000100

 Pattern 11
    Support=21, Class balance={1.0: 8, 0.0: 13}. Pattern AUC=0.7212, p-value=0.000100

 Pattern 12
    Support=21, Class balance={1.0: 11, 0.0: 10}. Pattern AUC=0.7091, p-value=0.000200

 Pattern 13
    Support=21, Class balance={1.0: 8, 0.0: 13}. Pattern AUC=0.7212, p-value=0.000200

 Pattern 14
    Support=26, Class balance={1.0: 20, 0.0: 6}. Pattern AUC=0.7500, p-value=0.001100

 Pattern 15
    Support=40, Class balance={1.0: 25, 0.0: 15}. Pattern AUC=0.7547, p-value=0.000100

 Pattern 16
    Support=32, Class balance={1.0: 24, 0.0: 8}. Pattern AUC=0.7604, p-value=0.000100

 Pattern 17
    Support=42, Class balance={1.0: 25, 0.0: 17}. Pattern AUC=0.7741, p-value=0.000100

 Pattern 18
    Support=41, Class balance={1.0: 23, 0.0: 18}. Pattern AUC=0.7923, p-value=0.000100

 Pattern 19
    Support=35, Class balance={1.0: 22, 0.0: 13}. Pattern AUC=0.7692, p-value=0.000100

 Pattern 20
    Support=36, Class balance={1.0: 23, 0.0: 13}. Pattern AUC=0.7759, p-value=0.000100

 Pattern 21
    Support=22, Class balance={1.0: 8, 0.0: 14}. Pattern AUC=0.7411, p-value=0.000300

 Pattern 22
    Support=35, Class balance={1.0: 22, 0.0: 13}. Pattern AUC=0.7692, p-value=0.000100

 Pattern 23
    Support=35, Class balance={1.0: 22, 0.0: 13}. Pattern AUC=0.7692, p-value=0.000100

 Pattern 24
    Support=22, Class balance={1.0: 10, 0.0: 12}. Pattern AUC=0.7417, p-value=0.000100

 Pattern 25
    Support=45, Class balance={1.0: 27, 0.0: 18}. Pattern AUC=0.7901, p-value=0.000100

 Pattern 26
    Support=48, Class balance={1.0: 28, 0.0: 20}. Pattern AUC=0.8161, p-value=0.000100

 Pattern 27
    Support=24, Class balance={1.0: 14, 0.0: 10}. Pattern AUC=0.7714, p-value=0.000300

 Pattern 28
    Support=34, Class balance={1.0: 17, 0.0: 17}. Pattern AUC=0.7820, p-value=0.000100

 Pattern 29
    Support=38, Class balance={1.0: 30, 0.0: 8}. Pattern AUC=0.7792, p-value=0.000300

 Pattern 30
    Support=33, Class balance={1.0: 25, 0.0: 8}. Pattern AUC=0.7950, p-value=0.001400

 Pattern 31
    Support=31, Class balance={1.0: 14, 0.0: 17}. Pattern AUC=0.7815, p-value=0.000100

 Pattern 32
    Support=47, Class balance={1.0: 30, 0.0: 17}. Pattern AUC=0.8020, p-value=0.000100

 Pattern 33
    Support=31, Class balance={1.0: 14, 0.0: 17}. Pattern AUC=0.7815, p-value=0.000100

 Pattern 34
    Support=27, Class balance={1.0: 20, 0.0: 7}. Pattern AUC=0.7643, p-value=0.000600

 Pattern 35
    Support=27, Class balance={1.0: 20, 0.0: 7}. Pattern AUC=0.7643, p-value=0.000400

 Pattern 36
    Support=54, Class balance={1.0: 34, 0.0: 20}. Pattern AUC=0.8279, p-value=0.000100

 Pattern 37
    Support=47, Class balance={1.0: 26, 0.0: 21}. Pattern AUC=0.8223, p-value=0.000100

 Pattern 38
    Support=25, Class balance={1.0: 12, 0.0: 13}. Pattern AUC=0.7756, p-value=0.000200

 Pattern 39
    Support=48, Class balance={1.0: 26, 0.0: 22}. Pattern AUC=0.8304, p-value=0.000100

 Pattern 40
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8214, p-value=0.001100

 Pattern 41
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8214, p-value=0.001400

 Pattern 42
    Support=53, Class balance={1.0: 36, 0.0: 17}. Pattern AUC=0.8219, p-value=0.000100

 Pattern 43
    Support=24, Class balance={1.0: 11, 0.0: 13}. Pattern AUC=0.7692, p-value=0.000200

 Pattern 44
    Support=38, Class balance={1.0: 18, 0.0: 20}. Pattern AUC=0.8083, p-value=0.000100

 Pattern 45
    Support=54, Class balance={1.0: 34, 0.0: 20}. Pattern AUC=0.8279, p-value=0.000100

 Pattern 46
    Support=54, Class balance={1.0: 34, 0.0: 20}. Pattern AUC=0.8279, p-value=0.000100

 Pattern 47
    Support=25, Class balance={1.0: 12, 0.0: 13}. Pattern AUC=0.7756, p-value=0.000100

 Pattern 48
    Support=54, Class balance={1.0: 34, 0.0: 20}. Pattern AUC=0.8279, p-value=0.000100

 Pattern 49
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8214, p-value=0.001300

 Pattern 50
    Support=59, Class balance={1.0: 39, 0.0: 20}. Pattern AUC=0.8487, p-value=0.000100

 Pattern 51
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8254, p-value=0.001400

 Pattern 52
    Support=60, Class balance={1.0: 34, 0.0: 26}. Pattern AUC=0.8382, p-value=0.000100

 Pattern 53
    Support=53, Class balance={1.0: 36, 0.0: 17}. Pattern AUC=0.8219, p-value=0.000100

 Pattern 54
    Support=37, Class balance={1.0: 27, 0.0: 10}. Pattern AUC=0.8111, p-value=0.000700

 Pattern 55
    Support=66, Class balance={1.0: 37, 0.0: 29}. Pattern AUC=0.8537, p-value=0.000100

 Pattern 56
    Support=44, Class balance={1.0: 27, 0.0: 17}. Pattern AUC=0.8105, p-value=0.000100

 Pattern 57
    Support=47, Class balance={1.0: 20, 0.0: 27}. Pattern AUC=0.8296, p-value=0.000100

 Pattern 58
    Support=69, Class balance={1.0: 37, 0.0: 32}. Pattern AUC=0.8674, p-value=0.000100

 Pattern 59
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8214, p-value=0.001200

 Pattern 60
    Support=37, Class balance={1.0: 28, 0.0: 9}. Pattern AUC=0.8214, p-value=0.001800

 Pattern 61
    Support=43, Class balance={1.0: 33, 0.0: 10}. Pattern AUC=0.8242, p-value=0.000800

 Pattern 62
    Support=31, Class balance={1.0: 25, 0.0: 6}. Pattern AUC=0.8000, p-value=0.002000

 Pattern 63
    Support=27, Class balance={1.0: 13, 0.0: 14}. Pattern AUC=0.7967, p-value=0.000300

 Pattern 64
    Support=46, Class balance={1.0: 21, 0.0: 25}. Pattern AUC=0.8971, p-value=0.003100

 Pattern 65
    Support=59, Class balance={1.0: 39, 0.0: 20}. Pattern AUC=0.8487, p-value=0.000100

 Pattern 66
    Support=59, Class balance={1.0: 39, 0.0: 20}. Pattern AUC=0.8487, p-value=0.000100

 Pattern 67
    Support=66, Class balance={1.0: 37, 0.0: 29}. Pattern AUC=0.8537, p-value=0.000100

 Pattern 68
    Support=66, Class balance={1.0: 37, 0.0: 29}. Pattern AUC=0.8537, p-value=0.000100

 Pattern 69
    Support=32, Class balance={1.0: 10, 0.0: 22}. Pattern AUC=0.7909, p-value=0.000100

 Pattern 70
    Support=59, Class balance={1.0: 39, 0.0: 20}. Pattern AUC=0.8487, p-value=0.000100

 Pattern 71
    Support=54, Class balance={1.0: 34, 0.0: 20}. Pattern AUC=0.8279, p-value=0.000100

 Pattern 72
    Support=73, Class balance={1.0: 29, 0.0: 44}. Pattern AUC=0.8699, p-value=0.000100

 Pattern 73
    Support=66, Class balance={1.0: 37, 0.0: 29}. Pattern AUC=0.8537, p-value=0.000100

 Pattern 74
    Support=34, Class balance={1.0: 11, 0.0: 23}. Pattern AUC=0.8103, p-value=0.000200

 Pattern 75
    Support=37, Class balance={1.0: 27, 0.0: 10}. Pattern AUC=0.8370, p-value=0.001900

 Pattern 76
    Support=80, Class balance={1.0: 42, 0.0: 38}. Pattern AUC=0.8997, p-value=0.000100

 Pattern 77
    Support=47, Class balance={1.0: 34, 0.0: 13}. Pattern AUC=0.8914, p-value=0.014499

 Pattern 78
    Support=29, Class balance={1.0: 8, 0.0: 21}. Pattern AUC=0.7917, p-value=0.000100

 Pattern 79
    Support=64, Class balance={1.0: 36, 0.0: 28}. Pattern AUC=0.8512, p-value=0.000100

 Pattern 80
    Support=77, Class balance={1.0: 36, 0.0: 41}. Pattern AUC=0.8638, p-value=0.000100

 Pattern 81
    Support=31, Class balance={1.0: 12, 0.0: 19}. Pattern AUC=0.8026, p-value=0.000100

 Pattern 82
    Support=72, Class balance={1.0: 29, 0.0: 43}. Pattern AUC=0.8669, p-value=0.000100

 Pattern 83
    Support=58, Class balance={1.0: 34, 0.0: 24}. Pattern AUC=0.8566, p-value=0.000100

 Pattern 84
    Support=32, Class balance={1.0: 12, 0.0: 20}. Pattern AUC=0.8000, p-value=0.000100

 Pattern 85
    Support=53, Class balance={1.0: 33, 0.0: 20}. Pattern AUC=0.8333, p-value=0.000100

 Pattern 86
    Support=66, Class balance={1.0: 36, 0.0: 30}. Pattern AUC=0.8611, p-value=0.000100

 Pattern 87
    Support=66, Class balance={1.0: 36, 0.0: 30}. Pattern AUC=0.8611, p-value=0.000100

 Pattern 88
    Support=50, Class balance={1.0: 30, 0.0: 20}. Pattern AUC=0.8317, p-value=0.000100

 Pattern 89
    Support=69, Class balance={1.0: 37, 0.0: 32}. Pattern AUC=0.8674, p-value=0.000100

 Pattern 90
    Support=45, Class balance={1.0: 33, 0.0: 12}. Pattern AUC=0.8510, p-value=0.001300

 Pattern 91
    Support=136, Class balance={1.0: 44, 0.0: 92}. Pattern AUC=0.9303, p-value=0.000100

 Pattern 92
    Support=82, Class balance={1.0: 42, 0.0: 40}. Pattern AUC=0.9048, p-value=0.000100

 Pattern 93
    Support=82, Class balance={1.0: 42, 0.0: 40}. Pattern AUC=0.9048, p-value=0.000200

 Pattern 94
    Support=110, Class balance={1.0: 39, 0.0: 71}. Pattern AUC=0.8978, p-value=0.000100

 Pattern 95
    Support=139, Class balance={1.0: 44, 0.0: 95}. Pattern AUC=0.9313, p-value=0.000100

 Pattern 96
    Support=139, Class balance={1.0: 44, 0.0: 95}. Pattern AUC=0.9313, p-value=0.000100

 Pattern 97
    Support=74, Class balance={1.0: 42, 0.0: 32}. Pattern AUC=0.8824, p-value=0.000100

 Pattern 98
    Support=77, Class balance={1.0: 42, 0.0: 35}. Pattern AUC=0.8925, p-value=0.000100

 Pattern 99
    Support=46, Class balance={1.0: 21, 0.0: 25}. Pattern AUC=0.8971, p-value=0.003700

 Applying FDR correction
  Pattern 0: AUC diff=0.2663, p=0.000700, adj_p=0.000864 --> SIGNIFICANT
  Pattern 1: AUC diff=0.2713, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 2: AUC diff=0.2502, p=0.006899, adj_p=0.007040 --> SIGNIFICANT
  Pattern 3: AUC diff=0.2811, p=0.003500, adj_p=0.003645 --> SIGNIFICANT
  Pattern 4: AUC diff=0.2663, p=0.000300, adj_p=0.000390 --> SIGNIFICANT
  Pattern 5: AUC diff=0.2333, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 6: AUC diff=0.2604, p=0.001500, adj_p=0.001648 --> SIGNIFICANT
  Pattern 7: AUC diff=0.2349, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 8: AUC diff=0.2155, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 9: AUC diff=0.2440, p=0.007999, adj_p=0.008080 --> SIGNIFICANT
  Pattern 10: AUC diff=0.2155, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 11: AUC diff=0.2451, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 12: AUC diff=0.2572, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 13: AUC diff=0.2451, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 14: AUC diff=0.2163, p=0.001100, adj_p=0.001309 --> SIGNIFICANT
  Pattern 15: AUC diff=0.2116, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 16: AUC diff=0.2058, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 17: AUC diff=0.1921, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 18: AUC diff=0.1740, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 19: AUC diff=0.1970, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 20: AUC diff=0.1903, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 21: AUC diff=0.2252, p=0.000300, adj_p=0.000390 --> SIGNIFICANT
  Pattern 22: AUC diff=0.1970, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 23: AUC diff=0.1970, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 24: AUC diff=0.2246, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 25: AUC diff=0.1761, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 26: AUC diff=0.1502, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 27: AUC diff=0.1948, p=0.000300, adj_p=0.000390 --> SIGNIFICANT
  Pattern 28: AUC diff=0.1843, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 29: AUC diff=0.1871, p=0.000300, adj_p=0.000390 --> SIGNIFICANT
  Pattern 30: AUC diff=0.1713, p=0.001400, adj_p=0.001555 --> SIGNIFICANT
  Pattern 31: AUC diff=0.1847, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 32: AUC diff=0.1643, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 33: AUC diff=0.1847, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 34: AUC diff=0.2020, p=0.000600, adj_p=0.000759 --> SIGNIFICANT
  Pattern 35: AUC diff=0.2020, p=0.000400, adj_p=0.000513 --> SIGNIFICANT
  Pattern 36: AUC diff=0.1383, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 37: AUC diff=0.1439, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 38: AUC diff=0.1906, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 39: AUC diff=0.1358, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 40: AUC diff=0.1448, p=0.001100, adj_p=0.001309 --> SIGNIFICANT
  Pattern 41: AUC diff=0.1448, p=0.001400, adj_p=0.001555 --> SIGNIFICANT
  Pattern 42: AUC diff=0.1444, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 43: AUC diff=0.1970, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 44: AUC diff=0.1579, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 45: AUC diff=0.1383, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 46: AUC diff=0.1383, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 47: AUC diff=0.1906, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 48: AUC diff=0.1383, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 49: AUC diff=0.1448, p=0.001300, adj_p=0.001494 --> SIGNIFICANT
  Pattern 50: AUC diff=0.1175, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 51: AUC diff=0.1409, p=0.001400, adj_p=0.001555 --> SIGNIFICANT
  Pattern 52: AUC diff=0.1280, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 53: AUC diff=0.1444, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 54: AUC diff=0.1551, p=0.000700, adj_p=0.000864 --> SIGNIFICANT
  Pattern 55: AUC diff=0.1126, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 56: AUC diff=0.1558, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 57: AUC diff=0.1366, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 58: AUC diff=0.0989, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 59: AUC diff=0.1448, p=0.001200, adj_p=0.001412 --> SIGNIFICANT
  Pattern 60: AUC diff=0.1448, p=0.001800, adj_p=0.001956 --> SIGNIFICANT
  Pattern 61: AUC diff=0.1420, p=0.000800, adj_p=0.000976 --> SIGNIFICANT
  Pattern 62: AUC diff=0.1663, p=0.002000, adj_p=0.002127 --> SIGNIFICANT
  Pattern 63: AUC diff=0.1696, p=0.000300, adj_p=0.000390 --> SIGNIFICANT
  Pattern 64: AUC diff=0.0691, p=0.003100, adj_p=0.003263 --> SIGNIFICANT
  Pattern 65: AUC diff=0.1175, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 66: AUC diff=0.1175, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 67: AUC diff=0.1126, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 68: AUC diff=0.1126, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 69: AUC diff=0.1753, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 70: AUC diff=0.1175, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 71: AUC diff=0.1383, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 72: AUC diff=0.0964, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 73: AUC diff=0.1126, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 74: AUC diff=0.1560, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 75: AUC diff=0.1292, p=0.001900, adj_p=0.002043 --> SIGNIFICANT
  Pattern 76: AUC diff=0.0665, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 77: AUC diff=0.0749, p=0.014499, adj_p=0.014499 --> SIGNIFICANT
  Pattern 78: AUC diff=0.1746, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 79: AUC diff=0.1151, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 80: AUC diff=0.1024, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 81: AUC diff=0.1636, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 82: AUC diff=0.0994, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 83: AUC diff=0.1096, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 84: AUC diff=0.1663, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 85: AUC diff=0.1329, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 86: AUC diff=0.1051, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 87: AUC diff=0.1051, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 88: AUC diff=0.1346, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 89: AUC diff=0.0989, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 90: AUC diff=0.1152, p=0.001300, adj_p=0.001494 --> SIGNIFICANT
  Pattern 91: AUC diff=0.0359, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 92: AUC diff=0.0615, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 93: AUC diff=0.0615, p=0.000200, adj_p=0.000278 --> SIGNIFICANT
  Pattern 94: AUC diff=0.0685, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 95: AUC diff=0.0349, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 96: AUC diff=0.0349, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 97: AUC diff=0.0838, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 98: AUC diff=0.0737, p=0.000100, adj_p=0.000154 --> SIGNIFICANT
  Pattern 99: AUC diff=0.0691, p=0.003700, adj_p=0.003814 --> SIGNIFICANT

 Found 100 significant patterns out of 100 tested.
  Validation completed in 1031.21 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=2.2467, ROC-AUC=0.7000, Support=25, Pattern={'23'}{'29'}{'46'}{'47'}{'52'}{'51'}{'51'}{'51'}{'53'}
  Pattern 1: Quality=2.1865, ROC-AUC=0.6950, Support=30, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 2: Quality=2.1342, ROC-AUC=0.7160, Support=30, Pattern={'29'}{'46'}{'47'}{'46'}{'51'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 3: Quality=2.1064, ROC-AUC=0.6852, Support=21, Pattern={'1'}{'13'}{'18'}{'19'}{'23'}{'46'}{'47'}{'52'}{'51'}{'52'}{'51'}{'54'}{'54'}{'54'}{'53'}
  Pattern 4: Quality=2.0328, ROC-AUC=0.7000, Support=25, Pattern={'1'}{'8'}{'18'}{'19'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 5: Quality=1.7576, ROC-AUC=0.7329, Support=37, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 6: Quality=1.7266, ROC-AUC=0.7059, Support=21, Pattern={'1'}{'8'}{'18'}{'19'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 7: Quality=1.6835, ROC-AUC=0.7314, Support=33, Pattern={'1'}{'8'}{'13'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 8: Quality=1.6443, ROC-AUC=0.7507, Support=38, Pattern={'13'}{'18'}{'18'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 9: Quality=1.6173, ROC-AUC=0.7222, Support=27, Pattern={'1'}{'8'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'47'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 10: Quality=1.5474, ROC-AUC=0.7507, Support=38, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 11: Quality=1.5466, ROC-AUC=0.7212, Support=21, Pattern={'8'}{'13'}{'17'}{'19'}{'23'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 12: Quality=1.5091, ROC-AUC=0.7091, Support=21, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 13: Quality=1.4983, ROC-AUC=0.7212, Support=21, Pattern={'8'}{'13'}{'18'}{'17'}{'19'}{'23'}{'25'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 14: Quality=1.4979, ROC-AUC=0.7500, Support=26, Pattern={'1'}{'46'}{'47'}{'46'}{'51'}{'52'}{'51'}{'51'}{'53'}
  Pattern 15: Quality=1.4660, ROC-AUC=0.7547, Support=40, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 16: Quality=1.3430, ROC-AUC=0.7604, Support=32, Pattern={'1'}{'13'}{'18'}{'19'}{'23'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'54'}{'54'}{'53'}
  Pattern 17: Quality=1.2222, ROC-AUC=0.7741, Support=42, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 18: Quality=1.1720, ROC-AUC=0.7923, Support=41, Pattern={'8'}{'16'}{'17'}{'46'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 19: Quality=1.1602, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'52'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 20: Quality=1.1478, ROC-AUC=0.7759, Support=36, Pattern={'8'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 21: Quality=1.1373, ROC-AUC=0.7411, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 22: Quality=1.1207, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 23: Quality=1.1022, ROC-AUC=0.7692, Support=35, Pattern={'1'}{'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 24: Quality=1.0958, ROC-AUC=0.7417, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 25: Quality=1.0646, ROC-AUC=0.7901, Support=45, Pattern={'8'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}
  Pattern 26: Quality=1.0545, ROC-AUC=0.8161, Support=48, Pattern={'29'}{'46'}{'51'}{'52'}{'51'}{'51'}{'54'}
  Pattern 27: Quality=1.0242, ROC-AUC=0.7714, Support=24, Pattern={'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 28: Quality=1.0225, ROC-AUC=0.7820, Support=34, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'25'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 29: Quality=1.0126, ROC-AUC=0.7792, Support=38, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 30: Quality=1.0084, ROC-AUC=0.7950, Support=33, Pattern={'13'}{'19'}{'23'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}{'54'}
  Pattern 31: Quality=0.9962, ROC-AUC=0.7815, Support=31, Pattern={'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 32: Quality=0.9641, ROC-AUC=0.8020, Support=47, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'53'}
  Pattern 33: Quality=0.9479, ROC-AUC=0.7815, Support=31, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 34: Quality=0.9369, ROC-AUC=0.7643, Support=27, Pattern={'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 35: Quality=0.9211, ROC-AUC=0.7643, Support=27, Pattern={'1'}{'8'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 36: Quality=0.9075, ROC-AUC=0.8279, Support=54, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'54'}{'54'}{'53'}
  Pattern 37: Quality=0.8751, ROC-AUC=0.8223, Support=47, Pattern={'8'}{'17'}{'46'}{'52'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 38: Quality=0.8717, ROC-AUC=0.7756, Support=25, Pattern={'1'}{'8'}{'17'}{'19'}{'23'}{'24'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 39: Quality=0.8709, ROC-AUC=0.8304, Support=48, Pattern={'17'}{'46'}{'51'}{'51'}{'51'}{'52'}{'54'}
  Pattern 40: Quality=0.8693, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}
  Pattern 41: Quality=0.8693, ROC-AUC=0.8214, Support=37, Pattern={'29'}{'46'}{'47'}{'51'}{'51'}{'54'}{'54'}
  Pattern 42: Quality=0.8654, ROC-AUC=0.8219, Support=53, Pattern={'13'}{'18'}{'19'}{'23'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}{'53'}
  Pattern 43: Quality=0.8474, ROC-AUC=0.7692, Support=24, Pattern={'1'}{'8'}{'18'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 44: Quality=0.8463, ROC-AUC=0.8083, Support=38, Pattern={'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}{'53'}{'54'}
  Pattern 45: Quality=0.8283, ROC-AUC=0.8279, Support=54, Pattern={'17'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}{'53'}{'54'}
  Pattern 46: Quality=0.8283, ROC-AUC=0.8279, Support=54, Pattern={'19'}{'24'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 47: Quality=0.8110, ROC-AUC=0.7756, Support=25, Pattern={'1'}{'18'}{'17'}{'19'}{'23'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'51'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 48: Quality=0.7935, ROC-AUC=0.8279, Support=54, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}{'52'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 49: Quality=0.7822, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'23'}{'29'}{'46'}{'47'}{'51'}{'51'}{'53'}{'54'}
  Pattern 50: Quality=0.7819, ROC-AUC=0.8487, Support=59, Pattern={'24'}{'29'}{'46'}{'51'}{'53'}{'53'}
  Pattern 51: Quality=0.7791, ROC-AUC=0.8254, Support=37, Pattern={'23'}{'29'}{'47'}{'46'}{'52'}{'52'}{'52'}{'54'}
  Pattern 52: Quality=0.7781, ROC-AUC=0.8382, Support=60, Pattern={'13'}{'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}
  Pattern 53: Quality=0.7752, ROC-AUC=0.8219, Support=53, Pattern={'8'}{'16'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}
  Pattern 54: Quality=0.7690, ROC-AUC=0.8111, Support=37, Pattern={'8'}{'18'}{'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'51'}{'54'}{'53'}{'53'}{'53'}
  Pattern 55: Quality=0.7615, ROC-AUC=0.8537, Support=66, Pattern={'19'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 56: Quality=0.7606, ROC-AUC=0.8105, Support=44, Pattern={'8'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}{'53'}
  Pattern 57: Quality=0.7469, ROC-AUC=0.8296, Support=47, Pattern={'1'}{'19'}{'23'}{'24'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 58: Quality=0.7459, ROC-AUC=0.8674, Support=69, Pattern={'29'}{'46'}{'51'}{'51'}
  Pattern 59: Quality=0.7444, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'24'}{'46'}{'47'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 60: Quality=0.7444, ROC-AUC=0.8214, Support=37, Pattern={'19'}{'23'}{'29'}{'46'}{'47'}{'46'}{'51'}{'51'}{'53'}{'54'}
  Pattern 61: Quality=0.7397, ROC-AUC=0.8242, Support=43, Pattern={'19'}{'23'}{'29'}{'46'}{'52'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 62: Quality=0.7382, ROC-AUC=0.8000, Support=31, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'47'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 63: Quality=0.7338, ROC-AUC=0.7967, Support=27, Pattern={'8'}{'24'}{'25'}{'24'}{'29'}{'46'}{'52'}{'52'}{'51'}{'52'}{'51'}{'54'}{'53'}{'54'}{'54'}
  Pattern 64: Quality=0.7320, ROC-AUC=0.8971, Support=46, Pattern={'40'}
  Pattern 65: Quality=0.7307, ROC-AUC=0.8487, Support=59, Pattern={'23'}{'29'}{'46'}{'51'}{'54'}{'54'}{'53'}
  Pattern 66: Quality=0.7307, ROC-AUC=0.8487, Support=59, Pattern={'24'}{'29'}{'46'}{'52'}{'51'}{'53'}{'53'}
  Pattern 67: Quality=0.7104, ROC-AUC=0.8537, Support=66, Pattern={'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}
  Pattern 68: Quality=0.7104, ROC-AUC=0.8537, Support=66, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'54'}{'53'}
  Pattern 69: Quality=0.7077, ROC-AUC=0.7909, Support=32, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 70: Quality=0.6850, ROC-AUC=0.8487, Support=59, Pattern={'17'}{'19'}{'23'}{'46'}{'51'}{'54'}{'53'}{'53'}
  Pattern 71: Quality=0.6770, ROC-AUC=0.8279, Support=54, Pattern={'1'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 72: Quality=0.6669, ROC-AUC=0.8699, Support=73, Pattern={'23'}{'51'}{'51'}{'51'}{'53'}
  Pattern 73: Quality=0.6646, ROC-AUC=0.8537, Support=66, Pattern={'23'}{'29'}{'46'}{'51'}{'51'}{'52'}{'54'}{'54'}
  Pattern 74: Quality=0.6605, ROC-AUC=0.8103, Support=34, Pattern={'8'}{'18'}{'18'}{'23'}{'24'}{'24'}{'27'}{'29'}{'51'}{'52'}{'51'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 75: Quality=0.6556, ROC-AUC=0.8370, Support=37, Pattern={'8'}{'46'}{'47'}{'52'}{'51'}{'51'}{'52'}{'53'}
  Pattern 76: Quality=0.6533, ROC-AUC=0.8997, Support=80, Pattern={'23'}{'46'}
  Pattern 77: Quality=0.6459, ROC-AUC=0.8914, Support=47, Pattern={'19'}{'47'}
  Pattern 78: Quality=0.6446, ROC-AUC=0.7917, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 79: Quality=0.6423, ROC-AUC=0.8512, Support=64, Pattern={'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 80: Quality=0.6401, ROC-AUC=0.8638, Support=77, Pattern={'23'}{'29'}{'51'}{'51'}{'54'}{'54'}{'53'}
  Pattern 81: Quality=0.6400, ROC-AUC=0.8026, Support=31, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'51'}{'52'}{'54'}{'53'}
  Pattern 82: Quality=0.6378, ROC-AUC=0.8669, Support=72, Pattern={'8'}{'23'}{'51'}{'51'}{'51'}{'53'}
  Pattern 83: Quality=0.6367, ROC-AUC=0.8566, Support=58, Pattern={'46'}{'51'}{'51'}{'52'}{'54'}{'54'}{'53'}
  Pattern 84: Quality=0.6291, ROC-AUC=0.8000, Support=32, Pattern={'8'}{'13'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'24'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 85: Quality=0.6262, ROC-AUC=0.8333, Support=53, Pattern={'18'}{'19'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}
  Pattern 86: Quality=0.6255, ROC-AUC=0.8611, Support=66, Pattern={'23'}{'29'}{'46'}{'52'}{'52'}{'52'}{'54'}
  Pattern 87: Quality=0.6255, ROC-AUC=0.8611, Support=66, Pattern={'19'}{'23'}{'46'}{'52'}{'52'}{'51'}{'54'}
  Pattern 88: Quality=0.6227, ROC-AUC=0.8317, Support=50, Pattern={'8'}{'13'}{'17'}{'18'}{'46'}{'52'}{'51'}{'52'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 89: Quality=0.6209, ROC-AUC=0.8674, Support=69, Pattern={'29'}{'46'}{'51'}{'52'}{'51'}{'54'}
  Pattern 90: Quality=0.6209, ROC-AUC=0.8510, Support=45, Pattern={'29'}{'46'}{'52'}{'54'}{'53'}{'53'}{'53'}
  Pattern 91: Quality=0.6200, ROC-AUC=0.9303, Support=136, Pattern={'23'}
  Pattern 92: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'46'}
  Pattern 93: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'29'}{'46'}
  Pattern 94: Quality=0.6183, ROC-AUC=0.8978, Support=110, Pattern={'29'}{'51'}{'51'}
  Pattern 95: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'29'}
  Pattern 96: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'19'}
  Pattern 97: Quality=0.6119, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'53'}
  Pattern 98: Quality=0.6090, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}
  Pattern 99: Quality=0.6071, ROC-AUC=0.8971, Support=46, Pattern={'29'}{'40'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=2.2467, ROC-AUC=0.7000, Support=25, Pattern={'23'}{'29'}{'46'}{'47'}{'52'}{'51'}{'51'}{'51'}{'53'}
  Pattern 1: Quality=2.1865, ROC-AUC=0.6950, Support=30, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 2: Quality=2.1342, ROC-AUC=0.7160, Support=30, Pattern={'29'}{'46'}{'47'}{'46'}{'51'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 3: Quality=1.5466, ROC-AUC=0.7212, Support=21, Pattern={'8'}{'13'}{'17'}{'19'}{'23'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
  Pattern 4: Quality=1.0958, ROC-AUC=0.7417, Support=22, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 5: Quality=1.0242, ROC-AUC=0.7714, Support=24, Pattern={'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
  Pattern 6: Quality=0.9369, ROC-AUC=0.7643, Support=27, Pattern={'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
  Pattern 7: Quality=0.7781, ROC-AUC=0.8382, Support=60, Pattern={'13'}{'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}
  Pattern 8: Quality=0.7606, ROC-AUC=0.8105, Support=44, Pattern={'8'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}{'53'}
  Pattern 9: Quality=0.7320, ROC-AUC=0.8971, Support=46, Pattern={'40'}
  Pattern 10: Quality=0.6669, ROC-AUC=0.8699, Support=73, Pattern={'23'}{'51'}{'51'}{'51'}{'53'}
  Pattern 11: Quality=0.6446, ROC-AUC=0.7917, Support=29, Pattern={'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
================================================================================

Quality: 2.2466615416689772, Extent: 25, ROCAUC: 0.7, Pattern: {'23'}{'29'}{'46'}{'47'}{'52'}{'51'}{'51'}{'51'}{'53'}
Quality: 2.1864844111947637, Extent: 30, ROCAUC: 0.6950000000000001, Pattern: {'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
Quality: 2.1341984039232296, Extent: 30, ROCAUC: 0.7160493827160495, Pattern: {'29'}{'46'}{'47'}{'46'}{'51'}{'53'}{'54'}{'53'}{'53'}{'54'}
Quality: 1.5466093721617753, Extent: 21, ROCAUC: 0.7211538461538461, Pattern: {'8'}{'13'}{'17'}{'19'}{'23'}{'27'}{'29'}{'52'}{'51'}{'52'}{'54'}{'53'}{'53'}{'54'}{'53'}
Quality: 1.095807255065437, Extent: 22, ROCAUC: 0.7416666666666667, Pattern: {'1'}{'8'}{'13'}{'16'}{'18'}{'17'}{'18'}{'19'}{'23'}{'24'}{'25'}{'24'}{'27'}{'29'}{'46'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
Quality: 1.0242492559611418, Extent: 24, ROCAUC: 0.7714285714285714, Pattern: {'1'}{'19'}{'23'}{'25'}{'29'}{'46'}{'51'}{'51'}{'53'}{'53'}{'54'}{'53'}{'54'}
Quality: 0.9368543566675447, Extent: 27, ROCAUC: 0.7642857142857142, Pattern: {'1'}{'13'}{'14'}{'16'}{'15'}{'18'}{'17'}{'18'}{'17'}{'19'}{'23'}{'24'}{'29'}{'46'}{'49'}{'52'}{'51'}{'52'}{'51'}{'52'}{'54'}{'53'}{'54'}{'53'}{'54'}
Quality: 0.7780846274039671, Extent: 60, ROCAUC: 0.8382352941176471, Pattern: {'13'}{'19'}{'23'}{'29'}{'46'}{'51'}{'51'}{'53'}{'54'}
Quality: 0.760574111879539, Extent: 44, ROCAUC: 0.8104575163398693, Pattern: {'8'}{'13'}{'16'}{'18'}{'17'}{'19'}{'23'}{'29'}{'51'}{'52'}{'51'}{'52'}{'54'}{'54'}{'53'}{'54'}{'53'}
Quality: 0.7320040618443311, Extent: 46, ROCAUC: 0.8971428571428571, Pattern: {'40'}
```



</details>

<details>
  <summary>Com max size = 6</summary>
  
`ipython3 -c "from mctsextent.main import get_patterns;get_patterns(filename='emm_context', time_budget=2000, top_k=10, theta=0.5, iterations_limit=1000)"`

```
================
ALL PATTERNS
================
  Pattern 0: Quality=1.2871, ROC-AUC=0.7857, Support=32, Pattern={'47'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 1: Quality=0.8649, ROC-AUC=0.8389, Support=29, Pattern={'40'}{'46'}{'54'}
  Pattern 2: Quality=0.7819, ROC-AUC=0.8487, Support=59, Pattern={'19'}{'29'}{'46'}{'51'}{'53'}{'53'}
  Pattern 3: Quality=0.7320, ROC-AUC=0.8971, Support=46, Pattern={'40'}
  Pattern 4: Quality=0.6999, ROC-AUC=0.8889, Support=21, Pattern={'43'}
  Pattern 5: Quality=0.6669, ROC-AUC=0.8743, Support=45, Pattern={'19'}{'47'}{'51'}
  Pattern 6: Quality=0.6200, ROC-AUC=0.9303, Support=136, Pattern={'23'}
  Pattern 7: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'29'}{'46'}
  Pattern 8: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'19'}
  Pattern 9: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'29'}
  Pattern 10: Quality=0.6127, ROC-AUC=0.9199, Support=42, Pattern={'45'}
  Pattern 11: Quality=0.6090, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}
  Pattern 12: Quality=0.6071, ROC-AUC=0.8971, Support=46, Pattern={'19'}{'40'}
  Pattern 13: Quality=0.6062, ROC-AUC=0.9241, Support=53, Pattern={'47'}
  Pattern 14: Quality=0.5943, ROC-AUC=0.8673, Support=62, Pattern={'19'}{'23'}{'29'}{'46'}{'53'}{'53'}
  Pattern 15: Quality=0.5943, ROC-AUC=0.8673, Support=62, Pattern={'23'}{'29'}{'46'}{'53'}{'54'}{'53'}
  Pattern 16: Quality=0.5902, ROC-AUC=0.8786, Support=77, Pattern={'19'}{'29'}{'51'}{'51'}{'51'}
  Pattern 17: Quality=0.5878, ROC-AUC=0.8743, Support=45, Pattern={'19'}{'47'}{'52'}{'51'}
  Pattern 18: Quality=0.5819, ROC-AUC=0.8860, Support=75, Pattern={'23'}{'29'}{'46'}{'51'}
  Pattern 19: Quality=0.5819, ROC-AUC=0.8978, Support=86, Pattern={'51'}{'51'}{'51'}
  Pattern 20: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'23'}{'29'}{'46'}
  Pattern 21: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'23'}{'46'}{'54'}
  Pattern 22: Quality=0.5750, ROC-AUC=0.8889, Support=21, Pattern={'40'}{'43'}
  Pattern 23: Quality=0.5735, ROC-AUC=0.9039, Support=49, Pattern={'47'}{'53'}
  Pattern 24: Quality=0.5546, ROC-AUC=0.8894, Support=76, Pattern={'29'}{'46'}{'52'}{'52'}
  Pattern 25: Quality=0.5490, ROC-AUC=0.8914, Support=47, Pattern={'23'}{'29'}{'47'}
  Pattern 26: Quality=0.5469, ROC-AUC=0.9207, Support=124, Pattern={'23'}{'51'}
  Pattern 27: Quality=0.5450, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'52'}{'53'}
  Pattern 28: Quality=0.5450, ROC-AUC=0.8824, Support=74, Pattern={'23'}{'29'}{'46'}{'52'}{'51'}
  Pattern 29: Quality=0.5445, ROC-AUC=0.9213, Support=126, Pattern={'19'}{'51'}
  Pattern 30: Quality=0.5445, ROC-AUC=0.9213, Support=126, Pattern={'29'}{'51'}
  Pattern 31: Quality=0.5413, ROC-AUC=0.8912, Support=77, Pattern={'23'}{'29'}{'46'}{'53'}
  Pattern 32: Quality=0.5391, ROC-AUC=0.8978, Support=110, Pattern={'19'}{'29'}{'51'}{'51'}
  Pattern 33: Quality=0.5368, ROC-AUC=0.8941, Support=88, Pattern={'23'}{'52'}{'53'}{'53'}
  Pattern 34: Quality=0.5354, ROC-AUC=0.9228, Support=127, Pattern={'23'}{'52'}
  Pattern 35: Quality=0.5343, ROC-AUC=0.8903, Support=104, Pattern={'18'}{'23'}{'51'}{'51'}{'53'}
  Pattern 36: Quality=0.5343, ROC-AUC=0.8903, Support=104, Pattern={'23'}{'29'}{'51'}{'51'}{'53'}
  Pattern 37: Quality=0.5332, ROC-AUC=0.8782, Support=76, Pattern={'23'}{'29'}{'51'}{'51'}{'52'}{'51'}
  Pattern 38: Quality=0.5319, ROC-AUC=0.9551, Support=128, Pattern={'46'}
  Pattern 39: Quality=0.5298, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}{'52'}
  Pattern 40: Quality=0.5221, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'29'}{'46'}
  Pattern 41: Quality=0.5159, ROC-AUC=0.8970, Support=90, Pattern={'29'}{'52'}{'53'}{'53'}
  Pattern 42: Quality=0.5157, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'53'}
  Pattern 43: Quality=0.5100, ROC-AUC=0.9275, Support=134, Pattern={'29'}{'53'}
  Pattern 44: Quality=0.5034, ROC-AUC=0.9098, Support=97, Pattern={'29'}{'53'}{'53'}
  Pattern 45: Quality=0.5028, ROC-AUC=0.9288, Support=134, Pattern={'23'}{'54'}
  Pattern 46: Quality=0.4999, ROC-AUC=0.8880, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'53'}
  Pattern 47: Quality=0.4989, ROC-AUC=0.9296, Support=135, Pattern={'23'}{'29'}
  Pattern 48: Quality=0.4978, ROC-AUC=0.9199, Support=52, Pattern={'47'}{'54'}
  Pattern 49: Quality=0.4967, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'23'}{'29'}{'46'}
  Pattern 50: Quality=0.4967, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'29'}{'46'}{'53'}
  Pattern 51: Quality=0.4943, ROC-AUC=0.9306, Support=138, Pattern={'29'}{'54'}
  Pattern 52: Quality=0.4907, ROC-AUC=0.9313, Support=139, Pattern={'19'}{'29'}
  Pattern 53: Quality=0.4903, ROC-AUC=0.8790, Support=64, Pattern={'24'}{'46'}{'51'}{'54'}{'53'}{'53'}
  Pattern 54: Quality=0.4894, ROC-AUC=0.8853, Support=40, Pattern={'47'}{'53'}{'54'}{'53'}
  Pattern 55: Quality=0.4878, ROC-AUC=0.9199, Support=42, Pattern={'40'}{'45'}
  Pattern 56: Quality=0.4877, ROC-AUC=0.8894, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'52'}
  Pattern 57: Quality=0.4875, ROC-AUC=0.9325, Support=148, Pattern={'51'}{'51'}
  Pattern 58: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'23'}{'29'}{'46'}{'52'}{'51'}
  Pattern 59: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'29'}{'46'}{'51'}{'52'}{'53'}
  Pattern 60: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'52'}{'53'}{'54'}
  Pattern 61: Quality=0.4833, ROC-AUC=0.9234, Support=52, Pattern={'46'}{'47'}
  Pattern 62: Quality=0.4813, ROC-AUC=0.9241, Support=53, Pattern={'17'}{'47'}
  Pattern 63: Quality=0.4813, ROC-AUC=0.9241, Support=53, Pattern={'47'}{'46'}
  Pattern 64: Quality=0.4795, ROC-AUC=0.8967, Support=108, Pattern={'23'}{'29'}{'51'}{'52'}{'51'}
  Pattern 65: Quality=0.4768, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'53'}
  Pattern 66: Quality=0.4763, ROC-AUC=0.8903, Support=104, Pattern={'19'}{'23'}{'29'}{'51'}{'51'}{'53'}
  Pattern 67: Quality=0.4744, ROC-AUC=0.8912, Support=77, Pattern={'19'}{'23'}{'29'}{'46'}{'53'}
  Pattern 68: Quality=0.4699, ROC-AUC=0.8941, Support=88, Pattern={'1'}{'23'}{'52'}{'53'}{'53'}
  Pattern 69: Quality=0.4698, ROC-AUC=0.8914, Support=47, Pattern={'23'}{'47'}{'46'}{'54'}
  Pattern 70: Quality=0.4661, ROC-AUC=0.9299, Support=64, Pattern={'23'}{'49'}
  Pattern 71: Quality=0.4594, ROC-AUC=0.9193, Support=124, Pattern={'29'}{'51'}{'52'}
  Pattern 72: Quality=0.4592, ROC-AUC=0.8708, Support=38, Pattern={'23'}{'46'}{'47'}{'46'}{'53'}{'53'}
  Pattern 73: Quality=0.4590, ROC-AUC=0.9195, Support=125, Pattern={'29'}{'52'}{'53'}
  Pattern 74: Quality=0.4560, ROC-AUC=0.9197, Support=123, Pattern={'23'}{'29'}{'51'}
  Pattern 75: Quality=0.4558, ROC-AUC=0.8819, Support=26, Pattern={'40'}{'45'}{'46'}{'54'}
  Pattern 76: Quality=0.4476, ROC-AUC=0.9213, Support=126, Pattern={'19'}{'29'}{'51'}
  Pattern 77: Quality=0.4440, ROC-AUC=0.9218, Support=126, Pattern={'19'}{'23'}{'52'}
  Pattern 78: Quality=0.4429, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'29'}{'46'}{'54'}
  Pattern 79: Quality=0.4429, ROC-AUC=0.9048, Support=82, Pattern={'18'}{'17'}{'19'}{'46'}
  Pattern 80: Quality=0.4419, ROC-AUC=0.8880, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'54'}{'54'}
  Pattern 81: Quality=0.4403, ROC-AUC=0.8905, Support=86, Pattern={'19'}{'23'}{'51'}{'53'}{'54'}{'54'}
  Pattern 82: Quality=0.4403, ROC-AUC=0.8905, Support=86, Pattern={'1'}{'23'}{'29'}{'51'}{'53'}{'53'}
  Pattern 83: Quality=0.4389, ROC-AUC=0.8912, Support=61, Pattern={'19'}{'53'}{'54'}{'53'}{'53'}
  Pattern 84: Quality=0.4366, ROC-AUC=0.9118, Support=50, Pattern={'47'}{'51'}{'52'}
  Pattern 85: Quality=0.4365, ROC-AUC=0.9423, Support=108, Pattern={'46'}{'51'}
  Pattern 86: Quality=0.4315, ROC-AUC=0.9242, Support=130, Pattern={'19'}{'29'}{'52'}
  Pattern 87: Quality=0.4310, ROC-AUC=0.8971, Support=46, Pattern={'23'}{'40'}{'53'}{'54'}
  Pattern 88: Quality=0.4309, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'53'}
  Pattern 89: Quality=0.4281, ROC-AUC=0.8845, Support=59, Pattern={'19'}{'23'}{'29'}{'53'}{'53'}{'53'}
  Pattern 90: Quality=0.4265, ROC-AUC=0.9352, Support=21, Pattern={'19'}{'56'}
  Pattern 91: Quality=0.4265, ROC-AUC=0.9352, Support=21, Pattern={'29'}{'56'}
  Pattern 92: Quality=0.4258, ROC-AUC=0.8898, Support=76, Pattern={'46'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 93: Quality=0.4224, ROC-AUC=0.9128, Support=118, Pattern={'29'}{'52'}{'52'}{'53'}
  Pattern 94: Quality=0.4220, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'53'}
  Pattern 95: Quality=0.4200, ROC-AUC=0.9123, Support=40, Pattern={'40'}{'45'}{'52'}
  Pattern 96: Quality=0.4196, ROC-AUC=0.8983, Support=79, Pattern={'24'}{'46'}{'51'}{'54'}{'53'}
  Pattern 97: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'53'}{'54'}
  Pattern 98: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'53'}
  Pattern 99: Quality=0.4155, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'53'}
  Pattern 100: Quality=0.4146, ROC-AUC=0.9139, Support=119, Pattern={'29'}{'51'}{'52'}{'53'}
  Pattern 101: Quality=0.4131, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'29'}{'53'}
  Pattern 102: Quality=0.4131, ROC-AUC=0.9275, Support=134, Pattern={'24'}{'29'}{'53'}
  Pattern 103: Quality=0.4131, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'53'}{'54'}
  Pattern 104: Quality=0.4131, ROC-AUC=0.9275, Support=134, Pattern={'29'}{'53'}{'54'}
  Pattern 105: Quality=0.4117, ROC-AUC=0.9524, Support=123, Pattern={'46'}{'54'}
  Pattern 106: Quality=0.4106, ROC-AUC=0.9530, Support=124, Pattern={'46'}{'52'}
  Pattern 107: Quality=0.4095, ROC-AUC=0.9549, Support=189, Pattern={'51'}{'54'}
  Pattern 108: Quality=0.4083, ROC-AUC=0.9555, Support=191, Pattern={'52'}{'51'}
  Pattern 109: Quality=0.4078, ROC-AUC=0.9558, Support=192, Pattern={'51'}{'52'}
  Pattern 110: Quality=0.4070, ROC-AUC=0.9551, Support=128, Pattern={'17'}{'46'}
  Pattern 111: Quality=0.4036, ROC-AUC=0.9155, Support=119, Pattern={'23'}{'29'}{'51'}{'53'}
  Pattern 112: Quality=0.4020, ROC-AUC=0.9296, Support=135, Pattern={'19'}{'23'}{'29'}
  Pattern 113: Quality=0.3999, ROC-AUC=0.9162, Support=121, Pattern={'29'}{'51'}{'53'}{'54'}
  Pattern 114: Quality=0.3989, ROC-AUC=0.8889, Support=21, Pattern={'17'}{'40'}{'43'}{'54'}
  Pattern 115: Quality=0.3958, ROC-AUC=0.9168, Support=121, Pattern={'1'}{'23'}{'52'}{'53'}
  Pattern 116: Quality=0.3948, ROC-AUC=0.9103, Support=73, Pattern={'46'}{'53'}{'53'}{'54'}
  Pattern 117: Quality=0.3938, ROC-AUC=0.9313, Support=139, Pattern={'19'}{'24'}{'29'}
  Pattern 118: Quality=0.3918, ROC-AUC=0.9299, Support=113, Pattern={'51'}{'53'}{'53'}
  Pattern 119: Quality=0.3909, ROC-AUC=0.9199, Support=42, Pattern={'19'}{'40'}{'45'}
  Pattern 120: Quality=0.3906, ROC-AUC=0.9325, Support=148, Pattern={'18'}{'51'}{'51'}
  Pattern 121: Quality=0.3831, ROC-AUC=0.9187, Support=122, Pattern={'23'}{'29'}{'52'}{'51'}
  Pattern 122: Quality=0.3799, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'54'}{'54'}
  Pattern 123: Quality=0.3799, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'53'}{'54'}
  Pattern 124: Quality=0.3798, ROC-AUC=0.9195, Support=125, Pattern={'19'}{'29'}{'52'}{'53'}
  Pattern 125: Quality=0.3798, ROC-AUC=0.9195, Support=125, Pattern={'29'}{'52'}{'53'}{'54'}
  Pattern 126: Quality=0.3769, ROC-AUC=0.9014, Support=67, Pattern={'13'}{'46'}{'54'}{'53'}{'53'}
  Pattern 127: Quality=0.3768, ROC-AUC=0.9197, Support=123, Pattern={'19'}{'23'}{'29'}{'51'}
  Pattern 128: Quality=0.3742, ROC-AUC=0.9203, Support=125, Pattern={'19'}{'29'}{'51'}{'54'}
  Pattern 129: Quality=0.3718, ROC-AUC=0.8970, Support=79, Pattern={'17'}{'19'}{'23'}{'29'}{'46'}{'54'}
  Pattern 130: Quality=0.3705, ROC-AUC=0.9209, Support=125, Pattern={'19'}{'23'}{'52'}{'54'}
  Pattern 131: Quality=0.3695, ROC-AUC=0.9079, Support=95, Pattern={'19'}{'23'}{'29'}{'53'}{'53'}
  Pattern 132: Quality=0.3690, ROC-AUC=0.8971, Support=48, Pattern={'18'}{'47'}{'52'}{'53'}{'54'}
  Pattern 133: Quality=0.3674, ROC-AUC=0.9174, Support=89, Pattern={'18'}{'46'}{'51'}{'51'}
  Pattern 134: Quality=0.3648, ROC-AUC=0.9218, Support=126, Pattern={'19'}{'23'}{'29'}{'52'}
  Pattern 135: Quality=0.3648, ROC-AUC=0.9218, Support=126, Pattern={'8'}{'18'}{'23'}{'52'}
  Pattern 136: Quality=0.3599, ROC-AUC=0.9110, Support=49, Pattern={'46'}{'47'}{'51'}{'52'}
  Pattern 137: Quality=0.3574, ROC-AUC=0.9233, Support=129, Pattern={'19'}{'29'}{'52'}{'54'}
  Pattern 138: Quality=0.3530, ROC-AUC=0.9348, Support=66, Pattern={'19'}{'29'}{'49'}
  Pattern 139: Quality=0.3515, ROC-AUC=0.9386, Support=104, Pattern={'46'}{'51'}{'54'}
  Pattern 140: Quality=0.3485, ROC-AUC=0.8904, Support=46, Pattern={'18'}{'17'}{'19'}{'46'}{'47'}{'46'}
  Pattern 141: Quality=0.3484, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'53'}{'53'}
  Pattern 142: Quality=0.3483, ROC-AUC=0.9395, Support=105, Pattern={'46'}{'52'}{'51'}
  Pattern 143: Quality=0.3476, ROC-AUC=0.9139, Support=119, Pattern={'29'}{'51'}{'52'}{'53'}{'54'}
  Pattern 144: Quality=0.3476, ROC-AUC=0.9139, Support=119, Pattern={'19'}{'29'}{'51'}{'52'}{'53'}
  Pattern 145: Quality=0.3452, ROC-AUC=0.9405, Support=106, Pattern={'46'}{'51'}{'52'}
  Pattern 146: Quality=0.3438, ROC-AUC=0.9306, Support=27, Pattern={'29'}{'47'}{'48'}
  Pattern 147: Quality=0.3420, ROC-AUC=0.9152, Support=124, Pattern={'52'}{'51'}{'52'}{'51'}{'53'}
  Pattern 148: Quality=0.3414, ROC-AUC=0.9441, Support=161, Pattern={'52'}{'51'}{'53'}
  Pattern 149: Quality=0.3411, ROC-AUC=0.9223, Support=91, Pattern={'46'}{'51'}{'54'}{'53'}
  Pattern 150: Quality=0.3408, ROC-AUC=0.9123, Support=40, Pattern={'23'}{'40'}{'45'}{'52'}
  Pattern 151: Quality=0.3402, ROC-AUC=0.9151, Support=120, Pattern={'8'}{'24'}{'29'}{'51'}{'53'}
  Pattern 152: Quality=0.3398, ROC-AUC=0.9445, Support=162, Pattern={'51'}{'52'}{'53'}
  Pattern 153: Quality=0.3396, ROC-AUC=0.9306, Support=22, Pattern={'47'}{'47'}{'54'}
  Pattern 154: Quality=0.3396, ROC-AUC=0.9306, Support=22, Pattern={'47'}{'47'}{'51'}
  Pattern 155: Quality=0.3396, ROC-AUC=0.9263, Support=131, Pattern={'19'}{'23'}{'29'}{'53'}
  Pattern 156: Quality=0.3396, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'54'}{'54'}
  Pattern 157: Quality=0.3366, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'51'}{'53'}{'54'}
  Pattern 158: Quality=0.3366, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'29'}{'51'}{'53'}
  Pattern 159: Quality=0.3354, ROC-AUC=0.9459, Support=165, Pattern={'8'}{'51'}{'53'}
  Pattern 160: Quality=0.3340, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'54'}{'53'}
  Pattern 161: Quality=0.3340, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'53'}{'54'}
  Pattern 162: Quality=0.3331, ROC-AUC=0.9165, Support=124, Pattern={'24'}{'52'}{'51'}{'51'}{'52'}
  Pattern 163: Quality=0.3305, ROC-AUC=0.9039, Support=49, Pattern={'8'}{'18'}{'47'}{'54'}{'54'}
  Pattern 164: Quality=0.3298, ROC-AUC=0.9173, Support=128, Pattern={'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 165: Quality=0.3296, ROC-AUC=0.9352, Support=21, Pattern={'51'}{'54'}{'56'}
  Pattern 166: Quality=0.3285, ROC-AUC=0.9406, Support=42, Pattern={'29'}{'47'}{'49'}
  Pattern 167: Quality=0.3251, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'54'}{'53'}
  Pattern 168: Quality=0.3251, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'53'}{'54'}
  Pattern 169: Quality=0.3235, ROC-AUC=0.9299, Support=142, Pattern={'18'}{'52'}{'51'}{'51'}
  Pattern 170: Quality=0.3235, ROC-AUC=0.9299, Support=142, Pattern={'52'}{'51'}{'52'}{'51'}
  Pattern 171: Quality=0.3229, ROC-AUC=0.9016, Support=70, Pattern={'46'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 172: Quality=0.3227, ROC-AUC=0.9177, Support=121, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}
  Pattern 173: Quality=0.3221, ROC-AUC=0.9178, Support=122, Pattern={'19'}{'23'}{'29'}{'52'}{'53'}
  Pattern 174: Quality=0.3194, ROC-AUC=0.9517, Support=179, Pattern={'8'}{'24'}{'53'}
  Pattern 175: Quality=0.3194, ROC-AUC=0.9517, Support=181, Pattern={'1'}{'52'}{'53'}
  Pattern 176: Quality=0.3192, ROC-AUC=0.9412, Support=20, Pattern={'47'}{'47'}{'49'}
  Pattern 177: Quality=0.3185, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'53'}{'54'}
  Pattern 178: Quality=0.3185, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'54'}{'53'}
  Pattern 179: Quality=0.3185, ROC-AUC=0.9520, Support=180, Pattern={'24'}{'53'}{'54'}
  Pattern 180: Quality=0.3182, ROC-AUC=0.9306, Support=138, Pattern={'19'}{'24'}{'29'}{'54'}
  Pattern 181: Quality=0.3161, ROC-AUC=0.9187, Support=122, Pattern={'23'}{'24'}{'29'}{'52'}{'51'}
  Pattern 182: Quality=0.3161, ROC-AUC=0.9187, Support=122, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}
  Pattern 183: Quality=0.3159, ROC-AUC=0.9532, Support=184, Pattern={'52'}{'51'}{'54'}
  Pattern 184: Quality=0.3151, ROC-AUC=0.9536, Support=185, Pattern={'51'}{'52'}{'54'}
  Pattern 185: Quality=0.3145, ROC-AUC=0.9539, Support=186, Pattern={'8'}{'52'}{'52'}
  Pattern 186: Quality=0.3138, ROC-AUC=0.9542, Support=187, Pattern={'52'}{'51'}{'52'}
  Pattern 187: Quality=0.3133, ROC-AUC=0.9193, Support=124, Pattern={'18'}{'24'}{'29'}{'51'}{'52'}
  Pattern 188: Quality=0.3123, ROC-AUC=0.9301, Support=115, Pattern={'8'}{'25'}{'52'}{'52'}
  Pattern 189: Quality=0.3122, ROC-AUC=0.9550, Support=188, Pattern={'8'}{'13'}{'51'}
  Pattern 190: Quality=0.3120, ROC-AUC=0.9113, Support=122, Pattern={'1'}{'51'}{'52'}{'52'}{'54'}{'54'}
  Pattern 191: Quality=0.3114, ROC-AUC=0.9325, Support=148, Pattern={'18'}{'51'}{'52'}{'51'}
  Pattern 192: Quality=0.3114, ROC-AUC=0.9555, Support=191, Pattern={'18'}{'52'}{'51'}
  Pattern 193: Quality=0.3098, ROC-AUC=0.9197, Support=123, Pattern={'17'}{'19'}{'23'}{'29'}{'51'}
  Pattern 194: Quality=0.3094, ROC-AUC=0.9157, Support=88, Pattern={'17'}{'18'}{'46'}{'51'}{'51'}
  Pattern 195: Quality=0.3072, ROC-AUC=0.9203, Support=125, Pattern={'19'}{'24'}{'29'}{'51'}{'54'}
  Pattern 196: Quality=0.3049, ROC-AUC=0.9085, Support=93, Pattern={'17'}{'18'}{'19'}{'25'}{'29'}{'51'}
  Pattern 197: Quality=0.3007, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'54'}{'53'}{'54'}
  Pattern 198: Quality=0.3005, ROC-AUC=0.9174, Support=89, Pattern={'18'}{'46'}{'51'}{'52'}{'51'}
  Pattern 199: Quality=0.2978, ROC-AUC=0.9218, Support=126, Pattern={'18'}{'19'}{'23'}{'29'}{'52'}
  Pattern 200: Quality=0.2939, ROC-AUC=0.9131, Support=117, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}{'53'}
  Pattern 201: Quality=0.2929, ROC-AUC=0.9110, Support=49, Pattern={'46'}{'47'}{'46'}{'52'}{'51'}
  Pattern 202: Quality=0.2929, ROC-AUC=0.9110, Support=49, Pattern={'46'}{'47'}{'46'}{'51'}{'52'}
  Pattern 203: Quality=0.2862, ROC-AUC=0.9361, Support=120, Pattern={'24'}{'52'}{'53'}{'53'}
  Pattern 204: Quality=0.2861, ROC-AUC=0.9143, Support=118, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'53'}
  Pattern 205: Quality=0.2861, ROC-AUC=0.9143, Support=118, Pattern={'1'}{'18'}{'23'}{'52'}{'52'}{'54'}
  Pattern 206: Quality=0.2861, ROC-AUC=0.9143, Support=118, Pattern={'23'}{'29'}{'52'}{'51'}{'54'}{'53'}
  Pattern 207: Quality=0.2798, ROC-AUC=0.9257, Support=138, Pattern={'17'}{'51'}{'51'}{'52'}{'54'}
  Pattern 208: Quality=0.2795, ROC-AUC=0.9365, Support=102, Pattern={'46'}{'51'}{'52'}{'54'}
  Pattern 209: Quality=0.2786, ROC-AUC=0.9155, Support=119, Pattern={'19'}{'23'}{'29'}{'51'}{'54'}{'53'}
  Pattern 210: Quality=0.2774, ROC-AUC=0.9319, Support=53, Pattern={'49'}{'53'}{'54'}{'53'}
  Pattern 211: Quality=0.2758, ROC-AUC=0.9375, Support=103, Pattern={'46'}{'52'}{'51'}{'52'}
  Pattern 212: Quality=0.2727, ROC-AUC=0.9263, Support=131, Pattern={'19'}{'23'}{'29'}{'54'}{'53'}
  Pattern 213: Quality=0.2715, ROC-AUC=0.9166, Support=120, Pattern={'19'}{'23'}{'29'}{'51'}{'52'}{'54'}
  Pattern 214: Quality=0.2715, ROC-AUC=0.9166, Support=120, Pattern={'19'}{'23'}{'29'}{'52'}{'51'}{'52'}
  Pattern 215: Quality=0.2693, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'54'}{'53'}{'53'}
  Pattern 216: Quality=0.2693, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'53'}{'53'}{'54'}
  Pattern 217: Quality=0.2691, ROC-AUC=0.9421, Support=157, Pattern={'52'}{'51'}{'52'}{'53'}
  Pattern 218: Quality=0.2681, ROC-AUC=0.9172, Support=122, Pattern={'18'}{'29'}{'52'}{'51'}{'52'}{'54'}
  Pattern 219: Quality=0.2670, ROC-AUC=0.9275, Support=134, Pattern={'19'}{'24'}{'29'}{'53'}{'54'}
  Pattern 220: Quality=0.2643, ROC-AUC=0.9434, Support=158, Pattern={'24'}{'52'}{'51'}{'54'}
  Pattern 221: Quality=0.2641, ROC-AUC=0.9178, Support=122, Pattern={'19'}{'23'}{'29'}{'52'}{'53'}{'54'}
  Pattern 222: Quality=0.2622, ROC-AUC=0.9441, Support=161, Pattern={'52'}{'51'}{'53'}{'54'}
  Pattern 223: Quality=0.2606, ROC-AUC=0.9445, Support=162, Pattern={'51'}{'52'}{'53'}{'54'}
  Pattern 224: Quality=0.2606, ROC-AUC=0.9445, Support=162, Pattern={'18'}{'51'}{'52'}{'53'}
  Pattern 225: Quality=0.2601, ROC-AUC=0.9268, Support=110, Pattern={'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 226: Quality=0.2598, ROC-AUC=0.9288, Support=134, Pattern={'19'}{'23'}{'24'}{'29'}{'54'}
  Pattern 227: Quality=0.2574, ROC-AUC=0.9212, Support=61, Pattern={'19'}{'23'}{'29'}{'49'}{'53'}
  Pattern 228: Quality=0.2572, ROC-AUC=0.9258, Support=94, Pattern={'46'}{'52'}{'54'}{'53'}{'54'}
  Pattern 229: Quality=0.2572, ROC-AUC=0.9258, Support=94, Pattern={'17'}{'46'}{'52'}{'53'}{'54'}
  Pattern 230: Quality=0.2548, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'54'}{'53'}{'54'}
  Pattern 231: Quality=0.2525, ROC-AUC=0.9460, Support=134, Pattern={'13'}{'54'}{'53'}{'53'}
  Pattern 232: Quality=0.2504, ROC-AUC=0.9352, Support=21, Pattern={'23'}{'52'}{'51'}{'56'}
  Pattern 233: Quality=0.2493, ROC-AUC=0.9406, Support=42, Pattern={'23'}{'47'}{'49'}{'54'}
  Pattern 234: Quality=0.2474, ROC-AUC=0.9211, Support=131, Pattern={'8'}{'17'}{'24'}{'51'}{'52'}{'51'}
  Pattern 235: Quality=0.2473, ROC-AUC=0.9480, Support=139, Pattern={'17'}{'54'}{'53'}{'53'}
  Pattern 236: Quality=0.2457, ROC-AUC=0.9299, Support=113, Pattern={'51'}{'54'}{'53'}{'54'}{'54'}
  Pattern 237: Quality=0.2446, ROC-AUC=0.9480, Support=112, Pattern={'13'}{'46'}{'52'}{'54'}
  Pattern 238: Quality=0.2430, ROC-AUC=0.9505, Support=174, Pattern={'16'}{'24'}{'53'}{'54'}
  Pattern 239: Quality=0.2427, ROC-AUC=0.9172, Support=88, Pattern={'8'}{'46'}{'51'}{'52'}{'54'}{'53'}
  Pattern 240: Quality=0.2402, ROC-AUC=0.9517, Support=179, Pattern={'8'}{'18'}{'24'}{'53'}
  Pattern 241: Quality=0.2400, ROC-AUC=0.9412, Support=20, Pattern={'29'}{'47'}{'47'}{'49'}
  Pattern 242: Quality=0.2394, ROC-AUC=0.9521, Support=182, Pattern={'18'}{'52'}{'53'}{'54'}
  Pattern 243: Quality=0.2394, ROC-AUC=0.9521, Support=182, Pattern={'17'}{'52'}{'53'}{'54'}
  Pattern 244: Quality=0.2394, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'54'}{'53'}{'54'}
  Pattern 245: Quality=0.2394, ROC-AUC=0.9520, Support=180, Pattern={'24'}{'54'}{'53'}{'54'}
  Pattern 246: Quality=0.2391, ROC-AUC=0.9125, Support=58, Pattern={'18'}{'29'}{'49'}{'51'}{'52'}{'53'}
  Pattern 247: Quality=0.2374, ROC-AUC=0.9529, Support=183, Pattern={'8'}{'52'}{'51'}{'54'}
  Pattern 248: Quality=0.2368, ROC-AUC=0.9518, Support=122, Pattern={'1'}{'18'}{'46'}{'54'}
  Pattern 249: Quality=0.2349, ROC-AUC=0.9110, Support=49, Pattern={'18'}{'17'}{'46'}{'47'}{'46'}{'51'}
  Pattern 250: Quality=0.2346, ROC-AUC=0.9542, Support=187, Pattern={'18'}{'52'}{'51'}{'52'}
  Pattern 251: Quality=0.2329, ROC-AUC=0.9272, Support=63, Pattern={'19'}{'29'}{'46'}{'49'}{'53'}
  Pattern 252: Quality=0.2328, ROC-AUC=0.9552, Support=190, Pattern={'1'}{'17'}{'52'}{'51'}
  Pattern 253: Quality=0.2310, ROC-AUC=0.9554, Support=148, Pattern={'8'}{'15'}{'51'}{'53'}
  Pattern 254: Quality=0.2277, ROC-AUC=0.9240, Support=129, Pattern={'18'}{'18'}{'19'}{'23'}{'29'}{'53'}
  Pattern 255: Quality=0.2261, ROC-AUC=0.9249, Support=137, Pattern={'1'}{'18'}{'51'}{'52'}{'52'}{'54'}
  Pattern 256: Quality=0.2255, ROC-AUC=0.9249, Support=135, Pattern={'18'}{'52'}{'51'}{'52'}{'51'}{'52'}
  Pattern 257: Quality=0.2252, ROC-AUC=0.9332, Support=99, Pattern={'46'}{'52'}{'51'}{'52'}{'54'}
  Pattern 258: Quality=0.2230, ROC-AUC=0.9299, Support=64, Pattern={'8'}{'24'}{'46'}{'49'}{'53'}
  Pattern 259: Quality=0.2226, ROC-AUC=0.9118, Support=43, Pattern={'8'}{'24'}{'24'}{'46'}{'49'}{'53'}
  Pattern 260: Quality=0.2208, ROC-AUC=0.9231, Support=106, Pattern={'24'}{'51'}{'52'}{'53'}{'53'}{'54'}
  Pattern 261: Quality=0.2193, ROC-AUC=0.9255, Support=130, Pattern={'1'}{'19'}{'23'}{'29'}{'53'}{'54'}
  Pattern 262: Quality=0.2180, ROC-AUC=0.9235, Support=105, Pattern={'16'}{'25'}{'52'}{'51'}{'54'}{'53'}
  Pattern 263: Quality=0.2159, ROC-AUC=0.9123, Support=40, Pattern={'1'}{'23'}{'40'}{'45'}{'52'}{'53'}
  Pattern 264: Quality=0.2159, ROC-AUC=0.9123, Support=40, Pattern={'23'}{'40'}{'45'}{'51'}{'54'}{'53'}
  Pattern 265: Quality=0.2147, ROC-AUC=0.9263, Support=131, Pattern={'18'}{'19'}{'23'}{'29'}{'54'}{'53'}
  Pattern 266: Quality=0.2147, ROC-AUC=0.9263, Support=131, Pattern={'19'}{'23'}{'24'}{'29'}{'53'}{'54'}
  Pattern 267: Quality=0.2147, ROC-AUC=0.9263, Support=131, Pattern={'18'}{'19'}{'23'}{'29'}{'53'}{'54'}
  Pattern 268: Quality=0.2146, ROC-AUC=0.9177, Support=60, Pattern={'8'}{'18'}{'23'}{'46'}{'49'}{'52'}
  Pattern 269: Quality=0.2104, ROC-AUC=0.9319, Support=53, Pattern={'49'}{'53'}{'54'}{'53'}{'54'}
  Pattern 270: Quality=0.2090, ROC-AUC=0.9254, Support=108, Pattern={'24'}{'51'}{'54'}{'53'}{'54'}{'54'}
  Pattern 271: Quality=0.2089, ROC-AUC=0.9383, Support=115, Pattern={'15'}{'19'}{'23'}{'29'}{'53'}
  Pattern 272: Quality=0.2023, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 273: Quality=0.2023, ROC-AUC=0.9407, Support=127, Pattern={'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 274: Quality=0.2022, ROC-AUC=0.9421, Support=157, Pattern={'52'}{'51'}{'52'}{'54'}{'53'}
  Pattern 275: Quality=0.2021, ROC-AUC=0.9420, Support=155, Pattern={'16'}{'52'}{'51'}{'54'}{'53'}
  Pattern 276: Quality=0.1953, ROC-AUC=0.9441, Support=161, Pattern={'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 277: Quality=0.1943, ROC-AUC=0.9278, Support=104, Pattern={'8'}{'15'}{'24'}{'29'}{'51'}{'53'}
  Pattern 278: Quality=0.1886, ROC-AUC=0.9461, Support=165, Pattern={'24'}{'52'}{'54'}{'53'}{'54'}
  Pattern 279: Quality=0.1882, ROC-AUC=0.9451, Support=133, Pattern={'24'}{'54'}{'53'}{'53'}{'54'}
  Pattern 280: Quality=0.1882, ROC-AUC=0.9451, Support=133, Pattern={'24'}{'54'}{'53'}{'54'}{'54'}
  Pattern 281: Quality=0.1812, ROC-AUC=0.9294, Support=92, Pattern={'16'}{'46'}{'52'}{'51'}{'52'}{'54'}
  Pattern 282: Quality=0.1771, ROC-AUC=0.9501, Support=175, Pattern={'8'}{'16'}{'52'}{'54'}{'53'}
  Pattern 283: Quality=0.1746, ROC-AUC=0.9416, Support=25, Pattern={'25'}{'46'}{'47'}{'49'}{'54'}
  Pattern 284: Quality=0.1732, ROC-AUC=0.9517, Support=179, Pattern={'17'}{'24'}{'54'}{'53'}{'54'}
  Pattern 285: Quality=0.1732, ROC-AUC=0.9517, Support=179, Pattern={'8'}{'24'}{'54'}{'53'}{'54'}
  Pattern 286: Quality=0.1732, ROC-AUC=0.9517, Support=181, Pattern={'17'}{'18'}{'52'}{'54'}{'53'}
  Pattern 287: Quality=0.1724, ROC-AUC=0.9521, Support=182, Pattern={'17'}{'52'}{'54'}{'53'}{'54'}
  Pattern 288: Quality=0.1693, ROC-AUC=0.9479, Support=44, Pattern={'47'}{'49'}{'54'}{'53'}{'54'}
  Pattern 289: Quality=0.1685, ROC-AUC=0.9538, Support=184, Pattern={'1'}{'8'}{'13'}{'51'}{'52'}
  Pattern 290: Quality=0.1683, ROC-AUC=0.9539, Support=186, Pattern={'17'}{'18'}{'52'}{'51'}{'52'}
  Pattern 291: Quality=0.1683, ROC-AUC=0.9539, Support=186, Pattern={'8'}{'17'}{'52'}{'51'}{'52'}
  Pattern 292: Quality=0.1650, ROC-AUC=0.9367, Support=146, Pattern={'24'}{'52'}{'51'}{'54'}{'53'}{'54'}
  Pattern 293: Quality=0.1613, ROC-AUC=0.9361, Support=120, Pattern={'18'}{'24'}{'52'}{'53'}{'54'}{'53'}
  Pattern 294: Quality=0.1613, ROC-AUC=0.9361, Support=120, Pattern={'24'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 295: Quality=0.1524, ROC-AUC=0.9319, Support=53, Pattern={'8'}{'46'}{'49'}{'54'}{'53'}{'53'}
  Pattern 296: Quality=0.1443, ROC-AUC=0.9407, Support=127, Pattern={'18'}{'52'}{'54'}{'53'}{'53'}{'54'}
  Pattern 297: Quality=0.1443, ROC-AUC=0.9407, Support=127, Pattern={'17'}{'52'}{'53'}{'54'}{'53'}{'54'}
  Pattern 298: Quality=0.1442, ROC-AUC=0.9421, Support=157, Pattern={'52'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 299: Quality=0.1373, ROC-AUC=0.9441, Support=161, Pattern={'8'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 300: Quality=0.1357, ROC-AUC=0.9445, Support=162, Pattern={'17'}{'51'}{'52'}{'54'}{'53'}{'54'}
  Pattern 301: Quality=0.1333, ROC-AUC=0.9401, Support=68, Pattern={'18'}{'46'}{'49'}{'51'}{'52'}{'51'}
  Pattern 302: Quality=0.1320, ROC-AUC=0.9445, Support=132, Pattern={'17'}{'24'}{'54'}{'53'}{'53'}{'54'}
  Pattern 303: Quality=0.1255, ROC-AUC=0.9352, Support=21, Pattern={'23'}{'24'}{'29'}{'52'}{'51'}{'56'}
  Pattern 304: Quality=0.1151, ROC-AUC=0.9412, Support=20, Pattern={'47'}{'47'}{'49'}{'54'}{'53'}{'54'}
  Pattern 305: Quality=0.1144, ROC-AUC=0.9521, Support=182, Pattern={'18'}{'17'}{'52'}{'54'}{'53'}{'54'}
  Pattern 306: Quality=0.1142, ROC-AUC=0.9521, Support=179, Pattern={'8'}{'13'}{'17'}{'52'}{'51'}{'52'}
  Pattern 307: Quality=0.1039, ROC-AUC=0.9556, Support=89, Pattern={'1'}{'14'}{'17'}{'46'}{'52'}{'51'}
================================================================================

================
APPLYING STATISTICAL VALIDATION
================

 Applying FDR correction
  Pattern 0: AUC diff=0.1805, p=0.011799, adj_p=0.014935 --> SIGNIFICANT
  Pattern 1: AUC diff=0.1274, p=0.003500, adj_p=0.004861 --> SIGNIFICANT
  Pattern 2: AUC diff=0.1175, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 3: AUC diff=0.0691, p=0.004100, adj_p=0.005616 --> SIGNIFICANT
  Pattern 4: AUC diff=0.0774, p=0.034497, adj_p=0.038760 --> SIGNIFICANT
  Pattern 5: AUC diff=0.0919, p=0.010199, adj_p=0.013076 --> SIGNIFICANT
  Pattern 6: AUC diff=0.0359, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 7: AUC diff=0.0615, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 8: AUC diff=0.0349, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 9: AUC diff=0.0349, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 10: AUC diff=0.0463, p=0.033497, adj_p=0.038064 --> SIGNIFICANT
  Pattern 11: AUC diff=0.0737, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 12: AUC diff=0.0691, p=0.003100, adj_p=0.004366 --> SIGNIFICANT
  Pattern 13: AUC diff=0.0421, p=0.045295, adj_p=0.047599 --> SIGNIFICANT
  Pattern 14: AUC diff=0.0989, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 15: AUC diff=0.0989, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 16: AUC diff=0.0877, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 17: AUC diff=0.0919, p=0.009099, adj_p=0.011817 --> SIGNIFICANT
  Pattern 18: AUC diff=0.0803, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 19: AUC diff=0.0685, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 20: AUC diff=0.0692, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 21: AUC diff=0.0692, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 22: AUC diff=0.0774, p=0.038996, adj_p=0.041931 --> SIGNIFICANT
  Pattern 23: AUC diff=0.0623, p=0.020798, adj_p=0.025058 --> SIGNIFICANT
  Pattern 24: AUC diff=0.0769, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 25: AUC diff=0.0749, p=0.014399, adj_p=0.017776 --> SIGNIFICANT
  Pattern 26: AUC diff=0.0455, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 27: AUC diff=0.0838, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 28: AUC diff=0.0838, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 29: AUC diff=0.0450, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 30: AUC diff=0.0450, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 31: AUC diff=0.0751, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 32: AUC diff=0.0685, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 33: AUC diff=0.0721, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 34: AUC diff=0.0435, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 35: AUC diff=0.0759, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 36: AUC diff=0.0759, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 37: AUC diff=0.0880, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 38: AUC diff=0.0111, p=0.083492, adj_p=0.085196 --> NOT SIGNIFICANT
  Pattern 39: AUC diff=0.0737, p=0.000200, adj_p=0.000294 --> SIGNIFICANT
  Pattern 40: AUC diff=0.0615, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 41: AUC diff=0.0693, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 42: AUC diff=0.0399, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 43: AUC diff=0.0387, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 44: AUC diff=0.0564, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 45: AUC diff=0.0375, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 46: AUC diff=0.0783, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 47: AUC diff=0.0367, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 48: AUC diff=0.0463, p=0.036596, adj_p=0.040216 --> SIGNIFICANT
  Pattern 49: AUC diff=0.0692, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 50: AUC diff=0.0692, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 51: AUC diff=0.0356, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 52: AUC diff=0.0349, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 53: AUC diff=0.0873, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 54: AUC diff=0.0810, p=0.027597, adj_p=0.032467 --> SIGNIFICANT
  Pattern 55: AUC diff=0.0463, p=0.036596, adj_p=0.040216 --> SIGNIFICANT
  Pattern 56: AUC diff=0.0769, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 57: AUC diff=0.0338, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 58: AUC diff=0.0838, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 59: AUC diff=0.0838, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 60: AUC diff=0.0838, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 61: AUC diff=0.0428, p=0.045695, adj_p=0.047599 --> SIGNIFICANT
  Pattern 62: AUC diff=0.0421, p=0.046395, adj_p=0.047830 --> SIGNIFICANT
  Pattern 63: AUC diff=0.0421, p=0.045095, adj_p=0.047599 --> SIGNIFICANT
  Pattern 64: AUC diff=0.0696, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 65: AUC diff=0.0351, p=0.001000, adj_p=0.001428 --> SIGNIFICANT
  Pattern 66: AUC diff=0.0759, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 67: AUC diff=0.0751, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 68: AUC diff=0.0721, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 69: AUC diff=0.0749, p=0.012999, adj_p=0.016248 --> SIGNIFICANT
  Pattern 70: AUC diff=0.0363, p=0.033297, adj_p=0.038064 --> SIGNIFICANT
  Pattern 71: AUC diff=0.0469, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 72: AUC diff=0.0954, p=0.019898, adj_p=0.024266 --> SIGNIFICANT
  Pattern 73: AUC diff=0.0468, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 74: AUC diff=0.0465, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 75: AUC diff=0.0843, p=0.037896, adj_p=0.041192 --> SIGNIFICANT
  Pattern 76: AUC diff=0.0450, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 77: AUC diff=0.0444, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 78: AUC diff=0.0615, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 79: AUC diff=0.0615, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 80: AUC diff=0.0783, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 81: AUC diff=0.0757, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 82: AUC diff=0.0757, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 83: AUC diff=0.0750, p=0.000300, adj_p=0.000435 --> SIGNIFICANT
  Pattern 84: AUC diff=0.0545, p=0.028697, adj_p=0.033369 --> SIGNIFICANT
  Pattern 85: AUC diff=0.0240, p=0.009099, adj_p=0.011817 --> SIGNIFICANT
  Pattern 86: AUC diff=0.0421, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 87: AUC diff=0.0691, p=0.004300, adj_p=0.005810 --> SIGNIFICANT
  Pattern 88: AUC diff=0.0199, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 89: AUC diff=0.0817, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 90: AUC diff=0.0311, p=0.185781, adj_p=0.187658 --> NOT SIGNIFICANT
  Pattern 91: AUC diff=0.0311, p=0.188081, adj_p=0.188081 --> NOT SIGNIFICANT
  Pattern 92: AUC diff=0.0764, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 93: AUC diff=0.0535, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 94: AUC diff=0.0177, p=0.005699, adj_p=0.007599 --> SIGNIFICANT
  Pattern 95: AUC diff=0.0540, p=0.024398, adj_p=0.029045 --> SIGNIFICANT
  Pattern 96: AUC diff=0.0679, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 97: AUC diff=0.0399, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 98: AUC diff=0.0399, p=0.000100, adj_p=0.000149 --> SIGNIFICANT
  Pattern 99: AUC diff=0.0142, p=0.000100, adj_p=0.000149 --> SIGNIFICANT

 Found 97 significant patterns out of 100 tested.
  Validation completed in 724.59 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=1.2871, ROC-AUC=0.7857, Support=32, Pattern={'47'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 1: Quality=0.8649, ROC-AUC=0.8389, Support=29, Pattern={'40'}{'46'}{'54'}
  Pattern 2: Quality=0.7819, ROC-AUC=0.8487, Support=59, Pattern={'19'}{'29'}{'46'}{'51'}{'53'}{'53'}
  Pattern 3: Quality=0.7320, ROC-AUC=0.8971, Support=46, Pattern={'40'}
  Pattern 4: Quality=0.6999, ROC-AUC=0.8889, Support=21, Pattern={'43'}
  Pattern 5: Quality=0.6669, ROC-AUC=0.8743, Support=45, Pattern={'19'}{'47'}{'51'}
  Pattern 6: Quality=0.6200, ROC-AUC=0.9303, Support=136, Pattern={'23'}
  Pattern 7: Quality=0.6190, ROC-AUC=0.9048, Support=82, Pattern={'29'}{'46'}
  Pattern 8: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'19'}
  Pattern 9: Quality=0.6157, ROC-AUC=0.9313, Support=139, Pattern={'29'}
  Pattern 10: Quality=0.6127, ROC-AUC=0.9199, Support=42, Pattern={'45'}
  Pattern 11: Quality=0.6090, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}
  Pattern 12: Quality=0.6071, ROC-AUC=0.8971, Support=46, Pattern={'19'}{'40'}
  Pattern 13: Quality=0.6062, ROC-AUC=0.9241, Support=53, Pattern={'47'}
  Pattern 14: Quality=0.5943, ROC-AUC=0.8673, Support=62, Pattern={'19'}{'23'}{'29'}{'46'}{'53'}{'53'}
  Pattern 15: Quality=0.5943, ROC-AUC=0.8673, Support=62, Pattern={'23'}{'29'}{'46'}{'53'}{'54'}{'53'}
  Pattern 16: Quality=0.5902, ROC-AUC=0.8786, Support=77, Pattern={'19'}{'29'}{'51'}{'51'}{'51'}
  Pattern 17: Quality=0.5878, ROC-AUC=0.8743, Support=45, Pattern={'19'}{'47'}{'52'}{'51'}
  Pattern 18: Quality=0.5819, ROC-AUC=0.8860, Support=75, Pattern={'23'}{'29'}{'46'}{'51'}
  Pattern 19: Quality=0.5819, ROC-AUC=0.8978, Support=86, Pattern={'51'}{'51'}{'51'}
  Pattern 20: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'23'}{'29'}{'46'}
  Pattern 21: Quality=0.5759, ROC-AUC=0.8970, Support=79, Pattern={'23'}{'46'}{'54'}
  Pattern 22: Quality=0.5750, ROC-AUC=0.8889, Support=21, Pattern={'40'}{'43'}
  Pattern 23: Quality=0.5735, ROC-AUC=0.9039, Support=49, Pattern={'47'}{'53'}
  Pattern 24: Quality=0.5546, ROC-AUC=0.8894, Support=76, Pattern={'29'}{'46'}{'52'}{'52'}
  Pattern 25: Quality=0.5490, ROC-AUC=0.8914, Support=47, Pattern={'23'}{'29'}{'47'}
  Pattern 26: Quality=0.5469, ROC-AUC=0.9207, Support=124, Pattern={'23'}{'51'}
  Pattern 27: Quality=0.5450, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'52'}{'53'}
  Pattern 28: Quality=0.5450, ROC-AUC=0.8824, Support=74, Pattern={'23'}{'29'}{'46'}{'52'}{'51'}
  Pattern 29: Quality=0.5445, ROC-AUC=0.9213, Support=126, Pattern={'19'}{'51'}
  Pattern 30: Quality=0.5445, ROC-AUC=0.9213, Support=126, Pattern={'29'}{'51'}
  Pattern 31: Quality=0.5413, ROC-AUC=0.8912, Support=77, Pattern={'23'}{'29'}{'46'}{'53'}
  Pattern 32: Quality=0.5391, ROC-AUC=0.8978, Support=110, Pattern={'19'}{'29'}{'51'}{'51'}
  Pattern 33: Quality=0.5368, ROC-AUC=0.8941, Support=88, Pattern={'23'}{'52'}{'53'}{'53'}
  Pattern 34: Quality=0.5354, ROC-AUC=0.9228, Support=127, Pattern={'23'}{'52'}
  Pattern 35: Quality=0.5343, ROC-AUC=0.8903, Support=104, Pattern={'18'}{'23'}{'51'}{'51'}{'53'}
  Pattern 36: Quality=0.5343, ROC-AUC=0.8903, Support=104, Pattern={'23'}{'29'}{'51'}{'51'}{'53'}
  Pattern 37: Quality=0.5332, ROC-AUC=0.8782, Support=76, Pattern={'23'}{'29'}{'51'}{'51'}{'52'}{'51'}
  Pattern 38: Quality=0.5298, ROC-AUC=0.8925, Support=77, Pattern={'29'}{'46'}{'51'}{'52'}
  Pattern 39: Quality=0.5221, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'29'}{'46'}
  Pattern 40: Quality=0.5159, ROC-AUC=0.8970, Support=90, Pattern={'29'}{'52'}{'53'}{'53'}
  Pattern 41: Quality=0.5157, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'53'}
  Pattern 42: Quality=0.5100, ROC-AUC=0.9275, Support=134, Pattern={'29'}{'53'}
  Pattern 43: Quality=0.5034, ROC-AUC=0.9098, Support=97, Pattern={'29'}{'53'}{'53'}
  Pattern 44: Quality=0.5028, ROC-AUC=0.9288, Support=134, Pattern={'23'}{'54'}
  Pattern 45: Quality=0.4999, ROC-AUC=0.8880, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'53'}
  Pattern 46: Quality=0.4989, ROC-AUC=0.9296, Support=135, Pattern={'23'}{'29'}
  Pattern 47: Quality=0.4978, ROC-AUC=0.9199, Support=52, Pattern={'47'}{'54'}
  Pattern 48: Quality=0.4967, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'23'}{'29'}{'46'}
  Pattern 49: Quality=0.4967, ROC-AUC=0.8970, Support=79, Pattern={'19'}{'29'}{'46'}{'53'}
  Pattern 50: Quality=0.4943, ROC-AUC=0.9306, Support=138, Pattern={'29'}{'54'}
  Pattern 51: Quality=0.4907, ROC-AUC=0.9313, Support=139, Pattern={'19'}{'29'}
  Pattern 52: Quality=0.4903, ROC-AUC=0.8790, Support=64, Pattern={'24'}{'46'}{'51'}{'54'}{'53'}{'53'}
  Pattern 53: Quality=0.4894, ROC-AUC=0.8853, Support=40, Pattern={'47'}{'53'}{'54'}{'53'}
  Pattern 54: Quality=0.4878, ROC-AUC=0.9199, Support=42, Pattern={'40'}{'45'}
  Pattern 55: Quality=0.4877, ROC-AUC=0.8894, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'52'}
  Pattern 56: Quality=0.4875, ROC-AUC=0.9325, Support=148, Pattern={'51'}{'51'}
  Pattern 57: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'23'}{'29'}{'46'}{'52'}{'51'}
  Pattern 58: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'19'}{'29'}{'46'}{'51'}{'52'}{'53'}
  Pattern 59: Quality=0.4870, ROC-AUC=0.8824, Support=74, Pattern={'29'}{'46'}{'51'}{'52'}{'53'}{'54'}
  Pattern 60: Quality=0.4833, ROC-AUC=0.9234, Support=52, Pattern={'46'}{'47'}
  Pattern 61: Quality=0.4813, ROC-AUC=0.9241, Support=53, Pattern={'17'}{'47'}
  Pattern 62: Quality=0.4813, ROC-AUC=0.9241, Support=53, Pattern={'47'}{'46'}
  Pattern 63: Quality=0.4795, ROC-AUC=0.8967, Support=108, Pattern={'23'}{'29'}{'51'}{'52'}{'51'}
  Pattern 64: Quality=0.4768, ROC-AUC=0.9311, Support=98, Pattern={'46'}{'53'}
  Pattern 65: Quality=0.4763, ROC-AUC=0.8903, Support=104, Pattern={'19'}{'23'}{'29'}{'51'}{'51'}{'53'}
  Pattern 66: Quality=0.4744, ROC-AUC=0.8912, Support=77, Pattern={'19'}{'23'}{'29'}{'46'}{'53'}
  Pattern 67: Quality=0.4699, ROC-AUC=0.8941, Support=88, Pattern={'1'}{'23'}{'52'}{'53'}{'53'}
  Pattern 68: Quality=0.4698, ROC-AUC=0.8914, Support=47, Pattern={'23'}{'47'}{'46'}{'54'}
  Pattern 69: Quality=0.4661, ROC-AUC=0.9299, Support=64, Pattern={'23'}{'49'}
  Pattern 70: Quality=0.4594, ROC-AUC=0.9193, Support=124, Pattern={'29'}{'51'}{'52'}
  Pattern 71: Quality=0.4592, ROC-AUC=0.8708, Support=38, Pattern={'23'}{'46'}{'47'}{'46'}{'53'}{'53'}
  Pattern 72: Quality=0.4590, ROC-AUC=0.9195, Support=125, Pattern={'29'}{'52'}{'53'}
  Pattern 73: Quality=0.4560, ROC-AUC=0.9197, Support=123, Pattern={'23'}{'29'}{'51'}
  Pattern 74: Quality=0.4558, ROC-AUC=0.8819, Support=26, Pattern={'40'}{'45'}{'46'}{'54'}
  Pattern 75: Quality=0.4476, ROC-AUC=0.9213, Support=126, Pattern={'19'}{'29'}{'51'}
  Pattern 76: Quality=0.4440, ROC-AUC=0.9218, Support=126, Pattern={'19'}{'23'}{'52'}
  Pattern 77: Quality=0.4429, ROC-AUC=0.9048, Support=82, Pattern={'19'}{'29'}{'46'}{'54'}
  Pattern 78: Quality=0.4429, ROC-AUC=0.9048, Support=82, Pattern={'18'}{'17'}{'19'}{'46'}
  Pattern 79: Quality=0.4419, ROC-AUC=0.8880, Support=76, Pattern={'19'}{'29'}{'46'}{'52'}{'54'}{'54'}
  Pattern 80: Quality=0.4403, ROC-AUC=0.8905, Support=86, Pattern={'19'}{'23'}{'51'}{'53'}{'54'}{'54'}
  Pattern 81: Quality=0.4403, ROC-AUC=0.8905, Support=86, Pattern={'1'}{'23'}{'29'}{'51'}{'53'}{'53'}
  Pattern 82: Quality=0.4389, ROC-AUC=0.8912, Support=61, Pattern={'19'}{'53'}{'54'}{'53'}{'53'}
  Pattern 83: Quality=0.4366, ROC-AUC=0.9118, Support=50, Pattern={'47'}{'51'}{'52'}
  Pattern 84: Quality=0.4365, ROC-AUC=0.9423, Support=108, Pattern={'46'}{'51'}
  Pattern 85: Quality=0.4315, ROC-AUC=0.9242, Support=130, Pattern={'19'}{'29'}{'52'}
  Pattern 86: Quality=0.4310, ROC-AUC=0.8971, Support=46, Pattern={'23'}{'40'}{'53'}{'54'}
  Pattern 87: Quality=0.4309, ROC-AUC=0.9463, Support=166, Pattern={'51'}{'53'}
  Pattern 88: Quality=0.4281, ROC-AUC=0.8845, Support=59, Pattern={'19'}{'23'}{'29'}{'53'}{'53'}{'53'}
  Pattern 89: Quality=0.4258, ROC-AUC=0.8898, Support=76, Pattern={'46'}{'51'}{'52'}{'51'}{'53'}{'54'}
  Pattern 90: Quality=0.4224, ROC-AUC=0.9128, Support=118, Pattern={'29'}{'52'}{'52'}{'53'}
  Pattern 91: Quality=0.4220, ROC-AUC=0.9485, Support=140, Pattern={'53'}{'53'}
  Pattern 92: Quality=0.4200, ROC-AUC=0.9123, Support=40, Pattern={'40'}{'45'}{'52'}
  Pattern 93: Quality=0.4196, ROC-AUC=0.8983, Support=79, Pattern={'24'}{'46'}{'51'}{'54'}{'53'}
  Pattern 94: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'53'}{'54'}
  Pattern 95: Quality=0.4188, ROC-AUC=0.9263, Support=131, Pattern={'23'}{'29'}{'53'}
  Pattern 96: Quality=0.4155, ROC-AUC=0.9521, Support=182, Pattern={'52'}{'53'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=1.2871, ROC-AUC=0.7857, Support=32, Pattern={'47'}{'53'}{'54'}{'53'}{'53'}{'54'}
  Pattern 1: Quality=0.8649, ROC-AUC=0.8389, Support=29, Pattern={'40'}{'46'}{'54'}
  Pattern 2: Quality=0.6999, ROC-AUC=0.8889, Support=21, Pattern={'43'}
  Pattern 3: Quality=0.6200, ROC-AUC=0.9303, Support=136, Pattern={'23'}
  Pattern 4: Quality=0.4903, ROC-AUC=0.8790, Support=64, Pattern={'24'}{'46'}{'51'}{'54'}{'53'}{'53'}
================================================================================

Quality: 1.287135094188847, Extent: 32, ROCAUC: 0.7857142857142857, Pattern: {'47'}{'53'}{'54'}{'53'}{'53'}{'54'}
Quality: 0.8649461079694997, Extent: 29, ROCAUC: 0.8388888888888889, Pattern: {'40'}{'46'}{'54'}
Quality: 0.699941629971768, Extent: 21, ROCAUC: 0.888888888888889, Pattern: {'43'}
Quality: 0.6200103140270936, Extent: 136, ROCAUC: 0.9303359683794465, Pattern: {'23'}
Quality: 0.49031485338210534, Extent: 64, ROCAUC: 0.8789743589743589, Pattern: {'24'}{'46'}{'51'}{'54'}{'53'}{'53'}
Average score :0.7924695999078628
```

</details>

### Dataset `emm_figures_rc`

<details>
  <summary>Sem max size</summary>
 
`ipython3 -c "from mctsextent.main import get_patterns;get_patterns(filename='emm_context', time_budget=2000, top_k=10, theta=0.5, iterations_limit=1000)"`

```

Quality: 2.0210932938995625, Extent: 21, ROCAUC: 0.75, Pattern: {'k'}{'k'}{'k'}{'k'}{'u'}{'t'}{'t'}{'t', 'k'}{'t'}{'t', 'k'}
Quality: 1.3059239218438707, Extent: 26, ROCAUC: 0.8, Pattern: {'k'}{'k'}{'t', 'k'}{'t', 'k'}{'t', 'k'}{'t', 'k'}{'k'}{'y', 'k'}{'y', 'k'}{'k'}{'t'}{'t', 'k'}
Quality: 1.1663813483556011, Extent: 20, ROCAUC: 0.7894736842105263, Pattern: {'t'}{'t', 'k'}{'t', 'k'}{'k'}{'k'}{'y', 'k'}{'t', 'k'}{'t'}{'t'}{'t'}{'t'}{'t', 'k'}{'t', 'k'}{'t', 'k'}{'t'}{'k'}
Quality: 0.9155560197925376, Extent: 26, ROCAUC: 0.875, Pattern: {'u', 'k'}{'u'}
Quality: 0.6327357727877427, Extent: 27, ROCAUC: 0.8461538461538461, Pattern: {'k'}{'t'}{'t', 'k'}{'t', 'k'}{'t', 'k'}{'y'}{'t'}{'t'}{'t'}{'t'}{'t'}{'t', 'k'}{'t', 'k'}{'t', 'k'}
Quality: 0.5773489622039272, Extent: 37, ROCAUC: 0.8611111111111112, Pattern: {'k'}{'k'}{'t'}{'t'}{'t'}{'t', 'k'}{'k'}{'k'}{'y'}{'t'}{'t'}{'t'}{'t'}{'t', 'k'}
Quality: 0.5364385538482233, Extent: 82, ROCAUC: 0.9726315789473683, Pattern: {'r', 'h'}
Quality: 0.32335626705162357, Extent: 27, ROCAUC: 0.875, Pattern: {'k'}{'t'}{'t', 'k'}{'t'}{'t'}{'t', 'k'}{'t'}{'t'}{'t'}{'h', 'k', 'f'}{'t'}{'t', 'k'}{'t'}{'h'}
Quality: 0.3204656323320243, Extent: 21, ROCAUC: 0.9090909090909091, Pattern: {'r'}{'h'}{'h', 'f'}{'h'}{'h'}{'h'}
Quality: 0.3055755144978929, Extent: 26, ROCAUC: 0.8680555555555556, Pattern: {'k'}{'t', 'k'}{'k'}{'k'}{'k'}{'k'}{'k'}{'k'}{'t', 'k'}{'t', 'k'}{'t'}{'k', 'h'}{'k', 'f'}{'r', 'h'}{'h'}{'h'}{'h'}
```

</details>

<details>
  <summary>Com max size = 6</summary>
 
`ipython3 -c "from mctsextent.main import get_patterns;get_patterns(filename='emm_context', time_budget=2000, top_k=10, theta=0.5, iterations_limit=1000)"`

```
Quality: 1.7530819531860897, Extent: 26, ROCAUC: 0.8, Pattern: {'u'}{'t'}{'u'}
Quality: 0.3175070206338666, Extent: 79, ROCAUC: 0.9711111111111111, Pattern: {'r'}{'r'}{'h'}
Quality: 0.2511705708123294, Extent: 54, ROCAUC: 0.9462068965517242, Pattern: {'r'}{'r'}{'h'}{'h'}{'h'}
Quality: 0.23357432476647222, Extent: 33, ROCAUC: 0.9323308270676691, Pattern: {'r'}{'r'}{'r'}{'h'}{'h'}{'h'}
Quality: 0.2309441851149837, Extent: 95, ROCAUC: 0.975473801560758, Pattern: {'t'}{'t'}{'t'}{'r'}
Quality: 0.20156482398998887, Extent: 53, ROCAUC: 0.9582043343653251, Pattern: {'r'}{'g'}{'h'}{'h'}{'h'}
Quality: 0.18272253390819604, Extent: 71, ROCAUC: 0.9660869565217391, Pattern: {'r'}{'h'}{'h'}{'h'}{'h'}
Quality: 0.14718786447686238, Extent: 53, ROCAUC: 0.9571428571428571, Pattern: {'j'}{'h'}{'h'}{'h'}{'h'}{'h'}
```

</details>


### Dataset `emm_skating`

<details>

<summary>Output</summary>

`ipython3 -c "from mctsextent.main import get_patterns;get_patterns(filename='emm_skating', time_budget=2000, top_k=10, theta=0.8, iterations_limit=1000)"`

```
Number iteration mcts: 1000
================
ALL PATTERNS
================
  Pattern 0: Quality=1.5264, ROC-AUC=0.7800, Support=51, Pattern={'15'}{'16'}{'16'}{'27'}{'27'}
  Pattern 1: Quality=0.6436, ROC-AUC=0.8523, Support=26, Pattern={'9'}{'16'}{'22'}{'32'}
  Pattern 2: Quality=0.5620, ROC-AUC=0.9560, Support=59, Pattern={'39'}
  Pattern 3: Quality=0.5472, ROC-AUC=0.9628, Support=55, Pattern={'31'}
  Pattern 4: Quality=0.5354, ROC-AUC=0.9742, Support=124, Pattern={'32'}
  Pattern 5: Quality=0.5176, ROC-AUC=0.8977, Support=63, Pattern={'12'}{'16'}{'28'}{'32'}
  Pattern 6: Quality=0.4860, ROC-AUC=0.8889, Support=35, Pattern={'9'}{'15'}{'28'}{'32'}
  Pattern 7: Quality=0.4251, ROC-AUC=0.9650, Support=96, Pattern={'16'}{'32'}
  Pattern 8: Quality=0.4239, ROC-AUC=0.9614, Support=51, Pattern={'28'}{'31'}
  Pattern 9: Quality=0.4126, ROC-AUC=0.9677, Support=44, Pattern={'9'}{'30'}
  Pattern 10: Quality=0.4113, ROC-AUC=0.9734, Support=116, Pattern={'15'}{'32'}
  Pattern 11: Quality=0.4065, ROC-AUC=0.9730, Support=43, Pattern={'16'}{'39'}
  Pattern 12: Quality=0.4047, ROC-AUC=0.9793, Support=165, Pattern={'16'}{'16'}
  Pattern 13: Quality=0.4024, ROC-AUC=0.9795, Support=81, Pattern={'16'}{'30'}
  Pattern 14: Quality=0.4016, ROC-AUC=0.9802, Support=67, Pattern={'6'}{'9'}
  Pattern 15: Quality=0.3924, ROC-AUC=0.9278, Support=29, Pattern={'6'}{'16'}{'32'}
  Pattern 16: Quality=0.3662, ROC-AUC=0.9444, Support=51, Pattern={'16'}{'16'}{'32'}
  Pattern 17: Quality=0.3438, ROC-AUC=0.9563, Support=73, Pattern={'16'}{'15'}{'32'}
  Pattern 18: Quality=0.3331, ROC-AUC=0.9622, Support=88, Pattern={'16'}{'22'}{'32'}
  Pattern 19: Quality=0.3282, ROC-AUC=0.9650, Support=96, Pattern={'13'}{'16'}{'32'}
  Pattern 20: Quality=0.3281, ROC-AUC=0.9635, Support=76, Pattern={'15'}{'16'}{'32'}
  Pattern 21: Quality=0.3224, ROC-AUC=0.9669, Support=81, Pattern={'6'}{'18'}{'23'}
  Pattern 22: Quality=0.3221, ROC-AUC=0.9678, Support=93, Pattern={'12'}{'18'}{'30'}
  Pattern 23: Quality=0.3204, ROC-AUC=0.9662, Support=59, Pattern={'6'}{'16'}{'16'}
  Pattern 24: Quality=0.3193, ROC-AUC=0.9657, Support=48, Pattern={'11'}{'16'}{'16'}
  Pattern 25: Quality=0.3181, ROC-AUC=0.9643, Support=34, Pattern={'16'}{'15'}{'39'}
  Pattern 26: Quality=0.3140, ROC-AUC=0.9744, Support=140, Pattern={'16'}{'16'}{'28'}
  Pattern 27: Quality=0.3134, ROC-AUC=0.9736, Support=106, Pattern={'15'}{'22'}{'32'}
  Pattern 28: Quality=0.3091, ROC-AUC=0.9768, Support=105, Pattern={'16'}{'16'}{'15'}
  Pattern 29: Quality=0.3084, ROC-AUC=0.9762, Support=73, Pattern={'16'}{'28'}{'30'}
  Pattern 30: Quality=0.3083, ROC-AUC=0.9783, Support=133, Pattern={'9'}{'15'}{'28'}
  Pattern 31: Quality=0.3081, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}
  Pattern 32: Quality=0.3080, ROC-AUC=0.9786, Support=138, Pattern={'16'}{'15'}{'23'}
  Pattern 33: Quality=0.3078, ROC-AUC=0.9793, Support=165, Pattern={'16'}{'16'}{'27'}
  Pattern 34: Quality=0.3076, ROC-AUC=0.9791, Support=150, Pattern={'16'}{'16'}{'22'}
  Pattern 35: Quality=0.3073, ROC-AUC=0.9787, Support=116, Pattern={'1'}{'21'}{'32'}
  Pattern 36: Quality=0.3070, ROC-AUC=0.9786, Support=102, Pattern={'11'}{'15'}{'28'}
  Pattern 37: Quality=0.3070, ROC-AUC=0.9793, Support=134, Pattern={'12'}{'16'}{'29'}
  Pattern 38: Quality=0.3067, ROC-AUC=0.9782, Support=80, Pattern={'16'}{'16'}{'29'}
  Pattern 39: Quality=0.3060, ROC-AUC=0.9785, Support=69, Pattern={'16'}{'15'}{'20'}
  Pattern 40: Quality=0.3051, ROC-AUC=0.9802, Support=87, Pattern={'11'}{'16'}{'28'}
  Pattern 41: Quality=0.3048, ROC-AUC=0.9800, Support=69, Pattern={'16'}{'16'}{'16'}
  Pattern 42: Quality=0.3047, ROC-AUC=0.9800, Support=65, Pattern={'6'}{'9'}{'15'}
  Pattern 43: Quality=0.2954, ROC-AUC=0.9509, Support=119, Pattern={'15'}{'18'}{'18'}{'22'}
  Pattern 44: Quality=0.2739, ROC-AUC=0.9491, Support=50, Pattern={'9'}{'16'}{'16'}{'28'}
  Pattern 45: Quality=0.2690, ROC-AUC=0.9511, Support=50, Pattern={'1'}{'12'}{'15'}{'39'}
  Pattern 46: Quality=0.2671, ROC-AUC=0.9227, Support=32, Pattern={'16'}{'15'}{'16'}{'15'}{'32'}
  Pattern 47: Quality=0.2644, ROC-AUC=0.9464, Support=26, Pattern={'6'}{'9'}{'16'}{'16'}
  Pattern 48: Quality=0.2635, ROC-AUC=0.9481, Support=29, Pattern={'16'}{'28'}{'31'}{'32'}
  Pattern 49: Quality=0.2553, ROC-AUC=0.9306, Support=42, Pattern={'16'}{'16'}{'18'}{'28'}{'32'}
  Pattern 50: Quality=0.2553, ROC-AUC=0.9306, Support=42, Pattern={'13'}{'16'}{'16'}{'28'}{'32'}
  Pattern 51: Quality=0.2531, ROC-AUC=0.9200, Support=53, Pattern={'12'}{'16'}{'15'}{'16'}{'19'}{'23'}
  Pattern 52: Quality=0.2516, ROC-AUC=0.9652, Support=118, Pattern={'1'}{'19'}{'18'}{'28'}
  Pattern 53: Quality=0.2502, ROC-AUC=0.9639, Support=88, Pattern={'1'}{'15'}{'28'}{'32'}
  Pattern 54: Quality=0.2489, ROC-AUC=0.9635, Support=76, Pattern={'15'}{'16'}{'18'}{'32'}
  Pattern 55: Quality=0.2477, ROC-AUC=0.9598, Support=41, Pattern={'16'}{'16'}{'20'}{'28'}
  Pattern 56: Quality=0.2412, ROC-AUC=0.9662, Support=59, Pattern={'1'}{'6'}{'16'}{'16'}
  Pattern 57: Quality=0.2400, ROC-AUC=0.9697, Support=97, Pattern={'16'}{'15'}{'19'}{'23'}
  Pattern 58: Quality=0.2384, ROC-AUC=0.9667, Support=47, Pattern={'11'}{'9'}{'15'}{'28'}
  Pattern 59: Quality=0.2349, ROC-AUC=0.9743, Support=139, Pattern={'16'}{'16'}{'27'}{'28'}
  Pattern 60: Quality=0.2343, ROC-AUC=0.9734, Support=101, Pattern={'16'}{'15'}{'16'}{'19'}
  Pattern 61: Quality=0.2333, ROC-AUC=0.9679, Support=28, Pattern={'15'}{'30'}{'31'}{'32'}
  Pattern 62: Quality=0.2320, ROC-AUC=0.9731, Support=63, Pattern={'15'}{'16'}{'20'}{'28'}
  Pattern 63: Quality=0.2318, ROC-AUC=0.9739, Support=73, Pattern={'6'}{'15'}{'15'}{'18'}
  Pattern 64: Quality=0.2315, ROC-AUC=0.9752, Support=94, Pattern={'16'}{'15'}{'16'}{'15'}
  Pattern 65: Quality=0.2299, ROC-AUC=0.9768, Support=105, Pattern={'16'}{'16'}{'15'}{'18'}
  Pattern 66: Quality=0.2295, ROC-AUC=0.9722, Support=29, Pattern={'6'}{'15'}{'16'}{'20'}
  Pattern 67: Quality=0.2294, ROC-AUC=0.9801, Support=283, Pattern={'12'}{'15'}{'27'}{'28'}
  Pattern 68: Quality=0.2293, ROC-AUC=0.9780, Support=132, Pattern={'1'}{'9'}{'15'}{'28'}
  Pattern 69: Quality=0.2289, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}{'18'}
  Pattern 70: Quality=0.2283, ROC-AUC=0.9749, Support=40, Pattern={'21'}{'28'}{'30'}{'31'}
  Pattern 71: Quality=0.2280, ROC-AUC=0.9740, Support=29, Pattern={'6'}{'11'}{'16'}{'18'}
  Pattern 72: Quality=0.2233, ROC-AUC=0.9452, Support=60, Pattern={'1'}{'16'}{'15'}{'28'}{'32'}
  Pattern 73: Quality=0.2186, ROC-AUC=0.9443, Support=48, Pattern={'1'}{'13'}{'27'}{'28'}{'39'}
  Pattern 74: Quality=0.2007, ROC-AUC=0.9429, Support=22, Pattern={'15'}{'16'}{'18'}{'31'}{'32'}
  Pattern 75: Quality=0.1886, ROC-AUC=0.9651, Support=149, Pattern={'1'}{'12'}{'15'}{'22'}{'29'}
  Pattern 76: Quality=0.1792, ROC-AUC=0.9365, Support=43, Pattern={'16'}{'16'}{'18'}{'22'}{'21'}{'32'}
  Pattern 77: Quality=0.1770, ROC-AUC=0.9607, Support=34, Pattern={'13'}{'16'}{'16'}{'28'}{'30'}
  Pattern 78: Quality=0.1764, ROC-AUC=0.9602, Support=30, Pattern={'6'}{'12'}{'16'}{'16'}{'29'}
  Pattern 79: Quality=0.1731, ROC-AUC=0.9657, Support=48, Pattern={'11'}{'13'}{'16'}{'16'}{'18'}
  Pattern 80: Quality=0.1716, ROC-AUC=0.9678, Support=58, Pattern={'16'}{'15'}{'27'}{'28'}{'30'}
  Pattern 81: Quality=0.1708, ROC-AUC=0.9710, Support=98, Pattern={'1'}{'15'}{'22'}{'21'}{'32'}
  Pattern 82: Quality=0.1685, ROC-AUC=0.9745, Support=159, Pattern={'1'}{'18'}{'19'}{'23'}{'27'}
  Pattern 83: Quality=0.1673, ROC-AUC=0.9743, Support=125, Pattern={'16'}{'16'}{'18'}{'22'}{'28'}
  Pattern 84: Quality=0.1672, ROC-AUC=0.9743, Support=124, Pattern={'16'}{'16'}{'22'}{'27'}{'28'}
  Pattern 85: Quality=0.1661, ROC-AUC=0.9749, Support=119, Pattern={'1'}{'16'}{'15'}{'23'}{'28'}
  Pattern 86: Quality=0.1657, ROC-AUC=0.9779, Support=262, Pattern={'12'}{'15'}{'22'}{'27'}{'28'}
  Pattern 87: Quality=0.1645, ROC-AUC=0.9752, Support=94, Pattern={'13'}{'16'}{'15'}{'16'}{'15'}
  Pattern 88: Quality=0.1626, ROC-AUC=0.9767, Support=93, Pattern={'6'}{'13'}{'12'}{'27'}{'28'}
  Pattern 89: Quality=0.1624, ROC-AUC=0.9801, Support=283, Pattern={'12'}{'15'}{'18'}{'27'}{'28'}
  Pattern 90: Quality=0.1620, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}{'18'}{'27'}
  Pattern 91: Quality=0.1618, ROC-AUC=0.9788, Support=144, Pattern={'1'}{'16'}{'15'}{'16'}{'22'}
  Pattern 92: Quality=0.1616, ROC-AUC=0.9790, Support=145, Pattern={'16'}{'15'}{'16'}{'22'}{'27'}
  Pattern 93: Quality=0.1600, ROC-AUC=0.9780, Support=62, Pattern={'1'}{'15'}{'15'}{'16'}{'23'}
  Pattern 94: Quality=0.1600, ROC-AUC=0.9788, Support=81, Pattern={'6'}{'12'}{'13'}{'21'}{'28'}
  Pattern 95: Quality=0.1599, ROC-AUC=0.9787, Support=75, Pattern={'1'}{'15'}{'16'}{'20'}{'27'}
  Pattern 96: Quality=0.1596, ROC-AUC=0.9799, Support=101, Pattern={'9'}{'13'}{'12'}{'16'}{'18'}
  Pattern 97: Quality=0.1328, ROC-AUC=0.9586, Support=68, Pattern={'6'}{'13'}{'13'}{'15'}{'18'}{'23'}
  Pattern 98: Quality=0.1292, ROC-AUC=0.9500, Support=21, Pattern={'1'}{'18'}{'19'}{'23'}{'28'}{'39'}
  Pattern 99: Quality=0.1276, ROC-AUC=0.9620, Support=78, Pattern={'1'}{'12'}{'18'}{'27'}{'28'}{'30'}
  Pattern 100: Quality=0.1254, ROC-AUC=0.9567, Support=34, Pattern={'1'}{'6'}{'15'}{'15'}{'16'}{'23'}
  Pattern 101: Quality=0.1226, ROC-AUC=0.9602, Support=43, Pattern={'1'}{'18'}{'27'}{'28'}{'30'}{'31'}
  Pattern 102: Quality=0.1219, ROC-AUC=0.9715, Support=266, Pattern={'1'}{'13'}{'13'}{'12'}{'15'}{'21'}
  Pattern 103: Quality=0.1198, ROC-AUC=0.9593, Support=30, Pattern={'11'}{'13'}{'16'}{'15'}{'16'}{'15'}
  Pattern 104: Quality=0.1181, ROC-AUC=0.9654, Support=62, Pattern={'15'}{'16'}{'18'}{'21'}{'22'}{'32'}
  Pattern 105: Quality=0.1121, ROC-AUC=0.9698, Support=70, Pattern={'1'}{'15'}{'16'}{'18'}{'20'}{'22'}
  Pattern 106: Quality=0.1106, ROC-AUC=0.9745, Support=159, Pattern={'1'}{'13'}{'18'}{'19'}{'23'}{'27'}
  Pattern 107: Quality=0.1100, ROC-AUC=0.9712, Support=68, Pattern={'6'}{'13'}{'16'}{'19'}{'27'}{'28'}
  Pattern 108: Quality=0.1080, ROC-AUC=0.9759, Support=152, Pattern={'13'}{'13'}{'15'}{'16'}{'19'}{'21'}
  Pattern 109: Quality=0.1069, ROC-AUC=0.9726, Support=54, Pattern={'16'}{'15'}{'21'}{'27'}{'28'}{'30'}
  Pattern 110: Quality=0.1051, ROC-AUC=0.9774, Support=129, Pattern={'1'}{'12'}{'16'}{'15'}{'16'}{'18'}
  Pattern 111: Quality=0.1049, ROC-AUC=0.9762, Support=86, Pattern={'13'}{'16'}{'18'}{'19'}{'20'}{'22'}
  Pattern 112: Quality=0.1040, ROC-AUC=0.9789, Support=159, Pattern={'13'}{'16'}{'15'}{'16'}{'18'}{'27'}
  Pattern 113: Quality=0.1038, ROC-AUC=0.9788, Support=144, Pattern={'1'}{'13'}{'16'}{'15'}{'16'}{'22'}
  Pattern 114: Quality=0.1037, ROC-AUC=0.9796, Support=189, Pattern={'1'}{'12'}{'13'}{'16'}{'15'}{'28'}
  Pattern 115: Quality=0.1033, ROC-AUC=0.9744, Support=34, Pattern={'1'}{'9'}{'15'}{'21'}{'28'}{'30'}
  Pattern 116: Quality=0.1029, ROC-AUC=0.9793, Support=134, Pattern={'1'}{'13'}{'12'}{'16'}{'27'}{'29'}
  Pattern 117: Quality=0.1028, ROC-AUC=0.9790, Support=114, Pattern={'1'}{'15'}{'16'}{'15'}{'19'}{'28'}
  Pattern 118: Quality=0.1020, ROC-AUC=0.9787, Support=77, Pattern={'6'}{'16'}{'15'}{'21'}{'27'}{'28'}
  Pattern 119: Quality=0.1009, ROC-AUC=0.9766, Support=24, Pattern={'9'}{'15'}{'16'}{'16'}{'16'}{'28'}
================================================================================

================
APPLYING STATISTICAL VALIDATION
================

 Applying FDR correction
  Pattern 0: AUC diff=0.2103, p=0.010399, adj_p=0.039996 --> SIGNIFICANT
  Pattern 1: AUC diff=0.1380, p=0.001200, adj_p=0.016665 --> SIGNIFICANT
  Pattern 2: AUC diff=0.0342, p=0.050995, adj_p=0.077265 --> NOT SIGNIFICANT
  Pattern 3: AUC diff=0.0275, p=0.039796, adj_p=0.066327 --> NOT SIGNIFICANT
  Pattern 4: AUC diff=0.0161, p=0.020898, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 5: AUC diff=0.0926, p=0.000500, adj_p=0.016665 --> SIGNIFICANT
  Pattern 6: AUC diff=0.1014, p=0.000100, adj_p=0.009999 --> SIGNIFICANT
  Pattern 7: AUC diff=0.0253, p=0.008499, adj_p=0.039996 --> SIGNIFICANT
  Pattern 8: AUC diff=0.0289, p=0.038896, adj_p=0.065926 --> NOT SIGNIFICANT
  Pattern 9: AUC diff=0.0225, p=0.064094, adj_p=0.086748 --> NOT SIGNIFICANT
  Pattern 10: AUC diff=0.0169, p=0.020398, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 11: AUC diff=0.0173, p=0.108689, adj_p=0.125897 --> NOT SIGNIFICANT
  Pattern 12: AUC diff=0.0110, p=0.008699, adj_p=0.039996 --> SIGNIFICANT
  Pattern 13: AUC diff=0.0107, p=0.106689, adj_p=0.125517 --> NOT SIGNIFICANT
  Pattern 14: AUC diff=0.0101, p=0.114689, adj_p=0.128864 --> NOT SIGNIFICANT
  Pattern 15: AUC diff=0.0625, p=0.003600, adj_p=0.027690 --> SIGNIFICANT
  Pattern 16: AUC diff=0.0458, p=0.002300, adj_p=0.020907 --> SIGNIFICANT
  Pattern 17: AUC diff=0.0340, p=0.004500, adj_p=0.031872 --> SIGNIFICANT
  Pattern 18: AUC diff=0.0281, p=0.028197, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 19: AUC diff=0.0253, p=0.008999, adj_p=0.039996 --> SIGNIFICANT
  Pattern 20: AUC diff=0.0267, p=0.012499, adj_p=0.044638 --> SIGNIFICANT
  Pattern 21: AUC diff=0.0234, p=0.019798, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 22: AUC diff=0.0224, p=0.061794, adj_p=0.086748 --> NOT SIGNIFICANT
  Pattern 23: AUC diff=0.0241, p=0.015198, adj_p=0.050662 --> NOT SIGNIFICANT
  Pattern 24: AUC diff=0.0246, p=0.037996, adj_p=0.065926 --> NOT SIGNIFICANT
  Pattern 25: AUC diff=0.0260, p=0.079492, adj_p=0.100623 --> NOT SIGNIFICANT
  Pattern 26: AUC diff=0.0159, p=0.001500, adj_p=0.016665 --> SIGNIFICANT
  Pattern 27: AUC diff=0.0167, p=0.064194, adj_p=0.086748 --> NOT SIGNIFICANT
  Pattern 28: AUC diff=0.0135, p=0.025197, adj_p=0.053612 --> NOT SIGNIFICANT
  Pattern 29: AUC diff=0.0141, p=0.059894, adj_p=0.085563 --> NOT SIGNIFICANT
  Pattern 30: AUC diff=0.0120, p=0.017498, adj_p=0.051760 --> NOT SIGNIFICANT
  Pattern 31: AUC diff=0.0114, p=0.010399, adj_p=0.039996 --> SIGNIFICANT
  Pattern 32: AUC diff=0.0117, p=0.038696, adj_p=0.065926 --> NOT SIGNIFICANT
  Pattern 33: AUC diff=0.0110, p=0.010099, adj_p=0.039996 --> SIGNIFICANT
  Pattern 34: AUC diff=0.0111, p=0.029397, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 35: AUC diff=0.0115, p=0.084992, adj_p=0.106239 --> NOT SIGNIFICANT
  Pattern 36: AUC diff=0.0117, p=0.050495, adj_p=0.077265 --> NOT SIGNIFICANT
  Pattern 37: AUC diff=0.0109, p=0.139586, adj_p=0.142435 --> NOT SIGNIFICANT
  Pattern 38: AUC diff=0.0121, p=0.093691, adj_p=0.112880 --> NOT SIGNIFICANT
  Pattern 39: AUC diff=0.0118, p=0.131487, adj_p=0.138407 --> NOT SIGNIFICANT
  Pattern 40: AUC diff=0.0100, p=0.103990, adj_p=0.123797 --> NOT SIGNIFICANT
  Pattern 41: AUC diff=0.0103, p=0.147785, adj_p=0.149278 --> NOT SIGNIFICANT
  Pattern 42: AUC diff=0.0103, p=0.121988, adj_p=0.134053 --> NOT SIGNIFICANT
  Pattern 43: AUC diff=0.0394, p=0.053595, adj_p=0.078398 --> NOT SIGNIFICANT
  Pattern 44: AUC diff=0.0412, p=0.001500, adj_p=0.016665 --> SIGNIFICANT
  Pattern 45: AUC diff=0.0392, p=0.045695, adj_p=0.071399 --> NOT SIGNIFICANT
  Pattern 46: AUC diff=0.0676, p=0.002900, adj_p=0.024164 --> SIGNIFICANT
  Pattern 47: AUC diff=0.0438, p=0.019098, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 48: AUC diff=0.0422, p=0.035596, adj_p=0.063922 --> NOT SIGNIFICANT
  Pattern 49: AUC diff=0.0597, p=0.000800, adj_p=0.016665 --> SIGNIFICANT
  Pattern 50: AUC diff=0.0597, p=0.000700, adj_p=0.016665 --> SIGNIFICANT
  Pattern 51: AUC diff=0.0703, p=0.030497, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 52: AUC diff=0.0251, p=0.043396, adj_p=0.069993 --> NOT SIGNIFICANT
  Pattern 53: AUC diff=0.0264, p=0.002100, adj_p=0.020907 --> SIGNIFICANT
  Pattern 54: AUC diff=0.0267, p=0.011599, adj_p=0.042959 --> SIGNIFICANT
  Pattern 55: AUC diff=0.0305, p=0.030297, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 56: AUC diff=0.0241, p=0.016398, adj_p=0.051245 --> NOT SIGNIFICANT
  Pattern 57: AUC diff=0.0206, p=0.089291, adj_p=0.108892 --> NOT SIGNIFICANT
  Pattern 58: AUC diff=0.0236, p=0.052595, adj_p=0.078398 --> NOT SIGNIFICANT
  Pattern 59: AUC diff=0.0159, p=0.001100, adj_p=0.016665 --> SIGNIFICANT
  Pattern 60: AUC diff=0.0169, p=0.054095, adj_p=0.078398 --> NOT SIGNIFICANT
  Pattern 61: AUC diff=0.0224, p=0.087691, adj_p=0.108261 --> NOT SIGNIFICANT
  Pattern 62: AUC diff=0.0171, p=0.068193, adj_p=0.090924 --> NOT SIGNIFICANT
  Pattern 63: AUC diff=0.0164, p=0.044196, adj_p=0.070152 --> NOT SIGNIFICANT
  Pattern 64: AUC diff=0.0151, p=0.021398, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 65: AUC diff=0.0135, p=0.022098, adj_p=0.052614 --> NOT SIGNIFICANT
  Pattern 66: AUC diff=0.0181, p=0.128287, adj_p=0.137943 --> NOT SIGNIFICANT
  Pattern 67: AUC diff=0.0101, p=0.005099, adj_p=0.031872 --> SIGNIFICANT
  Pattern 68: AUC diff=0.0123, p=0.016098, adj_p=0.051245 --> NOT SIGNIFICANT
  Pattern 69: AUC diff=0.0114, p=0.010199, adj_p=0.039996 --> SIGNIFICANT
  Pattern 70: AUC diff=0.0154, p=0.133387, adj_p=0.138944 --> NOT SIGNIFICANT
  Pattern 71: AUC diff=0.0162, p=0.149385, adj_p=0.149385 --> NOT SIGNIFICANT
  Pattern 72: AUC diff=0.0451, p=0.001000, adj_p=0.016665 --> SIGNIFICANT
  Pattern 73: AUC diff=0.0460, p=0.019798, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 74: AUC diff=0.0474, p=0.041596, adj_p=0.068190 --> NOT SIGNIFICANT
  Pattern 75: AUC diff=0.0252, p=0.071793, adj_p=0.093237 --> NOT SIGNIFICANT
  Pattern 76: AUC diff=0.0538, p=0.012999, adj_p=0.044823 --> SIGNIFICANT
  Pattern 77: AUC diff=0.0296, p=0.030197, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 78: AUC diff=0.0300, p=0.071393, adj_p=0.093237 --> NOT SIGNIFICANT
  Pattern 79: AUC diff=0.0246, p=0.035796, adj_p=0.063922 --> NOT SIGNIFICANT
  Pattern 80: AUC diff=0.0224, p=0.021198, adj_p=0.052190 --> NOT SIGNIFICANT
  Pattern 81: AUC diff=0.0192, p=0.064094, adj_p=0.086748 --> NOT SIGNIFICANT
  Pattern 82: AUC diff=0.0158, p=0.110089, adj_p=0.125897 --> NOT SIGNIFICANT
  Pattern 83: AUC diff=0.0160, p=0.005000, adj_p=0.031872 --> SIGNIFICANT
  Pattern 84: AUC diff=0.0160, p=0.007899, adj_p=0.039996 --> SIGNIFICANT
  Pattern 85: AUC diff=0.0154, p=0.017598, adj_p=0.051760 --> NOT SIGNIFICANT
  Pattern 86: AUC diff=0.0124, p=0.029897, adj_p=0.057541 --> NOT SIGNIFICANT
  Pattern 87: AUC diff=0.0151, p=0.023398, adj_p=0.053612 --> NOT SIGNIFICANT
  Pattern 88: AUC diff=0.0136, p=0.074893, adj_p=0.096016 --> NOT SIGNIFICANT
  Pattern 89: AUC diff=0.0101, p=0.005599, adj_p=0.032938 --> SIGNIFICANT
  Pattern 90: AUC diff=0.0114, p=0.009199, adj_p=0.039996 --> SIGNIFICANT
  Pattern 91: AUC diff=0.0115, p=0.023898, adj_p=0.053612 --> NOT SIGNIFICANT
  Pattern 92: AUC diff=0.0113, p=0.025097, adj_p=0.053612 --> NOT SIGNIFICANT
  Pattern 93: AUC diff=0.0123, p=0.137386, adj_p=0.141635 --> NOT SIGNIFICANT
  Pattern 94: AUC diff=0.0114, p=0.125987, adj_p=0.136943 --> NOT SIGNIFICANT
  Pattern 95: AUC diff=0.0116, p=0.130787, adj_p=0.138407 --> NOT SIGNIFICANT
  Pattern 96: AUC diff=0.0104, p=0.117288, adj_p=0.130320 --> NOT SIGNIFICANT
  Pattern 97: AUC diff=0.0317, p=0.024698, adj_p=0.053612 --> NOT SIGNIFICANT
  Pattern 98: AUC diff=0.0403, p=0.110789, adj_p=0.125897 --> NOT SIGNIFICANT
  Pattern 99: AUC diff=0.0283, p=0.031497, adj_p=0.058328 --> NOT SIGNIFICANT

 Found 29 significant patterns out of 100 tested.
  Validation completed in 721.76 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=1.5264, ROC-AUC=0.7800, Support=51, Pattern={'15'}{'16'}{'16'}{'27'}{'27'}
  Pattern 1: Quality=0.6436, ROC-AUC=0.8523, Support=26, Pattern={'9'}{'16'}{'22'}{'32'}
  Pattern 2: Quality=0.5176, ROC-AUC=0.8977, Support=63, Pattern={'12'}{'16'}{'28'}{'32'}
  Pattern 3: Quality=0.4860, ROC-AUC=0.8889, Support=35, Pattern={'9'}{'15'}{'28'}{'32'}
  Pattern 4: Quality=0.4251, ROC-AUC=0.9650, Support=96, Pattern={'16'}{'32'}
  Pattern 5: Quality=0.4047, ROC-AUC=0.9793, Support=165, Pattern={'16'}{'16'}
  Pattern 6: Quality=0.3924, ROC-AUC=0.9278, Support=29, Pattern={'6'}{'16'}{'32'}
  Pattern 7: Quality=0.3662, ROC-AUC=0.9444, Support=51, Pattern={'16'}{'16'}{'32'}
  Pattern 8: Quality=0.3438, ROC-AUC=0.9563, Support=73, Pattern={'16'}{'15'}{'32'}
  Pattern 9: Quality=0.3282, ROC-AUC=0.9650, Support=96, Pattern={'13'}{'16'}{'32'}
  Pattern 10: Quality=0.3281, ROC-AUC=0.9635, Support=76, Pattern={'15'}{'16'}{'32'}
  Pattern 11: Quality=0.3140, ROC-AUC=0.9744, Support=140, Pattern={'16'}{'16'}{'28'}
  Pattern 12: Quality=0.3081, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}
  Pattern 13: Quality=0.3078, ROC-AUC=0.9793, Support=165, Pattern={'16'}{'16'}{'27'}
  Pattern 14: Quality=0.2739, ROC-AUC=0.9491, Support=50, Pattern={'9'}{'16'}{'16'}{'28'}
  Pattern 15: Quality=0.2671, ROC-AUC=0.9227, Support=32, Pattern={'16'}{'15'}{'16'}{'15'}{'32'}
  Pattern 16: Quality=0.2553, ROC-AUC=0.9306, Support=42, Pattern={'16'}{'16'}{'18'}{'28'}{'32'}
  Pattern 17: Quality=0.2553, ROC-AUC=0.9306, Support=42, Pattern={'13'}{'16'}{'16'}{'28'}{'32'}
  Pattern 18: Quality=0.2502, ROC-AUC=0.9639, Support=88, Pattern={'1'}{'15'}{'28'}{'32'}
  Pattern 19: Quality=0.2489, ROC-AUC=0.9635, Support=76, Pattern={'15'}{'16'}{'18'}{'32'}
  Pattern 20: Quality=0.2349, ROC-AUC=0.9743, Support=139, Pattern={'16'}{'16'}{'27'}{'28'}
  Pattern 21: Quality=0.2294, ROC-AUC=0.9801, Support=283, Pattern={'12'}{'15'}{'27'}{'28'}
  Pattern 22: Quality=0.2289, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}{'18'}
  Pattern 23: Quality=0.2233, ROC-AUC=0.9452, Support=60, Pattern={'1'}{'16'}{'15'}{'28'}{'32'}
  Pattern 24: Quality=0.1792, ROC-AUC=0.9365, Support=43, Pattern={'16'}{'16'}{'18'}{'22'}{'21'}{'32'}
  Pattern 25: Quality=0.1673, ROC-AUC=0.9743, Support=125, Pattern={'16'}{'16'}{'18'}{'22'}{'28'}
  Pattern 26: Quality=0.1672, ROC-AUC=0.9743, Support=124, Pattern={'16'}{'16'}{'22'}{'27'}{'28'}
  Pattern 27: Quality=0.1624, ROC-AUC=0.9801, Support=283, Pattern={'12'}{'15'}{'18'}{'27'}{'28'}
  Pattern 28: Quality=0.1620, ROC-AUC=0.9789, Support=159, Pattern={'16'}{'15'}{'16'}{'18'}{'27'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=1.5264, ROC-AUC=0.7800, Support=51, Pattern={'15'}{'16'}{'16'}{'27'}{'27'}
  Pattern 1: Quality=0.6436, ROC-AUC=0.8523, Support=26, Pattern={'9'}{'16'}{'22'}{'32'}
  Pattern 2: Quality=0.5176, ROC-AUC=0.8977, Support=63, Pattern={'12'}{'16'}{'28'}{'32'}
  Pattern 3: Quality=0.4860, ROC-AUC=0.8889, Support=35, Pattern={'9'}{'15'}{'28'}{'32'}
  Pattern 4: Quality=0.4251, ROC-AUC=0.9650, Support=96, Pattern={'16'}{'32'}
  Pattern 5: Quality=0.4047, ROC-AUC=0.9793, Support=165, Pattern={'16'}{'16'}
  Pattern 6: Quality=0.3924, ROC-AUC=0.9278, Support=29, Pattern={'6'}{'16'}{'32'}
  Pattern 7: Quality=0.3662, ROC-AUC=0.9444, Support=51, Pattern={'16'}{'16'}{'32'}
  Pattern 8: Quality=0.3438, ROC-AUC=0.9563, Support=73, Pattern={'16'}{'15'}{'32'}
  Pattern 9: Quality=0.3281, ROC-AUC=0.9635, Support=76, Pattern={'15'}{'16'}{'32'}
  Pattern 10: Quality=0.2739, ROC-AUC=0.9491, Support=50, Pattern={'9'}{'16'}{'16'}{'28'}
  Pattern 11: Quality=0.2671, ROC-AUC=0.9227, Support=32, Pattern={'16'}{'15'}{'16'}{'15'}{'32'}
  Pattern 12: Quality=0.2502, ROC-AUC=0.9639, Support=88, Pattern={'1'}{'15'}{'28'}{'32'}
  Pattern 13: Quality=0.2294, ROC-AUC=0.9801, Support=283, Pattern={'12'}{'15'}{'27'}{'28'}
  Pattern 14: Quality=0.1673, ROC-AUC=0.9743, Support=125, Pattern={'16'}{'16'}{'18'}{'22'}{'28'}
================================================================================

Quality: 1.5264499368724451, Extent: 51, ROCAUC: 0.78, Pattern: {'15'}{'16'}{'16'}{'27'}{'27'}
Quality: 0.643646050760347, Extent: 26, ROCAUC: 0.8522727272727273, Pattern: {'9'}{'16'}{'22'}{'32'}
Quality: 0.5175555868819386, Extent: 63, ROCAUC: 0.8976608187134503, Pattern: {'12'}{'16'}{'28'}{'32'}
Quality: 0.48598578914157875, Extent: 35, ROCAUC: 0.8888888888888888, Pattern: {'9'}{'15'}{'28'}{'32'}
Quality: 0.4251142185356874, Extent: 96, ROCAUC: 0.9650037230081906, Pattern: {'16'}{'32'}
Quality: 0.4047010377388207, Extent: 165, ROCAUC: 0.9792643346556077, Pattern: {'16'}{'16'}
Quality: 0.39238745801972985, Extent: 29, ROCAUC: 0.9277777777777777, Pattern: {'6'}{'16'}{'32'}
Quality: 0.3661785737475164, Extent: 51, ROCAUC: 0.9444444444444444, Pattern: {'16'}{'16'}{'32'}
Quality: 0.3438072703843067, Extent: 73, ROCAUC: 0.9563218390804598, Pattern: {'16'}{'15'}{'32'}
Quality: 0.32808733940451984, Extent: 76, ROCAUC: 0.9635416666666667, Pattern: {'15'}{'16'}{'32'}
```

</details>

### Dataset `emm_splice_bin`

Não acha padrões pequenos

<details>


  <summary>Output</summary>

```
ALL PATTERNS
================
  Pattern 0: Quality=0.6756, ROC-AUC=0.6500, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}
  Pattern 1: Quality=-0.0505, ROC-AUC=0.7843, Support=20, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 2: Quality=-0.1383, ROC-AUC=0.8111, Support=21, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}
  Pattern 3: Quality=-0.1500, ROC-AUC=0.8333, Support=26, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}
  Pattern 4: Quality=-0.1706, ROC-AUC=0.8229, Support=22, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 5: Quality=-0.1841, ROC-AUC=0.8283, Support=20, Pattern={'C'}{'A'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 6: Quality=-0.2138, ROC-AUC=0.8712, Support=37, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 7: Quality=-0.2405, ROC-AUC=0.8775, Support=41, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 8: Quality=-0.2668, ROC-AUC=0.8818, Support=27, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 9: Quality=-0.2699, ROC-AUC=0.8929, Support=29, Pattern={'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}
  Pattern 10: Quality=-0.2705, ROC-AUC=0.9804, Support=597, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 11: Quality=-0.2706, ROC-AUC=0.8571, Support=22, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 12: Quality=-0.2728, ROC-AUC=0.9823, Support=588, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 13: Quality=-0.2730, ROC-AUC=0.8906, Support=44, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}
  Pattern 14: Quality=-0.2736, ROC-AUC=0.9826, Support=496, Pattern={'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 15: Quality=-0.2740, ROC-AUC=0.9828, Support=459, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 16: Quality=-0.2756, ROC-AUC=0.8990, Support=46, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}
  Pattern 17: Quality=-0.2780, ROC-AUC=0.8727, Support=27, Pattern={'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 18: Quality=-0.2842, ROC-AUC=0.8960, Support=35, Pattern={'T'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'A'}{'A'}{'T'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}
  Pattern 19: Quality=-0.2880, ROC-AUC=0.8846, Support=21, Pattern={'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'T'}{'G'}{'G'}{'G'}{'T'}{'A'}{'A'}{'C'}
  Pattern 20: Quality=-0.2901, ROC-AUC=0.9767, Support=386, Pattern={'G'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 21: Quality=-0.2930, ROC-AUC=0.9800, Support=510, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}
  Pattern 22: Quality=-0.2931, ROC-AUC=0.9792, Support=393, Pattern={'G'}{'T'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 23: Quality=-0.2936, ROC-AUC=0.9811, Support=604, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 24: Quality=-0.2945, ROC-AUC=0.9821, Support=668, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 25: Quality=-0.2946, ROC-AUC=0.9818, Support=581, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 26: Quality=-0.2946, ROC-AUC=0.9816, Support=544, Pattern={'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 27: Quality=-0.2948, ROC-AUC=0.9807, Support=366, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'G'}
  Pattern 28: Quality=-0.2950, ROC-AUC=0.9813, Support=431, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 29: Quality=-0.2952, ROC-AUC=0.9828, Support=684, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 30: Quality=-0.2952, ROC-AUC=0.9827, Support=645, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 31: Quality=-0.2953, ROC-AUC=0.9806, Support=311, Pattern={'C'}{'A'}{'G'}{'A'}{'A'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 32: Quality=-0.2953, ROC-AUC=0.9832, Support=788, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 33: Quality=-0.2954, ROC-AUC=0.9827, Support=629, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 34: Quality=-0.2954, ROC-AUC=0.9828, Support=644, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 35: Quality=-0.2955, ROC-AUC=0.9819, Support=444, Pattern={'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}
  Pattern 36: Quality=-0.2955, ROC-AUC=0.9825, Support=552, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}
  Pattern 37: Quality=-0.2955, ROC-AUC=0.9822, Support=491, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}
  Pattern 38: Quality=-0.2957, ROC-AUC=0.9826, Support=540, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'G'}
  Pattern 39: Quality=-0.2957, ROC-AUC=0.9824, Support=495, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}
  Pattern 40: Quality=-0.2957, ROC-AUC=0.9828, Support=556, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 41: Quality=-0.2958, ROC-AUC=0.9818, Support=380, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}
  Pattern 42: Quality=-0.2959, ROC-AUC=0.9817, Support=353, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 43: Quality=-0.2960, ROC-AUC=0.9830, Support=549, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 44: Quality=-0.2963, ROC-AUC=0.9829, Support=471, Pattern={'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'C'}{'G'}
  Pattern 45: Quality=-0.2963, ROC-AUC=0.9830, Support=470, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 46: Quality=-0.2964, ROC-AUC=0.9826, Support=408, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}
  Pattern 47: Quality=-0.2964, ROC-AUC=0.9822, Support=340, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 48: Quality=-0.2964, ROC-AUC=0.9830, Support=453, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}
  Pattern 49: Quality=-0.2965, ROC-AUC=0.9815, Support=261, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}
  Pattern 50: Quality=-0.2966, ROC-AUC=0.9815, Support=246, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'T'}
  Pattern 51: Quality=-0.2966, ROC-AUC=0.9828, Support=389, Pattern={'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'G'}
  Pattern 52: Quality=-0.2967, ROC-AUC=0.9833, Support=454, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 53: Quality=-0.2970, ROC-AUC=0.9832, Support=372, Pattern={'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}{'A'}
  Pattern 54: Quality=-0.2973, ROC-AUC=0.9832, Support=340, Pattern={'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 55: Quality=-0.2973, ROC-AUC=0.9831, Support=314, Pattern={'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'T'}
  Pattern 56: Quality=-0.2981, ROC-AUC=0.9143, Support=42, Pattern={'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'A'}{'A'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 57: Quality=-0.2987, ROC-AUC=0.8889, Support=45, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}
  Pattern 58: Quality=-0.3026, ROC-AUC=0.9644, Support=135, Pattern={'T'}{'A'}{'A'}{'T'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}{'T'}
  Pattern 59: Quality=-0.3034, ROC-AUC=0.8947, Support=23, Pattern={'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'G'}{'A'}{'A'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 60: Quality=-0.3058, ROC-AUC=0.9085, Support=26, Pattern={'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'A'}{'C'}{'T'}{'A'}{'G'}{'A'}
  Pattern 61: Quality=-0.3060, ROC-AUC=0.9107, Support=44, Pattern={'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'A'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 62: Quality=-0.3061, ROC-AUC=0.8967, Support=33, Pattern={'A'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 63: Quality=-0.3064, ROC-AUC=0.8824, Support=25, Pattern={'G'}{'G'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 64: Quality=-0.3065, ROC-AUC=0.9671, Support=128, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'G'}{'A'}{'T'}{'T'}{'C'}{'G'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}
  Pattern 65: Quality=-0.3080, ROC-AUC=0.8750, Support=24, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 66: Quality=-0.3080, ROC-AUC=0.9696, Support=156, Pattern={'T'}{'T'}{'G'}{'C'}{'G'}{'T'}{'A'}{'G'}{'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 67: Quality=-0.3088, ROC-AUC=0.8910, Support=25, Pattern={'T'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'C'}{'G'}{'G'}
  Pattern 68: Quality=-0.3107, ROC-AUC=0.9745, Support=263, Pattern={'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 69: Quality=-0.3110, ROC-AUC=0.9773, Support=462, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}
  Pattern 70: Quality=-0.3112, ROC-AUC=0.9765, Support=377, Pattern={'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 71: Quality=-0.3112, ROC-AUC=0.9769, Support=405, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 72: Quality=-0.3118, ROC-AUC=0.8971, Support=21, Pattern={'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}
  Pattern 73: Quality=-0.3124, ROC-AUC=0.9774, Support=368, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'T'}{'G'}{'A'}
  Pattern 74: Quality=-0.3125, ROC-AUC=0.9242, Support=49, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'G'}
  Pattern 75: Quality=-0.3125, ROC-AUC=0.9783, Support=448, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 76: Quality=-0.3127, ROC-AUC=0.9040, Support=40, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 77: Quality=-0.3129, ROC-AUC=0.9766, Support=272, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 78: Quality=-0.3130, ROC-AUC=0.9751, Support=190, Pattern={'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'A'}{'T'}{'G'}{'A'}{'G'}
  Pattern 79: Quality=-0.3130, ROC-AUC=0.8791, Support=20, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}
  Pattern 80: Quality=-0.3132, ROC-AUC=0.9769, Support=273, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}
  Pattern 81: Quality=-0.3133, ROC-AUC=0.9758, Support=209, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}
  Pattern 82: Quality=-0.3134, ROC-AUC=0.9780, Support=348, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}
  Pattern 83: Quality=-0.3135, ROC-AUC=0.9766, Support=237, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}
  Pattern 84: Quality=-0.3138, ROC-AUC=0.9773, Support=264, Pattern={'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'A'}{'A'}{'C'}{'C'}
  Pattern 85: Quality=-0.3138, ROC-AUC=0.9799, Support=534, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 86: Quality=-0.3139, ROC-AUC=0.9620, Support=207, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 87: Quality=-0.3139, ROC-AUC=0.9762, Support=198, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 88: Quality=-0.3140, ROC-AUC=0.9789, Support=385, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 89: Quality=-0.3140, ROC-AUC=0.9798, Support=493, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 90: Quality=-0.3141, ROC-AUC=0.9777, Support=273, Pattern={'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}
  Pattern 91: Quality=-0.3141, ROC-AUC=0.9796, Support=452, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 92: Quality=-0.3141, ROC-AUC=0.9797, Support=465, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 93: Quality=-0.3141, ROC-AUC=0.9781, Support=301, Pattern={'T'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 94: Quality=-0.3141, ROC-AUC=0.9000, Support=44, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 95: Quality=-0.3142, ROC-AUC=0.9803, Support=548, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 96: Quality=-0.3143, ROC-AUC=0.9790, Support=366, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}
  Pattern 97: Quality=-0.3145, ROC-AUC=0.9791, Support=358, Pattern={'G'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 98: Quality=-0.3146, ROC-AUC=0.9800, Support=455, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 99: Quality=-0.3149, ROC-AUC=0.9782, Support=257, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'G'}
  Pattern 100: Quality=-0.3149, ROC-AUC=0.9796, Support=373, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}
  Pattern 101: Quality=-0.3149, ROC-AUC=0.9778, Support=226, Pattern={'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'A'}{'T'}{'G'}{'A'}{'C'}{'G'}
  Pattern 102: Quality=-0.3149, ROC-AUC=0.9794, Support=347, Pattern={'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 103: Quality=-0.3152, ROC-AUC=0.9799, Support=379, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 104: Quality=-0.3152, ROC-AUC=0.9809, Support=506, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}
  Pattern 105: Quality=-0.3153, ROC-AUC=0.9775, Support=190, Pattern={'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}{'T'}{'C'}{'A'}{'C'}
  Pattern 106: Quality=-0.3153, ROC-AUC=0.9786, Support=248, Pattern={'T'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 107: Quality=-0.3154, ROC-AUC=0.9817, Support=632, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 108: Quality=-0.3155, ROC-AUC=0.9812, Support=526, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}
  Pattern 109: Quality=-0.3155, ROC-AUC=0.9812, Support=510, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 110: Quality=-0.3155, ROC-AUC=0.9815, Support=567, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}
  Pattern 111: Quality=-0.3155, ROC-AUC=0.9821, Support=681, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}
  Pattern 112: Quality=-0.3156, ROC-AUC=0.9797, Support=314, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 113: Quality=-0.3156, ROC-AUC=0.9795, Support=297, Pattern={'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}
  Pattern 114: Quality=-0.3156, ROC-AUC=0.9783, Support=210, Pattern={'T'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'C'}{'T'}{'A'}{'G'}{'A'}
  Pattern 115: Quality=-0.3158, ROC-AUC=0.9808, Support=412, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 116: Quality=-0.3158, ROC-AUC=0.9812, Support=482, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 117: Quality=-0.3158, ROC-AUC=0.9808, Support=418, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}
  Pattern 118: Quality=-0.3159, ROC-AUC=0.9809, Support=419, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'A'}{'A'}{'G'}{'C'}{'G'}
  Pattern 119: Quality=-0.3159, ROC-AUC=0.9802, Support=333, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'A'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 120: Quality=-0.3159, ROC-AUC=0.9798, Support=294, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}
  Pattern 121: Quality=-0.3159, ROC-AUC=0.9810, Support=429, Pattern={'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 122: Quality=-0.3160, ROC-AUC=0.9797, Support=282, Pattern={'C'}{'A'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'A'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}
  Pattern 123: Quality=-0.3161, ROC-AUC=0.9805, Support=344, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'A'}
  Pattern 124: Quality=-0.3161, ROC-AUC=0.9811, Support=414, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 125: Quality=-0.3161, ROC-AUC=0.9801, Support=298, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'T'}
  Pattern 126: Quality=-0.3161, ROC-AUC=0.9784, Support=183, Pattern={'T'}{'C'}{'T'}{'A'}{'C'}{'A'}{'T'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}
  Pattern 127: Quality=-0.3162, ROC-AUC=0.9808, Support=365, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}
  Pattern 128: Quality=-0.3162, ROC-AUC=0.9816, Support=464, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'A'}{'C'}{'G'}{'C'}
  Pattern 129: Quality=-0.3163, ROC-AUC=0.9823, Support=593, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}
  Pattern 130: Quality=-0.3163, ROC-AUC=0.9812, Support=401, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 131: Quality=-0.3163, ROC-AUC=0.9818, Support=496, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 132: Quality=-0.3163, ROC-AUC=0.9798, Support=252, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'G'}{'T'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 133: Quality=-0.3164, ROC-AUC=0.9784, Support=166, Pattern={'C'}{'A'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'A'}{'A'}{'A'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 134: Quality=-0.3165, ROC-AUC=0.9808, Support=322, Pattern={'A'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 135: Quality=-0.3166, ROC-AUC=0.9823, Support=537, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 136: Quality=-0.3167, ROC-AUC=0.9830, Support=673, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 137: Quality=-0.3167, ROC-AUC=0.9829, Support=633, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 138: Quality=-0.3167, ROC-AUC=0.9815, Support=378, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 139: Quality=-0.3168, ROC-AUC=0.9819, Support=432, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'A'}
  Pattern 140: Quality=-0.3168, ROC-AUC=0.9831, Support=685, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}
  Pattern 141: Quality=-0.3168, ROC-AUC=0.9794, Support=191, Pattern={'G'}{'G'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'T'}{'T'}{'T'}{'G'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'A'}
  Pattern 142: Quality=-0.3168, ROC-AUC=0.9828, Support=597, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 143: Quality=-0.3168, ROC-AUC=0.9826, Support=555, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 144: Quality=-0.3168, ROC-AUC=0.9802, Support=244, Pattern={'C'}{'G'}{'A'}{'T'}{'C'}{'T'}{'T'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}{'T'}{'T'}{'G'}{'C'}{'C'}
  Pattern 145: Quality=-0.3168, ROC-AUC=0.9830, Support=624, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 146: Quality=-0.3168, ROC-AUC=0.9818, Support=400, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}
  Pattern 147: Quality=-0.3169, ROC-AUC=0.9829, Support=596, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 148: Quality=-0.3169, ROC-AUC=0.9789, Support=161, Pattern={'G'}{'T'}{'T'}{'T'}{'A'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}
  Pattern 149: Quality=-0.3169, ROC-AUC=0.9831, Support=646, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 150: Quality=-0.3169, ROC-AUC=0.9808, Support=285, Pattern={'G'}{'G'}{'A'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 151: Quality=-0.3169, ROC-AUC=0.9809, Support=290, Pattern={'C'}{'C'}{'A'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}
  Pattern 152: Quality=-0.3170, ROC-AUC=0.9825, Support=502, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}
  Pattern 153: Quality=-0.3170, ROC-AUC=0.9805, Support=247, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}
  Pattern 154: Quality=-0.3170, ROC-AUC=0.9825, Support=488, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 155: Quality=-0.3171, ROC-AUC=0.9830, Support=565, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 156: Quality=-0.3172, ROC-AUC=0.9826, Support=464, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}
  Pattern 157: Quality=-0.3173, ROC-AUC=0.9828, Support=489, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 158: Quality=-0.3173, ROC-AUC=0.9193, Support=32, Pattern={'C'}{'T'}{'G'}{'G'}{'T'}{'A'}{'T'}{'A'}{'C'}{'G'}{'A'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'A'}
  Pattern 159: Quality=-0.3173, ROC-AUC=0.9826, Support=450, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 160: Quality=-0.3173, ROC-AUC=0.9792, Support=149, Pattern={'T'}{'G'}{'C'}{'A'}{'T'}{'A'}{'G'}{'G'}{'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'T'}{'T'}{'A'}{'G'}{'T'}
  Pattern 161: Quality=-0.3174, ROC-AUC=0.9830, Support=508, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 162: Quality=-0.3174, ROC-AUC=0.9822, Support=378, Pattern={'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 163: Quality=-0.3174, ROC-AUC=0.9829, Support=491, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 164: Quality=-0.3174, ROC-AUC=0.9830, Support=496, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 165: Quality=-0.3175, ROC-AUC=0.9826, Support=421, Pattern={'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}
  Pattern 166: Quality=-0.3176, ROC-AUC=0.9830, Support=463, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 167: Quality=-0.3176, ROC-AUC=0.9825, Support=383, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}
  Pattern 168: Quality=-0.3176, ROC-AUC=0.9816, Support=273, Pattern={'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}
  Pattern 169: Quality=-0.3176, ROC-AUC=0.9832, Support=484, Pattern={'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 170: Quality=-0.3177, ROC-AUC=0.9831, Support=478, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 171: Quality=-0.3177, ROC-AUC=0.9810, Support=224, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'T'}{'C'}{'A'}{'C'}{'T'}
  Pattern 172: Quality=-0.3177, ROC-AUC=0.9828, Support=407, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}
  Pattern 173: Quality=-0.3177, ROC-AUC=0.9814, Support=249, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 174: Quality=-0.3177, ROC-AUC=0.9828, Support=407, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 175: Quality=-0.3177, ROC-AUC=0.9818, Support=283, Pattern={'G'}{'G'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'C'}
  Pattern 176: Quality=-0.3179, ROC-AUC=0.9823, Support=312, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}
  Pattern 177: Quality=-0.3179, ROC-AUC=0.9819, Support=262, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 178: Quality=-0.3180, ROC-AUC=0.9832, Support=433, Pattern={'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 179: Quality=-0.3182, ROC-AUC=0.9817, Support=219, Pattern={'T'}{'C'}{'A'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 180: Quality=-0.3182, ROC-AUC=0.9831, Support=358, Pattern={'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}
  Pattern 181: Quality=-0.3182, ROC-AUC=0.9308, Support=61, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 182: Quality=-0.3184, ROC-AUC=0.9821, Support=224, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'A'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'A'}{'G'}{'T'}{'G'}{'T'}
  Pattern 183: Quality=-0.3187, ROC-AUC=0.9829, Support=267, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'T'}
  Pattern 184: Quality=-0.3188, ROC-AUC=0.8939, Support=23, Pattern={'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'G'}{'A'}{'C'}{'C'}{'T'}
  Pattern 185: Quality=-0.3198, ROC-AUC=0.9667, Support=251, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}
  Pattern 186: Quality=-0.3204, ROC-AUC=0.9645, Support=172, Pattern={'G'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 187: Quality=-0.3219, ROC-AUC=0.9219, Support=54, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'A'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 188: Quality=-0.3222, ROC-AUC=0.9370, Support=81, Pattern={'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'A'}
  Pattern 189: Quality=-0.3234, ROC-AUC=0.9711, Support=364, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}
  Pattern 190: Quality=-0.3239, ROC-AUC=0.9048, Support=60, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 191: Quality=-0.3240, ROC-AUC=0.9414, Support=106, Pattern={'C'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 192: Quality=-0.3251, ROC-AUC=0.9130, Support=31, Pattern={'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'G'}{'A'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'A'}{'G'}{'G'}{'A'}
  Pattern 193: Quality=-0.3258, ROC-AUC=0.9684, Support=174, Pattern={'C'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}
  Pattern 194: Quality=-0.3260, ROC-AUC=0.9691, Support=191, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 195: Quality=-0.3267, ROC-AUC=0.9739, Support=427, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}
  Pattern 196: Quality=-0.3267, ROC-AUC=0.9709, Support=239, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'A'}{'C'}{'G'}
  Pattern 197: Quality=-0.3268, ROC-AUC=0.9721, Support=296, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'A'}
  Pattern 198: Quality=-0.3271, ROC-AUC=0.9728, Support=325, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}
  Pattern 199: Quality=-0.3279, ROC-AUC=0.9516, Support=92, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}
  Pattern 200: Quality=-0.3280, ROC-AUC=0.8984, Support=32, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'A'}{'C'}{'A'}{'G'}{'T'}
  Pattern 201: Quality=-0.3280, ROC-AUC=0.9730, Support=294, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 202: Quality=-0.3282, ROC-AUC=0.9710, Support=201, Pattern={'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'C'}{'G'}
  Pattern 203: Quality=-0.3282, ROC-AUC=0.8935, Support=26, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}
  Pattern 204: Quality=-0.3285, ROC-AUC=0.9542, Support=115, Pattern={'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 205: Quality=-0.3286, ROC-AUC=0.9737, Support=320, Pattern={'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 206: Quality=-0.3286, ROC-AUC=0.9132, Support=44, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'T'}{'T'}{'G'}{'G'}{'C'}{'T'}
  Pattern 207: Quality=-0.3287, ROC-AUC=0.9737, Support=312, Pattern={'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}
  Pattern 208: Quality=-0.3289, ROC-AUC=0.8947, Support=27, Pattern={'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}
  Pattern 209: Quality=-0.3290, ROC-AUC=0.9709, Support=176, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 210: Quality=-0.3290, ROC-AUC=0.9200, Support=40, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 211: Quality=-0.3292, ROC-AUC=0.9408, Support=83, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'A'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 212: Quality=-0.3293, ROC-AUC=0.9731, Support=253, Pattern={'T'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 213: Quality=-0.3295, ROC-AUC=0.9737, Support=280, Pattern={'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 214: Quality=-0.3296, ROC-AUC=0.9744, Support=313, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 215: Quality=-0.3298, ROC-AUC=0.9367, Support=60, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 216: Quality=-0.3300, ROC-AUC=0.9043, Support=28, Pattern={'C'}{'C'}{'T'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 217: Quality=-0.3302, ROC-AUC=0.9744, Support=289, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'G'}{'G'}{'A'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 218: Quality=-0.3303, ROC-AUC=0.9746, Support=298, Pattern={'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 219: Quality=-0.3303, ROC-AUC=0.9717, Support=165, Pattern={'T'}{'G'}{'G'}{'T'}{'G'}{'C'}{'A'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 220: Quality=-0.3303, ROC-AUC=0.9745, Support=287, Pattern={'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 221: Quality=-0.3304, ROC-AUC=0.9743, Support=272, Pattern={'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'G'}
  Pattern 222: Quality=-0.3311, ROC-AUC=0.9759, Support=337, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 223: Quality=-0.3312, ROC-AUC=0.9761, Support=350, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}
  Pattern 224: Quality=-0.3313, ROC-AUC=0.9702, Support=106, Pattern={'C'}{'T'}{'T'}{'A'}{'C'}{'T'}{'T'}{'A'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}
  Pattern 225: Quality=-0.3319, ROC-AUC=0.9767, Support=357, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}
  Pattern 226: Quality=-0.3320, ROC-AUC=0.9774, Support=416, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}
  Pattern 227: Quality=-0.3321, ROC-AUC=0.9725, Support=141, Pattern={'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'T'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}
  Pattern 228: Quality=-0.3322, ROC-AUC=0.9788, Support=574, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 229: Quality=-0.3323, ROC-AUC=0.9750, Support=221, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'A'}{'G'}{'T'}
  Pattern 230: Quality=-0.3324, ROC-AUC=0.9760, Support=277, Pattern={'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 231: Quality=-0.3324, ROC-AUC=0.9752, Support=226, Pattern={'G'}{'A'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'C'}{'G'}
  Pattern 232: Quality=-0.3324, ROC-AUC=0.9770, Support=342, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}
  Pattern 233: Quality=-0.3326, ROC-AUC=0.9779, Support=413, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 234: Quality=-0.3327, ROC-AUC=0.9770, Support=329, Pattern={'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 235: Quality=-0.3329, ROC-AUC=0.9785, Support=462, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 236: Quality=-0.3330, ROC-AUC=0.9745, Support=174, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 237: Quality=-0.3332, ROC-AUC=0.9784, Support=413, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 238: Quality=-0.3336, ROC-AUC=0.9783, Support=375, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 239: Quality=-0.3337, ROC-AUC=0.9756, Support=191, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}
  Pattern 240: Quality=-0.3337, ROC-AUC=0.9726, Support=102, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'A'}{'G'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}
  Pattern 241: Quality=-0.3338, ROC-AUC=0.9749, Support=159, Pattern={'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}
  Pattern 242: Quality=-0.3338, ROC-AUC=0.8909, Support=21, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'A'}
  Pattern 243: Quality=-0.3339, ROC-AUC=0.9789, Support=408, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 244: Quality=-0.3339, ROC-AUC=0.9776, Support=287, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'G'}{'A'}{'T'}{'C'}{'T'}{'G'}
  Pattern 245: Quality=-0.3339, ROC-AUC=0.9740, Support=125, Pattern={'G'}{'T'}{'A'}{'T'}{'G'}{'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'G'}{'T'}{'C'}{'A'}{'T'}
  Pattern 246: Quality=-0.3340, ROC-AUC=0.9769, Support=240, Pattern={'G'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'G'}{'G'}
  Pattern 247: Quality=-0.3340, ROC-AUC=0.9764, Support=213, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 248: Quality=-0.3340, ROC-AUC=0.9788, Support=388, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 249: Quality=-0.3342, ROC-AUC=0.9759, Support=180, Pattern={'G'}{'G'}{'A'}{'G'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}
  Pattern 250: Quality=-0.3342, ROC-AUC=0.9801, Support=543, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 251: Quality=-0.3343, ROC-AUC=0.9784, Support=334, Pattern={'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 252: Quality=-0.3343, ROC-AUC=0.9770, Support=224, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 253: Quality=-0.3344, ROC-AUC=0.9795, Support=432, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}
  Pattern 254: Quality=-0.3345, ROC-AUC=0.9765, Support=192, Pattern={'G'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'A'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 255: Quality=-0.3346, ROC-AUC=0.9717, Support=69, Pattern={'T'}{'A'}{'T'}{'A'}{'A'}{'T'}{'G'}{'G'}{'A'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}
  Pattern 256: Quality=-0.3347, ROC-AUC=0.9792, Support=378, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}
  Pattern 257: Quality=-0.3348, ROC-AUC=0.9801, Support=479, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 258: Quality=-0.3348, ROC-AUC=0.9793, Support=366, Pattern={'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}
  Pattern 259: Quality=-0.3348, ROC-AUC=0.9780, Support=258, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 260: Quality=-0.3349, ROC-AUC=0.9742, Support=105, Pattern={'G'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}{'A'}
  Pattern 261: Quality=-0.3349, ROC-AUC=0.9786, Support=291, Pattern={'T'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 262: Quality=-0.3349, ROC-AUC=0.9775, Support=218, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'A'}
  Pattern 263: Quality=-0.3350, ROC-AUC=0.9786, Support=288, Pattern={'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'A'}
  Pattern 264: Quality=-0.3350, ROC-AUC=0.9234, Support=65, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 265: Quality=-0.3350, ROC-AUC=0.9796, Support=385, Pattern={'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 266: Quality=-0.3351, ROC-AUC=0.9805, Support=491, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 267: Quality=-0.3351, ROC-AUC=0.9809, Support=556, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 268: Quality=-0.3351, ROC-AUC=0.9774, Support=204, Pattern={'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 269: Quality=-0.3351, ROC-AUC=0.9780, Support=235, Pattern={'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 270: Quality=-0.3352, ROC-AUC=0.9776, Support=214, Pattern={'G'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}
  Pattern 271: Quality=-0.3352, ROC-AUC=0.9812, Support=595, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 272: Quality=-0.3353, ROC-AUC=0.9804, Support=440, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'G'}
  Pattern 273: Quality=-0.3354, ROC-AUC=0.9805, Support=448, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}
  Pattern 274: Quality=-0.3355, ROC-AUC=0.9777, Support=198, Pattern={'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 275: Quality=-0.3355, ROC-AUC=0.9793, Support=307, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'A'}{'C'}{'C'}
  Pattern 276: Quality=-0.3355, ROC-AUC=0.9651, Support=263, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 277: Quality=-0.3355, ROC-AUC=0.9798, Support=348, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 278: Quality=-0.3355, ROC-AUC=0.9777, Support=194, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}
  Pattern 279: Quality=-0.3355, ROC-AUC=0.9796, Support=330, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'T'}
  Pattern 280: Quality=-0.3357, ROC-AUC=0.9815, Support=578, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 281: Quality=-0.3358, ROC-AUC=0.9782, Support=210, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}
  Pattern 282: Quality=-0.3358, ROC-AUC=0.9809, Support=462, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 283: Quality=-0.3358, ROC-AUC=0.9788, Support=244, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}
  Pattern 284: Quality=-0.3358, ROC-AUC=0.9773, Support=165, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}
  Pattern 285: Quality=-0.3358, ROC-AUC=0.9788, Support=242, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'C'}
  Pattern 286: Quality=-0.3358, ROC-AUC=0.9780, Support=195, Pattern={'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}
  Pattern 287: Quality=-0.3358, ROC-AUC=0.9792, Support=273, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}
  Pattern 288: Quality=-0.3359, ROC-AUC=0.9798, Support=317, Pattern={'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 289: Quality=-0.3359, ROC-AUC=0.9818, Support=600, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 290: Quality=-0.3359, ROC-AUC=0.9808, Support=423, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}
  Pattern 291: Quality=-0.3360, ROC-AUC=0.9808, Support=411, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 292: Quality=-0.3360, ROC-AUC=0.9795, Support=282, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 293: Quality=-0.3360, ROC-AUC=0.9816, Support=543, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 294: Quality=-0.3361, ROC-AUC=0.9806, Support=374, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 295: Quality=-0.3361, ROC-AUC=0.9798, Support=293, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}
  Pattern 296: Quality=-0.3361, ROC-AUC=0.9804, Support=346, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 297: Quality=-0.3361, ROC-AUC=0.9808, Support=394, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}
  Pattern 298: Quality=-0.3362, ROC-AUC=0.9817, Support=519, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 299: Quality=-0.3362, ROC-AUC=0.9281, Support=26, Pattern={'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'G'}{'T'}{'C'}{'G'}
  Pattern 300: Quality=-0.3363, ROC-AUC=0.9799, Support=290, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 301: Quality=-0.3363, ROC-AUC=0.9792, Support=236, Pattern={'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 302: Quality=-0.3363, ROC-AUC=0.9801, Support=302, Pattern={'C'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}
  Pattern 303: Quality=-0.3363, ROC-AUC=0.9797, Support=265, Pattern={'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}
  Pattern 304: Quality=-0.3364, ROC-AUC=0.9809, Support=366, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}
  Pattern 305: Quality=-0.3365, ROC-AUC=0.9815, Support=443, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 306: Quality=-0.3366, ROC-AUC=0.9797, Support=241, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}
  Pattern 307: Quality=-0.3366, ROC-AUC=0.9806, Support=320, Pattern={'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}
  Pattern 308: Quality=-0.3367, ROC-AUC=0.9776, Support=131, Pattern={'A'}{'A'}{'G'}{'C'}{'A'}{'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 309: Quality=-0.3367, ROC-AUC=0.9810, Support=351, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}
  Pattern 310: Quality=-0.3367, ROC-AUC=0.9811, Support=359, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'A'}
  Pattern 311: Quality=-0.3367, ROC-AUC=0.9821, Support=508, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 312: Quality=-0.3368, ROC-AUC=0.9663, Support=284, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'T'}
  Pattern 313: Quality=-0.3368, ROC-AUC=0.9762, Support=90, Pattern={'G'}{'T'}{'C'}{'G'}{'A'}{'G'}{'C'}{'A'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'A'}{'A'}{'T'}{'T'}{'T'}{'T'}
  Pattern 314: Quality=-0.3368, ROC-AUC=0.9794, Support=207, Pattern={'G'}{'G'}{'C'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}
  Pattern 315: Quality=-0.3368, ROC-AUC=0.9824, Support=553, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 316: Quality=-0.3368, ROC-AUC=0.9760, Support=85, Pattern={'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'A'}{'A'}{'A'}{'G'}
  Pattern 317: Quality=-0.3368, ROC-AUC=0.9810, Support=330, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}
  Pattern 318: Quality=-0.3369, ROC-AUC=0.9805, Support=285, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 319: Quality=-0.3369, ROC-AUC=0.9782, Support=142, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'C'}{'T'}
  Pattern 320: Quality=-0.3370, ROC-AUC=0.9794, Support=189, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'A'}{'A'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 321: Quality=-0.3371, ROC-AUC=0.9808, Support=284, Pattern={'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 322: Quality=-0.3372, ROC-AUC=0.9800, Support=216, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}
  Pattern 323: Quality=-0.3372, ROC-AUC=0.9818, Support=382, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 324: Quality=-0.3373, ROC-AUC=0.9821, Support=410, Pattern={'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 325: Quality=-0.3373, ROC-AUC=0.9820, Support=407, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 326: Quality=-0.3373, ROC-AUC=0.9831, Support=596, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 327: Quality=-0.3373, ROC-AUC=0.9807, Support=253, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}
  Pattern 328: Quality=-0.3373, ROC-AUC=0.9800, Support=203, Pattern={'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'A'}
  Pattern 329: Quality=-0.3374, ROC-AUC=0.9808, Support=259, Pattern={'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 330: Quality=-0.3374, ROC-AUC=0.9828, Support=509, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 331: Quality=-0.3374, ROC-AUC=0.9797, Support=179, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 332: Quality=-0.3375, ROC-AUC=0.9823, Support=412, Pattern={'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}
  Pattern 333: Quality=-0.3375, ROC-AUC=0.9824, Support=425, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 334: Quality=-0.3375, ROC-AUC=0.9631, Support=172, Pattern={'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}
  Pattern 335: Quality=-0.3375, ROC-AUC=0.9806, Support=227, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}
  Pattern 336: Quality=-0.3375, ROC-AUC=0.9801, Support=194, Pattern={'C'}{'T'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'A'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}
  Pattern 337: Quality=-0.3376, ROC-AUC=0.9827, Support=464, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 338: Quality=-0.3376, ROC-AUC=0.9825, Support=425, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 339: Quality=-0.3376, ROC-AUC=0.9622, Support=152, Pattern={'G'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 340: Quality=-0.3376, ROC-AUC=0.9821, Support=361, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 341: Quality=-0.3377, ROC-AUC=0.9827, Support=442, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 342: Quality=-0.3377, ROC-AUC=0.9819, Support=325, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}
  Pattern 343: Quality=-0.3377, ROC-AUC=0.9825, Support=401, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 344: Quality=-0.3377, ROC-AUC=0.9821, Support=344, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 345: Quality=-0.3378, ROC-AUC=0.9832, Support=512, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 346: Quality=-0.3378, ROC-AUC=0.9832, Support=499, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 347: Quality=-0.3378, ROC-AUC=0.9811, Support=232, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 348: Quality=-0.3378, ROC-AUC=0.9830, Support=458, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 349: Quality=-0.3378, ROC-AUC=0.9804, Support=187, Pattern={'C'}{'A'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}
  Pattern 350: Quality=-0.3378, ROC-AUC=0.9819, Support=309, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 351: Quality=-0.3379, ROC-AUC=0.9000, Support=28, Pattern={'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 352: Quality=-0.3379, ROC-AUC=0.9830, Support=451, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 353: Quality=-0.3379, ROC-AUC=0.9826, Support=376, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 354: Quality=-0.3380, ROC-AUC=0.9831, Support=447, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 355: Quality=-0.3380, ROC-AUC=0.9832, Support=460, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 356: Quality=-0.3381, ROC-AUC=0.9826, Support=349, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}
  Pattern 357: Quality=-0.3381, ROC-AUC=0.9814, Support=230, Pattern={'G'}{'T'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}
  Pattern 358: Quality=-0.3381, ROC-AUC=0.9821, Support=291, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}
  Pattern 359: Quality=-0.3381, ROC-AUC=0.9824, Support=317, Pattern={'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 360: Quality=-0.3381, ROC-AUC=0.9821, Support=283, Pattern={'A'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 361: Quality=-0.3382, ROC-AUC=0.9808, Support=181, Pattern={'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 362: Quality=-0.3382, ROC-AUC=0.9813, Support=214, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}
  Pattern 363: Quality=-0.3382, ROC-AUC=0.9828, Support=366, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}
  Pattern 364: Quality=-0.3382, ROC-AUC=0.9808, Support=180, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}
  Pattern 365: Quality=-0.3382, ROC-AUC=0.9818, Support=247, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}
  Pattern 366: Quality=-0.3383, ROC-AUC=0.9827, Support=333, Pattern={'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 367: Quality=-0.3383, ROC-AUC=0.9826, Support=312, Pattern={'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 368: Quality=-0.3383, ROC-AUC=0.9802, Support=138, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'A'}{'G'}{'T'}{'G'}{'G'}{'A'}{'T'}{'A'}{'C'}{'G'}{'C'}
  Pattern 369: Quality=-0.3384, ROC-AUC=0.9822, Support=262, Pattern={'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 370: Quality=-0.3384, ROC-AUC=0.9827, Support=323, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 371: Quality=-0.3384, ROC-AUC=0.9830, Support=351, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 372: Quality=-0.3384, ROC-AUC=0.9808, Support=159, Pattern={'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 373: Quality=-0.3385, ROC-AUC=0.9823, Support=262, Pattern={'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'G'}{'T'}{'G'}
  Pattern 374: Quality=-0.3385, ROC-AUC=0.9814, Support=187, Pattern={'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}
  Pattern 375: Quality=-0.3386, ROC-AUC=0.9823, Support=245, Pattern={'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}
  Pattern 376: Quality=-0.3386, ROC-AUC=0.9616, Support=129, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 377: Quality=-0.3386, ROC-AUC=0.9800, Support=115, Pattern={'T'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'T'}{'T'}{'T'}{'A'}{'G'}{'G'}{'T'}{'A'}{'C'}{'T'}{'T'}{'T'}{'G'}
  Pattern 378: Quality=-0.3387, ROC-AUC=0.9824, Support=247, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 379: Quality=-0.3388, ROC-AUC=0.9832, Support=303, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 380: Quality=-0.3388, ROC-AUC=0.9815, Support=165, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 381: Quality=-0.3389, ROC-AUC=0.9830, Support=269, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}
  Pattern 382: Quality=-0.3389, ROC-AUC=0.9831, Support=279, Pattern={'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 383: Quality=-0.3389, ROC-AUC=0.9205, Support=30, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'A'}{'G'}{'C'}{'A'}
  Pattern 384: Quality=-0.3389, ROC-AUC=0.9806, Support=114, Pattern={'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'G'}{'T'}{'A'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}
  Pattern 385: Quality=-0.3390, ROC-AUC=0.9823, Support=201, Pattern={'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 386: Quality=-0.3390, ROC-AUC=0.9823, Support=191, Pattern={'A'}{'A'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 387: Quality=-0.3391, ROC-AUC=0.9823, Support=187, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 388: Quality=-0.3392, ROC-AUC=0.9585, Support=84, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 389: Quality=-0.3392, ROC-AUC=0.9831, Support=241, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 390: Quality=-0.3392, ROC-AUC=0.9821, Support=164, Pattern={'T'}{'A'}{'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'A'}{'A'}{'G'}
  Pattern 391: Quality=-0.3392, ROC-AUC=0.9831, Support=231, Pattern={'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 392: Quality=-0.3393, ROC-AUC=0.9830, Support=209, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'C'}
  Pattern 393: Quality=-0.3394, ROC-AUC=0.9829, Support=188, Pattern={'A'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}
  Pattern 394: Quality=-0.3395, ROC-AUC=0.9825, Support=155, Pattern={'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}
  Pattern 395: Quality=-0.3396, ROC-AUC=0.9831, Support=177, Pattern={'T'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'T'}{'A'}{'C'}{'A'}{'G'}{'G'}{'G'}
  Pattern 396: Quality=-0.3398, ROC-AUC=0.9827, Support=137, Pattern={'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}
  Pattern 397: Quality=-0.3398, ROC-AUC=0.9823, Support=119, Pattern={'T'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'A'}
  Pattern 398: Quality=-0.3398, ROC-AUC=0.9823, Support=113, Pattern={'T'}{'G'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'T'}{'T'}{'C'}{'T'}
  Pattern 399: Quality=-0.3398, ROC-AUC=0.9832, Support=161, Pattern={'C'}{'T'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}
  Pattern 400: Quality=-0.3400, ROC-AUC=0.9828, Support=125, Pattern={'A'}{'G'}{'G'}{'T'}{'A'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}
  Pattern 401: Quality=-0.3400, ROC-AUC=0.9640, Support=157, Pattern={'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 402: Quality=-0.3400, ROC-AUC=0.9333, Support=63, Pattern={'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}
  Pattern 403: Quality=-0.3402, ROC-AUC=0.9612, Support=106, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'A'}{'C'}{'C'}
  Pattern 404: Quality=-0.3403, ROC-AUC=0.9636, Support=143, Pattern={'A'}{'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'A'}{'G'}{'G'}{'A'}
  Pattern 405: Quality=-0.3404, ROC-AUC=0.9620, Support=116, Pattern={'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 406: Quality=-0.3413, ROC-AUC=0.9667, Support=203, Pattern={'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'A'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 407: Quality=-0.3414, ROC-AUC=0.9710, Support=408, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 408: Quality=-0.3415, ROC-AUC=0.9651, Support=158, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'A'}
  Pattern 409: Quality=-0.3415, ROC-AUC=0.9008, Support=37, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 410: Quality=-0.3420, ROC-AUC=0.9555, Support=174, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 411: Quality=-0.3427, ROC-AUC=0.9503, Support=100, Pattern={'C'}{'C'}{'A'}{'C'}{'A'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 412: Quality=-0.3428, ROC-AUC=0.9696, Support=275, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'T'}{'G'}{'C'}{'A'}{'C'}
  Pattern 413: Quality=-0.3428, ROC-AUC=0.9286, Support=42, Pattern={'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'A'}{'A'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}
  Pattern 414: Quality=-0.3430, ROC-AUC=0.9677, Support=200, Pattern={'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}
  Pattern 415: Quality=-0.3431, ROC-AUC=0.9675, Support=192, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 416: Quality=-0.3432, ROC-AUC=0.9692, Support=246, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 417: Quality=-0.3440, ROC-AUC=0.9372, Support=123, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}
  Pattern 418: Quality=-0.3442, ROC-AUC=0.9656, Support=128, Pattern={'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'A'}{'C'}{'G'}{'G'}{'G'}
  Pattern 419: Quality=-0.3442, ROC-AUC=0.9675, Support=168, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 420: Quality=-0.3444, ROC-AUC=0.9641, Support=101, Pattern={'G'}{'G'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 421: Quality=-0.3445, ROC-AUC=0.9205, Support=43, Pattern={'C'}{'G'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 422: Quality=-0.3446, ROC-AUC=0.9667, Support=142, Pattern={'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 423: Quality=-0.3447, ROC-AUC=0.9693, Support=212, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'A'}{'C'}
  Pattern 424: Quality=-0.3447, ROC-AUC=0.9417, Support=43, Pattern={'T'}{'A'}{'G'}{'A'}{'A'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}
  Pattern 425: Quality=-0.3449, ROC-AUC=0.9118, Support=27, Pattern={'G'}{'A'}{'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 426: Quality=-0.3449, ROC-AUC=0.9118, Support=27, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'A'}
  Pattern 427: Quality=-0.3450, ROC-AUC=0.9444, Support=53, Pattern={'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}
  Pattern 428: Quality=-0.3455, ROC-AUC=0.9125, Support=42, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'G'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 429: Quality=-0.3456, ROC-AUC=0.9674, Support=141, Pattern={'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'C'}
  Pattern 430: Quality=-0.3459, ROC-AUC=0.9712, Support=255, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'A'}{'G'}{'C'}
  Pattern 431: Quality=-0.3459, ROC-AUC=0.8872, Support=26, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}
  Pattern 432: Quality=-0.3462, ROC-AUC=0.9703, Support=208, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'C'}
  Pattern 433: Quality=-0.3462, ROC-AUC=0.9412, Support=38, Pattern={'A'}{'C'}{'T'}{'A'}{'G'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'G'}{'T'}{'T'}{'G'}{'C'}
  Pattern 434: Quality=-0.3465, ROC-AUC=0.9457, Support=54, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 435: Quality=-0.3466, ROC-AUC=0.9000, Support=23, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}
  Pattern 436: Quality=-0.3468, ROC-AUC=0.9641, Support=74, Pattern={'T'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'G'}{'A'}{'A'}{'A'}{'A'}{'A'}{'A'}{'A'}{'A'}
  Pattern 437: Quality=-0.3469, ROC-AUC=0.9659, Support=95, Pattern={'A'}{'A'}{'A'}{'T'}{'T'}{'A'}{'T'}{'T'}{'T'}{'T'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 438: Quality=-0.3470, ROC-AUC=0.9521, Support=93, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 439: Quality=-0.3471, ROC-AUC=0.8981, Support=21, Pattern={'G'}{'A'}{'A'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 440: Quality=-0.3472, ROC-AUC=0.9464, Support=55, Pattern={'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'A'}{'G'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 441: Quality=-0.3472, ROC-AUC=0.9474, Support=60, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}
  Pattern 442: Quality=-0.3472, ROC-AUC=0.9000, Support=32, Pattern={'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}
  Pattern 443: Quality=-0.3473, ROC-AUC=0.9513, Support=85, Pattern={'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'C'}
  Pattern 444: Quality=-0.3473, ROC-AUC=0.9674, Support=112, Pattern={'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 445: Quality=-0.3473, ROC-AUC=0.9279, Support=34, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'A'}{'A'}{'G'}{'A'}{'G'}{'C'}{'G'}{'G'}
  Pattern 446: Quality=-0.3473, ROC-AUC=0.9585, Support=179, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}
  Pattern 447: Quality=-0.3474, ROC-AUC=0.9664, Support=96, Pattern={'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'G'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 448: Quality=-0.3475, ROC-AUC=0.9731, Support=293, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}
  Pattern 449: Quality=-0.3478, ROC-AUC=0.9174, Support=33, Pattern={'C'}{'C'}{'A'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'A'}{'G'}{'A'}
  Pattern 450: Quality=-0.3478, ROC-AUC=0.9725, Support=252, Pattern={'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 451: Quality=-0.3481, ROC-AUC=0.9735, Support=297, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 452: Quality=-0.3484, ROC-AUC=0.9341, Support=20, Pattern={'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'A'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'C'}
  Pattern 453: Quality=-0.3484, ROC-AUC=0.9698, Support=142, Pattern={'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}
  Pattern 454: Quality=-0.3484, ROC-AUC=0.9634, Support=54, Pattern={'G'}{'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'G'}{'A'}{'A'}{'C'}{'T'}{'A'}{'A'}{'A'}
  Pattern 455: Quality=-0.3488, ROC-AUC=0.8917, Support=22, Pattern={'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 456: Quality=-0.3488, ROC-AUC=0.9490, Support=62, Pattern={'G'}{'G'}{'G'}{'A'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'C'}{'G'}
  Pattern 457: Quality=-0.3489, ROC-AUC=0.9626, Support=45, Pattern={'G'}{'G'}{'A'}{'T'}{'A'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}
  Pattern 458: Quality=-0.3489, ROC-AUC=0.9743, Support=311, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 459: Quality=-0.3489, ROC-AUC=0.9694, Support=123, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 460: Quality=-0.3490, ROC-AUC=0.9649, Support=61, Pattern={'C'}{'G'}{'A'}{'C'}{'T'}{'A'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'T'}{'A'}{'A'}{'C'}{'T'}{'T'}
  Pattern 461: Quality=-0.3494, ROC-AUC=0.9727, Support=204, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}
  Pattern 462: Quality=-0.3495, ROC-AUC=0.9685, Support=96, Pattern={'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}
  Pattern 463: Quality=-0.3495, ROC-AUC=0.9742, Support=271, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 464: Quality=-0.3497, ROC-AUC=0.9687, Support=97, Pattern={'A'}{'A'}{'G'}{'T'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}
  Pattern 465: Quality=-0.3498, ROC-AUC=0.9712, Support=146, Pattern={'A'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 466: Quality=-0.3498, ROC-AUC=0.9671, Support=74, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}
  Pattern 467: Quality=-0.3500, ROC-AUC=0.9659, Support=60, Pattern={'G'}{'T'}{'A'}{'T'}{'G'}{'A'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'G'}{'T'}{'C'}{'A'}{'T'}
  Pattern 468: Quality=-0.3500, ROC-AUC=0.9736, Support=223, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 469: Quality=-0.3501, ROC-AUC=0.9727, Support=185, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'G'}{'A'}
  Pattern 470: Quality=-0.3503, ROC-AUC=0.9648, Support=48, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'T'}{'C'}{'T'}{'T'}{'A'}{'G'}{'T'}{'A'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 471: Quality=-0.3504, ROC-AUC=0.9704, Support=114, Pattern={'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'A'}{'A'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 472: Quality=-0.3505, ROC-AUC=0.9748, Support=261, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}
  Pattern 473: Quality=-0.3506, ROC-AUC=0.9286, Support=31, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 474: Quality=-0.3506, ROC-AUC=0.9701, Support=103, Pattern={'G'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 475: Quality=-0.3511, ROC-AUC=0.9749, Support=245, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 476: Quality=-0.3512, ROC-AUC=0.9735, Support=176, Pattern={'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 477: Quality=-0.3513, ROC-AUC=0.9711, Support=109, Pattern={'T'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}
  Pattern 478: Quality=-0.3513, ROC-AUC=0.9321, Support=70, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 479: Quality=-0.3514, ROC-AUC=0.9729, Support=152, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}
  Pattern 480: Quality=-0.3517, ROC-AUC=0.9723, Support=126, Pattern={'C'}{'G'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}
  Pattern 481: Quality=-0.3518, ROC-AUC=0.9768, Support=327, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}
  Pattern 482: Quality=-0.3518, ROC-AUC=0.9739, Support=170, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 483: Quality=-0.3518, ROC-AUC=0.9760, Support=269, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 484: Quality=-0.3518, ROC-AUC=0.9730, Support=142, Pattern={'C'}{'C'}{'G'}{'A'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 485: Quality=-0.3521, ROC-AUC=0.9770, Support=317, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}
  Pattern 486: Quality=-0.3522, ROC-AUC=0.9715, Support=99, Pattern={'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 487: Quality=-0.3522, ROC-AUC=0.9688, Support=62, Pattern={'A'}{'A'}{'G'}{'C'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'T'}
  Pattern 488: Quality=-0.3523, ROC-AUC=0.9572, Support=112, Pattern={'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 489: Quality=-0.3523, ROC-AUC=0.9740, Support=157, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'A'}
  Pattern 490: Quality=-0.3524, ROC-AUC=0.9788, Support=491, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 491: Quality=-0.3526, ROC-AUC=0.9722, Support=102, Pattern={'A'}{'A'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 492: Quality=-0.3527, ROC-AUC=0.9709, Support=79, Pattern={'G'}{'A'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}{'G'}{'A'}
  Pattern 493: Quality=-0.3527, ROC-AUC=0.9749, Support=173, Pattern={'A'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 494: Quality=-0.3527, ROC-AUC=0.9287, Support=54, Pattern={'C'}{'A'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'C'}
  Pattern 495: Quality=-0.3528, ROC-AUC=0.9762, Support=227, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 496: Quality=-0.3528, ROC-AUC=0.9773, Support=296, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 497: Quality=-0.3529, ROC-AUC=0.9748, Support=162, Pattern={'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'G'}
  Pattern 498: Quality=-0.3530, ROC-AUC=0.9358, Support=45, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'A'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 499: Quality=-0.3530, ROC-AUC=0.9699, Support=62, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'A'}{'G'}{'G'}{'T'}{'T'}{'C'}{'G'}
  Pattern 500: Quality=-0.3530, ROC-AUC=0.9731, Support=110, Pattern={'G'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'G'}
  Pattern 501: Quality=-0.3531, ROC-AUC=0.9754, Support=178, Pattern={'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}
  Pattern 502: Quality=-0.3533, ROC-AUC=0.9785, Support=361, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 503: Quality=-0.3535, ROC-AUC=0.9797, Support=490, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 504: Quality=-0.3535, ROC-AUC=0.9785, Support=339, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 505: Quality=-0.3536, ROC-AUC=0.9595, Support=133, Pattern={'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 506: Quality=-0.3536, ROC-AUC=0.9745, Support=129, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'T'}{'T'}{'A'}
  Pattern 507: Quality=-0.3538, ROC-AUC=0.9736, Support=103, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}{'G'}
  Pattern 508: Quality=-0.3538, ROC-AUC=0.9761, Support=175, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 509: Quality=-0.3538, ROC-AUC=0.9763, Support=183, Pattern={'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 510: Quality=-0.3538, ROC-AUC=0.9774, Support=238, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 511: Quality=-0.3539, ROC-AUC=0.9759, Support=164, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 512: Quality=-0.3541, ROC-AUC=0.9797, Support=412, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 513: Quality=-0.3541, ROC-AUC=0.9751, Support=128, Pattern={'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'G'}{'G'}{'A'}{'T'}
  Pattern 514: Quality=-0.3541, ROC-AUC=0.9778, Support=246, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 515: Quality=-0.3542, ROC-AUC=0.9719, Support=67, Pattern={'G'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}{'A'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 516: Quality=-0.3545, ROC-AUC=0.9729, Support=74, Pattern={'C'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}
  Pattern 517: Quality=-0.3545, ROC-AUC=0.9740, Support=91, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'A'}{'A'}{'G'}{'T'}{'G'}{'A'}{'T'}{'A'}{'A'}{'C'}{'G'}
  Pattern 518: Quality=-0.3546, ROC-AUC=0.9250, Support=21, Pattern={'T'}{'G'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'C'}{'A'}{'C'}{'C'}{'A'}{'A'}{'G'}{'A'}{'C'}{'T'}{'T'}{'C'}{'T'}
  Pattern 519: Quality=-0.3546, ROC-AUC=0.9772, Support=188, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 520: Quality=-0.3546, ROC-AUC=0.9792, Support=320, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 521: Quality=-0.3546, ROC-AUC=0.9744, Support=96, Pattern={'A'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'A'}{'A'}{'T'}{'C'}{'C'}
  Pattern 522: Quality=-0.3546, ROC-AUC=0.9776, Support=204, Pattern={'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}
  Pattern 523: Quality=-0.3547, ROC-AUC=0.9770, Support=171, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}
  Pattern 524: Quality=-0.3548, ROC-AUC=0.9804, Support=423, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 525: Quality=-0.3548, ROC-AUC=0.9741, Support=86, Pattern={'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'C'}{'T'}{'C'}
  Pattern 526: Quality=-0.3548, ROC-AUC=0.9275, Support=47, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}
  Pattern 527: Quality=-0.3548, ROC-AUC=0.9789, Support=275, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 528: Quality=-0.3550, ROC-AUC=0.9172, Support=26, Pattern={'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 529: Quality=-0.3550, ROC-AUC=0.9767, Support=147, Pattern={'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}
  Pattern 530: Quality=-0.3551, ROC-AUC=0.9767, Support=142, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 531: Quality=-0.3551, ROC-AUC=0.9802, Support=362, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}
  Pattern 532: Quality=-0.3551, ROC-AUC=0.9804, Support=392, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 533: Quality=-0.3551, ROC-AUC=0.9785, Support=219, Pattern={'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 534: Quality=-0.3552, ROC-AUC=0.9483, Support=37, Pattern={'G'}{'G'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'A'}{'T'}{'A'}{'G'}{'G'}{'C'}
  Pattern 535: Quality=-0.3553, ROC-AUC=0.9337, Support=35, Pattern={'G'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}
  Pattern 536: Quality=-0.3553, ROC-AUC=0.9801, Support=335, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 537: Quality=-0.3553, ROC-AUC=0.9749, Support=88, Pattern={'C'}{'A'}{'A'}{'T'}{'C'}{'T'}{'A'}{'A'}{'G'}{'T'}{'G'}{'T'}{'G'}{'A'}{'A'}{'A'}{'C'}{'A'}{'A'}{'A'}{'C'}
  Pattern 538: Quality=-0.3553, ROC-AUC=0.9760, Support=112, Pattern={'T'}{'T'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 539: Quality=-0.3553, ROC-AUC=0.9801, Support=331, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 540: Quality=-0.3553, ROC-AUC=0.9806, Support=386, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 541: Quality=-0.3554, ROC-AUC=0.9775, Support=158, Pattern={'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'A'}{'G'}{'G'}{'T'}
  Pattern 542: Quality=-0.3554, ROC-AUC=0.9816, Support=523, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 543: Quality=-0.3554, ROC-AUC=0.9634, Support=187, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}
  Pattern 544: Quality=-0.3555, ROC-AUC=0.9812, Support=442, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 545: Quality=-0.3555, ROC-AUC=0.9813, Support=460, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 546: Quality=-0.3555, ROC-AUC=0.9779, Support=168, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 547: Quality=-0.3556, ROC-AUC=0.9786, Support=197, Pattern={'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}
  Pattern 548: Quality=-0.3557, ROC-AUC=0.9758, Support=96, Pattern={'C'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}
  Pattern 549: Quality=-0.3557, ROC-AUC=0.9811, Support=399, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 550: Quality=-0.3557, ROC-AUC=0.9779, Support=157, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}
  Pattern 551: Quality=-0.3558, ROC-AUC=0.9802, Support=295, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 552: Quality=-0.3558, ROC-AUC=0.9782, Support=164, Pattern={'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 553: Quality=-0.3558, ROC-AUC=0.9753, Support=80, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}
  Pattern 554: Quality=-0.3558, ROC-AUC=0.9802, Support=285, Pattern={'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 555: Quality=-0.3558, ROC-AUC=0.9781, Support=158, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}
  Pattern 556: Quality=-0.3559, ROC-AUC=0.9769, Support=116, Pattern={'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 557: Quality=-0.3559, ROC-AUC=0.9798, Support=252, Pattern={'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 558: Quality=-0.3559, ROC-AUC=0.9804, Support=297, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 559: Quality=-0.3560, ROC-AUC=0.9803, Support=283, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 560: Quality=-0.3560, ROC-AUC=0.9778, Support=143, Pattern={'G'}{'A'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 561: Quality=-0.3560, ROC-AUC=0.9818, Support=455, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 562: Quality=-0.3560, ROC-AUC=0.9807, Support=321, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 563: Quality=-0.3560, ROC-AUC=0.9817, Support=444, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 564: Quality=-0.3560, ROC-AUC=0.9788, Support=178, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 565: Quality=-0.3561, ROC-AUC=0.9797, Support=229, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 566: Quality=-0.3561, ROC-AUC=0.9763, Support=91, Pattern={'T'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}
  Pattern 567: Quality=-0.3562, ROC-AUC=0.9271, Support=22, Pattern={'G'}{'A'}{'G'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}{'G'}{'A'}{'C'}{'T'}{'G'}
  Pattern 568: Quality=-0.3563, ROC-AUC=0.9807, Support=292, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 569: Quality=-0.3563, ROC-AUC=0.9794, Support=195, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 570: Quality=-0.3563, ROC-AUC=0.9768, Support=97, Pattern={'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'A'}{'T'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 571: Quality=-0.3563, ROC-AUC=0.9798, Support=216, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}
  Pattern 572: Quality=-0.3563, ROC-AUC=0.9800, Support=224, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}
  Pattern 573: Quality=-0.3564, ROC-AUC=0.9808, Support=287, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 574: Quality=-0.3564, ROC-AUC=0.9125, Support=32, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 575: Quality=-0.3564, ROC-AUC=0.9817, Support=378, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 576: Quality=-0.3564, ROC-AUC=0.9756, Support=70, Pattern={'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 577: Quality=-0.3564, ROC-AUC=0.9750, Support=62, Pattern={'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'A'}{'A'}{'T'}
  Pattern 578: Quality=-0.3565, ROC-AUC=0.9795, Support=188, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}
  Pattern 579: Quality=-0.3565, ROC-AUC=0.9816, Support=359, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 580: Quality=-0.3565, ROC-AUC=0.9809, Support=280, Pattern={'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 581: Quality=-0.3566, ROC-AUC=0.9754, Support=64, Pattern={'G'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'T'}{'T'}
  Pattern 582: Quality=-0.3566, ROC-AUC=0.9827, Support=506, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 583: Quality=-0.3566, ROC-AUC=0.9814, Support=318, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 584: Quality=-0.3566, ROC-AUC=0.9768, Support=85, Pattern={'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'A'}{'A'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 585: Quality=-0.3566, ROC-AUC=0.9795, Support=174, Pattern={'C'}{'G'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}
  Pattern 586: Quality=-0.3567, ROC-AUC=0.9799, Support=198, Pattern={'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 587: Quality=-0.3567, ROC-AUC=0.9802, Support=216, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 588: Quality=-0.3567, ROC-AUC=0.9823, Support=431, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 589: Quality=-0.3568, ROC-AUC=0.9812, Support=280, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 590: Quality=-0.3568, ROC-AUC=0.9799, Support=182, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}{'C'}
  Pattern 591: Quality=-0.3568, ROC-AUC=0.9804, Support=214, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 592: Quality=-0.3569, ROC-AUC=0.9794, Support=153, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 593: Quality=-0.3569, ROC-AUC=0.9815, Support=292, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}
  Pattern 594: Quality=-0.3569, ROC-AUC=0.9819, Support=335, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 595: Quality=-0.3569, ROC-AUC=0.9781, Support=106, Pattern={'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}
  Pattern 596: Quality=-0.3570, ROC-AUC=0.9828, Support=446, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 597: Quality=-0.3570, ROC-AUC=0.9459, Support=81, Pattern={'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'G'}
  Pattern 598: Quality=-0.3570, ROC-AUC=0.9830, Support=489, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 599: Quality=-0.3571, ROC-AUC=0.9819, Support=316, Pattern={'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 600: Quality=-0.3571, ROC-AUC=0.9544, Support=57, Pattern={'C'}{'G'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'G'}{'A'}
  Pattern 601: Quality=-0.3571, ROC-AUC=0.9791, Support=128, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'A'}{'T'}{'T'}{'A'}{'C'}{'A'}{'G'}{'G'}{'A'}
  Pattern 602: Quality=-0.3571, ROC-AUC=0.9554, Support=63, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'T'}
  Pattern 603: Quality=-0.3572, ROC-AUC=0.9814, Support=249, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}
  Pattern 604: Quality=-0.3572, ROC-AUC=0.9778, Support=87, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}
  Pattern 605: Quality=-0.3572, ROC-AUC=0.9814, Support=249, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 606: Quality=-0.3572, ROC-AUC=0.9795, Support=137, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'A'}{'C'}{'C'}
  Pattern 607: Quality=-0.3572, ROC-AUC=0.9821, Support=313, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 608: Quality=-0.3573, ROC-AUC=0.9809, Support=205, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'A'}
  Pattern 609: Quality=-0.3573, ROC-AUC=0.9831, Support=459, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 610: Quality=-0.3573, ROC-AUC=0.9832, Support=461, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 611: Quality=-0.3573, ROC-AUC=0.9812, Support=225, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 612: Quality=-0.3573, ROC-AUC=0.9585, Support=87, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'A'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}
  Pattern 613: Quality=-0.3573, ROC-AUC=0.9805, Support=178, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}
  Pattern 614: Quality=-0.3574, ROC-AUC=0.9576, Support=78, Pattern={'C'}{'T'}{'A'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}
  Pattern 615: Quality=-0.3574, ROC-AUC=0.9819, Support=276, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}
  Pattern 616: Quality=-0.3575, ROC-AUC=0.9231, Support=33, Pattern={'G'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 617: Quality=-0.3575, ROC-AUC=0.9444, Support=22, Pattern={'A'}{'A'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'C'}{'G'}{'G'}{'T'}{'A'}{'C'}{'A'}{'G'}{'G'}{'T'}{'T'}
  Pattern 618: Quality=-0.3575, ROC-AUC=0.9831, Support=400, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 619: Quality=-0.3576, ROC-AUC=0.9827, Support=339, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 620: Quality=-0.3576, ROC-AUC=0.9804, Support=152, Pattern={'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}
  Pattern 621: Quality=-0.3576, ROC-AUC=0.9816, Support=225, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}
  Pattern 622: Quality=-0.3576, ROC-AUC=0.9809, Support=176, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 623: Quality=-0.3577, ROC-AUC=0.9598, Support=98, Pattern={'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 624: Quality=-0.3577, ROC-AUC=0.9826, Support=294, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 625: Quality=-0.3577, ROC-AUC=0.9826, Support=302, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 626: Quality=-0.3578, ROC-AUC=0.9490, Support=102, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}
  Pattern 627: Quality=-0.3578, ROC-AUC=0.9807, Support=154, Pattern={'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 628: Quality=-0.3578, ROC-AUC=0.9818, Support=217, Pattern={'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 629: Quality=-0.3578, ROC-AUC=0.9829, Support=333, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 630: Quality=-0.3578, ROC-AUC=0.9808, Support=156, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 631: Quality=-0.3578, ROC-AUC=0.9801, Support=123, Pattern={'C'}{'C'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}
  Pattern 632: Quality=-0.3578, ROC-AUC=0.9827, Support=302, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 633: Quality=-0.3579, ROC-AUC=0.9820, Support=227, Pattern={'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 634: Quality=-0.3579, ROC-AUC=0.9825, Support=268, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 635: Quality=-0.3579, ROC-AUC=0.9817, Support=195, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}
  Pattern 636: Quality=-0.3579, ROC-AUC=0.9833, Support=346, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 637: Quality=-0.3580, ROC-AUC=0.9812, Support=164, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 638: Quality=-0.3580, ROC-AUC=0.9473, Support=87, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 639: Quality=-0.3581, ROC-AUC=0.9827, Support=262, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 640: Quality=-0.3581, ROC-AUC=0.9763, Support=39, Pattern={'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'A'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'C'}{'A'}{'T'}{'G'}{'A'}{'C'}
  Pattern 641: Quality=-0.3581, ROC-AUC=0.9490, Support=100, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'A'}{'C'}
  Pattern 642: Quality=-0.3581, ROC-AUC=0.9784, Support=64, Pattern={'T'}{'T'}{'G'}{'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'G'}{'T'}{'T'}{'G'}{'A'}{'T'}{'C'}
  Pattern 643: Quality=-0.3582, ROC-AUC=0.9810, Support=134, Pattern={'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 644: Quality=-0.3582, ROC-AUC=0.9800, Support=94, Pattern={'G'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}
  Pattern 645: Quality=-0.3582, ROC-AUC=0.9823, Support=204, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 646: Quality=-0.3583, ROC-AUC=0.9446, Support=68, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 647: Quality=-0.3584, ROC-AUC=0.9825, Support=206, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}
  Pattern 648: Quality=-0.3584, ROC-AUC=0.9830, Support=246, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}
  Pattern 649: Quality=-0.3584, ROC-AUC=0.9816, Support=141, Pattern={'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 650: Quality=-0.3586, ROC-AUC=0.9823, Support=163, Pattern={'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 651: Quality=-0.3588, ROC-AUC=0.9831, Support=198, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'C'}
  Pattern 652: Quality=-0.3588, ROC-AUC=0.9815, Support=107, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}{'T'}{'A'}{'C'}{'A'}{'A'}{'T'}
  Pattern 653: Quality=-0.3588, ROC-AUC=0.9805, Support=78, Pattern={'G'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'T'}{'A'}{'A'}{'G'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 654: Quality=-0.3589, ROC-AUC=0.9829, Support=175, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}
  Pattern 655: Quality=-0.3589, ROC-AUC=0.9820, Support=119, Pattern={'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 656: Quality=-0.3589, ROC-AUC=0.9826, Support=147, Pattern={'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 657: Quality=-0.3590, ROC-AUC=0.9412, Support=50, Pattern={'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 658: Quality=-0.3590, ROC-AUC=0.9801, Support=61, Pattern={'C'}{'G'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'T'}{'G'}{'A'}{'G'}{'G'}{'T'}{'A'}
  Pattern 659: Quality=-0.3590, ROC-AUC=0.9828, Support=155, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 660: Quality=-0.3590, ROC-AUC=0.9808, Support=74, Pattern={'A'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'A'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}
  Pattern 661: Quality=-0.3590, ROC-AUC=0.9823, Support=122, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'A'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}
  Pattern 662: Quality=-0.3590, ROC-AUC=0.9815, Support=91, Pattern={'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}
  Pattern 663: Quality=-0.3591, ROC-AUC=0.9829, Support=148, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}
  Pattern 664: Quality=-0.3591, ROC-AUC=0.9821, Support=103, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}
  Pattern 665: Quality=-0.3592, ROC-AUC=0.9822, Support=105, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'A'}{'G'}{'T'}{'G'}{'C'}{'A'}{'T'}
  Pattern 666: Quality=-0.3592, ROC-AUC=0.9825, Support=117, Pattern={'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}
  Pattern 667: Quality=-0.3592, ROC-AUC=0.9827, Support=120, Pattern={'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}
  Pattern 668: Quality=-0.3593, ROC-AUC=0.9589, Support=76, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'A'}{'T'}{'C'}{'C'}{'C'}
  Pattern 669: Quality=-0.3594, ROC-AUC=0.9832, Support=134, Pattern={'A'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'A'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}
  Pattern 670: Quality=-0.3594, ROC-AUC=0.9185, Support=24, Pattern={'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'T'}
  Pattern 671: Quality=-0.3594, ROC-AUC=0.9826, Support=99, Pattern={'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'A'}
  Pattern 672: Quality=-0.3595, ROC-AUC=0.9822, Support=81, Pattern={'G'}{'T'}{'G'}{'G'}{'A'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'T'}{'A'}{'A'}{'G'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}
  Pattern 673: Quality=-0.3597, ROC-AUC=0.9830, Support=93, Pattern={'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'G'}
  Pattern 674: Quality=-0.3597, ROC-AUC=0.9830, Support=87, Pattern={'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}
  Pattern 675: Quality=-0.3598, ROC-AUC=0.9476, Support=81, Pattern={'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}
  Pattern 676: Quality=-0.3598, ROC-AUC=0.9830, Support=77, Pattern={'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'T'}{'T'}{'G'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'A'}{'C'}
  Pattern 677: Quality=-0.3599, ROC-AUC=0.9829, Support=74, Pattern={'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}
  Pattern 678: Quality=-0.3599, ROC-AUC=0.9286, Support=20, Pattern={'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'T'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}
  Pattern 679: Quality=-0.3600, ROC-AUC=0.9829, Support=61, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'A'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}{'T'}
  Pattern 680: Quality=-0.3601, ROC-AUC=0.9562, Support=52, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'T'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 681: Quality=-0.3604, ROC-AUC=0.9622, Support=103, Pattern={'G'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'A'}{'G'}
  Pattern 682: Quality=-0.3604, ROC-AUC=0.9352, Support=30, Pattern={'T'}{'A'}{'A'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'A'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'T'}
  Pattern 683: Quality=-0.3608, ROC-AUC=0.9478, Support=78, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'G'}
  Pattern 684: Quality=-0.3609, ROC-AUC=0.9578, Support=57, Pattern={'C'}{'T'}{'G'}{'T'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'A'}
  Pattern 685: Quality=-0.3611, ROC-AUC=0.9379, Support=35, Pattern={'C'}{'T'}{'A'}{'C'}{'T'}{'T'}{'A'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 686: Quality=-0.3612, ROC-AUC=0.9656, Support=149, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 687: Quality=-0.3617, ROC-AUC=0.9545, Support=37, Pattern={'A'}{'G'}{'T'}{'G'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}{'T'}{'A'}{'T'}{'G'}{'C'}{'A'}{'T'}{'T'}{'A'}{'T'}{'G'}
  Pattern 688: Quality=-0.3619, ROC-AUC=0.9648, Support=124, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}
  Pattern 689: Quality=-0.3619, ROC-AUC=0.9359, Support=29, Pattern={'G'}{'G'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}
  Pattern 690: Quality=-0.3620, ROC-AUC=0.9188, Support=38, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 691: Quality=-0.3622, ROC-AUC=0.9660, Support=143, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}
  Pattern 692: Quality=-0.3622, ROC-AUC=0.9545, Support=35, Pattern={'A'}{'C'}{'T'}{'A'}{'T'}{'C'}{'A'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}
  Pattern 693: Quality=-0.3623, ROC-AUC=0.9464, Support=64, Pattern={'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'G'}
  Pattern 694: Quality=-0.3624, ROC-AUC=0.9619, Support=79, Pattern={'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}
  Pattern 695: Quality=-0.3625, ROC-AUC=0.9182, Support=21, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'G'}
  Pattern 696: Quality=-0.3626, ROC-AUC=0.9133, Support=28, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 697: Quality=-0.3626, ROC-AUC=0.9290, Support=39, Pattern={'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 698: Quality=-0.3626, ROC-AUC=0.9627, Support=86, Pattern={'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}
  Pattern 699: Quality=-0.3627, ROC-AUC=0.9630, Support=88, Pattern={'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 700: Quality=-0.3628, ROC-AUC=0.9695, Support=230, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 701: Quality=-0.3629, ROC-AUC=0.9474, Support=67, Pattern={'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}
  Pattern 702: Quality=-0.3633, ROC-AUC=0.9226, Support=26, Pattern={'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'A'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}
  Pattern 703: Quality=-0.3636, ROC-AUC=0.9598, Support=53, Pattern={'T'}{'T'}{'G'}{'A'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}
  Pattern 704: Quality=-0.3637, ROC-AUC=0.9460, Support=57, Pattern={'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 705: Quality=-0.3637, ROC-AUC=0.9668, Support=133, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'A'}{'C'}{'A'}{'G'}{'C'}
  Pattern 706: Quality=-0.3639, ROC-AUC=0.9612, Support=61, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}
  Pattern 707: Quality=-0.3640, ROC-AUC=0.9628, Support=74, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 708: Quality=-0.3641, ROC-AUC=0.9637, Support=83, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}
  Pattern 709: Quality=-0.3641, ROC-AUC=0.9650, Support=99, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'G'}{'A'}{'G'}
  Pattern 710: Quality=-0.3642, ROC-AUC=0.9538, Support=113, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 711: Quality=-0.3643, ROC-AUC=0.8889, Support=26, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 712: Quality=-0.3644, ROC-AUC=0.9648, Support=93, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 713: Quality=-0.3647, ROC-AUC=0.9706, Support=222, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 714: Quality=-0.3647, ROC-AUC=0.9657, Support=100, Pattern={'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 715: Quality=-0.3648, ROC-AUC=0.9638, Support=76, Pattern={'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'G'}{'T'}
  Pattern 716: Quality=-0.3650, ROC-AUC=0.9563, Support=141, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'A'}{'C'}{'G'}
  Pattern 717: Quality=-0.3651, ROC-AUC=0.9538, Support=107, Pattern={'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 718: Quality=-0.3657, ROC-AUC=0.9447, Support=45, Pattern={'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 719: Quality=-0.3658, ROC-AUC=0.9730, Support=297, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 720: Quality=-0.3661, ROC-AUC=0.9286, Support=33, Pattern={'G'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'A'}{'G'}
  Pattern 721: Quality=-0.3662, ROC-AUC=0.9444, Support=43, Pattern={'G'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 722: Quality=-0.3662, ROC-AUC=0.9200, Support=20, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}
  Pattern 723: Quality=-0.3663, ROC-AUC=0.9606, Support=41, Pattern={'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'T'}{'T'}{'C'}
  Pattern 724: Quality=-0.3664, ROC-AUC=0.9687, Support=128, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'G'}{'A'}
  Pattern 725: Quality=-0.3665, ROC-AUC=0.9471, Support=53, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'A'}{'G'}{'G'}{'T'}{'G'}{'T'}{'G'}{'G'}{'A'}{'G'}{'C'}{'A'}{'C'}{'C'}
  Pattern 726: Quality=-0.3665, ROC-AUC=0.9720, Support=223, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 727: Quality=-0.3666, ROC-AUC=0.9598, Support=36, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'G'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'A'}
  Pattern 728: Quality=-0.3666, ROC-AUC=0.9695, Support=141, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 729: Quality=-0.3668, ROC-AUC=0.9450, Support=104, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 730: Quality=-0.3670, ROC-AUC=0.9660, Support=76, Pattern={'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'A'}{'A'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 731: Quality=-0.3671, ROC-AUC=0.9566, Support=127, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 732: Quality=-0.3672, ROC-AUC=0.9489, Support=59, Pattern={'G'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'A'}{'A'}{'G'}{'G'}{'G'}{'G'}
  Pattern 733: Quality=-0.3673, ROC-AUC=0.9357, Support=50, Pattern={'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}
  Pattern 734: Quality=-0.3673, ROC-AUC=0.9735, Support=262, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 735: Quality=-0.3674, ROC-AUC=0.9626, Support=45, Pattern={'T'}{'T'}{'A'}{'A'}{'C'}{'T'}{'T'}{'A'}{'A'}{'A'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'A'}{'G'}
  Pattern 736: Quality=-0.3675, ROC-AUC=0.9685, Support=105, Pattern={'T'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 737: Quality=-0.3675, ROC-AUC=0.9609, Support=36, Pattern={'G'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}{'G'}{'A'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 738: Quality=-0.3676, ROC-AUC=0.9583, Support=26, Pattern={'C'}{'T'}{'T'}{'A'}{'C'}{'T'}{'T'}{'A'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}
  Pattern 739: Quality=-0.3676, ROC-AUC=0.9017, Support=31, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 740: Quality=-0.3678, ROC-AUC=0.9406, Support=70, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'A'}
  Pattern 741: Quality=-0.3679, ROC-AUC=0.9610, Support=200, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 742: Quality=-0.3680, ROC-AUC=0.9467, Support=46, Pattern={'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}
  Pattern 743: Quality=-0.3680, ROC-AUC=0.9563, Support=116, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 744: Quality=-0.3681, ROC-AUC=0.9543, Support=94, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 745: Quality=-0.3682, ROC-AUC=0.9743, Support=269, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 746: Quality=-0.3684, ROC-AUC=0.9306, Support=34, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}
  Pattern 747: Quality=-0.3684, ROC-AUC=0.9695, Support=106, Pattern={'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 748: Quality=-0.3685, ROC-AUC=0.9505, Support=63, Pattern={'C'}{'A'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 749: Quality=-0.3686, ROC-AUC=0.9727, Support=184, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 750: Quality=-0.3690, ROC-AUC=0.9712, Support=127, Pattern={'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}
  Pattern 751: Quality=-0.3691, ROC-AUC=0.9743, Support=230, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 752: Quality=-0.3691, ROC-AUC=0.9712, Support=126, Pattern={'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 753: Quality=-0.3692, ROC-AUC=0.9724, Support=154, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 754: Quality=-0.3693, ROC-AUC=0.9711, Support=121, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'A'}{'T'}{'C'}{'G'}{'C'}
  Pattern 755: Quality=-0.3695, ROC-AUC=0.9689, Support=79, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}
  Pattern 756: Quality=-0.3696, ROC-AUC=0.9757, Support=288, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 757: Quality=-0.3697, ROC-AUC=0.9375, Support=20, Pattern={'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'A'}{'G'}{'C'}{'A'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 758: Quality=-0.3697, ROC-AUC=0.9657, Support=46, Pattern={'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'A'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 759: Quality=-0.3698, ROC-AUC=0.9709, Support=105, Pattern={'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}
  Pattern 760: Quality=-0.3699, ROC-AUC=0.9720, Support=126, Pattern={'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 761: Quality=-0.3700, ROC-AUC=0.9560, Support=98, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 762: Quality=-0.3700, ROC-AUC=0.9011, Support=20, Pattern={'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 763: Quality=-0.3700, ROC-AUC=0.9333, Support=38, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}
  Pattern 764: Quality=-0.3700, ROC-AUC=0.9711, Support=105, Pattern={'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 765: Quality=-0.3700, ROC-AUC=0.9500, Support=54, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 766: Quality=-0.3700, ROC-AUC=0.9719, Support=120, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 767: Quality=-0.3700, ROC-AUC=0.9725, Support=136, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'A'}
  Pattern 768: Quality=-0.3701, ROC-AUC=0.9704, Support=92, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}
  Pattern 769: Quality=-0.3701, ROC-AUC=0.9679, Support=59, Pattern={'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'A'}{'G'}
  Pattern 770: Quality=-0.3701, ROC-AUC=0.9761, Support=285, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 771: Quality=-0.3703, ROC-AUC=0.9748, Support=201, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}
  Pattern 772: Quality=-0.3704, ROC-AUC=0.9683, Support=60, Pattern={'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}
  Pattern 773: Quality=-0.3704, ROC-AUC=0.9537, Support=75, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'T'}{'A'}{'C'}
  Pattern 774: Quality=-0.3704, ROC-AUC=0.9738, Support=161, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'A'}{'C'}{'G'}{'T'}{'G'}{'G'}
  Pattern 775: Quality=-0.3704, ROC-AUC=0.9643, Support=33, Pattern={'T'}{'T'}{'A'}{'G'}{'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'A'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 776: Quality=-0.3704, ROC-AUC=0.9721, Support=115, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 777: Quality=-0.3705, ROC-AUC=0.9566, Support=101, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'A'}{'C'}{'T'}{'G'}{'A'}
  Pattern 778: Quality=-0.3705, ROC-AUC=0.9721, Support=115, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 779: Quality=-0.3705, ROC-AUC=0.9686, Support=62, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'T'}{'T'}{'T'}{'A'}{'A'}{'C'}{'A'}{'G'}{'A'}
  Pattern 780: Quality=-0.3705, ROC-AUC=0.9766, Support=296, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 781: Quality=-0.3707, ROC-AUC=0.9715, Support=98, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'A'}
  Pattern 782: Quality=-0.3708, ROC-AUC=0.9762, Support=248, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 783: Quality=-0.3709, ROC-AUC=0.9759, Support=231, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 784: Quality=-0.3709, ROC-AUC=0.9727, Support=118, Pattern={'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}
  Pattern 785: Quality=-0.3709, ROC-AUC=0.9747, Support=179, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 786: Quality=-0.3709, ROC-AUC=0.9714, Support=91, Pattern={'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}
  Pattern 787: Quality=-0.3710, ROC-AUC=0.9281, Support=49, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 788: Quality=-0.3710, ROC-AUC=0.9374, Support=48, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}
  Pattern 789: Quality=-0.3710, ROC-AUC=0.9769, Support=286, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 790: Quality=-0.3712, ROC-AUC=0.9720, Support=97, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 791: Quality=-0.3712, ROC-AUC=0.9527, Support=64, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}
  Pattern 792: Quality=-0.3712, ROC-AUC=0.9765, Support=245, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 793: Quality=-0.3713, ROC-AUC=0.9559, Support=88, Pattern={'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 794: Quality=-0.3714, ROC-AUC=0.9735, Support=121, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 795: Quality=-0.3715, ROC-AUC=0.9719, Support=90, Pattern={'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 796: Quality=-0.3716, ROC-AUC=0.9766, Support=237, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 797: Quality=-0.3716, ROC-AUC=0.9700, Support=61, Pattern={'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'A'}{'T'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}
  Pattern 798: Quality=-0.3716, ROC-AUC=0.9323, Support=33, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'A'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 799: Quality=-0.3716, ROC-AUC=0.9703, Support=64, Pattern={'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'A'}{'T'}{'G'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'G'}{'C'}{'G'}{'G'}
  Pattern 800: Quality=-0.3716, ROC-AUC=0.9602, Support=140, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 801: Quality=-0.3716, ROC-AUC=0.9713, Support=76, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}
  Pattern 802: Quality=-0.3717, ROC-AUC=0.9753, Support=170, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 803: Quality=-0.3717, ROC-AUC=0.9741, Support=130, Pattern={'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 804: Quality=-0.3717, ROC-AUC=0.9733, Support=109, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'T'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 805: Quality=-0.3718, ROC-AUC=0.9737, Support=117, Pattern={'A'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 806: Quality=-0.3718, ROC-AUC=0.9167, Support=25, Pattern={'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}
  Pattern 807: Quality=-0.3718, ROC-AUC=0.9772, Support=257, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 808: Quality=-0.3718, ROC-AUC=0.9730, Support=102, Pattern={'G'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}
  Pattern 809: Quality=-0.3719, ROC-AUC=0.9671, Support=36, Pattern={'G'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'T'}{'G'}{'T'}{'A'}{'G'}
  Pattern 810: Quality=-0.3719, ROC-AUC=0.9705, Support=62, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 811: Quality=-0.3720, ROC-AUC=0.9723, Support=85, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}
  Pattern 812: Quality=-0.3721, ROC-AUC=0.9725, Support=87, Pattern={'A'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'A'}{'G'}{'C'}{'T'}{'A'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}{'C'}
  Pattern 813: Quality=-0.3721, ROC-AUC=0.9784, Support=329, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 814: Quality=-0.3721, ROC-AUC=0.9688, Support=44, Pattern={'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}
  Pattern 815: Quality=-0.3721, ROC-AUC=0.9737, Support=108, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}
  Pattern 816: Quality=-0.3721, ROC-AUC=0.9771, Support=231, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 817: Quality=-0.3721, ROC-AUC=0.9757, Support=167, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 818: Quality=-0.3722, ROC-AUC=0.9747, Support=131, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 819: Quality=-0.3724, ROC-AUC=0.9782, Support=290, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 820: Quality=-0.3724, ROC-AUC=0.9756, Support=154, Pattern={'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 821: Quality=-0.3724, ROC-AUC=0.9769, Support=206, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'T'}{'G'}
  Pattern 822: Quality=-0.3724, ROC-AUC=0.9794, Support=398, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 823: Quality=-0.3725, ROC-AUC=0.9697, Support=47, Pattern={'T'}{'G'}{'G'}{'A'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}
  Pattern 824: Quality=-0.3725, ROC-AUC=0.9730, Support=84, Pattern={'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 825: Quality=-0.3726, ROC-AUC=0.9701, Support=49, Pattern={'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 826: Quality=-0.3726, ROC-AUC=0.9475, Support=99, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 827: Quality=-0.3727, ROC-AUC=0.9791, Support=340, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 828: Quality=-0.3727, ROC-AUC=0.9762, Support=161, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}
  Pattern 829: Quality=-0.3727, ROC-AUC=0.9778, Support=237, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 830: Quality=-0.3727, ROC-AUC=0.9754, Support=134, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}
  Pattern 831: Quality=-0.3727, ROC-AUC=0.9760, Support=152, Pattern={'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 832: Quality=-0.3727, ROC-AUC=0.9789, Support=320, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 833: Quality=-0.3728, ROC-AUC=0.9764, Support=166, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 834: Quality=-0.3728, ROC-AUC=0.9551, Support=72, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'A'}{'A'}{'T'}{'G'}{'G'}{'G'}
  Pattern 835: Quality=-0.3728, ROC-AUC=0.9767, Support=176, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 836: Quality=-0.3729, ROC-AUC=0.9714, Support=57, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'T'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}
  Pattern 837: Quality=-0.3729, ROC-AUC=0.9517, Support=51, Pattern={'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'G'}{'C'}{'T'}{'G'}{'A'}{'T'}
  Pattern 838: Quality=-0.3729, ROC-AUC=0.9792, Support=328, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 839: Quality=-0.3730, ROC-AUC=0.9751, Support=117, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}
  Pattern 840: Quality=-0.3730, ROC-AUC=0.9716, Support=57, Pattern={'G'}{'A'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 841: Quality=-0.3731, ROC-AUC=0.9734, Support=80, Pattern={'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 842: Quality=-0.3731, ROC-AUC=0.9769, Support=170, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'A'}
  Pattern 843: Quality=-0.3732, ROC-AUC=0.9746, Support=99, Pattern={'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 844: Quality=-0.3733, ROC-AUC=0.9778, Support=199, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'A'}
  Pattern 845: Quality=-0.3733, ROC-AUC=0.9803, Support=403, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 846: Quality=-0.3734, ROC-AUC=0.9474, Support=33, Pattern={'G'}{'G'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'A'}
  Pattern 847: Quality=-0.3734, ROC-AUC=0.9778, Support=198, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 848: Quality=-0.3735, ROC-AUC=0.9792, Support=281, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 849: Quality=-0.3735, ROC-AUC=0.9742, Support=83, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 850: Quality=-0.3735, ROC-AUC=0.9797, Support=319, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 851: Quality=-0.3736, ROC-AUC=0.9793, Support=276, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 852: Quality=-0.3739, ROC-AUC=0.9773, Support=149, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}
  Pattern 853: Quality=-0.3740, ROC-AUC=0.9724, Support=49, Pattern={'G'}{'G'}{'G'}{'T'}{'A'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'C'}{'T'}{'G'}
  Pattern 854: Quality=-0.3740, ROC-AUC=0.9734, Support=59, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}
  Pattern 855: Quality=-0.3741, ROC-AUC=0.9799, Support=283, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 856: Quality=-0.3741, ROC-AUC=0.9806, Support=343, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 857: Quality=-0.3742, ROC-AUC=0.9807, Support=352, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 858: Quality=-0.3742, ROC-AUC=0.9770, Support=126, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 859: Quality=-0.3742, ROC-AUC=0.9286, Support=23, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'C'}{'A'}{'G'}{'A'}{'G'}{'G'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}
  Pattern 860: Quality=-0.3742, ROC-AUC=0.9806, Support=333, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 861: Quality=-0.3744, ROC-AUC=0.9741, Support=61, Pattern={'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 862: Quality=-0.3744, ROC-AUC=0.9755, Support=82, Pattern={'T'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 863: Quality=-0.3744, ROC-AUC=0.9792, Support=210, Pattern={'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 864: Quality=-0.3744, ROC-AUC=0.9810, Support=362, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 865: Quality=-0.3744, ROC-AUC=0.9795, Support=226, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 866: Quality=-0.3744, ROC-AUC=0.9744, Support=63, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'A'}{'A'}{'C'}{'T'}{'A'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 867: Quality=-0.3744, ROC-AUC=0.9722, Support=41, Pattern={'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'A'}{'A'}{'C'}{'C'}
  Pattern 868: Quality=-0.3745, ROC-AUC=0.9766, Support=101, Pattern={'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 869: Quality=-0.3745, ROC-AUC=0.9445, Support=70, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 870: Quality=-0.3746, ROC-AUC=0.9759, Support=84, Pattern={'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}
  Pattern 871: Quality=-0.3746, ROC-AUC=0.9788, Support=172, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}
  Pattern 872: Quality=-0.3747, ROC-AUC=0.9759, Support=83, Pattern={'A'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 873: Quality=-0.3747, ROC-AUC=0.9775, Support=120, Pattern={'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'A'}{'C'}{'A'}{'C'}{'G'}
  Pattern 874: Quality=-0.3747, ROC-AUC=0.9543, Support=57, Pattern={'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}
  Pattern 875: Quality=-0.3747, ROC-AUC=0.9752, Support=69, Pattern={'G'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'A'}{'G'}{'C'}{'G'}{'C'}{'A'}
  Pattern 876: Quality=-0.3748, ROC-AUC=0.9764, Support=87, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 877: Quality=-0.3749, ROC-AUC=0.9813, Support=336, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 878: Quality=-0.3749, ROC-AUC=0.9788, Support=158, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 879: Quality=-0.3749, ROC-AUC=0.9770, Support=96, Pattern={'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 880: Quality=-0.3749, ROC-AUC=0.9817, Support=373, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 881: Quality=-0.3750, ROC-AUC=0.9375, Support=40, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 882: Quality=-0.3751, ROC-AUC=0.9762, Support=75, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}{'T'}{'C'}{'T'}{'A'}{'A'}{'G'}
  Pattern 883: Quality=-0.3751, ROC-AUC=0.9227, Support=31, Pattern={'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 884: Quality=-0.3751, ROC-AUC=0.9500, Support=36, Pattern={'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}
  Pattern 885: Quality=-0.3752, ROC-AUC=0.9802, Support=213, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 886: Quality=-0.3752, ROC-AUC=0.9817, Support=337, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 887: Quality=-0.3752, ROC-AUC=0.9819, Support=364, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 888: Quality=-0.3752, ROC-AUC=0.9301, Support=24, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'A'}{'C'}{'C'}
  Pattern 889: Quality=-0.3752, ROC-AUC=0.9811, Support=274, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 890: Quality=-0.3752, ROC-AUC=0.9609, Support=114, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 891: Quality=-0.3752, ROC-AUC=0.9801, Support=198, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 892: Quality=-0.3753, ROC-AUC=0.9823, Support=405, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 893: Quality=-0.3753, ROC-AUC=0.9796, Support=169, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}
  Pattern 894: Quality=-0.3754, ROC-AUC=0.9816, Support=298, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 895: Quality=-0.3754, ROC-AUC=0.9755, Support=56, Pattern={'T'}{'T'}{'C'}{'A'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}
  Pattern 896: Quality=-0.3754, ROC-AUC=0.9769, Support=77, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'T'}{'G'}{'A'}{'T'}{'C'}
  Pattern 897: Quality=-0.3754, ROC-AUC=0.9758, Support=59, Pattern={'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'A'}{'T'}{'T'}{'C'}
  Pattern 898: Quality=-0.3755, ROC-AUC=0.9757, Support=57, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}{'A'}{'C'}{'C'}{'A'}
  Pattern 899: Quality=-0.3756, ROC-AUC=0.9786, Support=113, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'A'}{'C'}{'T'}{'G'}{'T'}{'G'}
  Pattern 900: Quality=-0.3756, ROC-AUC=0.9828, Support=413, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 901: Quality=-0.3757, ROC-AUC=0.9762, Support=60, Pattern={'T'}{'T'}{'T'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 902: Quality=-0.3757, ROC-AUC=0.9820, Support=315, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 903: Quality=-0.3757, ROC-AUC=0.9809, Support=211, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 904: Quality=-0.3757, ROC-AUC=0.9811, Support=227, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 905: Quality=-0.3757, ROC-AUC=0.9813, Support=242, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 906: Quality=-0.3758, ROC-AUC=0.9814, Support=242, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 907: Quality=-0.3758, ROC-AUC=0.9814, Support=233, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 908: Quality=-0.3758, ROC-AUC=0.9811, Support=210, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}
  Pattern 909: Quality=-0.3758, ROC-AUC=0.9798, Support=141, Pattern={'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 910: Quality=-0.3759, ROC-AUC=0.9831, Support=420, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 911: Quality=-0.3760, ROC-AUC=0.9762, Support=50, Pattern={'T'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'T'}{'A'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'A'}{'C'}{'A'}{'A'}{'A'}{'G'}{'C'}
  Pattern 912: Quality=-0.3760, ROC-AUC=0.9786, Support=91, Pattern={'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'T'}{'G'}{'C'}{'T'}{'T'}
  Pattern 913: Quality=-0.3761, ROC-AUC=0.9799, Support=132, Pattern={'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'A'}
  Pattern 914: Quality=-0.3761, ROC-AUC=0.9831, Support=383, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 915: Quality=-0.3762, ROC-AUC=0.9826, Support=299, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 916: Quality=-0.3762, ROC-AUC=0.9558, Support=58, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}
  Pattern 917: Quality=-0.3762, ROC-AUC=0.9762, Support=45, Pattern={'G'}{'G'}{'T'}{'T'}{'A'}{'C'}{'A'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 918: Quality=-0.3763, ROC-AUC=0.9812, Support=179, Pattern={'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 919: Quality=-0.3763, ROC-AUC=0.9817, Support=214, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}
  Pattern 920: Quality=-0.3763, ROC-AUC=0.9816, Support=200, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 921: Quality=-0.3763, ROC-AUC=0.9807, Support=149, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}
  Pattern 922: Quality=-0.3763, ROC-AUC=0.9807, Support=147, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 923: Quality=-0.3764, ROC-AUC=0.9217, Support=28, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 924: Quality=-0.3764, ROC-AUC=0.9773, Support=54, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'C'}{'A'}{'T'}{'A'}{'G'}
  Pattern 925: Quality=-0.3764, ROC-AUC=0.9827, Support=277, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 926: Quality=-0.3765, ROC-AUC=0.9524, Support=40, Pattern={'C'}{'A'}{'G'}{'A'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}
  Pattern 927: Quality=-0.3765, ROC-AUC=0.9807, Support=137, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}
  Pattern 928: Quality=-0.3765, ROC-AUC=0.9801, Support=111, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 929: Quality=-0.3765, ROC-AUC=0.9770, Support=47, Pattern={'T'}{'C'}{'T'}{'G'}{'T'}{'A'}{'A'}{'T'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'A'}{'A'}{'C'}
  Pattern 930: Quality=-0.3765, ROC-AUC=0.9810, Support=143, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}
  Pattern 931: Quality=-0.3765, ROC-AUC=0.9781, Support=61, Pattern={'T'}{'G'}{'G'}{'C'}{'G'}{'A'}{'A'}{'A'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}
  Pattern 932: Quality=-0.3766, ROC-AUC=0.9814, Support=161, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 933: Quality=-0.3766, ROC-AUC=0.9473, Support=80, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}
  Pattern 934: Quality=-0.3766, ROC-AUC=0.9817, Support=175, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 935: Quality=-0.3766, ROC-AUC=0.9818, Support=181, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 936: Quality=-0.3766, ROC-AUC=0.9809, Support=132, Pattern={'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 937: Quality=-0.3766, ROC-AUC=0.9794, Support=84, Pattern={'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'A'}
  Pattern 938: Quality=-0.3766, ROC-AUC=0.9810, Support=135, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}
  Pattern 939: Quality=-0.3766, ROC-AUC=0.9785, Support=64, Pattern={'A'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'A'}{'G'}{'T'}{'A'}{'A'}{'T'}{'G'}{'C'}{'A'}{'A'}{'T'}{'T'}
  Pattern 940: Quality=-0.3767, ROC-AUC=0.9788, Support=68, Pattern={'A'}{'G'}{'C'}{'A'}{'A'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}
  Pattern 941: Quality=-0.3767, ROC-AUC=0.9765, Support=37, Pattern={'T'}{'G'}{'C'}{'A'}{'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'A'}{'T'}{'T'}{'A'}{'A'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 942: Quality=-0.3768, ROC-AUC=0.9829, Support=253, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 943: Quality=-0.3768, ROC-AUC=0.9829, Support=243, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 944: Quality=-0.3768, ROC-AUC=0.9813, Support=140, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 945: Quality=-0.3768, ROC-AUC=0.9814, Support=141, Pattern={'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}
  Pattern 946: Quality=-0.3769, ROC-AUC=0.9783, Support=55, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'A'}{'A'}{'G'}
  Pattern 947: Quality=-0.3769, ROC-AUC=0.9812, Support=129, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}
  Pattern 948: Quality=-0.3769, ROC-AUC=0.9815, Support=140, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 949: Quality=-0.3769, ROC-AUC=0.9825, Support=192, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 950: Quality=-0.3770, ROC-AUC=0.9822, Support=169, Pattern={'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 951: Quality=-0.3770, ROC-AUC=0.9789, Support=60, Pattern={'T'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'A'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'C'}
  Pattern 952: Quality=-0.3770, ROC-AUC=0.9795, Support=72, Pattern={'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}
  Pattern 953: Quality=-0.3770, ROC-AUC=0.9804, Support=93, Pattern={'T'}{'G'}{'T'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'T'}{'C'}{'C'}{'C'}
  Pattern 954: Quality=-0.3771, ROC-AUC=0.9807, Support=93, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}
  Pattern 955: Quality=-0.3771, ROC-AUC=0.9798, Support=71, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 956: Quality=-0.3771, ROC-AUC=0.9489, Support=27, Pattern={'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}
  Pattern 957: Quality=-0.3772, ROC-AUC=0.9818, Support=126, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}
  Pattern 958: Quality=-0.3772, ROC-AUC=0.9573, Support=62, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'A'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}
  Pattern 959: Quality=-0.3772, ROC-AUC=0.9777, Support=36, Pattern={'A'}{'A'}{'A'}{'T'}{'T'}{'T'}{'A'}{'T'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'A'}{'T'}
  Pattern 960: Quality=-0.3773, ROC-AUC=0.9600, Support=84, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 961: Quality=-0.3773, ROC-AUC=0.9789, Support=47, Pattern={'G'}{'A'}{'A'}{'G'}{'T'}{'C'}{'G'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'C'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}
  Pattern 962: Quality=-0.3774, ROC-AUC=0.9828, Support=162, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 963: Quality=-0.3774, ROC-AUC=0.9795, Support=55, Pattern={'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 964: Quality=-0.3774, ROC-AUC=0.9826, Support=151, Pattern={'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 965: Quality=-0.3775, ROC-AUC=0.9828, Support=149, Pattern={'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 966: Quality=-0.3775, ROC-AUC=0.9831, Support=169, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 967: Quality=-0.3775, ROC-AUC=0.9545, Support=45, Pattern={'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 968: Quality=-0.3775, ROC-AUC=0.9396, Support=41, Pattern={'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'G'}
  Pattern 969: Quality=-0.3776, ROC-AUC=0.9810, Support=71, Pattern={'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'A'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}
  Pattern 970: Quality=-0.3776, ROC-AUC=0.9824, Support=117, Pattern={'C'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}
  Pattern 971: Quality=-0.3776, ROC-AUC=0.9823, Support=114, Pattern={'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 972: Quality=-0.3776, ROC-AUC=0.9825, Support=118, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}
  Pattern 973: Quality=-0.3777, ROC-AUC=0.9783, Support=31, Pattern={'T'}{'G'}{'T'}{'T'}{'G'}{'A'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}
  Pattern 974: Quality=-0.3777, ROC-AUC=0.9818, Support=91, Pattern={'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 975: Quality=-0.3777, ROC-AUC=0.9798, Support=47, Pattern={'T'}{'A'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'T'}{'G'}{'T'}{'C'}
  Pattern 976: Quality=-0.3777, ROC-AUC=0.9290, Support=41, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 977: Quality=-0.3777, ROC-AUC=0.9618, Support=101, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}
  Pattern 978: Quality=-0.3778, ROC-AUC=0.9487, Support=25, Pattern={'A'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'A'}{'G'}
  Pattern 979: Quality=-0.3779, ROC-AUC=0.9474, Support=22, Pattern={'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'C'}{'A'}{'T'}{'T'}{'G'}{'G'}{'A'}{'A'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'A'}{'T'}
  Pattern 980: Quality=-0.3779, ROC-AUC=0.9805, Support=50, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'T'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 981: Quality=-0.3779, ROC-AUC=0.9821, Support=86, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 982: Quality=-0.3779, ROC-AUC=0.9806, Support=49, Pattern={'C'}{'A'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'A'}{'A'}{'A'}{'C'}{'A'}{'G'}
  Pattern 983: Quality=-0.3781, ROC-AUC=0.9832, Support=108, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 984: Quality=-0.3781, ROC-AUC=0.9222, Support=27, Pattern={'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'A'}
  Pattern 985: Quality=-0.3781, ROC-AUC=0.9604, Support=82, Pattern={'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}
  Pattern 986: Quality=-0.3781, ROC-AUC=0.9532, Support=37, Pattern={'C'}{'G'}{'A'}{'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 987: Quality=-0.3781, ROC-AUC=0.9133, Support=42, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 988: Quality=-0.3782, ROC-AUC=0.9830, Support=87, Pattern={'T'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 989: Quality=-0.3782, ROC-AUC=0.9818, Support=55, Pattern={'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}
  Pattern 990: Quality=-0.3783, ROC-AUC=0.9531, Support=36, Pattern={'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'T'}{'C'}{'T'}
  Pattern 991: Quality=-0.3785, ROC-AUC=0.9796, Support=21, Pattern={'T'}{'T'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'A'}{'C'}{'C'}{'G'}
  Pattern 992: Quality=-0.3785, ROC-AUC=0.9831, Support=67, Pattern={'G'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}
  Pattern 993: Quality=-0.3785, ROC-AUC=0.9544, Support=40, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}
  Pattern 994: Quality=-0.3786, ROC-AUC=0.9127, Support=27, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 995: Quality=-0.3787, ROC-AUC=0.9826, Support=43, Pattern={'C'}{'A'}{'T'}{'T'}{'A'}{'T'}{'T'}{'A'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}
  Pattern 996: Quality=-0.3789, ROC-AUC=0.9585, Support=60, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}
  Pattern 997: Quality=-0.3790, ROC-AUC=0.9826, Support=28, Pattern={'T'}{'T'}{'T'}{'T'}{'A'}{'A'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}
  Pattern 998: Quality=-0.3790, ROC-AUC=0.9558, Support=44, Pattern={'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 999: Quality=-0.3794, ROC-AUC=0.9633, Support=104, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1000: Quality=-0.3800, ROC-AUC=0.9595, Support=60, Pattern={'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'G'}{'A'}{'A'}{'G'}{'A'}{'A'}{'A'}
  Pattern 1001: Quality=-0.3800, ROC-AUC=0.9264, Support=32, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'A'}{'C'}{'A'}{'A'}{'G'}{'C'}{'C'}
  Pattern 1002: Quality=-0.3800, ROC-AUC=0.9622, Support=83, Pattern={'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1003: Quality=-0.3801, ROC-AUC=0.9440, Support=50, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}
  Pattern 1004: Quality=-0.3801, ROC-AUC=0.9456, Support=57, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1005: Quality=-0.3801, ROC-AUC=0.9398, Support=36, Pattern={'C'}{'T'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1006: Quality=-0.3803, ROC-AUC=0.9652, Support=122, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1007: Quality=-0.3804, ROC-AUC=0.9642, Support=104, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'T'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1008: Quality=-0.3806, ROC-AUC=0.9644, Support=105, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1009: Quality=-0.3806, ROC-AUC=0.9634, Support=92, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'G'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1010: Quality=-0.3806, ROC-AUC=0.9542, Support=31, Pattern={'T'}{'T'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1011: Quality=-0.3807, ROC-AUC=0.9333, Support=22, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'T'}{'T'}{'A'}{'C'}{'C'}
  Pattern 1012: Quality=-0.3810, ROC-AUC=0.9650, Support=109, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1013: Quality=-0.3811, ROC-AUC=0.9558, Support=35, Pattern={'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1014: Quality=-0.3812, ROC-AUC=0.9654, Support=113, Pattern={'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'C'}
  Pattern 1015: Quality=-0.3813, ROC-AUC=0.9524, Support=24, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'A'}{'A'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 1016: Quality=-0.3813, ROC-AUC=0.9589, Support=48, Pattern={'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}
  Pattern 1017: Quality=-0.3814, ROC-AUC=0.9571, Support=39, Pattern={'C'}{'A'}{'T'}{'C'}{'A'}{'C'}{'T'}{'T'}{'G'}{'C'}{'A'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1018: Quality=-0.3815, ROC-AUC=0.9555, Support=32, Pattern={'T'}{'A'}{'C'}{'A'}{'C'}{'A'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'G'}{'G'}{'C'}{'A'}
  Pattern 1019: Quality=-0.3815, ROC-AUC=0.9375, Support=28, Pattern={'G'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'T'}{'G'}
  Pattern 1020: Quality=-0.3816, ROC-AUC=0.9598, Support=52, Pattern={'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}
  Pattern 1021: Quality=-0.3816, ROC-AUC=0.9539, Support=27, Pattern={'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'A'}{'C'}{'T'}{'T'}{'A'}{'G'}
  Pattern 1022: Quality=-0.3821, ROC-AUC=0.9628, Support=70, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'T'}{'C'}{'C'}{'A'}
  Pattern 1023: Quality=-0.3822, ROC-AUC=0.9634, Support=76, Pattern={'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'G'}{'G'}
  Pattern 1024: Quality=-0.3823, ROC-AUC=0.9651, Support=94, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1025: Quality=-0.3824, ROC-AUC=0.9537, Support=24, Pattern={'T'}{'C'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}
  Pattern 1026: Quality=-0.3824, ROC-AUC=0.9545, Support=26, Pattern={'C'}{'A'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}
  Pattern 1027: Quality=-0.3829, ROC-AUC=0.9622, Support=59, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}{'A'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1028: Quality=-0.3831, ROC-AUC=0.9579, Support=34, Pattern={'A'}{'A'}{'A'}{'G'}{'T'}{'T'}{'G'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}
  Pattern 1029: Quality=-0.3831, ROC-AUC=0.9635, Support=68, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}{'A'}
  Pattern 1030: Quality=-0.3833, ROC-AUC=0.9673, Support=115, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1031: Quality=-0.3834, ROC-AUC=0.9301, Support=35, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1032: Quality=-0.3836, ROC-AUC=0.9713, Support=215, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1033: Quality=-0.3836, ROC-AUC=0.9365, Support=23, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'A'}
  Pattern 1034: Quality=-0.3837, ROC-AUC=0.9658, Support=86, Pattern={'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1035: Quality=-0.3838, ROC-AUC=0.9671, Support=104, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'A'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1036: Quality=-0.3838, ROC-AUC=0.9685, Support=128, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1037: Quality=-0.3839, ROC-AUC=0.9561, Support=25, Pattern={'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'A'}{'A'}{'A'}{'C'}{'T'}{'A'}{'T'}
  Pattern 1038: Quality=-0.3839, ROC-AUC=0.9675, Support=108, Pattern={'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1039: Quality=-0.3841, ROC-AUC=0.9515, Support=76, Pattern={'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1040: Quality=-0.3841, ROC-AUC=0.9244, Support=24, Pattern={'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'A'}
  Pattern 1041: Quality=-0.3842, ROC-AUC=0.9668, Support=93, Pattern={'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1042: Quality=-0.3844, ROC-AUC=0.9417, Support=32, Pattern={'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}
  Pattern 1043: Quality=-0.3845, ROC-AUC=0.9396, Support=27, Pattern={'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'T'}
  Pattern 1044: Quality=-0.3846, ROC-AUC=0.9711, Support=179, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1045: Quality=-0.3847, ROC-AUC=0.9663, Support=81, Pattern={'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 1046: Quality=-0.3847, ROC-AUC=0.9623, Support=46, Pattern={'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}
  Pattern 1047: Quality=-0.3847, ROC-AUC=0.9706, Support=159, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1048: Quality=-0.3848, ROC-AUC=0.9412, Support=30, Pattern={'C'}{'T'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 1049: Quality=-0.3851, ROC-AUC=0.9616, Support=40, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'T'}{'T'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1050: Quality=-0.3854, ROC-AUC=0.9707, Support=147, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 1051: Quality=-0.3855, ROC-AUC=0.9689, Support=107, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1052: Quality=-0.3855, ROC-AUC=0.9580, Support=24, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}
  Pattern 1053: Quality=-0.3857, ROC-AUC=0.9583, Support=138, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1054: Quality=-0.3857, ROC-AUC=0.9713, Support=154, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 1055: Quality=-0.3859, ROC-AUC=0.9614, Support=34, Pattern={'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'A'}{'A'}{'T'}{'C'}{'C'}{'A'}{'G'}
  Pattern 1056: Quality=-0.3859, ROC-AUC=0.9713, Support=150, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1057: Quality=-0.3860, ROC-AUC=0.9600, Support=28, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 1058: Quality=-0.3861, ROC-AUC=0.9735, Support=221, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1059: Quality=-0.3863, ROC-AUC=0.9647, Support=50, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}
  Pattern 1060: Quality=-0.3863, ROC-AUC=0.9672, Support=71, Pattern={'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'A'}
  Pattern 1061: Quality=-0.3863, ROC-AUC=0.9691, Support=96, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'G'}{'C'}
  Pattern 1062: Quality=-0.3866, ROC-AUC=0.9615, Support=31, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}
  Pattern 1063: Quality=-0.3866, ROC-AUC=0.9643, Support=44, Pattern={'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'G'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1064: Quality=-0.3866, ROC-AUC=0.9605, Support=27, Pattern={'A'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'T'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}
  Pattern 1065: Quality=-0.3867, ROC-AUC=0.9719, Support=148, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1066: Quality=-0.3869, ROC-AUC=0.9376, Support=50, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1067: Quality=-0.3869, ROC-AUC=0.9603, Support=25, Pattern={'C'}{'G'}{'T'}{'A'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}
  Pattern 1068: Quality=-0.3871, ROC-AUC=0.9673, Support=62, Pattern={'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}
  Pattern 1069: Quality=-0.3871, ROC-AUC=0.9461, Support=38, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1070: Quality=-0.3872, ROC-AUC=0.9695, Support=89, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1071: Quality=-0.3873, ROC-AUC=0.9717, Support=127, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1072: Quality=-0.3874, ROC-AUC=0.9634, Support=34, Pattern={'G'}{'A'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'A'}
  Pattern 1073: Quality=-0.3874, ROC-AUC=0.9603, Support=23, Pattern={'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'T'}{'A'}
  Pattern 1074: Quality=-0.3874, ROC-AUC=0.9632, Support=33, Pattern={'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'A'}{'T'}{'C'}{'G'}{'C'}
  Pattern 1075: Quality=-0.3874, ROC-AUC=0.9688, Support=75, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'A'}{'T'}{'C'}{'C'}
  Pattern 1076: Quality=-0.3874, ROC-AUC=0.9543, Support=80, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1077: Quality=-0.3876, ROC-AUC=0.9681, Support=64, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'T'}
  Pattern 1078: Quality=-0.3876, ROC-AUC=0.9706, Support=97, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1079: Quality=-0.3876, ROC-AUC=0.9691, Support=75, Pattern={'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1080: Quality=-0.3877, ROC-AUC=0.9538, Support=74, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1081: Quality=-0.3880, ROC-AUC=0.9673, Support=53, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1082: Quality=-0.3880, ROC-AUC=0.9636, Support=31, Pattern={'C'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 1083: Quality=-0.3881, ROC-AUC=0.9699, Support=79, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1084: Quality=-0.3885, ROC-AUC=0.9735, Support=142, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'A'}{'C'}
  Pattern 1085: Quality=-0.3885, ROC-AUC=0.9625, Support=24, Pattern={'G'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'A'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 1086: Quality=-0.3886, ROC-AUC=0.9394, Support=20, Pattern={'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'A'}{'A'}{'G'}{'A'}
  Pattern 1087: Quality=-0.3886, ROC-AUC=0.9683, Support=54, Pattern={'C'}{'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1088: Quality=-0.3886, ROC-AUC=0.9717, Support=96, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1089: Quality=-0.3887, ROC-AUC=0.9680, Support=51, Pattern={'T'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'G'}{'G'}{'G'}{'A'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1090: Quality=-0.3887, ROC-AUC=0.9469, Support=36, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1091: Quality=-0.3888, ROC-AUC=0.9657, Support=35, Pattern={'T'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'A'}{'A'}{'A'}{'C'}{'A'}{'G'}{'A'}
  Pattern 1092: Quality=-0.3888, ROC-AUC=0.9766, Support=263, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 1093: Quality=-0.3889, ROC-AUC=0.9658, Support=35, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'A'}{'A'}{'A'}{'C'}{'C'}{'A'}
  Pattern 1094: Quality=-0.3892, ROC-AUC=0.9676, Support=43, Pattern={'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'A'}{'A'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}
  Pattern 1095: Quality=-0.3892, ROC-AUC=0.9737, Support=126, Pattern={'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1096: Quality=-0.3892, ROC-AUC=0.9667, Support=37, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1097: Quality=-0.3894, ROC-AUC=0.9756, Support=181, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1098: Quality=-0.3895, ROC-AUC=0.9652, Support=28, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1099: Quality=-0.3896, ROC-AUC=0.9763, Support=204, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1100: Quality=-0.3896, ROC-AUC=0.9271, Support=22, Pattern={'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 1101: Quality=-0.3896, ROC-AUC=0.9271, Support=22, Pattern={'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'G'}{'T'}{'C'}
  Pattern 1102: Quality=-0.3897, ROC-AUC=0.9751, Support=150, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 1103: Quality=-0.3899, ROC-AUC=0.9669, Support=33, Pattern={'T'}{'C'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1104: Quality=-0.3899, ROC-AUC=0.9446, Support=74, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1105: Quality=-0.3900, ROC-AUC=0.9777, Support=261, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1106: Quality=-0.3900, ROC-AUC=0.9735, Support=101, Pattern={'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1107: Quality=-0.3901, ROC-AUC=0.9611, Support=140, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1108: Quality=-0.3902, ROC-AUC=0.9715, Support=65, Pattern={'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 1109: Quality=-0.3904, ROC-AUC=0.9784, Support=285, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1110: Quality=-0.3904, ROC-AUC=0.9768, Support=185, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1111: Quality=-0.3906, ROC-AUC=0.9778, Support=229, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1112: Quality=-0.3906, ROC-AUC=0.9685, Support=35, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1113: Quality=-0.3906, ROC-AUC=0.9688, Support=36, Pattern={'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'T'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 1114: Quality=-0.3907, ROC-AUC=0.9729, Support=75, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'A'}{'A'}{'C'}
  Pattern 1115: Quality=-0.3907, ROC-AUC=0.9692, Support=38, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'A'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1116: Quality=-0.3907, ROC-AUC=0.9458, Support=79, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1117: Quality=-0.3908, ROC-AUC=0.9499, Support=40, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'G'}{'T'}{'C'}
  Pattern 1118: Quality=-0.3908, ROC-AUC=0.9423, Support=21, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}
  Pattern 1119: Quality=-0.3909, ROC-AUC=0.9707, Support=46, Pattern={'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'C'}
  Pattern 1120: Quality=-0.3910, ROC-AUC=0.9769, Support=160, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1121: Quality=-0.3910, ROC-AUC=0.9457, Support=27, Pattern={'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 1122: Quality=-0.3910, ROC-AUC=0.9787, Support=257, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1123: Quality=-0.3911, ROC-AUC=0.9697, Support=37, Pattern={'T'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}
  Pattern 1124: Quality=-0.3912, ROC-AUC=0.9769, Support=154, Pattern={'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1125: Quality=-0.3912, ROC-AUC=0.9777, Support=187, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1126: Quality=-0.3912, ROC-AUC=0.9726, Support=60, Pattern={'G'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}
  Pattern 1127: Quality=-0.3913, ROC-AUC=0.9712, Support=45, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1128: Quality=-0.3913, ROC-AUC=0.9689, Support=30, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}
  Pattern 1129: Quality=-0.3914, ROC-AUC=0.9787, Support=229, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1130: Quality=-0.3914, ROC-AUC=0.9732, Support=64, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}
  Pattern 1131: Quality=-0.3915, ROC-AUC=0.9487, Support=34, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1132: Quality=-0.3915, ROC-AUC=0.9801, Support=337, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1133: Quality=-0.3915, ROC-AUC=0.9787, Support=219, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1134: Quality=-0.3916, ROC-AUC=0.9755, Support=100, Pattern={'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1135: Quality=-0.3916, ROC-AUC=0.9763, Support=117, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1136: Quality=-0.3916, ROC-AUC=0.9797, Support=283, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1137: Quality=-0.3917, ROC-AUC=0.9708, Support=37, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'T'}{'A'}
  Pattern 1138: Quality=-0.3917, ROC-AUC=0.9731, Support=57, Pattern={'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}
  Pattern 1139: Quality=-0.3917, ROC-AUC=0.9783, Support=187, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 1140: Quality=-0.3918, ROC-AUC=0.9716, Support=42, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}
  Pattern 1141: Quality=-0.3918, ROC-AUC=0.9764, Support=113, Pattern={'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1142: Quality=-0.3918, ROC-AUC=0.9763, Support=108, Pattern={'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1143: Quality=-0.3918, ROC-AUC=0.9802, Support=309, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1144: Quality=-0.3919, ROC-AUC=0.9484, Support=32, Pattern={'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}
  Pattern 1145: Quality=-0.3919, ROC-AUC=0.9474, Support=29, Pattern={'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'A'}{'G'}{'G'}{'G'}{'A'}{'T'}{'A'}
  Pattern 1146: Quality=-0.3920, ROC-AUC=0.9688, Support=24, Pattern={'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'G'}{'C'}{'T'}{'C'}
  Pattern 1147: Quality=-0.3920, ROC-AUC=0.9728, Support=49, Pattern={'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1148: Quality=-0.3920, ROC-AUC=0.9749, Support=75, Pattern={'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'A'}{'C'}{'C'}{'T'}
  Pattern 1149: Quality=-0.3921, ROC-AUC=0.9754, Support=81, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1150: Quality=-0.3922, ROC-AUC=0.9503, Support=37, Pattern={'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'T'}
  Pattern 1151: Quality=-0.3922, ROC-AUC=0.9781, Support=153, Pattern={'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1152: Quality=-0.3923, ROC-AUC=0.9743, Support=60, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1153: Quality=-0.3923, ROC-AUC=0.9725, Support=41, Pattern={'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'A'}{'A'}{'G'}{'C'}
  Pattern 1154: Quality=-0.3924, ROC-AUC=0.9772, Support=111, Pattern={'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1155: Quality=-0.3925, ROC-AUC=0.9729, Support=42, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'A'}{'T'}{'G'}
  Pattern 1156: Quality=-0.3925, ROC-AUC=0.9766, Support=92, Pattern={'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1157: Quality=-0.3925, ROC-AUC=0.9758, Support=76, Pattern={'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1158: Quality=-0.3926, ROC-AUC=0.9760, Support=78, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'A'}{'T'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}
  Pattern 1159: Quality=-0.3927, ROC-AUC=0.9348, Support=31, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'G'}{'A'}
  Pattern 1160: Quality=-0.3927, ROC-AUC=0.9632, Support=148, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1161: Quality=-0.3927, ROC-AUC=0.9769, Support=92, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'T'}
  Pattern 1162: Quality=-0.3928, ROC-AUC=0.9741, Support=48, Pattern={'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}
  Pattern 1163: Quality=-0.3928, ROC-AUC=0.9740, Support=47, Pattern={'G'}{'T'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'T'}
  Pattern 1164: Quality=-0.3928, ROC-AUC=0.9740, Support=46, Pattern={'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}
  Pattern 1165: Quality=-0.3930, ROC-AUC=0.9765, Support=74, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 1166: Quality=-0.3931, ROC-AUC=0.9752, Support=54, Pattern={'A'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'A'}{'A'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'T'}{'G'}{'G'}
  Pattern 1167: Quality=-0.3931, ROC-AUC=0.9796, Support=160, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1168: Quality=-0.3931, ROC-AUC=0.9770, Support=81, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 1169: Quality=-0.3931, ROC-AUC=0.9813, Support=270, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1170: Quality=-0.3932, ROC-AUC=0.9706, Support=21, Pattern={'T'}{'T'}{'A'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'T'}{'G'}{'A'}{'A'}{'G'}{'C'}{'T'}{'A'}{'A'}{'C'}{'A'}{'A'}{'A'}
  Pattern 1171: Quality=-0.3932, ROC-AUC=0.9814, Support=278, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1172: Quality=-0.3932, ROC-AUC=0.9765, Support=68, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1173: Quality=-0.3933, ROC-AUC=0.9761, Support=60, Pattern={'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'A'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1174: Quality=-0.3933, ROC-AUC=0.9750, Support=47, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}
  Pattern 1175: Quality=-0.3933, ROC-AUC=0.9759, Support=56, Pattern={'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1176: Quality=-0.3934, ROC-AUC=0.9813, Support=248, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1177: Quality=-0.3934, ROC-AUC=0.9343, Support=29, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 1178: Quality=-0.3934, ROC-AUC=0.9779, Support=90, Pattern={'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1179: Quality=-0.3935, ROC-AUC=0.9780, Support=87, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}
  Pattern 1180: Quality=-0.3935, ROC-AUC=0.9795, Support=129, Pattern={'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1181: Quality=-0.3936, ROC-AUC=0.9510, Support=35, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'G'}{'T'}{'A'}{'C'}{'C'}{'A'}
  Pattern 1182: Quality=-0.3936, ROC-AUC=0.9206, Support=25, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}
  Pattern 1183: Quality=-0.3936, ROC-AUC=0.9815, Support=238, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1184: Quality=-0.3936, ROC-AUC=0.9822, Support=297, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1185: Quality=-0.3937, ROC-AUC=0.9744, Support=34, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}
  Pattern 1186: Quality=-0.3937, ROC-AUC=0.9750, Support=39, Pattern={'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}{'A'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'T'}{'T'}
  Pattern 1187: Quality=-0.3938, ROC-AUC=0.9789, Support=101, Pattern={'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'A'}{'G'}
  Pattern 1188: Quality=-0.3938, ROC-AUC=0.9271, Support=36, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1189: Quality=-0.3938, ROC-AUC=0.9824, Support=294, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1190: Quality=-0.3938, ROC-AUC=0.9766, Support=54, Pattern={'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1191: Quality=-0.3939, ROC-AUC=0.9750, Support=36, Pattern={'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}
  Pattern 1192: Quality=-0.3939, ROC-AUC=0.9769, Support=55, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 1193: Quality=-0.3940, ROC-AUC=0.9767, Support=51, Pattern={'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1194: Quality=-0.3940, ROC-AUC=0.9812, Support=180, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1195: Quality=-0.3940, ROC-AUC=0.9819, Support=224, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1196: Quality=-0.3940, ROC-AUC=0.9737, Support=25, Pattern={'T'}{'A'}{'G'}{'A'}{'G'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1197: Quality=-0.3941, ROC-AUC=0.9822, Support=236, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1198: Quality=-0.3942, ROC-AUC=0.9807, Support=138, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1199: Quality=-0.3942, ROC-AUC=0.9392, Support=39, Pattern={'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1200: Quality=-0.3943, ROC-AUC=0.9787, Support=73, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1201: Quality=-0.3943, ROC-AUC=0.9821, Support=212, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1202: Quality=-0.3943, ROC-AUC=0.9787, Support=71, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1203: Quality=-0.3943, ROC-AUC=0.9807, Support=124, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}
  Pattern 1204: Quality=-0.3944, ROC-AUC=0.9798, Support=93, Pattern={'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1205: Quality=-0.3944, ROC-AUC=0.9338, Support=54, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}
  Pattern 1206: Quality=-0.3945, ROC-AUC=0.9758, Support=32, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}
  Pattern 1207: Quality=-0.3945, ROC-AUC=0.9791, Support=72, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}
  Pattern 1208: Quality=-0.3945, ROC-AUC=0.9770, Support=40, Pattern={'C'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}
  Pattern 1209: Quality=-0.3945, ROC-AUC=0.9744, Support=22, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'A'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1210: Quality=-0.3945, ROC-AUC=0.9823, Support=196, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1211: Quality=-0.3946, ROC-AUC=0.9795, Support=75, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}
  Pattern 1212: Quality=-0.3946, ROC-AUC=0.9806, Support=103, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1213: Quality=-0.3947, ROC-AUC=0.9825, Support=193, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1214: Quality=-0.3947, ROC-AUC=0.9786, Support=55, Pattern={'A'}{'C'}{'A'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}
  Pattern 1215: Quality=-0.3947, ROC-AUC=0.9831, Support=241, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1216: Quality=-0.3948, ROC-AUC=0.9782, Support=48, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'A'}{'T'}
  Pattern 1217: Quality=-0.3948, ROC-AUC=0.9780, Support=44, Pattern={'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'G'}{'G'}{'C'}
  Pattern 1218: Quality=-0.3948, ROC-AUC=0.9487, Support=25, Pattern={'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}
  Pattern 1219: Quality=-0.3948, ROC-AUC=0.9806, Support=92, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}
  Pattern 1220: Quality=-0.3948, ROC-AUC=0.9773, Support=36, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}
  Pattern 1221: Quality=-0.3949, ROC-AUC=0.9818, Support=134, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'G'}{'T'}{'T'}{'G'}{'C'}
  Pattern 1222: Quality=-0.3949, ROC-AUC=0.9762, Support=27, Pattern={'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'A'}{'A'}
  Pattern 1223: Quality=-0.3949, ROC-AUC=0.9788, Support=53, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}
  Pattern 1224: Quality=-0.3949, ROC-AUC=0.9785, Support=48, Pattern={'C'}{'G'}{'T'}{'T'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1225: Quality=-0.3949, ROC-AUC=0.9803, Support=78, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}
  Pattern 1226: Quality=-0.3949, ROC-AUC=0.9799, Support=68, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1227: Quality=-0.3949, ROC-AUC=0.9778, Support=38, Pattern={'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}
  Pattern 1228: Quality=-0.3949, ROC-AUC=0.9822, Support=145, Pattern={'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1229: Quality=-0.3949, ROC-AUC=0.9827, Support=174, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1230: Quality=-0.3950, ROC-AUC=0.9656, Support=166, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1231: Quality=-0.3950, ROC-AUC=0.9774, Support=33, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'G'}{'A'}{'A'}
  Pattern 1232: Quality=-0.3951, ROC-AUC=0.9770, Support=28, Pattern={'C'}{'T'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'A'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'T'}{'C'}{'G'}{'G'}{'T'}{'A'}
  Pattern 1233: Quality=-0.3951, ROC-AUC=0.9791, Support=48, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'A'}{'C'}{'A'}{'C'}{'A'}{'G'}
  Pattern 1234: Quality=-0.3951, ROC-AUC=0.9798, Support=58, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}
  Pattern 1235: Quality=-0.3951, ROC-AUC=0.9816, Support=101, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 1236: Quality=-0.3952, ROC-AUC=0.9831, Support=177, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1237: Quality=-0.3952, ROC-AUC=0.9789, Support=44, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 1238: Quality=-0.3952, ROC-AUC=0.9799, Support=55, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'T'}
  Pattern 1239: Quality=-0.3952, ROC-AUC=0.9771, Support=26, Pattern={'C'}{'A'}{'A'}{'A'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'A'}{'A'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}
  Pattern 1240: Quality=-0.3953, ROC-AUC=0.9829, Support=148, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'A'}{'G'}
  Pattern 1241: Quality=-0.3953, ROC-AUC=0.9816, Support=92, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}
  Pattern 1242: Quality=-0.3954, ROC-AUC=0.9643, Support=131, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1243: Quality=-0.3955, ROC-AUC=0.9796, Support=42, Pattern={'C'}{'A'}{'G'}{'A'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}{'A'}{'C'}{'T'}{'G'}{'G'}{'T'}{'T'}{'G'}{'C'}{'C'}
  Pattern 1244: Quality=-0.3956, ROC-AUC=0.9830, Support=122, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1245: Quality=-0.3956, ROC-AUC=0.9590, Support=66, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}
  Pattern 1246: Quality=-0.3956, ROC-AUC=0.9819, Support=79, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1247: Quality=-0.3957, ROC-AUC=0.9548, Support=41, Pattern={'T'}{'G'}{'G'}{'G'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}
  Pattern 1248: Quality=-0.3958, ROC-AUC=0.9810, Support=47, Pattern={'C'}{'T'}{'G'}{'A'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1249: Quality=-0.3959, ROC-AUC=0.9808, Support=43, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}
  Pattern 1250: Quality=-0.3960, ROC-AUC=0.9798, Support=29, Pattern={'G'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'A'}{'C'}{'A'}{'T'}{'T'}{'G'}{'G'}{'T'}{'G'}{'T'}{'G'}{'T'}
  Pattern 1251: Quality=-0.3960, ROC-AUC=0.9792, Support=24, Pattern={'G'}{'T'}{'A'}{'A'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'A'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}
  Pattern 1252: Quality=-0.3960, ROC-AUC=0.9825, Support=70, Pattern={'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1253: Quality=-0.3960, ROC-AUC=0.9826, Support=68, Pattern={'C'}{'T'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1254: Quality=-0.3960, ROC-AUC=0.9549, Support=40, Pattern={'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'A'}{'C'}{'T'}{'C'}
  Pattern 1255: Quality=-0.3961, ROC-AUC=0.9487, Support=22, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 1256: Quality=-0.3961, ROC-AUC=0.9826, Support=64, Pattern={'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 1257: Quality=-0.3961, ROC-AUC=0.9815, Support=41, Pattern={'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'A'}{'A'}{'G'}
  Pattern 1258: Quality=-0.3961, ROC-AUC=0.9825, Support=59, Pattern={'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1259: Quality=-0.3962, ROC-AUC=0.9828, Support=63, Pattern={'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}
  Pattern 1260: Quality=-0.3962, ROC-AUC=0.9321, Support=45, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}
  Pattern 1261: Quality=-0.3962, ROC-AUC=0.9600, Support=70, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}
  Pattern 1262: Quality=-0.3962, ROC-AUC=0.9804, Support=26, Pattern={'C'}{'T'}{'A'}{'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'A'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}
  Pattern 1263: Quality=-0.3962, ROC-AUC=0.9464, Support=62, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1264: Quality=-0.3964, ROC-AUC=0.9407, Support=39, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 1265: Quality=-0.3964, ROC-AUC=0.9828, Support=49, Pattern={'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1266: Quality=-0.3966, ROC-AUC=0.9826, Support=34, Pattern={'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'C'}{'A'}{'A'}{'A'}{'T'}
  Pattern 1267: Quality=-0.3966, ROC-AUC=0.9823, Support=29, Pattern={'C'}{'T'}{'A'}{'A'}{'A'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1268: Quality=-0.3967, ROC-AUC=0.9828, Support=33, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'A'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1269: Quality=-0.3973, ROC-AUC=0.9592, Support=56, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1270: Quality=-0.3976, ROC-AUC=0.9510, Support=23, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1271: Quality=-0.3976, ROC-AUC=0.9495, Support=20, Pattern={'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'A'}
  Pattern 1272: Quality=-0.3977, ROC-AUC=0.9583, Support=48, Pattern={'G'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1273: Quality=-0.3983, ROC-AUC=0.9316, Support=40, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1274: Quality=-0.3984, ROC-AUC=0.9589, Support=48, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'A'}{'G'}{'T'}{'C'}
  Pattern 1275: Quality=-0.3984, ROC-AUC=0.9653, Support=109, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1276: Quality=-0.3987, ROC-AUC=0.9333, Support=20, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1277: Quality=-0.3989, ROC-AUC=0.9594, Support=48, Pattern={'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 1278: Quality=-0.3992, ROC-AUC=0.9447, Support=45, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1279: Quality=-0.3999, ROC-AUC=0.9011, Support=20, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1280: Quality=-0.4001, ROC-AUC=0.9669, Support=111, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1281: Quality=-0.4003, ROC-AUC=0.9608, Support=47, Pattern={'A'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'A'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1282: Quality=-0.4003, ROC-AUC=0.9674, Support=116, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1283: Quality=-0.4003, ROC-AUC=0.9531, Support=20, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'T'}{'C'}
  Pattern 1284: Quality=-0.4004, ROC-AUC=0.9545, Support=23, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}
  Pattern 1285: Quality=-0.4005, ROC-AUC=0.9697, Support=165, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1286: Quality=-0.4005, ROC-AUC=0.9673, Support=112, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1287: Quality=-0.4010, ROC-AUC=0.9450, Support=41, Pattern={'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1288: Quality=-0.4012, ROC-AUC=0.9459, Support=44, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'T'}{'G'}{'C'}
  Pattern 1289: Quality=-0.4014, ROC-AUC=0.9630, Support=53, Pattern={'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1290: Quality=-0.4018, ROC-AUC=0.9464, Support=44, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 1291: Quality=-0.4020, ROC-AUC=0.9664, Support=78, Pattern={'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1292: Quality=-0.4020, ROC-AUC=0.9640, Support=55, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1293: Quality=-0.4025, ROC-AUC=0.9648, Support=58, Pattern={'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1294: Quality=-0.4025, ROC-AUC=0.9592, Support=28, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}
  Pattern 1295: Quality=-0.4026, ROC-AUC=0.9488, Support=51, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1296: Quality=-0.4026, ROC-AUC=0.9573, Support=22, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'A'}
  Pattern 1297: Quality=-0.4027, ROC-AUC=0.9722, Support=187, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1298: Quality=-0.4027, ROC-AUC=0.9659, Support=65, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 1299: Quality=-0.4029, ROC-AUC=0.9701, Support=124, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1300: Quality=-0.4033, ROC-AUC=0.9640, Support=45, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'A'}{'T'}{'C'}{'A'}{'G'}{'C'}
  Pattern 1301: Quality=-0.4033, ROC-AUC=0.9583, Support=22, Pattern={'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}
  Pattern 1302: Quality=-0.4040, ROC-AUC=0.9705, Support=108, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1303: Quality=-0.4045, ROC-AUC=0.9638, Support=35, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1304: Quality=-0.4046, ROC-AUC=0.9695, Support=82, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1305: Quality=-0.4047, ROC-AUC=0.9738, Support=178, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1306: Quality=-0.4047, ROC-AUC=0.9608, Support=23, Pattern={'T'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1307: Quality=-0.4048, ROC-AUC=0.9444, Support=30, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1308: Quality=-0.4049, ROC-AUC=0.9636, Support=32, Pattern={'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'A'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'A'}{'C'}
  Pattern 1309: Quality=-0.4049, ROC-AUC=0.9663, Support=46, Pattern={'T'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1310: Quality=-0.4050, ROC-AUC=0.9423, Support=25, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1311: Quality=-0.4050, ROC-AUC=0.9669, Support=50, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 1312: Quality=-0.4050, ROC-AUC=0.9699, Support=81, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 1313: Quality=-0.4051, ROC-AUC=0.9632, Support=29, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}
  Pattern 1314: Quality=-0.4052, ROC-AUC=0.9625, Support=26, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 1315: Quality=-0.4052, ROC-AUC=0.9659, Support=41, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1316: Quality=-0.4053, ROC-AUC=0.9651, Support=36, Pattern={'G'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1317: Quality=-0.4055, ROC-AUC=0.9412, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 1318: Quality=-0.4057, ROC-AUC=0.9681, Support=52, Pattern={'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'G'}{'G'}{'T'}{'G'}
  Pattern 1319: Quality=-0.4057, ROC-AUC=0.9689, Support=59, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1320: Quality=-0.4060, ROC-AUC=0.9754, Support=192, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1321: Quality=-0.4062, ROC-AUC=0.9748, Support=162, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1322: Quality=-0.4063, ROC-AUC=0.9666, Support=36, Pattern={'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1323: Quality=-0.4063, ROC-AUC=0.9675, Support=41, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1324: Quality=-0.4064, ROC-AUC=0.9647, Support=27, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'A'}{'A'}{'G'}
  Pattern 1325: Quality=-0.4064, ROC-AUC=0.9663, Support=34, Pattern={'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1326: Quality=-0.4064, ROC-AUC=0.9674, Support=40, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'C'}{'G'}{'G'}
  Pattern 1327: Quality=-0.4064, ROC-AUC=0.9645, Support=26, Pattern={'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1328: Quality=-0.4064, ROC-AUC=0.9630, Support=21, Pattern={'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1329: Quality=-0.4065, ROC-AUC=0.9726, Support=95, Pattern={'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}
  Pattern 1330: Quality=-0.4065, ROC-AUC=0.9333, Support=31, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'A'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1331: Quality=-0.4065, ROC-AUC=0.9680, Support=42, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1332: Quality=-0.4066, ROC-AUC=0.9588, Support=105, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1333: Quality=-0.4070, ROC-AUC=0.9667, Support=31, Pattern={'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1334: Quality=-0.4070, ROC-AUC=0.9643, Support=22, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'A'}{'A'}{'G'}{'A'}{'C'}{'C'}
  Pattern 1335: Quality=-0.4073, ROC-AUC=0.9441, Support=24, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1336: Quality=-0.4076, ROC-AUC=0.9745, Support=107, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1337: Quality=-0.4076, ROC-AUC=0.9741, Support=97, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1338: Quality=-0.4076, ROC-AUC=0.9737, Support=89, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1339: Quality=-0.4078, ROC-AUC=0.9683, Support=32, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}
  Pattern 1340: Quality=-0.4079, ROC-AUC=0.9487, Support=34, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1341: Quality=-0.4079, ROC-AUC=0.9481, Support=32, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}
  Pattern 1342: Quality=-0.4079, ROC-AUC=0.9770, Support=173, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1343: Quality=-0.4085, ROC-AUC=0.9720, Support=50, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}
  Pattern 1344: Quality=-0.4086, ROC-AUC=0.9770, Support=140, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1345: Quality=-0.4087, ROC-AUC=0.9722, Support=49, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1346: Quality=-0.4087, ROC-AUC=0.9704, Support=35, Pattern={'G'}{'T'}{'T'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'A'}{'C'}
  Pattern 1347: Quality=-0.4089, ROC-AUC=0.9770, Support=125, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1348: Quality=-0.4090, ROC-AUC=0.9762, Support=101, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1349: Quality=-0.4091, ROC-AUC=0.9755, Support=83, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1350: Quality=-0.4092, ROC-AUC=0.9444, Support=21, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1351: Quality=-0.4092, ROC-AUC=0.9765, Support=101, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}
  Pattern 1352: Quality=-0.4094, ROC-AUC=0.9727, Support=42, Pattern={'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'G'}{'C'}
  Pattern 1353: Quality=-0.4095, ROC-AUC=0.9792, Support=187, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1354: Quality=-0.4097, ROC-AUC=0.9782, Support=131, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1355: Quality=-0.4098, ROC-AUC=0.9783, Support=126, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}
  Pattern 1356: Quality=-0.4100, ROC-AUC=0.9754, Support=60, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 1357: Quality=-0.4100, ROC-AUC=0.9714, Support=26, Pattern={'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'A'}{'A'}
  Pattern 1358: Quality=-0.4101, ROC-AUC=0.9700, Support=20, Pattern={'T'}{'A'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1359: Quality=-0.4101, ROC-AUC=0.9752, Support=54, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}
  Pattern 1360: Quality=-0.4102, ROC-AUC=0.9760, Support=64, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1361: Quality=-0.4102, ROC-AUC=0.9727, Support=31, Pattern={'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}
  Pattern 1362: Quality=-0.4102, ROC-AUC=0.9752, Support=51, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1363: Quality=-0.4102, ROC-AUC=0.9755, Support=55, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1364: Quality=-0.4104, ROC-AUC=0.9791, Support=127, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}
  Pattern 1365: Quality=-0.4108, ROC-AUC=0.9791, Support=104, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1366: Quality=-0.4109, ROC-AUC=0.9722, Support=21, Pattern={'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1367: Quality=-0.4109, ROC-AUC=0.9770, Support=58, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1368: Quality=-0.4110, ROC-AUC=0.9808, Support=157, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1369: Quality=-0.4111, ROC-AUC=0.9778, Support=65, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 1370: Quality=-0.4111, ROC-AUC=0.9770, Support=52, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1371: Quality=-0.4112, ROC-AUC=0.9740, Support=25, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'T'}{'T'}{'T'}{'G'}
  Pattern 1372: Quality=-0.4112, ROC-AUC=0.9819, Support=205, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1373: Quality=-0.4113, ROC-AUC=0.9770, Support=47, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1374: Quality=-0.4113, ROC-AUC=0.9820, Support=200, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1375: Quality=-0.4113, ROC-AUC=0.9794, Support=88, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1376: Quality=-0.4113, ROC-AUC=0.9744, Support=25, Pattern={'T'}{'T'}{'T'}{'A'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1377: Quality=-0.4115, ROC-AUC=0.9813, Support=147, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1378: Quality=-0.4116, ROC-AUC=0.9753, Support=27, Pattern={'G'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1379: Quality=-0.4118, ROC-AUC=0.9750, Support=22, Pattern={'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'A'}{'T'}{'C'}{'A'}{'T'}
  Pattern 1380: Quality=-0.4120, ROC-AUC=0.9827, Support=177, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1381: Quality=-0.4120, ROC-AUC=0.9794, Support=57, Pattern={'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'T'}
  Pattern 1382: Quality=-0.4120, ROC-AUC=0.9792, Support=53, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1383: Quality=-0.4122, ROC-AUC=0.9602, Support=75, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1384: Quality=-0.4122, ROC-AUC=0.9133, Support=25, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1385: Quality=-0.4122, ROC-AUC=0.9811, Support=85, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1386: Quality=-0.4123, ROC-AUC=0.9797, Support=53, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 1387: Quality=-0.4123, ROC-AUC=0.9803, Support=62, Pattern={'G'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1388: Quality=-0.4123, ROC-AUC=0.9793, Support=44, Pattern={'G'}{'G'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1389: Quality=-0.4124, ROC-AUC=0.9815, Support=84, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1390: Quality=-0.4126, ROC-AUC=0.9545, Support=38, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1391: Quality=-0.4127, ROC-AUC=0.9500, Support=24, Pattern={'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1392: Quality=-0.4127, ROC-AUC=0.9778, Support=21, Pattern={'T'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1393: Quality=-0.4127, ROC-AUC=0.9828, Support=100, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1394: Quality=-0.4128, ROC-AUC=0.9792, Support=30, Pattern={'T'}{'T'}{'A'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}
  Pattern 1395: Quality=-0.4128, ROC-AUC=0.9809, Support=48, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1396: Quality=-0.4129, ROC-AUC=0.9816, Support=58, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 1397: Quality=-0.4129, ROC-AUC=0.9803, Support=36, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'A'}{'A'}{'C'}{'T'}{'A'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1398: Quality=-0.4130, ROC-AUC=0.9820, Support=61, Pattern={'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1399: Quality=-0.4130, ROC-AUC=0.9561, Support=43, Pattern={'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1400: Quality=-0.4132, ROC-AUC=0.9796, Support=21, Pattern={'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'A'}{'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'C'}{'T'}
  Pattern 1401: Quality=-0.4133, ROC-AUC=0.9812, Support=33, Pattern={'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1402: Quality=-0.4133, ROC-AUC=0.9821, Support=42, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'A'}{'C'}{'A'}{'A'}{'G'}{'T'}
  Pattern 1403: Quality=-0.4134, ROC-AUC=0.9804, Support=23, Pattern={'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1404: Quality=-0.4134, ROC-AUC=0.9808, Support=25, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}
  Pattern 1405: Quality=-0.4134, ROC-AUC=0.9827, Support=46, Pattern={'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1406: Quality=-0.4135, ROC-AUC=0.9808, Support=21, Pattern={'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}
  Pattern 1407: Quality=-0.4137, ROC-AUC=0.9583, Support=51, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1408: Quality=-0.4138, ROC-AUC=0.9818, Support=21, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'T'}{'A'}{'A'}{'C'}{'A'}
  Pattern 1409: Quality=-0.4144, ROC-AUC=0.9231, Support=23, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1410: Quality=-0.4147, ROC-AUC=0.9538, Support=28, Pattern={'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}
  Pattern 1411: Quality=-0.4152, ROC-AUC=0.9533, Support=25, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'T'}
  Pattern 1412: Quality=-0.4157, ROC-AUC=0.9216, Support=20, Pattern={'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1413: Quality=-0.4158, ROC-AUC=0.9602, Support=49, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'T'}{'G'}{'A'}{'G'}
  Pattern 1414: Quality=-0.4162, ROC-AUC=0.9375, Support=24, Pattern={'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1415: Quality=-0.4163, ROC-AUC=0.9598, Support=44, Pattern={'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1416: Quality=-0.4169, ROC-AUC=0.9668, Support=102, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}
  Pattern 1417: Quality=-0.4178, ROC-AUC=0.9583, Support=30, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1418: Quality=-0.4183, ROC-AUC=0.9595, Support=32, Pattern={'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}
  Pattern 1419: Quality=-0.4184, ROC-AUC=0.9571, Support=24, Pattern={'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1420: Quality=-0.4184, ROC-AUC=0.9643, Support=58, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1421: Quality=-0.4185, ROC-AUC=0.9596, Support=31, Pattern={'G'}{'C'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 1422: Quality=-0.4186, ROC-AUC=0.9455, Support=38, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1423: Quality=-0.4191, ROC-AUC=0.9298, Support=28, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}
  Pattern 1424: Quality=-0.4193, ROC-AUC=0.9642, Support=49, Pattern={'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1425: Quality=-0.4200, ROC-AUC=0.9641, Support=43, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'T'}{'C'}{'A'}{'G'}
  Pattern 1426: Quality=-0.4210, ROC-AUC=0.9649, Support=40, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'A'}{'C'}
  Pattern 1427: Quality=-0.4211, ROC-AUC=0.9596, Support=20, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}
  Pattern 1428: Quality=-0.4211, ROC-AUC=0.9689, Support=73, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1429: Quality=-0.4213, ROC-AUC=0.9670, Support=52, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1430: Quality=-0.4216, ROC-AUC=0.9625, Support=26, Pattern={'C'}{'T'}{'A'}{'A'}{'G'}{'A'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'A'}{'C'}{'A'}{'A'}
  Pattern 1431: Quality=-0.4224, ROC-AUC=0.9715, Support=87, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1432: Quality=-0.4226, ROC-AUC=0.9738, Support=131, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1433: Quality=-0.4228, ROC-AUC=0.9705, Support=66, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1434: Quality=-0.4231, ROC-AUC=0.9507, Support=43, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1435: Quality=-0.4231, ROC-AUC=0.9667, Support=33, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1436: Quality=-0.4234, ROC-AUC=0.9683, Support=39, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1437: Quality=-0.4236, ROC-AUC=0.9667, Support=29, Pattern={'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}
  Pattern 1438: Quality=-0.4236, ROC-AUC=0.9709, Support=58, Pattern={'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1439: Quality=-0.4239, ROC-AUC=0.9444, Support=23, Pattern={'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}
  Pattern 1440: Quality=-0.4239, ROC-AUC=0.9741, Support=99, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1441: Quality=-0.4242, ROC-AUC=0.9658, Support=22, Pattern={'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}
  Pattern 1442: Quality=-0.4243, ROC-AUC=0.9691, Support=36, Pattern={'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}
  Pattern 1443: Quality=-0.4243, ROC-AUC=0.9720, Support=59, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1444: Quality=-0.4248, ROC-AUC=0.9725, Support=55, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1445: Quality=-0.4249, ROC-AUC=0.9679, Support=25, Pattern={'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'A'}{'T'}{'C'}{'T'}
  Pattern 1446: Quality=-0.4249, ROC-AUC=0.9716, Support=46, Pattern={'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1447: Quality=-0.4249, ROC-AUC=0.9718, Support=47, Pattern={'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1448: Quality=-0.4250, ROC-AUC=0.9444, Support=21, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1449: Quality=-0.4254, ROC-AUC=0.9764, Support=106, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1450: Quality=-0.4254, ROC-AUC=0.9734, Support=54, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1451: Quality=-0.4255, ROC-AUC=0.9706, Support=31, Pattern={'G'}{'C'}{'A'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1452: Quality=-0.4257, ROC-AUC=0.9692, Support=23, Pattern={'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'A'}
  Pattern 1453: Quality=-0.4260, ROC-AUC=0.9697, Support=23, Pattern={'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 1454: Quality=-0.4260, ROC-AUC=0.9704, Support=26, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1455: Quality=-0.4261, ROC-AUC=0.9748, Support=58, Pattern={'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1456: Quality=-0.4261, ROC-AUC=0.9704, Support=24, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1457: Quality=-0.4263, ROC-AUC=0.9739, Support=44, Pattern={'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1458: Quality=-0.4264, ROC-AUC=0.9745, Support=48, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'C'}{'G'}{'C'}
  Pattern 1459: Quality=-0.4264, ROC-AUC=0.9740, Support=43, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}
  Pattern 1460: Quality=-0.4266, ROC-AUC=0.9706, Support=21, Pattern={'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}
  Pattern 1461: Quality=-0.4266, ROC-AUC=0.9767, Support=73, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1462: Quality=-0.4267, ROC-AUC=0.9766, Support=68, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 1463: Quality=-0.4269, ROC-AUC=0.9728, Support=28, Pattern={'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1464: Quality=-0.4269, ROC-AUC=0.9720, Support=24, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1465: Quality=-0.4270, ROC-AUC=0.9487, Support=25, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'A'}{'G'}{'C'}
  Pattern 1466: Quality=-0.4271, ROC-AUC=0.9770, Support=64, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 1467: Quality=-0.4271, ROC-AUC=0.9783, Support=88, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1468: Quality=-0.4272, ROC-AUC=0.9757, Support=45, Pattern={'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1469: Quality=-0.4275, ROC-AUC=0.9762, Support=43, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1470: Quality=-0.4275, ROC-AUC=0.9813, Support=177, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1471: Quality=-0.4275, ROC-AUC=0.9772, Support=53, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1472: Quality=-0.4276, ROC-AUC=0.9762, Support=40, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}
  Pattern 1473: Quality=-0.4278, ROC-AUC=0.9760, Support=35, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'A'}{'G'}
  Pattern 1474: Quality=-0.4278, ROC-AUC=0.9737, Support=21, Pattern={'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'A'}{'G'}
  Pattern 1475: Quality=-0.4282, ROC-AUC=0.9762, Support=29, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1476: Quality=-0.4283, ROC-AUC=0.9752, Support=22, Pattern={'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}
  Pattern 1477: Quality=-0.4285, ROC-AUC=0.9802, Support=69, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}
  Pattern 1478: Quality=-0.4288, ROC-AUC=0.9804, Support=59, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 1479: Quality=-0.4289, ROC-AUC=0.9500, Support=23, Pattern={'T'}{'A'}{'T'}{'G'}{'T'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1480: Quality=-0.4289, ROC-AUC=0.9815, Support=75, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1481: Quality=-0.4289, ROC-AUC=0.9795, Support=40, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}
  Pattern 1482: Quality=-0.4290, ROC-AUC=0.9359, Support=25, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'T'}{'C'}{'C'}
  Pattern 1483: Quality=-0.4290, ROC-AUC=0.9779, Support=25, Pattern={'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1484: Quality=-0.4290, ROC-AUC=0.9832, Support=134, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1485: Quality=-0.4291, ROC-AUC=0.9783, Support=25, Pattern={'G'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 1486: Quality=-0.4291, ROC-AUC=0.9810, Support=55, Pattern={'C'}{'T'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1487: Quality=-0.4294, ROC-AUC=0.9821, Support=64, Pattern={'C'}{'A'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1488: Quality=-0.4295, ROC-AUC=0.9829, Support=76, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 1489: Quality=-0.4296, ROC-AUC=0.9792, Support=20, Pattern={'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}
  Pattern 1490: Quality=-0.4298, ROC-AUC=0.9812, Support=28, Pattern={'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'G'}{'T'}{'G'}
  Pattern 1491: Quality=-0.4299, ROC-AUC=0.9810, Support=22, Pattern={'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}
  Pattern 1492: Quality=-0.4301, ROC-AUC=0.9821, Support=26, Pattern={'T'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}
  Pattern 1493: Quality=-0.4303, ROC-AUC=0.9558, Support=35, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'G'}
  Pattern 1494: Quality=-0.4312, ROC-AUC=0.9524, Support=22, Pattern={'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'A'}{'A'}
  Pattern 1495: Quality=-0.4317, ROC-AUC=0.9529, Support=22, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}
  Pattern 1496: Quality=-0.4317, ROC-AUC=0.9583, Support=39, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1497: Quality=-0.4322, ROC-AUC=0.9608, Support=49, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'G'}{'G'}
  Pattern 1498: Quality=-0.4327, ROC-AUC=0.9583, Support=34, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1499: Quality=-0.4335, ROC-AUC=0.9554, Support=22, Pattern={'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1500: Quality=-0.4339, ROC-AUC=0.9600, Support=35, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}{'G'}
  Pattern 1501: Quality=-0.4360, ROC-AUC=0.9394, Support=20, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1502: Quality=-0.4361, ROC-AUC=0.9583, Support=20, Pattern={'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'C'}{'A'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}
  Pattern 1503: Quality=-0.4363, ROC-AUC=0.9592, Support=21, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'G'}
  Pattern 1504: Quality=-0.4367, ROC-AUC=0.9667, Support=53, Pattern={'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1505: Quality=-0.4371, ROC-AUC=0.9600, Support=20, Pattern={'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1506: Quality=-0.4375, ROC-AUC=0.9643, Support=32, Pattern={'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1507: Quality=-0.4380, ROC-AUC=0.9675, Support=46, Pattern={'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1508: Quality=-0.4383, ROC-AUC=0.9294, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 1509: Quality=-0.4385, ROC-AUC=0.9643, Support=26, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 1510: Quality=-0.4388, ROC-AUC=0.9673, Support=37, Pattern={'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}
  Pattern 1511: Quality=-0.4390, ROC-AUC=0.9703, Support=57, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1512: Quality=-0.4403, ROC-AUC=0.9719, Support=54, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1513: Quality=-0.4405, ROC-AUC=0.9489, Support=30, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1514: Quality=-0.4406, ROC-AUC=0.9669, Support=22, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1515: Quality=-0.4417, ROC-AUC=0.9688, Support=20, Pattern={'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1516: Quality=-0.4417, ROC-AUC=0.9706, Support=27, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1517: Quality=-0.4423, ROC-AUC=0.9765, Support=74, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1518: Quality=-0.4430, ROC-AUC=0.9767, Support=56, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}
  Pattern 1519: Quality=-0.4431, ROC-AUC=0.9737, Support=27, Pattern={'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1520: Quality=-0.4435, ROC-AUC=0.9788, Support=75, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1521: Quality=-0.4438, ROC-AUC=0.9762, Support=33, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}
  Pattern 1522: Quality=-0.4440, ROC-AUC=0.9783, Support=47, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'G'}{'C'}{'C'}
  Pattern 1523: Quality=-0.4441, ROC-AUC=0.9776, Support=38, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1524: Quality=-0.4441, ROC-AUC=0.9762, Support=26, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}
  Pattern 1525: Quality=-0.4443, ROC-AUC=0.9773, Support=31, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1526: Quality=-0.4443, ROC-AUC=0.9778, Support=34, Pattern={'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'T'}
  Pattern 1527: Quality=-0.4444, ROC-AUC=0.9778, Support=33, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 1528: Quality=-0.4444, ROC-AUC=0.9778, Support=33, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'C'}
  Pattern 1529: Quality=-0.4446, ROC-AUC=0.9805, Support=62, Pattern={'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}
  Pattern 1530: Quality=-0.4447, ROC-AUC=0.9790, Support=37, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'G'}{'T'}
  Pattern 1531: Quality=-0.4447, ROC-AUC=0.9811, Support=68, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1532: Quality=-0.4447, ROC-AUC=0.9773, Support=23, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 1533: Quality=-0.4450, ROC-AUC=0.9510, Support=23, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1534: Quality=-0.4451, ROC-AUC=0.9810, Support=46, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1535: Quality=-0.4451, ROC-AUC=0.9827, Support=82, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}
  Pattern 1536: Quality=-0.4460, ROC-AUC=0.9825, Support=25, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'A'}{'G'}{'A'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1537: Quality=-0.4473, ROC-AUC=0.9538, Support=23, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1538: Quality=-0.4521, ROC-AUC=0.9596, Support=20, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1539: Quality=-0.4532, ROC-AUC=0.9643, Support=29, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1540: Quality=-0.4542, ROC-AUC=0.9636, Support=21, Pattern={'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1541: Quality=-0.4543, ROC-AUC=0.9696, Support=50, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1542: Quality=-0.4564, ROC-AUC=0.9728, Support=49, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}
  Pattern 1543: Quality=-0.4591, ROC-AUC=0.9761, Support=30, Pattern={'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1544: Quality=-0.4591, ROC-AUC=0.9760, Support=29, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 1545: Quality=-0.4597, ROC-AUC=0.9765, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}
  Pattern 1546: Quality=-0.4601, ROC-AUC=0.9792, Support=32, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}
  Pattern 1547: Quality=-0.4607, ROC-AUC=0.9822, Support=45, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 1548: Quality=-0.4607, ROC-AUC=0.9821, Support=43, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1549: Quality=-0.4608, ROC-AUC=0.9800, Support=20, Pattern={'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 1550: Quality=-0.4612, ROC-AUC=0.9818, Support=21, Pattern={'G'}{'A'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}
  Pattern 1551: Quality=-0.4612, ROC-AUC=0.9825, Support=25, Pattern={'C'}{'G'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}
  Pattern 1552: Quality=-0.4709, ROC-AUC=0.9683, Support=24, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'G'}{'G'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1553: Quality=-0.4717, ROC-AUC=0.9713, Support=30, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}
  Pattern 1554: Quality=-0.4742, ROC-AUC=0.9773, Support=31, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1555: Quality=-0.4745, ROC-AUC=0.9769, Support=23, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1556: Quality=-0.4748, ROC-AUC=0.9800, Support=41, Pattern={'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 1557: Quality=-0.4751, ROC-AUC=0.9813, Support=49, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
================================================================================

================
APPLYING STATISTICAL VALIDATION
================
 Applying FDR correction
  Pattern 0: AUC diff=0.3433, p=0.001700, adj_p=0.002125 --> SIGNIFICANT
  Pattern 1: AUC diff=0.2090, p=0.005000, adj_p=0.005376 --> SIGNIFICANT
  Pattern 2: AUC diff=0.1822, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 3: AUC diff=0.1599, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 4: AUC diff=0.1704, p=0.000500, adj_p=0.000847 --> SIGNIFICANT
  Pattern 5: AUC diff=0.1650, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 6: AUC diff=0.1221, p=0.000800, adj_p=0.001250 --> SIGNIFICANT
  Pattern 7: AUC diff=0.1158, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 8: AUC diff=0.1114, p=0.001000, adj_p=0.001428 --> SIGNIFICANT
  Pattern 9: AUC diff=0.1004, p=0.012899, adj_p=0.013029 --> SIGNIFICANT
  Pattern 10: AUC diff=0.0129, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 11: AUC diff=0.1361, p=0.001000, adj_p=0.001428 --> SIGNIFICANT
  Pattern 12: AUC diff=0.0110, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 13: AUC diff=0.1026, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 14: AUC diff=0.0107, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 15: AUC diff=0.0105, p=0.000700, adj_p=0.001147 --> SIGNIFICANT
  Pattern 16: AUC diff=0.0942, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 17: AUC diff=0.1205, p=0.000500, adj_p=0.000847 --> SIGNIFICANT
  Pattern 18: AUC diff=0.0973, p=0.001100, adj_p=0.001507 --> SIGNIFICANT
  Pattern 19: AUC diff=0.1087, p=0.003400, adj_p=0.003863 --> SIGNIFICANT
  Pattern 20: AUC diff=0.0166, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 21: AUC diff=0.0133, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 22: AUC diff=0.0140, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 23: AUC diff=0.0122, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 24: AUC diff=0.0112, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 25: AUC diff=0.0114, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 26: AUC diff=0.0116, p=0.000500, adj_p=0.000847 --> SIGNIFICANT
  Pattern 27: AUC diff=0.0126, p=0.000600, adj_p=0.001000 --> SIGNIFICANT
  Pattern 28: AUC diff=0.0119, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 29: AUC diff=0.0105, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 30: AUC diff=0.0106, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 31: AUC diff=0.0127, p=0.002700, adj_p=0.003176 --> SIGNIFICANT
  Pattern 32: AUC diff=0.0100, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 33: AUC diff=0.0105, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 34: AUC diff=0.0105, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 35: AUC diff=0.0114, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 36: AUC diff=0.0108, p=0.000300, adj_p=0.000638 --> SIGNIFICANT
  Pattern 37: AUC diff=0.0111, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 38: AUC diff=0.0106, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 39: AUC diff=0.0108, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 40: AUC diff=0.0105, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 41: AUC diff=0.0115, p=0.001600, adj_p=0.002078 --> SIGNIFICANT
  Pattern 42: AUC diff=0.0116, p=0.001600, adj_p=0.002078 --> SIGNIFICANT
  Pattern 43: AUC diff=0.0103, p=0.000300, adj_p=0.000638 --> SIGNIFICANT
  Pattern 44: AUC diff=0.0104, p=0.002100, adj_p=0.002592 --> SIGNIFICANT
  Pattern 45: AUC diff=0.0103, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 46: AUC diff=0.0106, p=0.000800, adj_p=0.001250 --> SIGNIFICANT
  Pattern 47: AUC diff=0.0111, p=0.002700, adj_p=0.003176 --> SIGNIFICANT
  Pattern 48: AUC diff=0.0103, p=0.001000, adj_p=0.001428 --> SIGNIFICANT
  Pattern 49: AUC diff=0.0117, p=0.004800, adj_p=0.005217 --> SIGNIFICANT
  Pattern 50: AUC diff=0.0118, p=0.005199, adj_p=0.005531 --> SIGNIFICANT
  Pattern 51: AUC diff=0.0105, p=0.001700, adj_p=0.002125 --> SIGNIFICANT
  Pattern 52: AUC diff=0.0100, p=0.000900, adj_p=0.001364 --> SIGNIFICANT
  Pattern 53: AUC diff=0.0101, p=0.003100, adj_p=0.003563 --> SIGNIFICANT
  Pattern 54: AUC diff=0.0100, p=0.005899, adj_p=0.006082 --> SIGNIFICANT
  Pattern 55: AUC diff=0.0101, p=0.015998, adj_p=0.015998 --> SIGNIFICANT
  Pattern 56: AUC diff=0.0790, p=0.001100, adj_p=0.001507 --> SIGNIFICANT
  Pattern 57: AUC diff=0.1044, p=0.006999, adj_p=0.007142 --> SIGNIFICANT
  Pattern 58: AUC diff=0.0289, p=0.002300, adj_p=0.002805 --> SIGNIFICANT
  Pattern 59: AUC diff=0.0985, p=0.005799, adj_p=0.006041 --> SIGNIFICANT
  Pattern 60: AUC diff=0.0848, p=0.001500, adj_p=0.002000 --> SIGNIFICANT
  Pattern 61: AUC diff=0.0826, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 62: AUC diff=0.0966, p=0.000800, adj_p=0.001250 --> SIGNIFICANT
  Pattern 63: AUC diff=0.1109, p=0.001700, adj_p=0.002125 --> SIGNIFICANT
  Pattern 64: AUC diff=0.0261, p=0.004300, adj_p=0.004725 --> SIGNIFICANT
  Pattern 65: AUC diff=0.1183, p=0.000900, adj_p=0.001364 --> SIGNIFICANT
  Pattern 66: AUC diff=0.0237, p=0.001400, adj_p=0.001892 --> SIGNIFICANT
  Pattern 67: AUC diff=0.1022, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 68: AUC diff=0.0187, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 69: AUC diff=0.0160, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 70: AUC diff=0.0167, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 71: AUC diff=0.0164, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 72: AUC diff=0.0962, p=0.005599, adj_p=0.005894 --> SIGNIFICANT
  Pattern 73: AUC diff=0.0159, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 74: AUC diff=0.0690, p=0.000300, adj_p=0.000638 --> SIGNIFICANT
  Pattern 75: AUC diff=0.0150, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 76: AUC diff=0.0892, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 77: AUC diff=0.0167, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 78: AUC diff=0.0182, p=0.003700, adj_p=0.004157 --> SIGNIFICANT
  Pattern 79: AUC diff=0.1141, p=0.002400, adj_p=0.002891 --> SIGNIFICANT
  Pattern 80: AUC diff=0.0164, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 81: AUC diff=0.0174, p=0.003800, adj_p=0.004222 --> SIGNIFICANT
  Pattern 82: AUC diff=0.0153, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 83: AUC diff=0.0167, p=0.001000, adj_p=0.001428 --> SIGNIFICANT
  Pattern 84: AUC diff=0.0160, p=0.000400, adj_p=0.000741 --> SIGNIFICANT
  Pattern 85: AUC diff=0.0134, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 86: AUC diff=0.0312, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 87: AUC diff=0.0170, p=0.003000, adj_p=0.003488 --> SIGNIFICANT
  Pattern 88: AUC diff=0.0144, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 89: AUC diff=0.0135, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 90: AUC diff=0.0156, p=0.000300, adj_p=0.000638 --> SIGNIFICANT
  Pattern 91: AUC diff=0.0137, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 92: AUC diff=0.0136, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 93: AUC diff=0.0151, p=0.000500, adj_p=0.000847 --> SIGNIFICANT
  Pattern 94: AUC diff=0.0933, p=0.000300, adj_p=0.000638 --> SIGNIFICANT
  Pattern 95: AUC diff=0.0130, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 96: AUC diff=0.0143, p=0.000200, adj_p=0.000476 --> SIGNIFICANT
  Pattern 97: AUC diff=0.0141, p=0.000500, adj_p=0.000847 --> SIGNIFICANT
  Pattern 98: AUC diff=0.0132, p=0.000100, adj_p=0.000345 --> SIGNIFICANT
  Pattern 99: AUC diff=0.0150, p=0.001100, adj_p=0.001507 --> SIGNIFICANT

 Found 100 significant patterns out of 100 tested.
  Validation completed in 952.51 seconds.
================
PATTERNS AFTER STATISTICAL VALIDATION
================
  Pattern 0: Quality=0.6756, ROC-AUC=0.6500, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}
  Pattern 1: Quality=-0.0505, ROC-AUC=0.7843, Support=20, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 2: Quality=-0.1383, ROC-AUC=0.8111, Support=21, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}
  Pattern 3: Quality=-0.1500, ROC-AUC=0.8333, Support=26, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}
  Pattern 4: Quality=-0.1706, ROC-AUC=0.8229, Support=22, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 5: Quality=-0.1841, ROC-AUC=0.8283, Support=20, Pattern={'C'}{'A'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 6: Quality=-0.2138, ROC-AUC=0.8712, Support=37, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 7: Quality=-0.2405, ROC-AUC=0.8775, Support=41, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 8: Quality=-0.2668, ROC-AUC=0.8818, Support=27, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 9: Quality=-0.2699, ROC-AUC=0.8929, Support=29, Pattern={'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}
  Pattern 10: Quality=-0.2705, ROC-AUC=0.9804, Support=597, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 11: Quality=-0.2706, ROC-AUC=0.8571, Support=22, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 12: Quality=-0.2728, ROC-AUC=0.9823, Support=588, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 13: Quality=-0.2730, ROC-AUC=0.8906, Support=44, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}
  Pattern 14: Quality=-0.2736, ROC-AUC=0.9826, Support=496, Pattern={'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 15: Quality=-0.2740, ROC-AUC=0.9828, Support=459, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 16: Quality=-0.2756, ROC-AUC=0.8990, Support=46, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}
  Pattern 17: Quality=-0.2780, ROC-AUC=0.8727, Support=27, Pattern={'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 18: Quality=-0.2842, ROC-AUC=0.8960, Support=35, Pattern={'T'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'A'}{'A'}{'T'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}
  Pattern 19: Quality=-0.2880, ROC-AUC=0.8846, Support=21, Pattern={'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'T'}{'G'}{'G'}{'G'}{'T'}{'A'}{'A'}{'C'}
  Pattern 20: Quality=-0.2901, ROC-AUC=0.9767, Support=386, Pattern={'G'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 21: Quality=-0.2930, ROC-AUC=0.9800, Support=510, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}
  Pattern 22: Quality=-0.2931, ROC-AUC=0.9792, Support=393, Pattern={'G'}{'T'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 23: Quality=-0.2936, ROC-AUC=0.9811, Support=604, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 24: Quality=-0.2945, ROC-AUC=0.9821, Support=668, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 25: Quality=-0.2946, ROC-AUC=0.9818, Support=581, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 26: Quality=-0.2946, ROC-AUC=0.9816, Support=544, Pattern={'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 27: Quality=-0.2948, ROC-AUC=0.9807, Support=366, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'G'}
  Pattern 28: Quality=-0.2950, ROC-AUC=0.9813, Support=431, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 29: Quality=-0.2952, ROC-AUC=0.9828, Support=684, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 30: Quality=-0.2952, ROC-AUC=0.9827, Support=645, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 31: Quality=-0.2953, ROC-AUC=0.9806, Support=311, Pattern={'C'}{'A'}{'G'}{'A'}{'A'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 32: Quality=-0.2953, ROC-AUC=0.9832, Support=788, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 33: Quality=-0.2954, ROC-AUC=0.9827, Support=629, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 34: Quality=-0.2954, ROC-AUC=0.9828, Support=644, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 35: Quality=-0.2955, ROC-AUC=0.9819, Support=444, Pattern={'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}
  Pattern 36: Quality=-0.2955, ROC-AUC=0.9825, Support=552, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}
  Pattern 37: Quality=-0.2955, ROC-AUC=0.9822, Support=491, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}
  Pattern 38: Quality=-0.2957, ROC-AUC=0.9826, Support=540, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'G'}
  Pattern 39: Quality=-0.2957, ROC-AUC=0.9824, Support=495, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}
  Pattern 40: Quality=-0.2957, ROC-AUC=0.9828, Support=556, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 41: Quality=-0.2958, ROC-AUC=0.9818, Support=380, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}
  Pattern 42: Quality=-0.2959, ROC-AUC=0.9817, Support=353, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 43: Quality=-0.2960, ROC-AUC=0.9830, Support=549, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 44: Quality=-0.2963, ROC-AUC=0.9829, Support=471, Pattern={'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'C'}{'G'}
  Pattern 45: Quality=-0.2963, ROC-AUC=0.9830, Support=470, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 46: Quality=-0.2964, ROC-AUC=0.9826, Support=408, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}
  Pattern 47: Quality=-0.2964, ROC-AUC=0.9822, Support=340, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 48: Quality=-0.2964, ROC-AUC=0.9830, Support=453, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}
  Pattern 49: Quality=-0.2965, ROC-AUC=0.9815, Support=261, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}
  Pattern 50: Quality=-0.2966, ROC-AUC=0.9815, Support=246, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'T'}
  Pattern 51: Quality=-0.2966, ROC-AUC=0.9828, Support=389, Pattern={'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'G'}
  Pattern 52: Quality=-0.2967, ROC-AUC=0.9833, Support=454, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 53: Quality=-0.2970, ROC-AUC=0.9832, Support=372, Pattern={'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}{'A'}
  Pattern 54: Quality=-0.2973, ROC-AUC=0.9832, Support=340, Pattern={'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 55: Quality=-0.2973, ROC-AUC=0.9831, Support=314, Pattern={'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'T'}
  Pattern 56: Quality=-0.2981, ROC-AUC=0.9143, Support=42, Pattern={'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'A'}{'A'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 57: Quality=-0.2987, ROC-AUC=0.8889, Support=45, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}
  Pattern 58: Quality=-0.3026, ROC-AUC=0.9644, Support=135, Pattern={'T'}{'A'}{'A'}{'T'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}{'T'}
  Pattern 59: Quality=-0.3034, ROC-AUC=0.8947, Support=23, Pattern={'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'G'}{'A'}{'A'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 60: Quality=-0.3058, ROC-AUC=0.9085, Support=26, Pattern={'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'A'}{'C'}{'T'}{'A'}{'G'}{'A'}
  Pattern 61: Quality=-0.3060, ROC-AUC=0.9107, Support=44, Pattern={'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'A'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 62: Quality=-0.3061, ROC-AUC=0.8967, Support=33, Pattern={'A'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 63: Quality=-0.3064, ROC-AUC=0.8824, Support=25, Pattern={'G'}{'G'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 64: Quality=-0.3065, ROC-AUC=0.9671, Support=128, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'G'}{'A'}{'T'}{'T'}{'C'}{'G'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}
  Pattern 65: Quality=-0.3080, ROC-AUC=0.8750, Support=24, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 66: Quality=-0.3080, ROC-AUC=0.9696, Support=156, Pattern={'T'}{'T'}{'G'}{'C'}{'G'}{'T'}{'A'}{'G'}{'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 67: Quality=-0.3088, ROC-AUC=0.8910, Support=25, Pattern={'T'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'C'}{'G'}{'G'}
  Pattern 68: Quality=-0.3107, ROC-AUC=0.9745, Support=263, Pattern={'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 69: Quality=-0.3110, ROC-AUC=0.9773, Support=462, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}
  Pattern 70: Quality=-0.3112, ROC-AUC=0.9765, Support=377, Pattern={'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 71: Quality=-0.3112, ROC-AUC=0.9769, Support=405, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 72: Quality=-0.3118, ROC-AUC=0.8971, Support=21, Pattern={'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}
  Pattern 73: Quality=-0.3124, ROC-AUC=0.9774, Support=368, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'T'}{'G'}{'A'}
  Pattern 74: Quality=-0.3125, ROC-AUC=0.9242, Support=49, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'G'}
  Pattern 75: Quality=-0.3125, ROC-AUC=0.9783, Support=448, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 76: Quality=-0.3127, ROC-AUC=0.9040, Support=40, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 77: Quality=-0.3129, ROC-AUC=0.9766, Support=272, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 78: Quality=-0.3130, ROC-AUC=0.9751, Support=190, Pattern={'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'A'}{'T'}{'G'}{'A'}{'G'}
  Pattern 79: Quality=-0.3130, ROC-AUC=0.8791, Support=20, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}
  Pattern 80: Quality=-0.3132, ROC-AUC=0.9769, Support=273, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}
  Pattern 81: Quality=-0.3133, ROC-AUC=0.9758, Support=209, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}
  Pattern 82: Quality=-0.3134, ROC-AUC=0.9780, Support=348, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}
  Pattern 83: Quality=-0.3135, ROC-AUC=0.9766, Support=237, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}
  Pattern 84: Quality=-0.3138, ROC-AUC=0.9773, Support=264, Pattern={'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'A'}{'A'}{'C'}{'C'}
  Pattern 85: Quality=-0.3138, ROC-AUC=0.9799, Support=534, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 86: Quality=-0.3139, ROC-AUC=0.9620, Support=207, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 87: Quality=-0.3139, ROC-AUC=0.9762, Support=198, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 88: Quality=-0.3140, ROC-AUC=0.9789, Support=385, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 89: Quality=-0.3140, ROC-AUC=0.9798, Support=493, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 90: Quality=-0.3141, ROC-AUC=0.9777, Support=273, Pattern={'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}
  Pattern 91: Quality=-0.3141, ROC-AUC=0.9796, Support=452, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 92: Quality=-0.3141, ROC-AUC=0.9797, Support=465, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 93: Quality=-0.3141, ROC-AUC=0.9781, Support=301, Pattern={'T'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 94: Quality=-0.3141, ROC-AUC=0.9000, Support=44, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 95: Quality=-0.3142, ROC-AUC=0.9803, Support=548, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 96: Quality=-0.3143, ROC-AUC=0.9790, Support=366, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}
  Pattern 97: Quality=-0.3145, ROC-AUC=0.9791, Support=358, Pattern={'G'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 98: Quality=-0.3146, ROC-AUC=0.9800, Support=455, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 99: Quality=-0.3149, ROC-AUC=0.9782, Support=257, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'G'}
================================================================================

================
FILTERING BY SIMILARITY
================
  Pattern 0: Quality=0.6756, ROC-AUC=0.6500, Support=22, Pattern={'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}
  Pattern 1: Quality=-0.0505, ROC-AUC=0.7843, Support=20, Pattern={'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}
  Pattern 2: Quality=-0.1383, ROC-AUC=0.8111, Support=21, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}
  Pattern 3: Quality=-0.1500, ROC-AUC=0.8333, Support=26, Pattern={'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}
  Pattern 4: Quality=-0.1706, ROC-AUC=0.8229, Support=22, Pattern={'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 5: Quality=-0.1841, ROC-AUC=0.8283, Support=20, Pattern={'C'}{'A'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
  Pattern 6: Quality=-0.2138, ROC-AUC=0.8712, Support=37, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 7: Quality=-0.2405, ROC-AUC=0.8775, Support=41, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}
  Pattern 8: Quality=-0.2668, ROC-AUC=0.8818, Support=27, Pattern={'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}
  Pattern 9: Quality=-0.2699, ROC-AUC=0.8929, Support=29, Pattern={'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}
  Pattern 10: Quality=-0.2705, ROC-AUC=0.9804, Support=597, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 11: Quality=-0.2706, ROC-AUC=0.8571, Support=22, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}
  Pattern 12: Quality=-0.2728, ROC-AUC=0.9823, Support=588, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'C'}{'T'}{'G'}
  Pattern 13: Quality=-0.2730, ROC-AUC=0.8906, Support=44, Pattern={'C'}{'T'}{'C'}{'A'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'A'}{'G'}
  Pattern 14: Quality=-0.2736, ROC-AUC=0.9826, Support=496, Pattern={'T'}{'G'}{'T'}{'C'}{'G'}{'G'}{'C'}{'T'}{'G'}{'C'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}
  Pattern 15: Quality=-0.2740, ROC-AUC=0.9828, Support=459, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 16: Quality=-0.2756, ROC-AUC=0.8990, Support=46, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'T'}{'T'}{'C'}{'G'}
  Pattern 17: Quality=-0.2780, ROC-AUC=0.8727, Support=27, Pattern={'G'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 18: Quality=-0.2842, ROC-AUC=0.8960, Support=35, Pattern={'T'}{'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'G'}{'A'}{'A'}{'T'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}
  Pattern 19: Quality=-0.2880, ROC-AUC=0.8846, Support=21, Pattern={'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}{'T'}{'G'}{'G'}{'G'}{'T'}{'A'}{'A'}{'C'}
  Pattern 20: Quality=-0.2901, ROC-AUC=0.9767, Support=386, Pattern={'G'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'A'}{'C'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'G'}
  Pattern 21: Quality=-0.2930, ROC-AUC=0.9800, Support=510, Pattern={'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}
  Pattern 22: Quality=-0.2931, ROC-AUC=0.9792, Support=393, Pattern={'G'}{'T'}{'A'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 23: Quality=-0.2936, ROC-AUC=0.9811, Support=604, Pattern={'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}
  Pattern 24: Quality=-0.2945, ROC-AUC=0.9821, Support=668, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 25: Quality=-0.2946, ROC-AUC=0.9818, Support=581, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'T'}{'C'}
  Pattern 26: Quality=-0.2946, ROC-AUC=0.9816, Support=544, Pattern={'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'C'}{'T'}{'G'}{'G'}{'G'}
  Pattern 27: Quality=-0.2948, ROC-AUC=0.9807, Support=366, Pattern={'G'}{'T'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'G'}{'A'}{'A'}{'G'}{'C'}{'G'}
  Pattern 28: Quality=-0.2950, ROC-AUC=0.9813, Support=431, Pattern={'G'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'G'}{'G'}
  Pattern 29: Quality=-0.2952, ROC-AUC=0.9828, Support=684, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}
  Pattern 30: Quality=-0.2952, ROC-AUC=0.9827, Support=645, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'G'}{'C'}{'A'}{'C'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 31: Quality=-0.2953, ROC-AUC=0.9806, Support=311, Pattern={'C'}{'A'}{'G'}{'A'}{'A'}{'C'}{'A'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 32: Quality=-0.2953, ROC-AUC=0.9832, Support=788, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'G'}
  Pattern 33: Quality=-0.2954, ROC-AUC=0.9827, Support=629, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}
  Pattern 34: Quality=-0.2954, ROC-AUC=0.9828, Support=644, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 35: Quality=-0.2955, ROC-AUC=0.9819, Support=444, Pattern={'T'}{'T'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'G'}
  Pattern 36: Quality=-0.2955, ROC-AUC=0.9825, Support=552, Pattern={'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'A'}{'G'}{'G'}
  Pattern 37: Quality=-0.2955, ROC-AUC=0.9822, Support=491, Pattern={'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}
  Pattern 38: Quality=-0.2957, ROC-AUC=0.9826, Support=540, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'T'}{'T'}{'T'}{'C'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'A'}{'G'}
  Pattern 39: Quality=-0.2957, ROC-AUC=0.9824, Support=495, Pattern={'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}
  Pattern 40: Quality=-0.2957, ROC-AUC=0.9828, Support=556, Pattern={'C'}{'C'}{'G'}{'A'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}
  Pattern 41: Quality=-0.2958, ROC-AUC=0.9818, Support=380, Pattern={'G'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'C'}{'T'}
  Pattern 42: Quality=-0.2959, ROC-AUC=0.9817, Support=353, Pattern={'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}{'C'}{'C'}{'C'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 43: Quality=-0.2960, ROC-AUC=0.9830, Support=549, Pattern={'C'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}
  Pattern 44: Quality=-0.2963, ROC-AUC=0.9829, Support=471, Pattern={'A'}{'T'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'C'}{'G'}{'A'}{'T'}{'C'}{'G'}
  Pattern 45: Quality=-0.2963, ROC-AUC=0.9830, Support=470, Pattern={'C'}{'A'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 46: Quality=-0.2964, ROC-AUC=0.9826, Support=408, Pattern={'C'}{'G'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}{'G'}
  Pattern 47: Quality=-0.2964, ROC-AUC=0.9822, Support=340, Pattern={'T'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'C'}{'T'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'G'}
  Pattern 48: Quality=-0.2964, ROC-AUC=0.9830, Support=453, Pattern={'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'T'}
  Pattern 49: Quality=-0.2965, ROC-AUC=0.9815, Support=261, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}
  Pattern 50: Quality=-0.2966, ROC-AUC=0.9815, Support=246, Pattern={'C'}{'G'}{'T'}{'T'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'T'}
  Pattern 51: Quality=-0.2966, ROC-AUC=0.9828, Support=389, Pattern={'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'T'}{'T'}{'C'}{'T'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}{'G'}
  Pattern 52: Quality=-0.2967, ROC-AUC=0.9833, Support=454, Pattern={'C'}{'C'}{'C'}{'T'}{'T'}{'G'}{'C'}{'T'}{'A'}{'G'}{'C'}{'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'T'}
  Pattern 53: Quality=-0.2970, ROC-AUC=0.9832, Support=372, Pattern={'T'}{'C'}{'T'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'T'}{'A'}
  Pattern 54: Quality=-0.2973, ROC-AUC=0.9832, Support=340, Pattern={'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'T'}{'G'}{'T'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'C'}{'C'}
  Pattern 55: Quality=-0.2973, ROC-AUC=0.9831, Support=314, Pattern={'G'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'T'}{'G'}{'T'}
  Pattern 56: Quality=-0.2981, ROC-AUC=0.9143, Support=42, Pattern={'C'}{'A'}{'C'}{'A'}{'G'}{'C'}{'A'}{'A'}{'T'}{'T'}{'C'}{'G'}{'G'}{'C'}{'G'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}
  Pattern 57: Quality=-0.2987, ROC-AUC=0.8889, Support=45, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'G'}
  Pattern 58: Quality=-0.3026, ROC-AUC=0.9644, Support=135, Pattern={'T'}{'A'}{'A'}{'T'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'C'}{'G'}{'G'}{'T'}
  Pattern 59: Quality=-0.3034, ROC-AUC=0.8947, Support=23, Pattern={'G'}{'G'}{'T'}{'T'}{'T'}{'G'}{'G'}{'A'}{'A'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'C'}{'G'}{'A'}{'G'}{'G'}{'C'}{'G'}{'C'}
  Pattern 60: Quality=-0.3058, ROC-AUC=0.9085, Support=26, Pattern={'T'}{'G'}{'T'}{'C'}{'A'}{'T'}{'C'}{'C'}{'C'}{'A'}{'C'}{'G'}{'T'}{'C'}{'T'}{'A'}{'A'}{'C'}{'T'}{'A'}{'G'}{'A'}
  Pattern 61: Quality=-0.3060, ROC-AUC=0.9107, Support=44, Pattern={'T'}{'T'}{'G'}{'C'}{'T'}{'T'}{'T'}{'C'}{'T'}{'T'}{'A'}{'A'}{'C'}{'C'}{'C'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'C'}{'A'}
  Pattern 62: Quality=-0.3061, ROC-AUC=0.8967, Support=33, Pattern={'A'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}
  Pattern 63: Quality=-0.3064, ROC-AUC=0.8824, Support=25, Pattern={'G'}{'G'}{'A'}{'C'}{'A'}{'A'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'G'}{'T'}{'G'}{'G'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 64: Quality=-0.3065, ROC-AUC=0.9671, Support=128, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'G'}{'A'}{'T'}{'T'}{'C'}{'G'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'T'}{'C'}
  Pattern 65: Quality=-0.3080, ROC-AUC=0.8750, Support=24, Pattern={'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'A'}
  Pattern 66: Quality=-0.3080, ROC-AUC=0.9696, Support=156, Pattern={'T'}{'T'}{'G'}{'C'}{'G'}{'T'}{'A'}{'G'}{'T'}{'C'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'A'}
  Pattern 67: Quality=-0.3088, ROC-AUC=0.8910, Support=25, Pattern={'T'}{'G'}{'G'}{'T'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'C'}{'A'}{'G'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'C'}{'G'}{'G'}
  Pattern 68: Quality=-0.3107, ROC-AUC=0.9745, Support=263, Pattern={'G'}{'C'}{'T'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'G'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}
  Pattern 69: Quality=-0.3110, ROC-AUC=0.9773, Support=462, Pattern={'C'}{'T'}{'G'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'C'}{'A'}{'G'}{'G'}{'T'}{'C'}{'G'}{'G'}{'G'}{'A'}
  Pattern 70: Quality=-0.3112, ROC-AUC=0.9765, Support=377, Pattern={'C'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'G'}
  Pattern 71: Quality=-0.3112, ROC-AUC=0.9769, Support=405, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}
  Pattern 72: Quality=-0.3118, ROC-AUC=0.8971, Support=21, Pattern={'T'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'A'}{'C'}{'T'}{'C'}{'G'}{'T'}{'C'}{'G'}
  Pattern 73: Quality=-0.3124, ROC-AUC=0.9774, Support=368, Pattern={'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'G'}{'G'}{'A'}{'C'}{'T'}{'G'}{'A'}
  Pattern 74: Quality=-0.3125, ROC-AUC=0.9242, Support=49, Pattern={'C'}{'C'}{'C'}{'G'}{'G'}{'C'}{'T'}{'C'}{'A'}{'G'}{'A'}{'T'}{'T'}{'C'}{'A'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'G'}
  Pattern 75: Quality=-0.3125, ROC-AUC=0.9783, Support=448, Pattern={'G'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'G'}{'C'}{'G'}{'G'}{'G'}{'G'}
  Pattern 76: Quality=-0.3127, ROC-AUC=0.9040, Support=40, Pattern={'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}
  Pattern 77: Quality=-0.3129, ROC-AUC=0.9766, Support=272, Pattern={'C'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}{'T'}{'C'}{'C'}
  Pattern 78: Quality=-0.3130, ROC-AUC=0.9751, Support=190, Pattern={'C'}{'C'}{'A'}{'T'}{'T'}{'G'}{'A'}{'A'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'A'}{'T'}{'G'}{'A'}{'G'}
  Pattern 79: Quality=-0.3130, ROC-AUC=0.8791, Support=20, Pattern={'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'A'}{'T'}{'C'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'G'}{'T'}{'G'}{'C'}
  Pattern 80: Quality=-0.3132, ROC-AUC=0.9769, Support=273, Pattern={'C'}{'T'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'T'}{'G'}{'C'}{'C'}
  Pattern 81: Quality=-0.3133, ROC-AUC=0.9758, Support=209, Pattern={'A'}{'G'}{'T'}{'A'}{'G'}{'A'}{'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'G'}{'C'}{'A'}{'G'}{'C'}{'T'}{'A'}
  Pattern 82: Quality=-0.3134, ROC-AUC=0.9780, Support=348, Pattern={'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'C'}{'G'}{'G'}{'T'}{'C'}{'C'}
  Pattern 83: Quality=-0.3135, ROC-AUC=0.9766, Support=237, Pattern={'C'}{'C'}{'C'}{'T'}{'G'}{'T'}{'C'}{'T'}{'A'}{'T'}{'C'}{'C'}{'G'}{'C'}{'G'}{'C'}{'T'}{'A'}{'G'}
  Pattern 84: Quality=-0.3138, ROC-AUC=0.9773, Support=264, Pattern={'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'A'}{'G'}{'T'}{'A'}{'A'}{'C'}{'C'}
  Pattern 85: Quality=-0.3139, ROC-AUC=0.9620, Support=207, Pattern={'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'A'}{'C'}{'C'}{'C'}
  Pattern 86: Quality=-0.3139, ROC-AUC=0.9762, Support=198, Pattern={'C'}{'C'}{'G'}{'T'}{'T'}{'G'}{'G'}{'C'}{'A'}{'A'}{'C'}{'A'}{'C'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}
  Pattern 87: Quality=-0.3140, ROC-AUC=0.9789, Support=385, Pattern={'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'G'}{'C'}{'G'}{'C'}
  Pattern 88: Quality=-0.3140, ROC-AUC=0.9798, Support=493, Pattern={'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'C'}{'G'}{'G'}{'C'}{'C'}
  Pattern 89: Quality=-0.3141, ROC-AUC=0.9777, Support=273, Pattern={'C'}{'G'}{'G'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'C'}
  Pattern 90: Quality=-0.3141, ROC-AUC=0.9797, Support=465, Pattern={'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'A'}{'C'}{'G'}{'C'}{'C'}{'C'}{'C'}
  Pattern 91: Quality=-0.3141, ROC-AUC=0.9781, Support=301, Pattern={'T'}{'G'}{'G'}{'G'}{'T'}{'T'}{'C'}{'T'}{'T'}{'G'}{'T'}{'G'}{'C'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}
  Pattern 92: Quality=-0.3141, ROC-AUC=0.9000, Support=44, Pattern={'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'G'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}
  Pattern 93: Quality=-0.3142, ROC-AUC=0.9803, Support=548, Pattern={'C'}{'G'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'G'}{'G'}{'C'}{'G'}{'G'}
  Pattern 94: Quality=-0.3143, ROC-AUC=0.9790, Support=366, Pattern={'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'G'}{'C'}{'C'}{'C'}{'A'}{'G'}{'C'}{'C'}{'T'}{'G'}{'A'}{'C'}{'G'}
  Pattern 95: Quality=-0.3145, ROC-AUC=0.9791, Support=358, Pattern={'G'}{'T'}{'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'T'}{'C'}{'G'}{'C'}{'C'}{'G'}{'G'}{'G'}{'C'}{'A'}{'G'}
  Pattern 96: Quality=-0.3146, ROC-AUC=0.9800, Support=455, Pattern={'C'}{'C'}{'C'}{'A'}{'C'}{'T'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}{'T'}
  Pattern 97: Quality=-0.3149, ROC-AUC=0.9782, Support=257, Pattern={'C'}{'A'}{'C'}{'T'}{'C'}{'T'}{'G'}{'G'}{'T'}{'A'}{'G'}{'C'}{'T'}{'G'}{'C'}{'C'}{'A'}{'T'}{'G'}
================================================================================

Quality: 0.6756346242775673, Extent: 22, ROCAUC: 0.65, Pattern: {'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'A'}{'G'}{'G'}{'T'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'A'}{'G'}{'A'}{'G'}
Quality: -0.05048013450354505, Extent: 20, ROCAUC: 0.7843137254901962, Pattern: {'T'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'T'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'A'}{'G'}{'C'}{'G'}{'A'}{'G'}{'C'}{'G'}{'C'}{'C'}
Quality: -0.13825588975973835, Extent: 21, ROCAUC: 0.8111111111111111, Pattern: {'G'}{'C'}{'C'}{'T'}{'C'}{'A'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'G'}{'G'}{'A'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'A'}
Quality: -0.1500065137931179, Extent: 26, ROCAUC: 0.8333333333333333, Pattern: {'G'}{'C'}{'C'}{'T'}{'T'}{'G'}{'G'}{'T'}{'C'}{'C'}{'C'}{'G'}{'T'}{'C'}{'C'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'G'}{'G'}
Quality: -0.17064075989266092, Extent: 22, ROCAUC: 0.8229166666666667, Pattern: {'C'}{'T'}{'C'}{'T'}{'C'}{'C'}{'A'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'G'}{'G'}{'G'}{'C'}{'C'}{'A'}{'G'}{'C'}
Quality: -0.18406351143923994, Extent: 20, ROCAUC: 0.8282828282828283, Pattern: {'C'}{'A'}{'A'}{'T'}{'C'}{'T'}{'T'}{'C'}{'C'}{'T'}{'T'}{'C'}{'C'}{'C'}{'T'}{'G'}{'G'}{'A'}{'A'}{'C'}{'C'}{'C'}{'C'}{'G'}{'G'}
Quality: -0.21384723083044244, Extent: 37, ROCAUC: 0.8712121212121211, Pattern: {'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'A'}{'G'}{'G'}{'G'}{'C'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'C'}{'C'}{'C'}{'C'}
Quality: -0.24048962308476685, Extent: 41, ROCAUC: 0.8774509803921569, Pattern: {'C'}{'T'}{'C'}{'C'}{'C'}{'T'}{'C'}{'C'}{'C'}{'G'}{'C'}{'C'}{'C'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'T'}{'C'}{'G'}{'C'}{'C'}
Quality: -0.26682311905135525, Extent: 27, ROCAUC: 0.8818181818181818, Pattern: {'C'}{'C'}{'G'}{'C'}{'A'}{'T'}{'G'}{'G'}{'G'}{'A'}{'G'}{'C'}{'C'}{'T'}{'A'}{'A'}{'G'}{'G'}{'C'}{'T'}{'T'}{'C'}{'C'}
Quality: -0.26991066163597677, Extent: 29, ROCAUC: 0.8928571428571429, Pattern: {'G'}{'C'}{'T'}{'G'}{'T'}{'G'}{'A'}{'G'}{'A'}{'G'}{'T'}{'C'}{'T'}{'G'}{'T'}{'A'}{'T'}{'C'}{'A'}{'C'}{'G'}{'G'}
Average score :-0.10088828197132763
```

</details>

## Próximos passos

Em paralelo (1 e 2)

1. Rodar resto dos exp sintéticos (1 semana)
2. Encontrar mais datasets sequenciais (1 semana)
  - Os atuais tem sequências longas, mas tem poucas instâncias (a não ser o emm_sequences-TZ-45.dat) 
3. Rodar com datasets reais (1 semana (outra))