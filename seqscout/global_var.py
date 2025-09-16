ITERATION_NUMBER = 0

def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1


class ModelRocAuc:
    MODEL_ROCAUC = 0

    @classmethod
    def set(cls, value):
        cls.MODEL_ROCAUC = value
    
    @classmethod
    def get(cls):
        return cls.MODEL_ROCAUC

