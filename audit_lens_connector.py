import time
import requests
import json
import threading
from datetime import datetime, timezone
from api import MCTS, RunStatus
import mctsextent.main as mcts_main
import general.conf as conf
from auditlens_weights import apply_auditlens_weights, get_weight_manager, focus_on_attributes

AUDITLENS_API_BASE = "http://localhost:8001"
CONNECTOR_VERSION = "1.0"

def log_info(message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] [{timestamp}] [Connector] {message}")

def serialize_pattern(pattern, max_gap=1, total_data_size=1000):
    """Serialize pattern to AuditLens format."""
    if hasattr(pattern, 'to_dict'):
        pat_data = pattern.to_dict()
    elif isinstance(pattern, dict):
        pat_data = pattern
    else:
        pat_data = {}
        for a in dir(pattern):
            if not a.startswith('_') and not callable(getattr(pattern, a)):
                pat_data[a] = getattr(pattern, a)

    quality = pat_data.get("quality", 0.0)
    support = pat_data.get("support", 0)
    support_pct = (support / total_data_size * 100.0) if total_data_size else 0.0
    
    desc_raw = pat_data.get("descriptor", [])
    if isinstance(desc_raw, str):
        pattern_str = desc_raw
        sequence = [{"itemset": [desc_raw], "gap_before": 0}]
    else:
        try:
            pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in desc_raw])
        except Exception:
            pattern_str = str(desc_raw)
        sequence = [
            {"itemset": list(itemset), "gap_before": 0 if idx == 0 else int(max_gap)}
            for idx, itemset in enumerate(desc_raw)
        ]

    err_c0 = pat_data.get("error_class_0", 0.0)
    err_c1 = pat_data.get("error_class_1", 0.0)
    std_c0 = pat_data.get("std_class_0", 0.05)
    std_c1 = pat_data.get("std_class_1", 0.05)
    size_c0 = pat_data.get("size_class_0", 0)
    size_c1 = pat_data.get("size_class_1", 0)
    
    sup = support or (size_c0 + size_c1)
    class_balance = (size_c0 / sup) if sup > 0 else 0.5
    
    delta_g = abs(err_c0 - err_c1)
    max_std = max(std_c0, std_c1)
    separation = delta_g / (1.0 + max_std**2)
    deviation = max(abs(err_c0 - 0.3), abs(err_c1 - 0.32))
    support_penalty = pat_data.get("support_penalty", 1.0)

    return {
        "id": pattern_str or f"p-{support}",
        "quality_score": float(quality),
        "attributes": {
            "support": int(sup),
            "complexity": float(len(sequence)),
            "separation": float(separation),
            "deviation": float(deviation),
            "class_balance": float(class_balance),
            "support_penalty_pgB": float(support_penalty),
            "delta_g": float(delta_g),
            "error_class_0": float(err_c0),
            "error_class_1": float(err_c1),
            "mean_error_mu": float((err_c0 * size_c0 + err_c1 * size_c1) / sup) if sup > 0 else float(err_c0),
            "std_error_sigma": float(max_std),
            "p_value_bh": float(pat_data.get("p_value_bh", 0.0)),
            "support_percentage": float(support_pct)
        },
        "example_slice": {
            "errors_class_0": [err_c0] * min(size_c0 or 10, 50),
            "errors_class_1": [err_c1] * min(size_c1 or 10, 50),
            "sequence": sequence
        }
    }

def send_snapshot(mcts_worker, status, elapsed, total_data_size, global_errors_c0, global_errors_c1, iterations_since_last=0):
    """Send snapshot to AuditLens and receive updated params/weights."""
    try:
        stats = mcts_worker.queue_stats()
        if status in ("paused", "finished"):
            log_info("Filtering non-redundant and statistically significant patterns...")
            patterns_raw = mcts_worker.get_non_redundant_patterns()
            log_info(f"Filtered to {len(patterns_raw)} final non-redundant significant patterns.")
        else:
            patterns_raw = mcts_worker.patterns[:50]
        
        serialized_patterns = []
        max_gap = getattr(conf, "MAX_GAP", 1)
        for p in patterns_raw:
            try:
                serialized_patterns.append(serialize_pattern(p, max_gap, total_data_size))
            except Exception as e:
                log_info(f"Error serializing pattern: {e}")
                
        avg_error = 0.0
        try:
            from seqscout.global_var import Model
            avg_error = float(Model.get_global_mean_error() or 0.0)
        except Exception:
            pass
            
        top_quality = serialized_patterns[0]["quality_score"] if serialized_patterns else 0.0
        explored_nodes = stats.get("explored_nodes", 0)
        search_space = getattr(mcts_worker, "iterations_limit", 50000)
        
        # Calculate dynamic rollout success rate and stability
        rollout_count = mcts_worker._stats.get("rollout_count", 0) if mcts_worker._stats else 0
        rollout_success_count = mcts_worker._stats.get("rollout_success_count", 0) if mcts_worker._stats else 0
        rollout_success_rate = rollout_success_count / rollout_count if rollout_count > 0 else 1.0
        stability = mcts_worker._stats.get("iteration_count", 0) - mcts_worker._stats.get("last_gain_iteration", 0) if mcts_worker._stats else 0
        explored_rate = iterations_since_last / elapsed if elapsed > 0 else 0.0

        metrics = {
            "iteration_count": stats.get("iteration_count", 0),
            "avg_error": avg_error,
            "tree_progress": min(1.0, explored_nodes / max(1, search_space)),
            "top_quality": top_quality,
            "explored_nodes": explored_nodes,
            "search_space": search_space,
            "explored_rate": explored_rate,
            "stability": stability,
            "rollout_success_rate": rollout_success_rate,
            "global_errors_class_0": global_errors_c0,
            "global_errors_class_1": global_errors_c1,
            
            # Config / Hyperparameters
            "uct_factor": float(getattr(conf, "UCT_FACTOR", 1.2)),
            "support_penalty": float(getattr(conf, "SUPPORT_PENALTY", 0.5)),
            "max_gap": int(getattr(conf, "MAX_GAP", 5)),
            
            # Tree / Search stats
            "max_depth": int(mcts_worker._stats.get("max_depth_reached", 0)) if mcts_worker._stats else 0,
            "total_elapsed_time": float(mcts_worker._stats.get("total_elapsed_time", 0.0)) if mcts_worker._stats else 0.0,

            # New Telemetry Metrics
            "pareto_frontier": mcts_worker.get_pareto_frontier(),
            "feature_importance": mcts_worker.get_feature_importance(),
            "depth_histogram": mcts_worker.get_depth_histogram(),
            "anytime_quality": mcts_worker.get_anytime_quality(),
            "path_diversity": mcts_worker.get_path_diversity(),
            "search_space_diagnostics": mcts_worker.get_search_space_diagnostics(),
        }

        payload = {
            "metrics": metrics,
            "patterns": serialized_patterns,
            "status": status,
            "consume": float(elapsed),
        }
        
        resp = requests.post(f"{AUDITLENS_API_BASE}/api/snapshots", json=payload, timeout=5)
        if resp.status_code == 200:
            resp_data = resp.json()
            
            # Update params dynamically
            params = resp_data.get("params", {})
            if "gamma" in params:
                conf.SUPPORT_PENALTY = float(params["gamma"])
            if "max_gap" in params:
                conf.MAX_GAP = int(params["max_gap"])
            if "uct_factor" in params:
                conf.UCT_FACTOR = float(params["uct_factor"])
            
            # Apply weights with priority handling
            if "weights" in params and params["weights"]:
                weights = params["weights"]
                
                # If the dict does not have our standard keys but has keys/values, treat it as a patterns dict!
                if isinstance(weights, dict) and not any(k in weights for k in ("nodes", "patterns", "attributes")):
                    weights = {"patterns": weights}
                
                # Method 1: Direct node weights (map node id -> weight)
                if isinstance(weights, dict):
                    if "nodes" in weights or "patterns" in weights or "attributes" in weights:
                        apply_auditlens_weights(weights)
                    elif all(isinstance(v, (int, float)) for v in weights.values()):
                        # Legacy format: direct node_id -> weight mapping
                        mcts_main.current_node_weights = {int(k): float(v) for k, v in weights.items()}
                        log_info(f"Applied {len(weights)} node weights")
                
                # Method 2: Attribute-based weights
                if "attributes" in params:
                    attr_weights = params["attributes"]
                    focus_on_attributes(attr_weights)
                    log_info(f"Applied attribute weights: {list(attr_weights.keys())}")
            else:
                from auditlens_weights import reset_weights
                reset_weights()
            
            log_info(f"Snapshot sent successfully. Iteration={metrics['iteration_count']}, RemainingBudget={resp_data.get('remaining_budget', 0.0):.1f}")
            return resp_data.get("remaining_budget", 0.0), resp_data.get("run_status", "running")
        else:
            log_info(f"Failed to send snapshot: {resp.status_code}")
    except Exception as e:
        log_info(f"Error sending snapshot: {e}")
    return 0.0, "paused"

def run_budget_cycle(mcts_worker, budget_seconds: float, total_data_size: int, global_errors_c0: list, global_errors_c1: list, last_snapshot_iteration: int) -> tuple:
    """Run the model for the requested time budget and send periodic intermediate snapshots."""
    if budget_seconds <= 0:
        return mcts_worker.status, time.time(), last_snapshot_iteration

    log_info(f"Starting budget cycle: {budget_seconds:.2f} seconds | Current iteration: {mcts_worker.iteration_count}")
    cycle_start_absolute = time.time()
    # Ensure iterations_limit is increased so the worker does not immediately pause
    # when the current iteration count already reached the configured cap.
    try:
        mcts_worker.run(iterations=10**10, time_budget=budget_seconds)
    except TypeError:
        # Fallback: older API may not accept iterations param; call without it
        mcts_worker.run(time_budget=budget_seconds)
    
    start_time = time.time()
    last_snapshot_time = start_time
    SNAPSHOT_INTERVAL_SECS = 2.0  # Send running snapshot every 2 seconds
    
    while True:
        status = mcts_worker.status
        if status in (RunStatus.PAUSED, RunStatus.STOPPED, RunStatus.ABORTED):
            elapsed_actual = time.time() - cycle_start_absolute
            log_info(f"Budget cycle completed: Status={status.name}, Elapsed={elapsed_actual:.2f}s (budget was {budget_seconds:.2f}s), Iterations={mcts_worker.iteration_count}")
            return status, last_snapshot_time, last_snapshot_iteration
            
        now = time.time()
        elapsed = now - start_time
        if elapsed >= budget_seconds:
            log_info(f"Budget time reached ({elapsed:.2f}s >= {budget_seconds:.2f}s). Pausing execution...")
            mcts_worker.pause()
            mcts_worker.wait_for_pause(timeout=5.0)
            elapsed_actual = time.time() - cycle_start_absolute
            log_info(f"Pause completed after {elapsed_actual:.2f}s total, Status={mcts_worker.status.name}")
            return mcts_worker.status, last_snapshot_time, last_snapshot_iteration
            
        # Send intermediate snapshots
        elapsed_since_last_snap = now - last_snapshot_time
        if elapsed_since_last_snap >= SNAPSHOT_INTERVAL_SECS:
            current_iter = mcts_worker.iteration_count
            if current_iter > last_snapshot_iteration:
                iters_diff = current_iter - last_snapshot_iteration
                send_snapshot(
                    mcts_worker,
                    "running",
                    elapsed_since_last_snap,
                    total_data_size,
                    global_errors_c0,
                    global_errors_c1,
                    iterations_since_last=iters_diff
                )
                last_snapshot_time = now
                last_snapshot_iteration = current_iter
            
        # Check backend config for early pause request
        try:
            resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=0.5)
            if resp.status_code == 200:
                config = resp.json()
                if config.get("status") in ("paused", "idle"):
                    log_info("Early pause requested by AuditLens. Pausing execution...")
                    mcts_worker.pause()
                    mcts_worker.wait_for_pause(timeout=5.0)
                    return mcts_worker.status, last_snapshot_time, last_snapshot_iteration
        except Exception:
            pass
            
        time.sleep(0.1)  # Poll more frequently for responsiveness

def main():
    log_info("Starting MCTS Extent with AuditLens integration...")
    
    # Initialize MCTS
    mcts_worker = MCTS(
        filename="synth_temp",
        top_k=50,
        iterations_limit=10000,
        time_budget=3600
    )
    
    # Try loading previous state
    if mcts_worker.load_state():
        log_info("Loaded previous MCTS state")
    else:
        log_info("Starting fresh MCTS tree")
    
    # Prepare global metrics
    total_data_size = 1000
    global_errors_c0 = []
    global_errors_c1 = []
    
    try:
        from seqscout.global_var import Model
        total_data = Model.get_data()
        if total_data:
            total_data_size = len(total_data)
        
        soft_errors = Model.get_soft_errors()
        target_class = Model.get_target_class()
        if soft_errors is not None and target_class is not None:
            import numpy as np
            y_true = target_class[:, 0]
            global_errors_c0 = list(map(float, soft_errors[y_true == 0]))
            global_errors_c1 = list(map(float, soft_errors[y_true == 1]))
    except Exception as e:
        log_info(f"Warning: Could not retrieve baseline data: {e}")

    last_known_weights = None
    last_known_params = {}
    last_snapshot_iteration = -1  # Guard: track the last snapshot iteration to prevent duplicates
    MIN_CYCLE_SECONDS = 0.5  # Guard: minimum real time for a valid budget cycle (relaxed from 2.0)
    last_status_sent = None

    log_info("Connecting to AuditLens...")
    
    connected = False
    while not connected:
        try:
            resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=1)
            if resp.status_code == 200:
                connected = True
                log_info("Connected to AuditLens")
        except Exception:
            pass
        if not connected:
            time.sleep(0.5)

    log_info("Initialized in IDLE state. Waiting for audit command...")

    # Main loop
    try:
        while True:
            # Check config and budget
            try:
                resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=1)
                if resp.status_code == 200:
                    config = resp.json()
                    remaining_budget = config.get("remaining_budget", 0.0)
                    audit_status = config.get("status", "idle")
                else:
                    remaining_budget = 0.0
                    audit_status = "idle"
            except Exception:
                remaining_budget = 0.0
                audit_status = "idle"

            current_model_status = mcts_worker.status
            is_running = current_model_status not in (
                RunStatus.IDLE,
                RunStatus.PAUSED,
                RunStatus.STOPPED,
                RunStatus.ABORTED,
            )

            weights = config.get("weights")
            params = {
                "max_gap": config.get("max_gap"),
                "gamma": config.get("gamma"),
                "uct_factor": config.get("uct_factor"),
                "support_penalty": config.get("support_penalty"),
                "min_support": config.get("min_support"),
            }

            # Update focus and weights
            if weights != last_known_weights or params != last_known_params:
                log_info("AuditLens updated focus/params for next budget cycle")
                mcts_worker.apply_focus(params=params, weights=weights)
                last_known_weights = json.loads(json.dumps(weights)) if weights else None
                last_known_params = dict(params)

            # Start a new budgeted run ONLY if the status is "running" and remaining_budget > 0
            if audit_status == "running" and remaining_budget > 0 and not is_running:
                last_status_sent = None
                
                if current_model_status == RunStatus.STOPPED:
                    log_info("MCTS search space is completely exhausted. Skipping budget cycle.")
                    if last_snapshot_iteration != mcts_worker.iteration_count:
                        send_snapshot(
                            mcts_worker,
                            "finished",
                            0,
                            total_data_size,
                            global_errors_c0,
                            global_errors_c1,
                        )
                        last_snapshot_iteration = mcts_worker.iteration_count
                        last_status_sent = "finished"
                    time.sleep(2.0)  # Avoid tight polling loop
                    continue
                
                print(f"[DEBUG] Executando ciclo com Budget: {remaining_budget}s | Pesos Aplicados: {weights}")
                cycle_start_time = time.time()
                initial_iterations = mcts_worker.iteration_count
                
                # Execute the budget cycle
                actual_status, last_snapshot_time, last_snapshot_iteration = run_budget_cycle(
                    mcts_worker,
                    remaining_budget,
                    total_data_size,
                    global_errors_c0,
                    global_errors_c1,
                    last_snapshot_iteration
                )
                elapsed = time.time() - cycle_start_time
                elapsed_final = max(0.0, time.time() - last_snapshot_time)
                
                mcts_worker.save_state()
                
                iterations_this_cycle = mcts_worker.iteration_count - initial_iterations
                rate = iterations_this_cycle / elapsed if elapsed > 0 else 0.0
                
                # Guard: skip snapshot if elapsed is suspiciously short or same iteration count
                # BUT bypass the guard if the algorithm legitimately finished (STOPPED or ABORTED)
                if actual_status not in (RunStatus.STOPPED, RunStatus.ABORTED):
                    current_iteration = mcts_worker.iteration_count
                    if elapsed < MIN_CYCLE_SECONDS:
                        log_info(
                            f"WARNING: Budget cycle of {remaining_budget:.0f}s completed in only "
                            f"{elapsed:.1f}s ({iterations_this_cycle} iterations). "
                            f"Skipping snapshot to prevent duplicate payload."
                        )
                        time.sleep(1.0)  # Prevent tight polling loop
                        continue
                    
                    if current_iteration == last_snapshot_iteration:
                        log_info(
                            f"WARNING: No new iterations since last snapshot "
                            f"(iteration={current_iteration}). Skipping duplicate."
                        )
                        time.sleep(1.0)
                        continue
                
                # Report paused state to AuditLens
                log_info(
                    f"Budget de {remaining_budget:.0f}s esgotado. "
                    f"Tempo Real decorrido: {elapsed:.1f}s. "
                    f"Iteracoes neste ciclo: {iterations_this_cycle} "
                    f"(Taxa: {rate:.1f} iteracoes/seg real)."
                )
                
                status_to_send = "paused" if actual_status == RunStatus.PAUSED else "finished"
                iterations_final_diff = mcts_worker.iteration_count - last_snapshot_iteration
                send_snapshot(
                    mcts_worker,
                    status_to_send,
                    elapsed_final,
                    total_data_size,
                    global_errors_c0,
                    global_errors_c1,
                    iterations_since_last=iterations_final_diff
                )
                last_snapshot_iteration = mcts_worker.iteration_count
                last_status_sent = status_to_send
                continue

            # React to explicit finalization/completion request
            if audit_status == "completed":
                if current_model_status not in (RunStatus.STOPPED, RunStatus.ABORTED):
                    log_info("Finalization requested. Pausing model and saving final state.")
                    if is_running:
                        mcts_worker.pause()
                        mcts_worker.wait_for_pause(timeout=5.0)
                    mcts_worker.save_state()
                
                if last_status_sent != "finished":
                    send_snapshot(
                        mcts_worker,
                        "finished",
                        0,
                        total_data_size,
                        global_errors_c0,
                        global_errors_c1,
                    )
                    last_snapshot_iteration = mcts_worker.iteration_count
                    last_status_sent = "finished"
                else:
                    log_info("Final snapshot already sent. Skipping duplicate.")
                
                log_info("Process finished. Remaining in waiting loop.")
                
                # Wait in completed loop until status changes
                while True:
                    try:
                        resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=1)
                        if resp.status_code == 200 and resp.json().get("status") != "completed":
                            break
                    except Exception:
                        pass
                    time.sleep(1.0)
                continue

            time.sleep(0.5)

    except KeyboardInterrupt:
        log_info("Interrupted by user. Pausing and saving state...")
        mcts_worker.pause()
        mcts_worker.wait_for_pause(timeout=5.0)
        mcts_worker.save_state()
        send_snapshot(
            mcts_worker,
            "paused",
            0,
            total_data_size,
            global_errors_c0,
            global_errors_c1,
        )
        print("[Connector] State saved.")

if __name__ == "__main__":
    main()