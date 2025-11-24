# Reunião 25/11

## Definição de dois objetivos do algoritmo

1. Deve ser capaz de encontrar padrões discriminantes independente do tamanho do dataset, tanto em questão de número de instâncias quanto em largura (tamanho de sequência) 

2. Deve ser capaz de encontrar padrões discriminantes independente do ruído do dataset
    - Dataset com ruído alto, muitos padrões discriminantes presentes.
    - Dataset com ruído baixo, poucos padrões presentes

Para responder ambas os objetivos, pensei nos seguintes experimentos.

### Primeiro objetivo

- 1 padrão com tamanho 3 e suporte 50, e AUC ~0.65
- Usar ruído de 0.25
- Dataset de tamanho 1k, 5k, 15k
- Tamanho de sequências entre 7 e 9, 10 e 15, 25 e 30
- Fixar em 15k iterações
- Total 4 arquivos:
    - `d_1k__l_7_9__n_0.25`
    - `d_1k__l_10_15__n_0.25`
    - `d_1k__l_25_30__n_0.25`

    - `d_5k__l_7_9__n_0.25`
    - `d_5k__l_10_15__n_0.25`
    - `d_5k__l_25_30__n_0.25`

    - `d_15k__l_7_9__n_0.25`
    - `d_15k__l_10_15__n_0.25`
    - `d_15k__l_25_30__n_0.25`

### Segundo objetivo

- 2 padrões com tamanho 3 (baseline) e 5 (desafio) e suporte 50, e AUC ~0.65
- Usar ruído de 0, 0.5 e 1
- Dataset de tamanho 5k
- Tamanho de sequências entre 10 e 15
- Fixar em 15k iterações
- Total 3 arquivos:
    - `d_5k__l_10_15__n_0`
    - `d_5k__l_10_15__n_0.5`
    - `d_5k__l_10_15__n_1`