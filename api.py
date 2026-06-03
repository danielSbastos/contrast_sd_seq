"""
Interactive MCTS API: background run, pause/resume/stop, live queue stats.

Output files (same as ``get_patterns``) are written from :meth:`MCTS.finalize_results`, not from
:meth:`MCTS.run` — the worker only fills the in-memory priority queue.
"""
from __future__ import annotations

import datetime
from datetime import timezone
import enum
import heapq
import threading
import pickle
import os
import time
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
from auditlens_weights import apply_auditlens_weights, focus_on_attributes


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
        "p_value_bh",
    )

    def __init__(self, quality: float, sequence, extend, pattern_delta: float, encoding_to_items, p_value_bh: float = 0.0):
        self.quality = float(quality)
        self.support = len(extend)
        self.pattern_delta = float(pattern_delta)
        self.descriptor = decode_sequence(sequence, encoding_to_items)
        self.p_value_bh = float(p_value_bh)
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality": self.quality,
            "support": self.support,
            "descriptor": self.descriptor,
            "pattern_delta": self.pattern_delta,
            "error_class_0": self.error_class_0,
            "error_class_1": self.error_class_1,
            "std_class_0": self.std_class_0,
            "std_class_1": self.std_class_1,
            "size_class_0": self.size_class_0,
            "size_class_1": self.size_class_1,
            "p_value_bh": self.p_value_bh,
        }

    def __repr__(self) -> str:
        return (
            f"PatternInfo(quality={self.quality!r}, support={self.support!r}, "
            f"pattern_delta={self.pattern_delta!r}, descriptor={self.descriptor!r}, "
            f"error_class_0={self.error_class_0!r}, error_class_1={self.error_class_1!r}, "
            f"std_class_0={self.std_class_0!r}, std_class_1={self.std_class_1!r}, "
            f"size_class_0={self.size_class_0!r}, size_class_1={self.size_class_1!r}, "
            f"p_value_bh={self.p_value_bh!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()


# Memory baseline for circuit breaker (sampled on first call)
_memory_baseline_mb = None

def check_circuit_breaker(node_hashmap_size: int, memory_limit_mb: float = 5000.0, iteration_count: int = 0) -> bool:
    global _memory_baseline_mb
    
    # 1. Skip circuit breaker for first 100 iterations (initialization phase)
    if iteration_count < 100:
        return False
    
    # 2. Tree size check (allow up to 100k nodes before hard limit)
    if node_hashmap_size > 100000:
        print(f"[WARNING] Circuit breaker: Node hashmap size threshold exceeded ({node_hashmap_size} > 100000).")
        return True
    
    # 3. Relative memory growth check (instead of absolute limit)
    try:
        import resource
        # ru_maxrss is in kilobytes on Linux
        maxrss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        maxrss_mb = maxrss_kb / 1024.0
        
        # Initialize baseline on first call after initialization
        if _memory_baseline_mb is None:
            _memory_baseline_mb = maxrss_mb
        
        # Check absolute limit (generous: 5000 MB)
        if maxrss_mb > memory_limit_mb:
            print(f"[WARNING] Circuit breaker: Process RSS memory usage exceeded hard limit ({maxrss_mb:.1f} MB > {memory_limit_mb:.1f} MB).")
            return True
        
        # Check relative growth: flag if doubled from baseline
        memory_growth = maxrss_mb - _memory_baseline_mb
        max_growth_mb = 2000.0  # Allow up to 2GB growth
        if memory_growth > max_growth_mb:
            print(f"[WARNING] Circuit breaker: Process memory growth too high ({memory_growth:.1f} MB > {max_growth_mb:.1f} MB).")
            return True
    except Exception as e:
        pass
    
    return False


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
        state_dir: str = ".mcts_state",
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
        self.state_dir = state_dir
        self.synth_patterns_path = synth_patterns_path

        self._data, self._target_class, self._log_losses, self.extra, self.encoding_to_items = (
            prepare_mcts_from_files(
                filename,
                max_gap=max_gap,
                support_penalty=support_penalty,
                sigmoid_offset=sigmoid_offset,
                synth_patterns_path=synth_patterns_path,
            )
        )
        from mctsextent.main import filter_empty_sequences
        from seqscout.global_var import Model
        Model.set_data(filter_empty_sequences(self._data))
        Model.set_target_class(self._target_class)

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
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._budget_remaining: int = 0
        self._run_deadline: Optional[float] = None

    def _set_phase_status(self, phase: str) -> None:
        self._status = _PHASE_TO_STATUS.get(phase, RunStatus.RUNNING_MAIN)

    def _ensure_tree(self) -> None:
        from mctsextent.main import filter_empty_sequences
        from seqscout.global_var import Model
        if Model.get_data() is None:
            filtered_data = filter_empty_sequences(self._data)
            Model.set_data(filtered_data)
            Model.set_target_class(self._target_class)

        if self._root_node is not None:
            return
        self._data, self._root_node, self._sorted_patterns, self._node_hashmap, self._item_log_losses, self._stats = (
            init_mcts_tree(self._data, self._target_class, self._log_losses, self.top_k, self.theta)
        )
        if "total_elapsed_time" not in self._stats:
            self._stats["total_elapsed_time"] = 0.0
        if "anytime_quality_history" not in self._stats:
            self._stats["anytime_quality_history"] = [[0.0, 0.0]]

    def _worker(self) -> None:
        self._ensure_tree()
        assert self._wall_begin is not None

        while True:
            # If we are about to pause (pause event is cleared), clear LRU caches and run GC.
            if not self._pause_event.is_set():
                try:
                    from general.utils import compute_quality, compute_sequence_expand, compute_cumulative_probs
                    compute_quality.cache_clear()
                    compute_sequence_expand.cache_clear()
                    compute_cumulative_probs.cache_clear()
                    import gc
                    gc.collect()
                    print("[INFO] Garbage collection run and MCTS caches cleared on pause wait.")
                except Exception as e:
                    print(f"[ERROR] Failed clearing caches: {e}")

            self._pause_event.wait()
            if self._stop_event.is_set():
                self._status = RunStatus.ABORTED if self._abort_requested else RunStatus.STOPPED
                with self._lock:
                    elapsed_this_run = (datetime.datetime.now(timezone.utc) - self._wall_begin).total_seconds()
                    self._stats["total_elapsed_time"] = self._stats.get("total_elapsed_time", 0.0) + elapsed_this_run
                    best_q = 0.0
                    if self._sorted_patterns and self._sorted_patterns.heap:
                        best_q = max(p[0] for p in self._sorted_patterns.heap)
                    history = self._stats.setdefault("anytime_quality_history", [])
                    history.append([self._stats["total_elapsed_time"], best_q])
                return

            run_iteration = False
            with self._lock:
                now = time.time()
                iter_count = self._stats.get("iteration_count", 0) if self._stats else 0
                
                # Enforce deadline, BUT allow at least 10 iterations per cycle before enforcing
                # This prevents early exit when deadline might be very short or timing is tight
                if self._run_deadline is not None:
                    time_until_deadline = self._run_deadline - now
                    if time_until_deadline <= 0 and iter_count >= 10:
                        # Deadline exceeded
                        self._run_deadline = None
                        self._status = RunStatus.PAUSED
                        self._pause_event.clear()
                        if iter_count % 1000 == 0:  # Log occasionally to avoid spam
                            print(f"[DEBUG] Deadline exceeded at iteration {iter_count}, time_until_deadline={time_until_deadline:.3f}s")
                        continue
                    
                if self._stats["iteration_count"] >= self.iterations_limit:
                    self._status = RunStatus.PAUSED
                    self._pause_event.clear()
                else:
                    run_iteration = True

            if not run_iteration:
                continue

            def check_abort() -> bool:
                if self._stop_event.is_set():
                    return True
                # Only check deadline during iteration if we've done many iterations (graceful termination)
                iter_count = self._stats.get("iteration_count", 0) if self._stats else 0
                if self._run_deadline is not None and time.time() >= self._run_deadline and iter_count >= 50:
                    return True
                # Circuit breaker check (with iteration count to skip early iterations)
                with self._lock:
                    node_count = len(self._node_hashmap) if self._node_hashmap is not None else 0
                if check_circuit_breaker(node_count, iteration_count=iter_count):
                    return True
                return False

            with self._lock:
                from mctsextent.main import current_node_weights
                status = mcts_one_iteration(
                    self._root_node,
                    self._sorted_patterns,
                    self._node_hashmap,
                    self._item_log_losses,
                    self._stats,
                    phase_hook=self._set_phase_status,
                    should_abort=check_abort,
                    node_weights=current_node_weights,
                )

                # Update anytime quality and elapsed time at the end of each iteration
                elapsed_this_run = (datetime.datetime.now(timezone.utc) - self._wall_begin).total_seconds()
                total_elapsed = self._stats.get("total_elapsed_time", 0.0) + elapsed_this_run
                
                best_q = 0.0
                if self._sorted_patterns and self._sorted_patterns.heap:
                    best_q = max(p[0] for p in self._sorted_patterns.heap)
                
                history = self._stats.setdefault("anytime_quality_history", [])
                if not history or best_q > history[-1][1]:
                    history.append([total_elapsed, best_q])

                if self._run_deadline is not None and time.time() >= self._run_deadline:
                    self._run_deadline = None
                    self._status = RunStatus.PAUSED
                    self._pause_event.clear()

            if status == "finished":
                # The search tree is exhausted, but we may still have time budget.
                # Keep running for the full budget unless deadline has been reached.
                if self._run_deadline is not None and time.time() >= self._run_deadline:
                    # Time budget exhausted - stop now
                    self._status = RunStatus.STOPPED
                    with self._lock:
                        elapsed_this_run = (datetime.datetime.now(timezone.utc) - self._wall_begin).total_seconds()
                        self._stats["total_elapsed_time"] = self._stats.get("total_elapsed_time", 0.0) + elapsed_this_run
                        best_q = 0.0
                        if self._sorted_patterns and self._sorted_patterns.heap:
                            best_q = max(p[0] for p in self._sorted_patterns.heap)
                        history = self._stats.setdefault("anytime_quality_history", [])
                        history.append([self._stats["total_elapsed_time"], best_q])
                    return
                else:
                    # Budget still available - keep searching
                    # Reset the search by allowing dead-end exploration
                    self._stats["iteration_count"] += 1  # Track that we tried to continue
                    if self._stats.get("iteration_count", 0) % 100 == 0:
                        print(f"[INFO] Search tree exhausted at iteration {self._stats['iteration_count']}, continuing with budget...")
                    continue
            if status == "aborted":
                if self._stop_event.is_set():
                    self._status = RunStatus.ABORTED if self._abort_requested else RunStatus.STOPPED
                    with self._lock:
                        elapsed_this_run = (datetime.datetime.now(timezone.utc) - self._wall_begin).total_seconds()
                        self._stats["total_elapsed_time"] = self._stats.get("total_elapsed_time", 0.0) + elapsed_this_run
                        best_q = 0.0
                        if self._sorted_patterns and self._sorted_patterns.heap:
                            best_q = max(p[0] for p in self._sorted_patterns.heap)
                        history = self._stats.setdefault("anytime_quality_history", [])
                        history.append([self._stats["total_elapsed_time"], best_q])
                    return
                else:
                    self._status = RunStatus.PAUSED
                    self._pause_event.clear()
                    with self._lock:
                        elapsed_this_run = (datetime.datetime.now(timezone.utc) - self._wall_begin).total_seconds()
                        self._stats["total_elapsed_time"] = self._stats.get("total_elapsed_time", 0.0) + elapsed_this_run
                        best_q = 0.0
                        if self._sorted_patterns and self._sorted_patterns.heap:
                            best_q = max(p[0] for p in self._sorted_patterns.heap)
                        history = self._stats.setdefault("anytime_quality_history", [])
                        history.append([self._stats["total_elapsed_time"], best_q])
                    continue

    @property
    def status(self) -> RunStatus:
        return self._status

    @property
    def budget_remaining(self) -> int:
        with self._lock:
            return self._budget_remaining

    def add_budget(self, budget: int) -> None:
        with self._lock:
            self._budget_remaining += int(budget)

    def apply_focus(self, params: Optional[Dict[str, Any]] = None, weights: Optional[Dict[str, Any]] = None) -> None:
        """Apply focus settings and AuditLens weights before a new budget run."""
        reset_tree = False
        if params is not None:
            if "max_gap" in params and params["max_gap"] is not None:
                try:
                    new_max_gap = int(params["max_gap"])
                    if getattr(conf, "MAX_GAP", None) != new_max_gap:
                        conf.MAX_GAP = new_max_gap
                        reset_tree = True
                except Exception:
                    pass
            if "uct_factor" in params and params["uct_factor"] is not None:
                try:
                    conf.UCT_FACTOR = float(params["uct_factor"])
                except Exception:
                    pass
            
            new_gamma = None
            if "gamma" in params and params["gamma"] is not None:
                new_gamma = float(params["gamma"])
            elif "support_penalty" in params and params["support_penalty"] is not None:
                new_gamma = float(params["support_penalty"])
                
            if new_gamma is not None:
                try:
                    if getattr(conf, "SUPPORT_PENALTY", None) != new_gamma:
                        conf.SUPPORT_PENALTY = new_gamma
                        reset_tree = True
                except Exception:
                    pass

            if "min_support" in params and params["min_support"] is not None:
                try:
                    new_min_support = int(params["min_support"])
                    if getattr(conf, "MIN_SUPPORT", None) != new_min_support:
                        conf.MIN_SUPPORT = new_min_support
                        reset_tree = True
                except Exception:
                    pass

        if reset_tree:
            print("[INFO] Parameter change detected (max_gap, gamma, or min_support). Re-loading data and resetting MCTS tree...")
            with self._lock:
                from mctsextent.main import prepare_mcts_from_files, filter_empty_sequences
                from seqscout.global_var import Model
                
                # Re-load data
                self._data, self._target_class, self._log_losses, self.extra, self.encoding_to_items = (
                    prepare_mcts_from_files(
                        self.filename,
                        max_gap=getattr(conf, "MAX_GAP", 1),
                        support_penalty=getattr(conf, "SUPPORT_PENALTY", 0.0),
                        sigmoid_offset=getattr(conf, "SIGMOID_OFFSET", 2.0),
                        synth_patterns_path=self.synth_patterns_path,
                    )
                )
                Model.set_data(filter_empty_sequences(self._data))
                Model.set_target_class(self._target_class)

                self._root_node = None
                self._sorted_patterns = None
                self._node_hashmap = None
                self._item_log_losses = None
                self._stats = None
                self._status = RunStatus.IDLE
                # Clear LRU caches
                try:
                    from general.utils import compute_quality, compute_sequence_expand, compute_cumulative_probs
                    compute_quality.cache_clear()
                    compute_sequence_expand.cache_clear()
                    compute_cumulative_probs.cache_clear()
                except Exception:
                    pass

        # Handle weights cleanly
        if weights:
            if isinstance(weights, str):
                try:
                    import json
                    weights = json.loads(weights)
                except Exception:
                    pass
            
            if isinstance(weights, dict):
                # If weights contains quality or support keys, update algorithm_weights in mcts_main
                import mctsextent.main as mcts_main
                mcts_main.algorithm_weights = {
                    "quality": float(weights.get("quality", 1.0)),
                    "support": float(weights.get("support", 0.0))
                }
                
                # Also treat standard focus weights if present
                if any(k in weights for k in ("nodes", "patterns", "attributes")):
                    apply_auditlens_weights(weights)
                else:
                    # If it's a direct dictionary of pattern_descriptor -> weight (but excluding algorithm weights keys)
                    pattern_weights = {k: v for k, v in weights.items() if k not in ("quality", "support")}
                    if pattern_weights:
                        apply_auditlens_weights({"patterns": pattern_weights})
                    else:
                        from auditlens_weights import reset_weights
                        reset_weights()
            else:
                from auditlens_weights import reset_weights
                reset_weights()
                import mctsextent.main as mcts_main
                mcts_main.algorithm_weights = {"quality": 1.0, "support": 0.0}
        else:
            from auditlens_weights import reset_weights
            reset_weights()
            import mctsextent.main as mcts_main
            mcts_main.algorithm_weights = {"quality": 1.0, "support": 0.0}

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
                    "explored_nodes": len(self._node_hashmap) if self._node_hashmap is not None else 0,
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
                "explored_nodes": len(self._node_hashmap) if self._node_hashmap is not None else 0,
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

        begin = self._wall_begin or datetime.datetime.now(timezone.utc)
        runtime_seconds = (datetime.datetime.now(timezone.utc) - begin).total_seconds()

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

    def run(
        self,
        iterations: Optional[int] = None,
        budget: Optional[int] = None,
        time_budget: Optional[float] = None,
    ) -> None:
        """
        Start or resume the background search.
        If ``iterations`` is set, increases the iteration cap.
        If ``budget`` is set, adds budget units that will be consumed one per iteration.
        If ``time_budget`` is set, the worker will execute for that many seconds and pause.
        """
        if iterations is not None:
            self.iterations_limit += int(iterations)
        if budget is not None:
            self.add_budget(int(budget))

        # Always reset wall clock and deadline so elapsed tracking is per-cycle,
        # not cumulative across budget cycles.
        self._wall_begin = datetime.datetime.now(timezone.utc)
        if time_budget is not None:
            self.time_budget = float(time_budget)
        self._run_deadline = time.time() + self.time_budget

        self._abort_requested = False
        self._stop_event.clear()
        self._pause_event.set()

        if self._thread is not None and self._thread.is_alive():
            self._status = RunStatus.RUNNING_MAIN
            return

        self._status = RunStatus.RUNNING_MAIN
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def wait_for_pause(self, poll_interval: float = 0.1, timeout: Optional[float] = None) -> RunStatus:
        """
        Block until the background worker pauses, stops, or aborts.
        This ensures the time-budget run completes before the connector sends the cycle snapshot.
        """
        start = datetime.datetime.now(timezone.utc)
        while True:
            status = self.status
            if status in (RunStatus.PAUSED, RunStatus.STOPPED, RunStatus.ABORTED):
                return status
            if timeout is not None and (datetime.datetime.now(timezone.utc) - start).total_seconds() >= timeout:
                return status
            time.sleep(poll_interval)

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

    def get_pareto_frontier(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not self._node_hashmap:
                return []
            
            # 1. Gather all nodes with computed quality > 0
            nodes_data = []
            total_data_size = len(self._data) if self._data else 1000
            
            for seq, node in self._node_hashmap.items():
                if node._quality is not None and node._quality > 0:
                    support_pct = (len(node.extend) / total_data_size) * 100.0
                    nodes_data.append((node._quality, support_pct, seq))
            
            if not nodes_data:
                return []
            
            # 2. Sort nodes by quality descending, then support percentage descending
            nodes_data.sort(key=lambda x: (x[0], x[1]), reverse=True)
            
            # 3. Compute 2D Pareto frontier (non-dominated nodes)
            pareto = []
            max_support_seen = -1.0
            
            for quality, support_pct, seq in nodes_data:
                if support_pct > max_support_seen:
                    max_support_seen = support_pct
                    desc = decode_sequence(seq, self.encoding_to_items)
                    try:
                        pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in desc])
                    except Exception:
                        pattern_str = str(desc)
                    pareto.append({
                        "quality": quality,
                        "support_percentage": support_pct,
                        "descriptor": pattern_str
                    })
            
            # Sort by support percentage ascending for visualization
            pareto.sort(key=lambda x: x["support_percentage"])
            return pareto

    def get_feature_importance(self) -> Dict[str, float]:
        with self._lock:
            if not self._node_hashmap:
                return {}
            
            # 1. Gather all nodes with computed quality > 0
            nodes = [node for node in self._node_hashmap.values() if node._quality is not None and node._quality > 0]
            if not nodes:
                return {}
            
            # 2. Sort by quality descending and take Top 5% (at least 5 nodes, at most all)
            nodes.sort(key=lambda x: x._quality, reverse=True)
            k = max(5, int(len(nodes) * 0.05))
            top_nodes = nodes[:k]
            
            # 3. Count occurrences of each item in the top nodes' sequences
            from collections import Counter
            item_counts = Counter()
            
            for node in top_nodes:
                if not node.intent:
                    continue
                # Unique items in this sequence
                seq_items = set()
                for itemset in node.intent:
                    for item in itemset:
                        seq_items.add(item)
                for item in seq_items:
                    item_counts[item] += 1
            
            # 4. Decode item IDs to names and convert to ratio
            importance = {}
            for item_id, count in item_counts.items():
                decoded_name = self.encoding_to_items.get(item_id, str(item_id)) if self.encoding_to_items else str(item_id)
                importance[decoded_name] = count / len(top_nodes)
                
            # Sort by importance descending
            importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            return importance

    def get_depth_histogram(self) -> List[int]:
        with self._lock:
            if not self._node_hashmap:
                return []
            
            # Get depths of all nodes
            depths = [node.depth for node in self._node_hashmap.values()]
            if not depths:
                return []
            
            max_depth = max(depths)
            histogram = [0] * (max_depth + 1)
            for d in depths:
                histogram[d] += 1
                
            return histogram

    def get_path_diversity(self) -> float:
        with self._lock:
            if not self._root_node or not self._root_node.children:
                return 0.0
            
            visits = [child.number_visits for child in self._root_node.children]
            total_visits = sum(visits)
            if total_visits <= 0:
                return 0.0
            
            import math
            entropy = 0.0
            for v in visits:
                p = v / total_visits
                if p > 0:
                    entropy -= p * math.log2(p)
            return entropy

    def get_anytime_quality(self) -> List[List[float]]:
        with self._lock:
            if self._stats is None:
                return []
            return self._stats.get("anytime_quality_history", [])

    def get_search_space_diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            if not self._node_hashmap:
                return {
                    "dead_end_ratio": 0.0,
                    "total_nodes": 0,
                    "dead_end_nodes": 0,
                    "min_support_active": conf.MIN_SUPPORT,
                }
            
            dead_ends = sum(1 for node in self._node_hashmap.values() if node.dead_end)
            total = len(self._node_hashmap)
            
            try:
                from mctsextent.main import _min_support_override
                min_support_active = _min_support_override if _min_support_override is not None else conf.MIN_SUPPORT
            except Exception:
                min_support_active = conf.MIN_SUPPORT
            
            return {
                "dead_end_ratio": dead_ends / total if total > 0 else 0.0,
                "total_nodes": total,
                "dead_end_nodes": dead_ends,
                "min_support_active": min_support_active,
            }

    def get_non_redundant_patterns(self) -> List[PatternInfo]:
        with self._lock:
            if not self._sorted_patterns or not self._sorted_patterns.heap:
                return []
            
            extra = dict(self.extra)
            extra["iteration_count"] = self._stats["iteration_count"] if self._stats else 0
            extra["phase_hook"] = self._set_phase_status
            
            prev_status = self._status
            try:
                from general.priorityset import filter_results
                results = filter_results(
                    self._sorted_patterns.heap,
                    self._data,
                    self._sorted_patterns.theta,
                    self.top_k,
                    extra=extra
                )
            except Exception as e:
                print(f"[ERROR] failed filtering non-redundant patterns: {e}")
                results = heapq.nlargest(self.top_k, self._sorted_patterns.heap)
            finally:
                self._status = prev_status
                
            out: List[PatternInfo] = []
            for item in results:
                if len(item) == 5:
                    quality, seq, extend, pattern_delta, corr_p = item
                else:
                    quality, seq, extend, pattern_delta = item
                    corr_p = 0.0
                out.append(PatternInfo(quality, seq, extend, pattern_delta, self.encoding_to_items, p_value_bh=corr_p))
            return out

    def save_state(self, path: Optional[str] = None) -> str:
        """Save tree state to disk for resumption."""
        if path is None:
            os.makedirs(self.state_dir, exist_ok=True)
            path = os.path.join(self.state_dir, f"{self.filename}_state.pkl")
        
        with self._lock:
            state = {
                "root_node": self._root_node,
                "sorted_patterns": self._sorted_patterns,
                "node_hashmap": self._node_hashmap,
                "stats": self._stats,
                "item_log_losses": self._item_log_losses,
            }
            with open(path, "wb") as f:
                pickle.dump(state, f)
        return path

    def load_state(self, path: Optional[str] = None) -> bool:
        """Load tree state from disk. Returns True if successful."""
        if path is None:
            path = os.path.join(self.state_dir, f"{self.filename}_state.pkl")
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, "rb") as f:
                state = pickle.load(f)
            
            with self._lock:
                self._root_node = state.get("root_node")
                self._sorted_patterns = state.get("sorted_patterns")
                self._node_hashmap = state.get("node_hashmap")
                self._stats = state.get("stats")
                self._item_log_losses = state.get("item_log_losses")
                if self._stats is not None:
                    if "total_elapsed_time" not in self._stats:
                        self._stats["total_elapsed_time"] = 0.0
                    if "anytime_quality_history" not in self._stats:
                        self._stats["anytime_quality_history"] = [[0.0, 0.0]]
            
            from mctsextent.main import filter_empty_sequences
            from seqscout.global_var import Model
            Model.set_data(filter_empty_sequences(self._data))
            Model.set_target_class(self._target_class)
            
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False
