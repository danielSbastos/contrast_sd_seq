# Reunião 10/11

## Nova medida de qualidade

`(1/(1-auc_diff))^sup_rel` -> `100 * auc_diff^2 * sup_rel^0.5`

- Mais simples e com um comportamento similar.
- Mudanças pequenas no AUC diff afetam fortemente a Qm
- O AUC ao quadrado enfatiza diffs altos e "suprimi" as pequenas (0.1 -> 0.01, 0.5 -> 0.25)
- Tradeoff:
  1. Subgrupos pequenos necessitam de um auc diff alto para competir
  2. Subgrupos grandes com auc diffs moderados podem ser ainda bem ranqueados
- Valores dos expoentes:
  1. Aumentar (supporte): favorizar subgrupos maiores
  2. Diminuir (AUC diff): sentividade reduzida para diffs pequenos

![alt text](imgs/qm.png "Medidade de qualidade")

![alt text](imgs/3d_qm.png "Variações (3d) da medida de qualidade")

## Possíveis testes synth

- Numero de iterações: 1k, 2k, 5k, 10k, 20k, 50k
- Dataset tamanhos 1k, 2k, 5k, 10k, 25k, 50k
- Sequências de tamanho 10-20, 20-35, 35-50
- Padrões injetáveis (suporte)
    - Suporte absoluto de 20
    - Suporte relativo de 0.1%
    - Suporte relativo de 1%
    - Suporte relativo de 5%
    - Suporte relativo de 10%
    - Suporte relativo de 20%
- Padrões injetáveis (AUC)
    - 0.5, 0.6, 0.7, 0.8, 0.9, (target 0.95), 1
    - 0.5, 0.6, 0.7, (target 0.75), 0.8, 0.9, 1
- Padrões injetáveis (tamanho)
    - 1, 2, 3, 5, 8
- Ruido
    - 0%, 25%, 50%, 75%, 100%
- Variação dos expoentes (?)

## Alguns experimentos

### Dataset 5k instâncias

```
Number iteration mcts: 2000 (não acha sempre com 2000)
Model ROC AUC: 0.9505164799999999
Quality: 0.7638556790209183, Extent: 20, ROCAUC: 0.68, Pattern: {'P'}{'Q', 'S'}{'P', 'R'}
Quality: 0.5553204980953805, Extent: 20, ROCAUC: 0.75, Pattern: {'N', 'M'}{'N', 'M'}{'N'}
Quality: 0.541224142364359, Extent: 20, ROCAUC: 0.8, Pattern: {'C'}{'E'}
Quality: 0.5236640269897461, Extent: 4008, ROCAUC: 0.9475549010545943, Pattern: {'T'}
Quality: 0.39962254397986596, Extent: 2365, ROCAUC: 0.9455703354072803, Pattern: {'W'}{'Y'}
Quality: 0.39841978227807984, Extent: 2355, ROCAUC: 0.9478724708767627, Pattern: {'U'}{'Y'}
Quality: 0.39836775292158966, Extent: 2399, ROCAUC: 0.9480314763614527, Pattern: {'Y'}{'Y'}
Quality: 0.39820422178590564, Extent: 2360, ROCAUC: 0.9485554163711094, Pattern: {'W'}{'W'}
Quality: 0.39813834911682167, Extent: 2429, ROCAUC: 0.9488295725206577, Pattern: {'W'}{'X'}
Quality: 0.39796820315832704, Extent: 2373, ROCAUC: 0.9498767449294925, Pattern: {'W'}{'U'}
Average score :0.4774785199710994

Number iteration mcts: 3000
Model ROC AUC: 0.9505164799999999
Quality: 0.9857044286372746, Extent: 20, ROCAUC: 0.68, Pattern: {'P', 'R'}
Quality: 0.7771692477117369, Extent: 20, ROCAUC: 0.75, Pattern: {'N'}
Quality: 0.6661628789726588, Extent: 20, ROCAUC: 0.8, Pattern: {'E'}
Quality: 0.5236640269897461, Extent: 4008, ROCAUC: 0.9475549010545943, Pattern: {'T'}
Quality: 0.39962254397986596, Extent: 2365, ROCAUC: 0.9455703354072803, Pattern: {'W'}{'Y'}
Quality: 0.39841978227807984, Extent: 2355, ROCAUC: 0.9478724708767627, Pattern: {'U'}{'Y'}
Quality: 0.39836775292158966, Extent: 2399, ROCAUC: 0.9480314763614527, Pattern: {'Y'}{'Y'}
Quality: 0.39820422178590564, Extent: 2360, ROCAUC: 0.9485554163711094, Pattern: {'W'}{'W'}
Quality: 0.39813834911682167, Extent: 2429, ROCAUC: 0.9488295725206577, Pattern: {'W'}{'X'}
Quality: 0.39796820315832704, Extent: 2373, ROCAUC: 0.9498767449294925, Pattern: {'W'}{'U'}
Average score :0.5343421435552007
```

### Dataset 10k instâncias

```
Number iteration mcts: 3000
compute_quality:  CacheInfo(hits=4403, misses=3608, maxsize=512, currsize=512)
compute_cumulative_probs:  CacheInfo(hits=2609, misses=12583, maxsize=512, currsize=512)
compute_sequence_expand:  CacheInfo(hits=1532, misses=3609, maxsize=512, currsize=512)
Model ROC AUC: 0.9505164799999999
Quality: 0.8607656920289748, Extent: 20, ROCAUC: 0.68, Pattern: {'S', 'Q'}{'R', 'P'}
Quality: 0.6661628789726588, Extent: 20, ROCAUC: 0.8, Pattern: {'E'}
Quality: 0.5553204980953805, Extent: 20, ROCAUC: 0.75, Pattern: {'N'}{'N', 'M'}{'N'}
Quality: 0.5236640269897461, Extent: 4008, ROCAUC: 0.9475549010545943, Pattern: {'T'}
Quality: 0.5036316218843924, Extent: 21, ROCAUC: 0.7000000000000001, Pattern: {'T'}{'W'}{'X'}{'X'}{'X'}{'Y'}
Quality: 0.39962254397986596, Extent: 2365, ROCAUC: 0.9455703354072803, Pattern: {'W'}{'Y'}
Quality: 0.39841978227807984, Extent: 2355, ROCAUC: 0.9478724708767627, Pattern: {'U'}{'Y'}
Quality: 0.39836775292158966, Extent: 2399, ROCAUC: 0.9480314763614527, Pattern: {'Y'}{'Y'}
Quality: 0.39820422178590564, Extent: 2360, ROCAUC: 0.9485554163711094, Pattern: {'W'}{'W'}
Quality: 0.39813834911682167, Extent: 2429, ROCAUC: 0.9488295725206577, Pattern: {'W'}{'X'}

Number iteration mcts: 5000
compute_quality:  CacheInfo(hits=7161, misses=6317, maxsize=512, currsize=512)
compute_cumulative_probs:  CacheInfo(hits=4552, misses=21624, maxsize=512, currsize=512)
compute_sequence_expand:  CacheInfo(hits=2276, misses=6318, maxsize=512, currsize=512)
Model ROC AUC: 0.95109044
Quality: 0.7265973992293893, Extent: 20, ROCAUC: 0.68, Pattern: {'Q'}{'R', 'P'}
Quality: 0.7037201394878954, Extent: 20, ROCAUC: 0.75, Pattern: {'N'}
Quality: 0.6249701006823256, Extent: 20, ROCAUC: 0.8, Pattern: {'E'}
Quality: 0.5233394252650097, Extent: 8039, ROCAUC: 0.9488237132768229, Pattern: {'U'}
Quality: 0.39872719992919925, Extent: 4734, ROCAUC: 0.9477079768990417, Pattern: {'Y'}{'X'}
Quality: 0.3985592740278038, Extent: 4719, ROCAUC: 0.9480879892111477, Pattern: {'X'}{'V'}
Quality: 0.3985459838838895, Extent: 4798, ROCAUC: 0.9481326838320575, Pattern: {'W'}{'X'}
Quality: 0.3984175897612616, Extent: 4774, ROCAUC: 0.9484613651106562, Pattern: {'W'}{'V'}
Quality: 0.3983466405036451, Extent: 4774, ROCAUC: 0.9486644998475715, Pattern: {'Y'}{'V'}
Quality: 0.39829870660357714, Extent: 4838, ROCAUC: 0.9488195402100444, Pattern: {'W'}{'Y'}
```

### Dataset 20k instâncias

```
Number iteration mcts: 10000
compute_quality:  CacheInfo(hits=13549, misses=13513, maxsize=512, currsize=512)
compute_cumulative_probs:  CacheInfo(hits=11810, misses=45123, maxsize=512, currsize=512)
compute_sequence_expand:  CacheInfo(hits=3700, misses=13514, maxsize=512, currsize=512)
Model ROC AUC: 0.95299778
Quality: 0.7585563039706141, Extent: 20, ROCAUC: 0.68, Pattern: {'R', 'P'}
Quality: 0.6531901951697006, Extent: 20, ROCAUC: 0.75, Pattern: {'N'}
Quality: 0.47196361823604416, Extent: 20, ROCAUC: 0.8, Pattern: {'C'}{'E'}
Quality: 0.23082162087178004, Extent: 1269, ROCAUC: 0.9341240467969893, Pattern: {'W'}{'T'}{'T'}{'T'}
Quality: 0.22883688555781412, Extent: 1340, ROCAUC: 0.9365668565724713, Pattern: {'X'}{'U'}{'X'}{'Y'}
Quality: 0.22823386262757606, Extent: 1231, ROCAUC: 0.9369550867372535, Pattern: {'Z'}{'X'}{'T'}{'T'}
Quality: 0.2281927654669712, Extent: 1264, ROCAUC: 0.9371122078968575, Pattern: {'W'}{'V'}{'T'}{'T'}
Quality: 0.2279639643600173, Extent: 1291, ROCAUC: 0.9374834939521841, Pattern: {'U'}{'T'}{'T'}{'X'}
Quality: 0.2278235299289344, Extent: 1297, ROCAUC: 0.9376804356614588, Pattern: {'Y'}{'X'}{'U'}{'Z'}
Quality: 0.22769251100998056, Extent: 1352, ROCAUC: 0.9380057803468208, Pattern: {'V'}{'T'}{'X'}{'T'}


--------------- (aqui rodei sem a condicional de auc_diff > 0.01) - não era sempre que os padrões eram encontrados
Number iteration mcts: 10000
compute_quality:  CacheInfo(hits=14150, misses=11845, maxsize=512, currsize=512)
compute_cumulative_probs:  CacheInfo(hits=11030, misses=42612, maxsize=512, currsize=512)
compute_sequence_expand:  CacheInfo(hits=4395, misses=11846, maxsize=512, currsize=512)
Model ROC AUC: 0.95299778
Quality: 0.7585563039706141, Extent: 20, ROCAUC: 0.68, Pattern: {'R', 'P'}
Quality: 0.5230025190235396, Extent: 16148, ROCAUC: 0.9518241206138071, Pattern: {'Y'}
Quality: 0.47196361823604416, Extent: 20, ROCAUC: 0.8, Pattern: {'C'}{'E'}
Quality: 0.3986458460257788, Extent: 9484, ROCAUC: 0.9497962178894187, Pattern: {'W'}{'T'}
Quality: 0.39837002079245176, Extent: 9451, ROCAUC: 0.9554988647406817, Pattern: {'Z'}{'W'}
Quality: 0.3983326161086834, Extent: 9417, ROCAUC: 0.955389765910029, Pattern: {'V'}{'V'}
Quality: 0.39832763462424503, Extent: 9406, ROCAUC: 0.9553752370414442, Pattern: {'Z'}{'U'}
Quality: 0.39827438480711086, Extent: 9422, ROCAUC: 0.9552049681750282, Pattern: {'U'}{'V'}
Quality: 0.3982675468963106, Extent: 9429, ROCAUC: 0.9508136821814909, Pattern: {'T'}{'T'}
Quality: 0.39825474700094354, Extent: 9432, ROCAUC: 0.9508569540116186, Pattern: {'X'}{'X'}
```

### Dataset 50k instâncias

- demora umas 2-3 horas

```
Number iteration mcts: 10000
compute_quality:  CacheInfo(hits=13452, misses=13748, maxsize=512, currsize=512)
compute_cumulative_probs:  CacheInfo(hits=12223, misses=45515, maxsize=512, currsize=512)
compute_sequence_expand:  CacheInfo(hits=3583, misses=13749, maxsize=512, currsize=512)
Model ROC AUC: 0.9522279312
Quality: 0.5692254313552014, Extent: 20, ROCAUC: 0.8, Pattern: {'E'}
Quality: 0.5461561017229015, Extent: 20, ROCAUC: 0.68, Pattern: {'Q'}{'R', 'P'}
Quality: 0.3828222679788451, Extent: 20, ROCAUC: 0.75, Pattern: {'N', 'M'}{'N', 'M'}{'N'}
Quality: 0.22563989791411987, Extent: 3198, ROCAUC: 0.9399843554443054, Pattern: {'T'}{'U'}{'Z'}{'Y'}
Quality: 0.22442259122763408, Extent: 3257, ROCAUC: 0.9421857287987565, Pattern: {'X'}{'Z'}{'V'}{'Z'}
Quality: 0.16209532497207624, Extent: 852, ROCAUC: 0.9287533068783068, Pattern: {'W'}{'T'}{'W'}{'Z'}{'Y'}
Quality: 0.16174285264580668, Extent: 850, ROCAUC: 0.9293222001207885, Pattern: {'W'}{'T'}{'T'}{'T'}{'Z'}
Quality: 0.16027415091932273, Extent: 844, ROCAUC: 0.9318934728198207, Pattern: {'V'}{'U'}{'U'}{'Z'}{'Y'}
Quality: 0.15993853136162028, Extent: 773, ROCAUC: 0.932101576416699, Pattern: {'T'}{'U'}{'Z'}{'V'}{'Y'}
Quality: 0.15985750284320777, Extent: 803, ROCAUC: 0.9324532617342879, Pattern: {'V'}{'X'}{'Z'}{'V'}{'Z'}
```

## Perguntas

1. Como que a qualidade dos padrões injetados muda a medida que a quantidade de iterações muda
2. Quantidade de vezes que um padrão é encontrado com base no tamanho do dataset e no número de iterações
    1. Para um dataset de tamanho x e um padrão de suporte y, qual é o número minimo de iterações necessárias
3. Qual a qualidade média dos top-10 subgrupos encontrados a medida que aumentamos o número de iterações?