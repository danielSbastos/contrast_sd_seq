"""
Interactive MCTS API: background run, pause/resume/stop, live queue stats.

Output files (same as ``get_patterns``) are written from :meth:`MCTS.finalize_results`, not from
:meth:`MCTS.run` — the worker only fills the in-memory priority queue.
"""
from __future__ import annotations

import datetime
import enum
import heapq
import threading
from typing import Any, Dict, List, Optional

import general.conf as conf

_QUEUE_STATS_TOP_N = 10


class RunStatus(enum.Enum):
    IDLE = enum.auto()
    PAUSED = enum.auto()
    STOPPED = enum.auto()
    ABORTED = enum.auto()
    # MCTS worker (per iteration)
    RUNNING_MAIN = enum.auto()
    RUNNING_ROLLOUT = enum.auto()
    RUNNING_BACKPROP = enum.auto()
    # Post-processing in ``finalize_results`` / ``filter_results``
    RUNNING_SIM = enum.auto()
    RUNNING_STATS = enum.auto()


_PHASE_TO_STATUS = {
    "MAIN": RunStatus.RUNNING_MAIN,
    "ROLLOUT": RunStatus.RUNNING_ROLLOUT,
    "BACKPROP": RunStatus.RUNNING_BACKPROP,
    "SIMILARITY_FILTER": RunStatus.RUNNING_SIM,
    "STATISTICAL_VALIDATION": RunStatus.RUNNING_STATS,
}

from general.utils import compute_subgroup_error_stats, decode_sequence, decode_sequences

from mctsextent.main import (
    build_iteration_metrics,
    init_mcts_tree,
    mcts_one_iteration,
    prepare_mcts_from_files,
)


class PatternInfo:
    """One pattern from the priority queue (aligned with ``decode_results`` fields)."""

    __slots__ = (
        "quality",
        "support",
        "descriptor",
        "pattern_delta",
        "error_class_0",
        "error_class_1",
        "std_class_0",
        "std_class_1",
        "size_class_0",
        "size_class_1",
    )

    def __init__(self, quality: float, sequence, extend, pattern_delta: float, encoding_to_items):
        self.quality = float(quality)
        self.support = len(extend)
        self.pattern_delta = float(pattern_delta)
        self.descriptor = decode_sequence(sequence, encoding_to_items)
        sg = compute_subgroup_error_stats(extend)
        if sg is not None:
            self.error_class_0 = sg["error_class_0"]
            self.error_class_1 = sg["error_class_1"]
            self.std_class_0 = sg["std_class_0"]
            self.std_class_1 = sg["std_class_1"]
            self.size_class_0 = sg["size_class_0"]
            self.size_class_1 = sg["size_class_1"]
        else:
            self.error_class_0 = None
            self.error_class_1 = None
            self.std_class_0 = None
            self.std_class_1 = None
            self.size_class_0 = None
            self.size_class_1 = None

    def __repr__(self) -> str:
        return (
            f"PatternInfo(quality={self.quality!r}, support={self.support!r}, "
            f"pattern_delta={self.pattern_delta!r}, descriptor={self.descriptor!r}, "
            f"error_class_0={self.error_class_0!r}, error_class_1={self.error_class_1!r}, "
            f"std_class_0={self.std_class_0!r}, std_class_1={self.std_class_1!r}, "
            f"size_class_0={self.size_class_0!r}, size_class_1={self.size_class_1!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class MCTS:
    """
    alg = MCTS(filename=..., **props)
    alg.run()       # background worker
    alg.pause()
    alg.run()       # resume
    alg.stop()
    """

    def __init__(
        self,
        filename: str,
        *,
        top_k: int = conf.TOP_K,
        time_budget: float = conf.TIME_BUDGET,
        theta: float = conf.THETA,
        iterations_limit: int = conf.ITERATIONS_NUMBER,
        max_length: int = 6,
        max_gap: int = conf.MAX_GAP,
        support_penalty: float = conf.SUPPORT_PENALTY,
        sigmoid_offset: float = conf.SIGMOID_OFFSET,
        synth_patterns_path: Optional[str] = None,
        **props,
    ):
        if props:
            raise TypeError(f"MCTS got unexpected keyword arguments: {sorted(props.keys())}")

        self.filename = filename
        self.top_k = top_k
        self.time_budget = time_budget
        self.theta = theta
        self.iterations_limit = iterations_limit
        self.max_length = max_length

        self._data, self._target_class, self._log_losses, self.extra, self.encoding_to_items = (
            prepare_mcts_from_files(
                filename,
                max_gap=max_gap,
                support_penalty=support_penalty,
                sigmoid_offset=sigmoid_offset,
                synth_patterns_path=synth_patterns_path,
            )
        )

        self._wall_begin: Optional[datetime.datetime] = None
        self._time_budget_td = datetime.timedelta(seconds=time_budget)

        self._root_node = None
        self._sorted_patterns = None
        self._node_hashmap = None
        self._item_log_losses = None
        self._stats = None

        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()
        self._abort_requested = False
        self._status = RunStatus.IDLE
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def _set_phase_status(self, phase: str) -> None:
        self._status = _PHASE_TO_STATUS.get(phase, RunStatus.RUNNING_MAIN)

    def _ensure_tree(self) -> None:
        if self._root_node is not None:
            return
        self._data, self._root_node, self._sorted_patterns, self._node_hashmap, self._item_log_losses, self._stats = (
            init_mcts_tree(self._data, self._target_class, self._log_losses, self.top_k, self.theta)
        )

    def _worker(self) -> None:
        self._ensure_tree()
        assert self._wall_begin is not None

        while True:
            self._pause_event.wait()
            if self._stop_event.is_set():
                self._status = RunStatus.ABORTED if self._abort_requested else RunStatus.STOPPED
                return
            with self._lock:
                if datetime.datetime.utcnow() - self._wall_begin > self._time_budget_td:
                    self._status = RunStatus.STOPPED
                    return
                if self._stats["iteration_count"] >= self.iterations_limit:
                    self._status = RunStatus.STOPPED
                    return
                status = mcts_one_iteration(
                    self._root_node,
                    self._sorted_patterns,
                    self._node_hashmap,
                    self._item_log_losses,
                    self._stats,
                    phase_hook=self._set_phase_status,
                    should_abort=lambda: self._stop_event.is_set(),
                )
            if status == "finished":
                self._status = RunStatus.STOPPED
                return
            if status == "aborted":
                self._status = RunStatus.ABORTED if self._abort_requested else RunStatus.STOPPED
                return

    @property
    def status(self) -> RunStatus:
        return self._status

    @property
    def iteration_count(self) -> int:
        with self._lock:
            if self._stats is None:
                return 0
            return self._stats["iteration_count"]

    @property
    def patterns(self) -> List[PatternInfo]:
        with self._lock:
            if not self._sorted_patterns or not self._sorted_patterns.heap:
                return []
            ranked = heapq.nlargest(len(self._sorted_patterns.heap), self._sorted_patterns.heap)
            out: List[PatternInfo] = []
            for quality, seq, extend, pattern_delta in ranked:
                out.append(PatternInfo(quality, seq, extend, pattern_delta, self.encoding_to_items))
            return out

    def queue_stats(self) -> Dict[str, Any]:
        """
        Snapshot over the **top 10** heap entries by quality: ``top10_avg_quality``,
        ``top10_avg_support``, and ``top10_patterns`` (one dict per pattern: ``quality``,
        ``pattern_descriptor``, ``error_class_*``, ``std_class_*``, ``size_class_*``).
        """
        with self._lock:
            ic = 0 if self._stats is None else self._stats["iteration_count"]
            enc = self.encoding_to_items

            null_row = {
                "pattern_descriptor": None,
                "error_class_0": None,
                "error_class_1": None,
                "std_class_0": None,
                "std_class_1": None,
                "size_class_0": None,
                "size_class_1": None,
            }

            if not self._sorted_patterns or not self._sorted_patterns.heap:
                return {
                    "top10_avg_quality": 0.0,
                    "top10_avg_support": 0.0,
                    "num_patterns": 0,
                    "iteration_count": ic,
                    "top10_patterns": [],
                }

            heap = self._sorted_patterns.heap
            n = len(heap)
            k = min(_QUEUE_STATS_TOP_N, n)
            top = heapq.nlargest(k, heap)

            sum_quality = 0.0
            sum_support = 0
            top10_patterns: List[Dict[str, Any]] = []
            for quality, seq, extend, _pattern_delta in top:
                sum_quality += quality
                sum_support += len(extend)
                desc = decode_sequence(seq, enc)
                sg = compute_subgroup_error_stats(extend)
                if sg is not None:
                    top10_patterns.append(
                        {
                            "quality": float(quality),
                            "pattern_descriptor": desc,
                            "error_class_0": sg["error_class_0"],
                            "error_class_1": sg["error_class_1"],
                            "std_class_0": sg["std_class_0"],
                            "std_class_1": sg["std_class_1"],
                            "size_class_0": sg["size_class_0"],
                            "size_class_1": sg["size_class_1"],
                        }
                    )
                else:
                    row = dict(null_row)
                    row["quality"] = float(quality)
                    row["pattern_descriptor"] = desc
                    top10_patterns.append(row)

            return {
                "top10_avg_quality": sum_quality / k,
                "top10_avg_support": sum_support / k,
                "num_patterns": n,
                "iteration_count": ic,
                "top10_patterns": top10_patterns,
            }

    def finalize_results(self, *, stop_worker: bool = True) -> Any:
        """
        Run the same post-processing as ``launch_mcts`` after search: similarity filter, statistical
        validation, and **writing output files** (via ``save_all_patterns`` / related helpers).
        Returns decoded sequences (same shape as ``get_patterns``).

        Files are not written during ``run()`` alone; call this when the run should be persisted.

        Stop the background worker first unless ``stop_worker=False`` (only safe if you know the
        worker is not mutating the queue).
        """
        if stop_worker:
            self.stop()

        self._ensure_tree()

        with self._lock:
            data = self._data
            sorted_patterns = self._sorted_patterns
            node_hashmap = self._node_hashmap
            stats = self._stats

        begin = self._wall_begin or datetime.datetime.utcnow()
        runtime_seconds = (datetime.datetime.utcnow() - begin).total_seconds()

        iteration_count = stats["iteration_count"]
        extra = dict(self.extra)
        extra["iteration_count"] = iteration_count
        extra["iteration_metrics"] = build_iteration_metrics(
            node_hashmap,
            iteration_count,
            runtime_seconds,
            stats["max_depth_reached"],
            stats["successful_expansions"],
            stats["valid_from_exploration"],
            stats["valid_from_exploitation"],
            sorted_patterns,
        )
        extra["phase_hook"] = self._set_phase_status

        try:
            results = sorted_patterns.get_top_k_non_redundant(
                data, self.top_k, pattern_max_len=self.max_length, extra=extra
            )
        finally:
            self._status = RunStatus.STOPPED

        return decode_sequences(results, self.encoding_to_items)

    def run(self, iterations: Optional[int] = None) -> None:
        """
        Start or resume the background search. If ``iterations`` is set, increases the
        iteration cap by that many steps so a paused/stopped run can continue (same tree).
        """
        if iterations is not None:
            self.iterations_limit += int(iterations)

        self._abort_requested = False
        self._stop_event.clear()
        self._pause_event.set()

        if self._thread is not None and self._thread.is_alive():
            return

        self._wall_begin = datetime.datetime.utcnow()
        self._status = RunStatus.RUNNING_MAIN
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        self._pause_event.clear()
        self._status = RunStatus.PAUSED

    def stop(self) -> None:
        """Stop the worker and report ``RunStatus.STOPPED`` when the thread ends."""
        self._abort_requested = False
        self._stop_event.set()
        self._pause_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3600.0)
            self._thread = None

    def abort(self) -> None:
        """Stop the worker; exit paths report ``RunStatus.ABORTED`` (via ``should_abort`` / worker)."""
        self._abort_requested = True
        self._stop_event.set()
        self._pause_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3600.0)
            self._thread = None
        self._abort_requested = False
