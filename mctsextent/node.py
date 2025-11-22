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

        self.quality, self.rocauc, self.extend = self.get_extend_and_quality(self.intent)

        if parent != None:
            self.parents = [parent]
            parent.children.append(self)
        else:
            self.parents = []

        self.children = []
        self.candidate_sequences_expand = []
        self.log_losses = []

        if self.intent is not None:
            candidate_sequences_expand = compute_sequence_expand(tuple(self.intent), tuple(self.extend))
        else:
            candidate_sequences_expand = compute_sequence_expand(self.intent, tuple(self.extend))

        log_losses = Model.get_log_losses()
        for idx, seq in candidate_sequences_expand:
            if log_losses[idx] >= conf.LOG_LOSS_THRESHOLD:
                self.candidate_sequences_expand.append(seq)
                self.log_losses.append(log_losses[idx])

        self.number_visits = 1
        self.dead_end = False

    def get_normalized_quality(self):
        return self.quality

    def get_extend_and_quality(self, subsequence):
        if self.intent == None:
            return 0, -1, []
        return compute_quality(sequence_mutable_to_immutable(subsequence))

    def is_fully_expanded(self):
        return len(self.candidate_sequences_expand) == 0

    def is_terminal(self):
        # a node is terminal if all positive sequences have been explored
        return len(self.extend) == len(Model.get_data())

    def is_dead_end(self):
        '''
        A terminal node is a dead end, and a node with all its children being dead ends is a dead end
        '''
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
        weights = self.log_losses

        random_object_idx = get_idx_from_cumulative_prop(weights) or 0
        random_object = self.candidate_sequences_expand[random_object_idx]
        selected_log_loss = self.log_losses[random_object_idx]

        self.candidate_sequences_expand.pop(random_object_idx)
        self.log_losses.pop(random_object_idx)

        if self.intent == None:
            sequence_children = sequence_mutable_to_immutable(random_object)
        else:
            sequence_children = sequence_mutable_to_immutable(find_LCS(random_object, self.intent))

        if sequence_children in self.node_hashmap:
            child = self.node_hashmap[sequence_children]
            child.parents.append(self)
            self.children.append(child)
        else:
            child = Node(sequence_children, self, self.node_hashmap)
            self.node_hashmap[sequence_children] = child

        return child, selected_log_loss

    def update(self, reward):
        """
        Update the quality of the node
        :param reward: the roll-out score
        :return: None
        """
        # Mean-update
        self.quality = (self.number_visits * self.quality + reward) / (
                self.number_visits + 1)
        self.number_visits += 1
