# this file holds the default value for problem configuration
TOP_K = 5
ITERATIONS_NUMBER = 10000
TIME_BUDGET = 60
THETA = 0.8
DATA = 'promoters'# promoters, sc2, splice, context, block, skating, jmlr, aslbu
#QUALITY_MEASURE = 'roc-auc'# WRAcc, F1, Informedness, Precision, Lift
QUALITY_MEASURE = 'ROCAUC'# WRAcc, F1, Informedness, Precision, Lift
PRECISION_MIN_SUPPORT = 20
LOG_LOSS_THRESHOLD = 0.0  # only expand sequences with log_loss >= threshold
USE_JACCARD_PRIORITY = True

# Do not change this value if you do not know what your are doing
TIME_BUDGET_XP = 2**30
BEAM_WIDTH = 50

