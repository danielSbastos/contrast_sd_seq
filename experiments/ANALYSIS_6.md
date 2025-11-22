# Reunião 25/11

## Definição de dois objetivos do algoritmo

1. Deve ser capaz de encontrar padrões discriminantes independente do tamanho do dataset, tanto em questão de número de instâncias quanto em largura (tamanho de sequência) 

2. Deve ser capaz de encontrar padrões discriminantes independente do ruído do dataset
    - Dataset com ruído alto, muitos padrões discriminantes presentes.
    - Dataset com ruído baixo, poucos padrões presentes

Para responder ambas os objetivos, pensei nos seguintes experimentos.

### Primeiro objetivo

- 2 padrões com tamanho 2 e 4 e suporte 50, e AUC ~0.6
- Usar ruído de 0 (conseguimos testar realmente o efeito de dimensões)
- Dataset de tamanho 5k, 10k e 20k
- Tamanho de sequências entre 10 e 15, 15 e 30, 30 e 50
- Fixar em 50k iterações
- Total 4 arquivos:
    - `d_5k__l_10_15__n_0`
    - `d_5k__l_15_30__n_0`
    - `d_5k__l_30_50__n_0`
    - `d_10k__l_10_15__n_0`
    - `d_10k__l_15_30__n_0`
    - `d_10k__l_30_50__n_0`
    - `d_20k__l_10_15__n_0`
    - `d_20k__l_15_30__n_0`
    - `d_20k__l_30_50__n_0`

### Segundo objetivo

- 2 padrões com tamanho 2 e 4 e suporte 50
- Usar ruído de 0, 0.5 e 1
- Dataset de tamanho 20k
- Tamanho de sequências 25 e 40
- Fixar em 50k iterações
- Total 2 arquivos:
    - `d_10k__l_15_30__n_0`
    - `d_10k__l_15_30__n_0.5`
    - `d_10k__l_15_30__n_1`
