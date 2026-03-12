# this file holds the default value for problem configuration
TOP_K = 100
ITERATIONS_NUMBER = 10000
TIME_BUDGET = 60
THETA = 0.1
MIN_SUPPORT = 60
MIN_INTENT_LEN = 10  # minimum intent/pattern length; keep trying other sequences in expand() if LCS is shorter
LOG_LOSS_THRESHOLD = 0  # only expand sequences with log_loss >= threshold
MAX_GAP = 1
SUPPORT_PENALTY = 0.0
SIGMOID_OFFSET = 2
# Do not change this value if you do not know what your are doing
TIME_BUDGET_XP = 2**30
BEAM_WIDTH = 50
