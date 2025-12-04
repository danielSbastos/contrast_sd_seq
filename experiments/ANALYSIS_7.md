# Reunião 04/12

## Experimentos com datasets reais

1. Análise de sentimentos (negativo e positivo) de tweets
   - Dataset: https://www.kaggle.com/datasets/halemogpa/processed
2. Chamadas sequenciais de API associadas à malware, ou não
   - Dataset: https://www.kaggle.com/datasets/ang3loliveira/malware-analysis-datasets-api-call-sequences
3. Histórico de notas em testes e se o aluno passou no curso
   - Dataset: https://analyse.kmi.open.ac.uk/open-dataset

### Métricas de cada modelo

#### Twitter

**AUC: 0.9348215**

```
==============================
TRAIN SET
==============================
Train Accuracy: 0.8573

Train Classification report (binary):
              precision    recall  f1-score   support

       Other       0.86      0.86      0.86      8000
           1       0.86      0.86      0.86      8000

    accuracy                           0.86     16000
   macro avg       0.86      0.86      0.86     16000
weighted avg       0.86      0.86      0.86     16000


Train Class distribution:
  Class 0 (others): 8000 samples
  Class 1 (1): 8000 samples

==============================
TEST SET
==============================
Test Accuracy: 0.7468

Test Classification report (binary):
              precision    recall  f1-score   support

       Other       0.75      0.74      0.74      2000
           1       0.74      0.75      0.75      2000

    accuracy                           0.75      4000
   macro avg       0.75      0.75      0.75      4000
weighted avg       0.75      0.75      0.75      4000


Test Class distribution:
  Class 0 (others): 2000 samples
  Class 1 (1): 2000 samples

```

#### Histórico dos alunos

**AUC: 0.9885594618055555**

```
==============================
TRAIN SET
==============================
Train Accuracy: 0.9369

Train Classification report (binary):
              precision    recall  f1-score   support

       Other       0.95      0.93      0.94      2400
           1       0.93      0.95      0.94      2400

    accuracy                           0.94      4800
   macro avg       0.94      0.94      0.94      4800
weighted avg       0.94      0.94      0.94      4800


Train Class distribution:
  Class 0 (others): 2400 samples
  Class 1 (1): 2400 samples

==============================
TEST SET
==============================
Test Accuracy: 0.7408

Test Classification report (binary):
              precision    recall  f1-score   support

       Other       0.73      0.75      0.74       600
           1       0.75      0.73      0.74       600

    accuracy                           0.74      1200
   macro avg       0.74      0.74      0.74      1200
weighted avg       0.74      0.74      0.74      1200


Test Class distribution:
  Class 0 (others): 600 samples
  Class 1 (1): 600 samples

```

#### Chamadas malware

**AUC: 0.9524014339513324**

```
==============================
TRAIN SET
==============================
Train Accuracy: 0.8485

Train Classification report (binary):
              precision    recall  f1-score   support

       Other       0.39      0.95      0.55       863
           1       0.99      0.84      0.91      8000

    accuracy                           0.85      8863
   macro avg       0.69      0.89      0.73      8863
weighted avg       0.93      0.85      0.87      8863


Train Class distribution:
  Class 0 (others): 863 samples
  Class 1 (1): 8000 samples

==============================
TEST SET
Test Accuracy: 0.8457

Test Classification report (binary):
              precision    recall  f1-score   support

       Other       0.38      0.94      0.54       216
           1       0.99      0.84      0.91      2000

    accuracy                           0.85      2216
   macro avg       0.69      0.89      0.72      2216
weighted avg       0.93      0.85      0.87      2216


Test Class distribution:
  Class 0 (others): 216 samples
  Class 1 (1): 2000 samples

```


## Top-3 slices por dataset

Levando em consideração um suporte mínimo de cada classe de 10 instâncias

### Twitter

Train size: 16000

```csv
pattern,quality,pattern_auc,support,class_balance,p_value,corrected_p,is_sig,global_auc
[{'probably'}],0.7944493078460397,0.8099547511312217,60,"{0.0: 34, 1.0: 26}",0.0019980019980019,0.0042510680808553,True,0.9348215
[{'missed'}],0.8408104262179303,0.804029304029304,110,"{0.0: 84, 1.0: 26}",0.0009990009990009,0.0024365878024414,True,0.9348215
"[{'!'}, {'not'}]",0.7349145541736907,0.7845315904139433,141,"{0.0: 90, 1.0: 51}",0.0009990009990009,0.0023785738071452,True,0.9348215
```

### Notas alunos

Train size: 4800

```csv
pattern,quality,pattern_auc,support,class_balance,p_value,corrected_p,is_sig,global_auc
"[{'TMA_15022_low'}, {'TMA_15023_low'}, {'TMA_15024_low'}]",1.1811093134341237,0.6918767507002801,38,"{0.0: 21, 1.0: 17}",0.000999000999000999,0.0014874014874014872,True,0.9885594618055555
[{'TMA_15024_low'}],1.1101878681498625,0.8095238095238095,79,"{0.0: 51, 1.0: 28}",0.000999000999000999,0.0014874014874014872,True,0.9885594618055555
"[{'TMA_15020_high'}, {'TMA_15021_low'}, {'TMA_15023_low'}]",1.254939162304669,0.6645833333333334,32,"{0.0: 20, 1.0: 12}",0.000999000999000999,0.0014874014874014872,True,0.9885594618055555
```


### Malware

Train size: 8863

```csv
"[{'264'}, {'264'}, {'264'}]",1.250513922245876,0.7452708658214116,350,"{1.0: 301, 0.0: 49}",0.0009990009990009,0.0011417154274297,True,0.9524014339513324
"[{'271'}, {'215'}, {'297'}]",1.092586534249156,0.7177234530175707,141,"{1.0: 119, 0.0: 22}",0.0009990009990009,0.0012210012210012,True,0.9524014339513324
[{'99'}],1.166048171320775,0.8536107569896253,2030,"{1.0: 1936, 0.0: 94}",0.0009990009990009,0.0012210012210012,True,0.9524014339513324
```

```csv
"[{'NtReadFile'}, {'NtReadFile'}, {'NtReadFile'}]",1.250513922245876,0.7452708658214116,350,"{1.0: 301, 0.0: 49}",0.0009990009990009,0.0011417154274297,True,0.9524014339513324
"[{'GetTempPathW'}, {'NtClose'}, {'NtCreateFile'}]",1.092586534249156,0.7177234530175707,141,"{1.0: 119, 0.0: 22}",0.0009990009990009,0.0012210012210012,True,0.9524014339513324
[{'GetNativeSystemInfo'}],1.166048171320775,0.8536107569896253,2030,"{1.0: 1936, 0.0: 94}",0.0009990009990009,0.0012210012210012,True,0.9524014339513324
```


- **NtReadFile**: Reads data from an open file.
- **GetTempPathW**: Retrieves the path of the directory designated for temporary files.
- **NtClose**: Deprecated. Closes the specified handle. NtClose is superseded by CloseHandle.
- **NtCreateFile**: Creates a new file or directory, or opens an existing file, device, directory, or volume.
- **GetNativeSystemInfo**: Retrieves information about the current system to an application running under WOW64. 