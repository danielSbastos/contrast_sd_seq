# Reunião 25/11

## Definição de dois objetivos do algoritmo

1. Deve ser capaz de encontrar padrões discriminantes independente do tamanho do dataset, tanto em questão de número de instâncias quanto em largura (tamanho de sequência) 

2. Deve ser capaz de encontrar padrões discriminantes independente do ruído do dataset
    - Dataset com ruído alto, muitos padrões discriminantes presentes.
    - Dataset com ruído baixo, poucos padrões presentes

3. Deve ser capaz de realizar composição de padrões
    - Padrões sozinhos não são interessantes, entretanto a sua composição, sim

Para responder ambas os objetivos, pensei nos seguintes experimentos.

### Primeiro objetivo

- 1 padrão com tamanho 3 e suporte 50, e AUC ~0.65

```json
[
  {
    "element": "{A} {B} {C}",
    "quantity": 50,
    "target_auc": 0.65
  }
]
```

- Usar ruído de 0.25
- Dataset de tamanho 5k, 15k
- Tamanho de sequências entre 7 e 10, 10 e 15, 25 e 30
- Fixar em 15k iterações
- Total 9 arquivos:
    - `d_5k__l_7_10__n_0.25`
    - `d_5k__l_10_15__n_0.25`
    - `d_5k__l_25_30__n_0.25`
    - `d_15k__l_7_10__n_0.25`
    - `d_15k__l_10_15__n_0.25`
    - `d_15k__l_25_30__n_0.25`

### Segundo objetivo

- 1 padrão com tamanho 3, suporte 50, e AUC ~0.65

```json
[
  {
    "element": "{A} {B} {C}",
    "quantity": 50,
    "target_auc": 0.65
  }
]
```


- Usar ruído de 0, 0.5 e 1
- Dataset de tamanho 5k
- Tamanho de sequências entre 10 e 15
- Fixar em 15k iterações
- Total 3 arquivos:
    - `d_5k__l_10_15__n_0`
    - `d_5k__l_10_15__n_0.5`
    - `d_5k__l_10_15__n_1`


### Terceiro objetivo

- 3 padrões, e com subpadrões com AUC alto

```json
[
  {
    "element": "{A} {B} {C}",
    "quantity": 50,
    "target_auc": 0.60
  },
  {
    "element": "{A} {B}",
    "quantity": 10,
    "target_auc": 0.99
  },
  {
    "element": "{A} {C}",
    "quantity": 10,
    "target_auc": 0.99
  },
  {
    "element": "{B} {C}",
    "quantity": 10,
    "target_auc": 0.99
  },
  {
    "element": "{A}",
    "quantity": 5,
    "target_auc": 0.99
  },
  {
    "element": "{B}",
    "quantity": 5,
    "target_auc": 0.99
  },
  {
    "element": "{C}",
    "quantity": 5,
    "target_auc": 0.99
  }
]
```

- Usar ruído de 0.25
- Dataset de tamanho 5k
- Tamanho de sequências de 10 e 15
- Fixar em 15k iterações
- Total 1 arquivo:
    - `d_5k__l_10_15__n_0.25__contrasting`
