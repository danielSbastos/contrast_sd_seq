# this file holds the default value for problem configuration
TOP_K = 5
ITERATIONS_NUMBER = 10000
TIME_BUDGET = 60
THETA = 0.8
MIN_SUPPORT = 20
LOG_LOSS_THRESHOLD = 0.0  # only expand sequences with log_loss >= threshold
USE_JACCARD_PRIORITY = False
CUMULATIVE_PROP_POWER = 2.0  # Power for non-linear weighting in get_idx_from_cumulative_prop (1.0=linear, 2.0=squared, higher=more emphasis on high values)

# Do not change this value if you do not know what your are doing
TIME_BUDGET_XP = 2**30
BEAM_WIDTH = 50

