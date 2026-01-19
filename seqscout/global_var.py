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

    @classmethod
    def set_data(cls, value):
        cls.DATA = value

    @classmethod
    def get_data(cls):
        return cls.DATA

    @classmethod
    def set_validation_data(cls, value):
        cls.VALIDATION_DATA = value

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


ITERATION_NUMBER = 0

def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1
