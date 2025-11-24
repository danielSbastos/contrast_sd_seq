from re import A
import general.conf as conf

from general.utils import find_LCS, sequence_mutable_to_immutable, compute_quality, \
    get_idx_from_cumulative_prop, compute_sequence_expand


from seqscout.global_var import Model


class Node():
    def __init__(self, intent, parent, node_hashmap):
        '''
        :param added_object:
        :param extend: identifiers of objects
        :param parent:
        :param data:
        :param target_class:
        '''

        self.intent = intent
        self.node_hashmap = node_hashmap
        self.depth = 0 if parent is None else parent.depth + 1

        self._quality = None
        self._rocauc = None
        self._extend = None
        self._candidate_sequences_expand = None
        self._log_losses = None

        if parent != None:
            self.parents = [parent]
            parent.children.append(self)
        else:
            self.parents = []

        self.children = []
        self.number_visits = 1
        self.dead_end = False

    @property
    def quality(self):
        if self._quality is None:
            self._quality, self._rocauc, self._extend = self.get_extend_and_quality(self.intent)
        return self._quality

    @property
    def rocauc(self):
        if self._rocauc is None:
            self._quality, self._rocauc, self._extend = self.get_extend_and_quality(self.intent)
        return self._rocauc

    @property
    def extend(self):
        if self._extend is None:
            self._quality, self._rocauc, self._extend = self.get_extend_and_quality(self.intent)
        return self._extend

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
        for idx, seq in candidate_sequences_expand:
            if log_losses[idx] >= conf.LOG_LOSS_THRESHOLD:
                self._candidate_sequences_expand.append(seq)
                self._log_losses.append(log_losses[idx])

    def get_normalized_quality(self):
        return self.quality

    def get_extend_and_quality(self, subsequence):
        if self.intent == None:
            return 0, -1, []
        return compute_quality(sequence_mutable_to_immutable(subsequence))

    def is_fully_expanded(self):
        return len(self.candidate_sequences_expand) == 0

    def is_terminal(self):
        return len(self.extend) == len(Model.get_data())

    def is_dead_end(self):
        if self.is_terminal() or self.dead_end:
            self.dead_end = True
            return True

        if not self.is_fully_expanded():
            return False

        for child in self.children:
            if not child.is_dead_end():
                return False

        self.dead_end = True
        return True

    def expand(self):
        if self._log_losses is None:
            self._initialize_candidates()
        
        weights = self._log_losses
        sequence_children = None
        selected_log_loss = 0.0
        random_object_idx = None
        
        max_retries = min(10, len(self._candidate_sequences_expand))
        for attempt in range(max_retries):
            if len(self._candidate_sequences_expand) == 0:
                break
                
            random_object_idx = get_idx_from_cumulative_prop(weights) or 0
            random_object = self._candidate_sequences_expand[random_object_idx]
            selected_log_loss = self._log_losses[random_object_idx]
            
            if self.intent == None:
                sequence_children = sequence_mutable_to_immutable(random_object)
            else:
                sequence_children = sequence_mutable_to_immutable(find_LCS(random_object, self.intent))
            
            if len(sequence_children) > 0:
                break
            
            self._candidate_sequences_expand.pop(random_object_idx)
            self._log_losses.pop(random_object_idx)
            weights = self._log_losses
        
        if sequence_children is not None and len(sequence_children) > 0 and random_object_idx is not None:
            if random_object_idx < len(self._candidate_sequences_expand):
                self._candidate_sequences_expand.pop(random_object_idx)
                self._log_losses.pop(random_object_idx)
        
        if sequence_children is None or len(sequence_children) == 0:
            sequence_children = tuple()
            selected_log_loss = 0.0

        if sequence_children in self.node_hashmap:
            child = self.node_hashmap[sequence_children]
            child.parents.append(self)
            self.children.append(child)
        else:
            child = Node(sequence_children, self, self.node_hashmap)
            self.node_hashmap[sequence_children] = child

        return child, selected_log_loss

    def update(self, reward):
        current_quality = self.quality
        self._quality = (self.number_visits * current_quality + reward) / (
                self.number_visits + 1)
        self.number_visits += 1