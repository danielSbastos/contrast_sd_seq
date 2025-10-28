# Reunião 21/10

## Mudanças

### Rollout probabilístico

- **Antes:** deleção de itens da sequência de forma aleatória
- **Agora:** deleção de itens da sequência com probabilidade baseada no log_loss médio de cada item. Antes da execução, o dataset é percorrido uma vez, e para cada item do alfabeto, o log_loss médio das sequências que ele faz parte é calculado. Esse log_loss é dado de entrada para a função `1/1+x` para transformar em probabilidade (enfase maior em log loss pequenos vs. médios e altos). Um CFD é utilizado, que nem no expand.

### Similaridade de Jaccard no expand

- **Antes:** expand probabilístico com base somente no log_loss das sequências
- **Agora:** continua sendo probabilistico, mas o log loss é ponderado pela similaridade de Jaccard das duas sequências

## Experimentos (Ablation)

### Overall Performance Impact (Fixed Time Budget - 90 seconds)

| Configuration | Avg Iterations (Synth 1-5) | Speed vs Baseline | Top Pattern Quality |
|--------------|---------------------------|-------------------|---------------------|
| Baseline (No features) | 8,413 | 100% (fastest) | 0.544 (good) |
| Jaccard only | 7,765 | -8% slower | 0.544 (same) |
| Weighted Rollout only | 5,570 | -34% slower | 0.544 (same) |
| Both features | 4,997 | -41% slower | 0.544 (same) |

**Key Insight**: Both features add 41% computational overhead, but **all configurations find the same top patterns with same quality**. The question is: do slower iterations actually help or just waste time?

---

### Detailed Analysis by Dataset Size

#### 1. Small but Long Dataset (1,700 sequences, seq length 15-30, 240s budget)

| Configuration | Iterations | Top-3 Patterns Found | Top Quality |
|--------------|-----------|---------------------|-------------|
| Baseline | 8,949 | ❌ **No** (only trivial X) | 0.523 (trivial) |
| Jaccard only | 4,843 | ✅ **Yes** (C, B, A, found) | 0.545 |
| Weighted Rollout | 5,633 | ✅ **Yes** (C, D, B, A found) | 0.545 |
| Both features | 4,711 | ✅ **Yes** (C, D, B, A found) | 0.545 |

**Verdict**: ✅ **47% overhead is ESSENTIAL** - baseline completely fails to discover meaningful patterns despite being fastest.

---

#### 2. Medium Datasets (Synth 1-5, 60s budget each)

#### Synth 1

| Configuration | Iterations | Found Top-3? | Pattern 1 | Pattern 2 | Pattern 3 |
|--------------|-----------|--------------|-----------|-----------|-----------|
| Baseline | 6,585 | ✅ Yes | C/D: 0.544 | A: 0.401 | {X}{W}{V}: 0.303 |
| Jaccard | 6,026 | ✅ Yes | C: 0.544 | A: 0.530 | B: 0.526 |
| Weighted | 4,160 | ✅ Yes | D: 0.544 | A: 0.530 | B: 0.526 |
| Both | 3,757 | ✅ Yes | C: 0.544 | A: 0.530 | B: 0.526 |

#### Synth 2

| Configuration | Iterations | Found Top-3? | Pattern 1 | Pattern 2 | Pattern 3 |
|--------------|-----------|--------------|-----------|-----------|-----------|
| Baseline | 10,173 | ✅ Yes | C/D: 0.543 | A: 0.535 | {X}{V}: 0.398 |
| Jaccard | 9,434 | ✅ Yes | C: 0.543 | A: 0.535 | {X}{V}: 0.398 |
| Weighted | 6,676 | ✅ Yes | D: 0.543 | A: 0.535 | B: 0.528 |
| Both | 5,816 | ✅ Yes | C/D: 0.543 | A: 0.535 | B: 0.528 |

#### Synth 3

| Configuration | Iterations | Found Top-3? | Pattern 1 | Pattern 2 | Pattern 3 |
|--------------|-----------|--------------|-----------|-----------|-----------|
| Baseline | 11,416 | ✅ Yes | A: 0.536 | D: 0.527 | {X}{T}: 0.400 |
| Jaccard | 10,498 | ✅ Yes | A: 0.536 | D/C: 0.527 | {X}{T}: 0.400 |
| Weighted | 7,344 | ✅ Yes | A: 0.536 | B: 0.529 | D/C: 0.527 |
| Both | 6,436 | ✅ Yes | A: 0.536 | B: 0.529 | D/C: 0.527 |

#### Synth 4

| Configuration | Iterations | Found Top-3? | Pattern 1 | Pattern 2 | Pattern 3 |
|--------------|-----------|--------------|-----------|-----------|-----------|
| Baseline | 6,623 | ✅ Yes | C/D: 0.546 | B: 0.526 | {X}: 0.524 |
| Jaccard | 6,036 | ✅ Yes | D: 0.546 | A: 0.529 | {X}: 0.524 |
| Weighted | 4,206 | ✅ Yes | D: 0.546 | A: 0.529 | B: 0.526 |
| Both | 3,818 | ✅ Yes | D: 0.546 | A: 0.529 | B: 0.526 |

**Analysis**: All find top-quality patterns. Slightly different ordering but all high quality (0.524-0.546).

#### Synth 5

| Configuration | Iterations | Found Top-3? | Pattern 1 | Pattern 2 | Pattern 3 |
|--------------|-----------|--------------|-----------|-----------|-----------|
| Baseline | 7,275 | ✅ Yes | A: 0.531 | D: 0.528 | {W}{X}: 0.399 |
| Jaccard | 6,832 | ✅ Yes | A: 0.531 | {W}{X}: 0.399 | ... |
| Weighted | 4,772 | ✅ Yes | A: 0.531 | D/C: 0.528 | B: 0.527 |
| Both | 4,240 | ✅ Yes | A: 0.531 | D: 0.528 | B/T: 0.399 |

**Analysis**: All successfully find top-quality patterns.
