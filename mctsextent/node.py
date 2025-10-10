import general.conf as conf

from general.utils import find_LCS, sequence_mutable_to_immutable, compute_quality_extend, is_subsequence



class Node():
    def __init__(self, intent, parent, data, log_losses, target_class, node_hashmap, quality_measure=conf.QUALITY_MEASURE, log_loss_threshold=conf.LOG_LOSS_THRESHOLD):
        '''
        :param added_object:
        :param extend: identifiers of objects
        :param parent:
        :param data:
        :param target_class:
        :param log_loss_threshold: minimum log_loss value for a sequence to be considered as expansion candidate
        '''

        self.intent = intent
        self.data = data
        self.node_hashmap = node_hashmap
        self.log_loss_threshold = log_loss_threshold

        # the extend is the id of sequences
        self.quality, self.rocauc, self.extend = self.get_extend_and_quality(data, self.intent, target_class, quality_measure=quality_measure)

        if parent != None:
            self.parents = [parent]
            parent.children.append(self)
        else:
            self.parents = []

        self.children = []
        self.candidate_sequences_expand = []
        self.log_losses = []

        candidate_sequences_expand = self.compute_sequence_expand(data) # dataset sequences to expand

        for idx, seq in candidate_sequences_expand:
            if log_losses[idx] >= log_loss_threshold:
                self.candidate_sequences_expand.append(seq)
                self.log_losses.append(log_losses[idx])

        self.number_visits = 1
        self.dead_end = False

    def get_normalized_quality(self, quality_measure=conf.QUALITY_MEASURE):
        if quality_measure == 'WRAcc':
            return (self.quality + 0.25) * 2
        else:
            return self.quality

    def get_extend_and_quality(self, data, subsequence, target_class, quality_measure=conf.QUALITY_MEASURE):
        if self.intent == None:
            return 0, -1, []
        return compute_quality_extend(data, subsequence, target_class, quality_measure=quality_measure)

    def compute_sequence_expand(self, data):
        # we cannot add sequences which are supersequences of pattern, or else the LCS will return the same node, creating a dag and many problems!

        # If root node (intent is None), consider all sequences
        if self.intent is None:
            return [[i, seq[1:]] for i, seq in enumerate(data) if i not in self.extend]

        # For non-root nodes: only expand with sequences that contain ALL elements from the intent
        # This prevents losing key pattern elements (especially rare ones) during LCS operations
        intent_elements = set()
        for itemset in self.intent:
            intent_elements.update(itemset)

        candidates = []
        for i, seq in enumerate(data):
            if i in self.extend:
                continue

            sequence = seq[1:]

            # Check if sequence is a supersequence of intent (skip if true)
            try:
                if is_subsequence(self.intent, sequence):
                    continue
            except TypeError:
                pass

            # Get all elements in this sequence
            sequence_elements = set()
            for itemset in sequence:
                sequence_elements.update(itemset)

            # Only include if sequence contains ALL elements from intent
            if intent_elements.issubset(sequence_elements):
                candidates.append([i, sequence])

        return candidates

    def is_fully_expanded(self):
        return len(self.candidate_sequences_expand) == 0

    def is_terminal(self):
        # a node is terminal if all positive sequences have been explored
        return len(self.extend) == len(self.data)

    def is_dead_end(self):
        '''
        A terminal node is a dead end, and a node with all its children being dead ends is a dead end
        '''
        if self.is_terminal() or self.dead_end:
            self.dead_end = True
            return True

        if not self.is_fully_expanded():
            # a node non-fully expanded is not a dead end
            return False

        for child in self.children:
            # improving time computing
            if not child.is_dead_end():
                return False

        self.dead_end = True
        return True

    def expand(self, data, log_losses, target_class, quality_measure=conf.QUALITY_MEASURE):
        max_loss_idx = self.log_losses.index(max(self.log_losses))

        random_object = self.candidate_sequences_expand[max_loss_idx]
        selected_log_loss = self.log_losses[max_loss_idx]

        self.candidate_sequences_expand.pop(max_loss_idx)
        self.log_losses.pop(max_loss_idx)

        if self.intent == None:
            sequence_children = sequence_mutable_to_immutable(random_object)
        else:
            sequence_children = sequence_mutable_to_immutable(find_LCS(random_object, self.intent))

        if sequence_children in self.node_hashmap:
            child = self.node_hashmap[sequence_children]
            child.parents.append(self)
            self.children.append(child)
        else:
            child = Node(sequence_children, self, data, log_losses, target_class, self.node_hashmap, quality_measure=quality_measure, log_loss_threshold=self.log_loss_threshold)
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
