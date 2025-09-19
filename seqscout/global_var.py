ITERATION_NUMBER = 0

def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1


class Model:
    MODEL_ROCAUC = 0
    LABELS = []

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

