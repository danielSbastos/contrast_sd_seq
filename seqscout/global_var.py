ITERATION_NUMBER = 0

def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1


class Model:
    MODEL_ROCAUC = 0
    LABELS = []
    TARGET_CLASS = None
    LOG_LOSSES = None
    DATA = None
    VALIDATION_DATA = None
    VALIDATION_TARGET_CLASS = None

    @classmethod
    def set_rocauc(cls, value):
        cls.MODEL_ROCAUC = value
    
    @classmethod
    def get_rocauc(cls):
        return cls.MODEL_ROCAUC

    @classmethod
    def set_labels(cls, value):
        cls.LABELS = value
        cls.LABELS.sort()

    @classmethod
    def get_labels(cls):
        return cls.LABELS
 
    @classmethod
    def is_multiclass(cls):
        return len(cls.LABELS) > 2

    @classmethod
    def set_target_class(cls, value):
        cls.TARGET_CLASS = value

    @classmethod
    def get_target_class(cls):
        return cls.TARGET_CLASS

    @classmethod
    def set_log_losses(cls, value):
        cls.LOG_LOSSES = value

    @classmethod
    def set_data(cls, value):
        cls.DATA = value

    @classmethod
    def get_log_losses(cls):
        return cls.LOG_LOSSES

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
