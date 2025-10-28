# Reunião 28/10

## Problema

O algoritmo é muito lento para datasets maiores (> 10k e/ou com sequências de tamanho de 15 - 30). 

## Mudanças

### Cache

Cache em
1. `compute_quality`
2. `compute_cumulative_probs`
3. `compute_sequence_expand`


As proporções de hits e misses do cache nas 14k iterações foram as seguintes:

```
compute_quality:  CacheInfo(hits=20257, misses=20237, maxsize=None, currsize=20237)
compute_sequence_expand:  CacheInfo(hits=6404, misses=21149, maxsize=None, currsize=21149)
compute_cumulative_probs:  CacheInfo(hits=20903, misses=112981, maxsize=128, currsize=128)
```

### Resultados

#### Datasets com ~ 1-2k com sequências da tamanho 8 - 15
Para os datasets **menores**. Com as estretégias de cache, foi possível reduzir de **90 segundos a 10 segundos** (!!!)

Number iteration mcts: 2468 (1700)
Number iteration mcts: 4456 (1100)
Number iteration mcts: 5051 (1000)
Number iteration mcts: 2492 (1700)
Number iteration mcts: 3049 (1530)

#### Datases com 1.7k com sequências da tamanho 15 - 30
Entretanto, para os datasets **médios**. A média de tempo foi para **60 segundos**, e ainda algumas execuções não encontram todos os padrões:

```
Number iteration mcts: 4395
Quality: 0.5438273036962049, Extent: 100, ROCAUC: 0.65, Pattern: {'C', 'D'}
Quality: 0.5243441530286608, Extent: 20, ROCAUC: 0.83, Pattern: {'B'}
Quality: 0.40093864966381365, Extent: 25, ROCAUC: 0.7628205128205128, Pattern: {'W'}{'A'}

Number iteration mcts: 4916
Quality: 0.5356078737845669, Extent: 100, ROCAUC: 0.7552, Pattern: {'C', 'D'}
Quality: 0.5262482534848336, Extent: 20, ROCAUC: 0.7, Pattern: {'B'}
Quality: 0.40417693307398705, Extent: 25, ROCAUC: 0.6038961038961039, Pattern: {'Y'}{'A'}

Number iteration mcts: 4834
Quality: 0.5306454627976425, Extent: 30, ROCAUC: 0.6, Pattern: {'A'}
Quality: 0.5261849797362237, Extent: 15, ROCAUC: 0.6428571428571428, Pattern: {'D', 'C'}
Quality: 0.39893917986127536, Extent: 292, ROCAUC: 0.9491437954492141, Pattern: {'W'}{'X'}

Number iteration mcts: 4364
Quality: 0.5442142170865749, Extent: 100, ROCAUC: 0.6452, Pattern: {'D'}
Quality: 0.5234088302763769, Extent: 700, ROCAUC: 0.945461224489796, Pattern: {'X'}
Quality: 0.4055294940131109, Extent: 22, ROCAUC: 0.5042735042735043, Pattern: {'Y'}{'A'}

Number iteration mcts: 4636
Quality: 0.5304119333088189, Extent: 30, ROCAUC: 0.6, Pattern: {'A'}
Quality: 0.5262126648659229, Extent: 20, ROCAUC: 0.7000000000000001, Pattern: {'B'}
Quality: 0.4000656067152921, Extent: 11, ROCAUC: 0.6666666666666666, Pattern: {'W'}{'C', 'D'}
```

#### Datases com 10k com sequências da tamanho 8 - 15

60 segundos não foi suficiente, e teve uma média de 405 iterações. Com 120 segundos, os padrões A e D são frequentemente encontrados, mas não o B. A média de iterações foi de 1100.

#### Datasets com 10k com sequências da tamanho 15 - 30

Em torno de 14k iterações em 3000 segundos (50 minutos) foram necessárias para obter os padrões:

```
Number iteration mcts: 14284
odel ROC AUC: 0.94726376
Quality: 0.5264070010521578, Extent: 100, ROCAUC: 0.6504000000000001, Pattern: {'D'}
Quality: 0.5245289050486368, Extent: 30, ROCAUC: 0.5244444444444444, Pattern: {'A'}
Quality: 0.5234469874516421, Extent: 20, ROCAUC: 0.7, Pattern: {'B'}
Quality: 0.04582896551634941, Extent: 23, ROCAUC: 0.9166666666666667, Pattern: {'Y'}{'U'}{'U'}{'U'}{'X'}{'T'}{'Y'}
Quality: 7.138856674893113e-05, Extent: 286, ROCAUC: 0.944770857814336, Pattern: {'Z'}{'Z'}{'W'}{'Z'}{'Z'}{'T'}{'W'}{'U'}
```

## Propostas

A velocidade ainda é um problema, podemos atacar as seguintes frente:

1. Progressive bias
> The aim of the progressive bias strategy is to direct the search according to – possibly time-expensive – heuristic knowledge. For that purpose, the selection strategy
is modified according to that knowledge. The influence of this modification is important when a few games have been played, but decreases fast (when more games
have been played) to ensure that the strategy converges to a selection strategy.

2. Progressive pruning/widening 
> when not much time is available and simultaneously the branching factor is high, MCTS performs poorly. Our solution, progressive unpruning, consists of (1) reducing the branching factor artificially when the selection function is applied, and (2) increasing it progressively as more time becomes available. When the number of games `n_p` in a node `p` equals the threshold `T`, progressive unpruning “prunes” most of the children. The children, which are not pruned from the beginning, are the `k_init` children with the highest heuristic values.

Artigo do 1. e 2.: Progressive Strategies for Monte-Carlo Tree Search

 3. Paralelizar