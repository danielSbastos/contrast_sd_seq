class Model:
    MODEL_ACCURACY = 0
    LABELS = []

    DATA = None
    VALIDATION_DATA = None
    VALIDATION_TARGET_CLASS = None

    LOG_LOSSES = None

    GLOBAL_MEAN_ERROR = None
    GLOBAL_STD_ERROR = None
    GLOBAL_ERRORS = None
    POSITIVE_CLASS = None

    HARD_ERRORS = None
    SOFT_ERRORS = None
    GLOBAL_HARD_ERROR = None
    MAX_QUALITY = 0.0

    @classmethod
    def set_accuracy(cls, value):
        cls.MODEL_ACCURACY = value

    @classmethod
    def get_accuracy(cls):
        return cls.MODEL_ACCURACY

    @classmethod
    def set_labels(cls, value):
        cls.LABELS = sorted(value)

    @classmethod
    def get_labels(cls):
        return cls.LABELS

    @classmethod
    def is_multiclass(cls):
        return len(cls.LABELS) > 2

    @classmethod
    def set_positive_class(cls, value):
        cls.POSITIVE_CLASS = value

    @classmethod
    def get_positive_class(cls):
        return cls.POSITIVE_CLASS

    @classmethod
    def set_target_class(cls, value):
        cls.TARGET_CLASS = value

    @classmethod
    def get_target_class(cls):
        return cls.TARGET_CLASS

    INVERTED_INDEX = None
    VALIDATION_INVERTED_INDEX = None

    @classmethod
    def set_data(cls, value):
        cls.DATA = value
        cls.INVERTED_INDEX = {}
        if value is not None:
            for idx, seq in enumerate(value):
                for itemset in seq:
                    for item in itemset:
                        if item not in cls.INVERTED_INDEX:
                            cls.INVERTED_INDEX[item] = set()
                        cls.INVERTED_INDEX[item].add(idx)

    @classmethod
    def get_data(cls):
        return cls.DATA

    @classmethod
    def set_validation_data(cls, value):
        cls.VALIDATION_DATA = value
        cls.VALIDATION_INVERTED_INDEX = {}
        if value is not None:
            for idx, seq in enumerate(value):
                for itemset in seq:
                    for item in itemset:
                        if item not in cls.VALIDATION_INVERTED_INDEX:
                            cls.VALIDATION_INVERTED_INDEX[item] = set()
                        cls.VALIDATION_INVERTED_INDEX[item].add(idx)

    @classmethod
    def get_validation_data(cls):
        return cls.VALIDATION_DATA



    @classmethod
    def set_validation_target_class(cls, value):
        cls.VALIDATION_TARGET_CLASS = value

    @classmethod
    def get_validation_target_class(cls):
        return cls.VALIDATION_TARGET_CLASS

    @classmethod
    def set_log_losses(cls, value):
        cls.LOG_LOSSES = value

    @classmethod
    def get_log_losses(cls):
        return cls.LOG_LOSSES

    @classmethod
    def set_global_mean_error(cls, value):
        cls.GLOBAL_MEAN_ERROR = value

    @classmethod
    def get_global_mean_error(cls):
        return cls.GLOBAL_MEAN_ERROR

    @classmethod
    def set_global_std_error(cls, value):
        cls.GLOBAL_STD_ERROR = value

    @classmethod
    def get_global_std_error(cls):
        return cls.GLOBAL_STD_ERROR

    @classmethod
    def set_global_errors(cls, errors):
        cls.GLOBAL_ERRORS = errors

    @classmethod
    def get_global_errors(cls):
        return cls.GLOBAL_ERRORS

    @classmethod
    def set_hard_errors(cls, errors):
        cls.HARD_ERRORS = errors

    @classmethod
    def get_hard_errors(cls):
        return cls.HARD_ERRORS

    @classmethod
    def set_soft_errors(cls, errors):
        cls.SOFT_ERRORS = errors

    @classmethod
    def get_soft_errors(cls):
        return cls.SOFT_ERRORS

    @classmethod
    def set_global_hard_error(cls, error):
        cls.GLOBAL_HARD_ERROR = error

    @classmethod
    def get_global_hard_error(cls):
        return cls.GLOBAL_HARD_ERROR

    @classmethod
    def update_max_quality(cls, quality):
        """Update the maximum quality seen so far."""
        if quality > cls.MAX_QUALITY:
            cls.MAX_QUALITY = quality

    @classmethod
    def get_max_quality(cls):
        return cls.MAX_QUALITY

    @classmethod
    def reset_max_quality(cls):
        """Reset max quality (useful when starting a new run)."""
        cls.MAX_QUALITY = 0.0


COUNT_DOMINANT_ERROR_CLASS_0 = 0
COUNT_DOMINANT_ERROR_CLASS_1 = 0

def increment_dominant_error_class(value):
    if value == 0:
        global COUNT_DOMINANT_ERROR_CLASS_0
        COUNT_DOMINANT_ERROR_CLASS_0 += 1
    else:
        global COUNT_DOMINANT_ERROR_CLASS_1
        COUNT_DOMINANT_ERROR_CLASS_1 += 1


ITERATION_NUMBER = 0
def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1


def get_candidate_sequence_indices(subsequence, is_validation=False):
    inv_index = Model.VALIDATION_INVERTED_INDEX if is_validation else Model.INVERTED_INDEX
    data_len = len(Model.VALIDATION_DATA if is_validation else Model.DATA)
    
    if not subsequence or inv_index is None:
        return range(data_len)
    
    items = []
    for itemset in subsequence:
        for item in itemset:
            items.append(item)
            
    if not items:
        return range(data_len)
        
    items.sort(key=lambda x: len(inv_index.get(x, ())))
    
    result = inv_index.get(items[0], set())
    if not result:
        return ()
        
    for item in items[1:]:
        result = result.intersection(inv_index.get(item, ()))
        if not result:
            return ()
            
    return result
