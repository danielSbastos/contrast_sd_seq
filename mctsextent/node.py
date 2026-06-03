from re import A
import general.conf as conf
from collections import Counter
import random

from general.utils import find_LCS, sequence_mutable_to_immutable, compute_quality, \
    get_idx_from_cumulative_prop, compute_sequence_expand


from seqscout.global_var import Model


class DeletedExtend:
    def __init__(self, size):
        self.size = size
    def __len__(self):
        return self.size
    def __iter__(self):
        return iter(())
    def __bool__(self):
        return self.size > 0


class Node():
    __slots__ = (
        'intent', 'depth', '_quality', '_accuracy', '_extend',
        '_size_class_0', '_size_class_1', '_candidate_sequences_expand',
        '_log_losses', '_class_balance_score', 'parents', 'children',
        'number_visits', 'dead_end', '_support'
    )
    def __init__(self, intent, parent, node_hashmap=None):
        '''
        :param added_object:
        :param extend: identifiers of objects
        :param parent:
        :param data:
        :param target_class:
        '''

        self.intent = intent
        self.depth = 0 if parent is None else parent.depth + 1

        self._quality = None
        self._accuracy = None
        self._extend = None
        self._size_class_0 = None
        self._size_class_1 = None
        self._candidate_sequences_expand = None
        self._log_losses = None
        self._class_balance_score = None

        if parent != None:
            self.parents = [parent]
            parent.children.append(self)
        else:
            self.parents = []

        self.children = []
        self.number_visits = 1
        self.dead_end = False

        self.check_and_propagate_dead_end()

    def _ensure_quality_computed(self):
        if self._quality is None:
            q, a, e, n0, n1 = self.get_extend_and_quality(self.intent)
            self._quality, self._accuracy, self._extend = q, a, e
            self._size_class_0, self._size_class_1 = n0, n1
            self._support = len(e) if e is not None else 0

    @property
    def quality(self):
        self._ensure_quality_computed()
        return self._quality

    @property
    def accuracy(self):
        self._ensure_quality_computed()
        return self._accuracy

    @property
    def extend(self):
        self._ensure_quality_computed()
        return self._extend

    @property
    def size_class_0(self):
        self._ensure_quality_computed()
        return self._size_class_0

    @property
    def size_class_1(self):
        self._ensure_quality_computed()
        return self._size_class_1

    @property
    def candidate_sequences_expand(self):
        if self._candidate_sequences_expand is None:
            self._initialize_candidates()
        return self._candidate_sequences_expand

    @property
    def log_losses(self):
        if self._log_losses is None:
            self._initialize_candidates()
        return self._log_losses

    def _initialize_candidates(self):
        if self.intent is not None:
            candidate_sequences_expand = compute_sequence_expand(tuple(self.intent), tuple(self.extend))
        else:
            candidate_sequences_expand = compute_sequence_expand(self.intent, tuple(self.extend))

        log_losses = Model.get_log_losses()
        self._candidate_sequences_expand = []
        self._log_losses = []
        for idx in candidate_sequences_expand:
            if log_losses[idx] >= conf.LOG_LOSS_THRESHOLD:
                self._candidate_sequences_expand.append(idx)
                self._log_losses.append(log_losses[idx])

        # Release the memory of the large extend list
        self._support = len(self._extend) if self._extend is not None else 0
        self._extend = DeletedExtend(self._support)

    def get_normalized_quality(self):
        return self.quality

    def get_extend_and_quality(self, subsequence):
        if self.intent is None:
            return 0, -1, [], 0, 0
        return compute_quality(sequence_mutable_to_immutable(subsequence))

    def is_fully_expanded(self):
        return len(self.candidate_sequences_expand) == 0

    def is_terminal(self):
        return len(self.extend) == len(Model.get_data())

    def is_dead_end(self):
        return self.dead_end

    def check_and_propagate_dead_end(self):
        if self.dead_end:
            return
        if self.is_terminal() or (self.is_fully_expanded() and all(child.dead_end for child in self.children)):
            self.dead_end = True
            for parent in self.parents:
                parent.check_and_propagate_dead_end()

    def expand(self, node_hashmap):
        if self._log_losses is None:
            self._initialize_candidates()
        
        if len(self._candidate_sequences_expand) == 0:
            sequence_children = tuple()
            selected_log_loss = 0.0
        else:
            random_object_idx = random.randint(0, len(self._candidate_sequences_expand) - 1)
            random_object_idx_val = self._candidate_sequences_expand.pop(random_object_idx)
            random_object = Model.get_data()[random_object_idx_val]
            selected_log_loss = self._log_losses.pop(random_object_idx)
            
            if self.intent == None:
                sequence_children = sequence_mutable_to_immutable(random_object)
            else:
                sequence_children = sequence_mutable_to_immutable(find_LCS(random_object, self.intent))
            
            if len(sequence_children) == 0:
                sequence_children = tuple()
                selected_log_loss = 0.0

        if sequence_children in node_hashmap:
            child = node_hashmap[sequence_children]
            if self not in child.parents:
                child.parents.append(self)
            if child not in self.children:
                self.children.append(child)
        else:
            child = Node(sequence_children, self, node_hashmap)
            node_hashmap[sequence_children] = child

        self.check_and_propagate_dead_end()

        return child, selected_log_loss

    def update(self, reward):
        current_quality = self.quality
        self._quality = (self.number_visits * current_quality + reward) / (
                self.number_visits + 1)
        self.number_visits += 1

    def __getstate__(self):
        state = {}
        for slot in self.__slots__:
            if hasattr(self, slot):
                state[slot] = getattr(self, slot)
        return state

    def __setstate__(self, state):
        if isinstance(state, dict):
            for slot in self.__slots__:
                if slot in state:
                    setattr(self, slot, state[slot])