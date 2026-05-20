import time
import requests
import random
from api import MCTS, RunStatus
import general.conf as conf

AUDITLENS_API_BASE = "http://localhost:8001"
UPDATE_INTERVAL = 10  # Send snapshot every X iterations

def serialize_pattern(pattern, max_gap=1, total_data_size=1000):
    """
    Serializes a pattern object dynamically into the dictionary structure expected by AuditLens.
    This function uses reflection to remain generic and independent of MCTSExtent details.
    """
    if hasattr(pattern, 'to_dict') and callable(pattern.to_dict):
        pat_data = pattern.to_dict()
    elif isinstance(pattern, dict):
        pat_data = pattern
    else:
        pat_data = {}
        for a in dir(pattern):
            if not a.startswith('_') and not callable(getattr(pattern, a)):
                pat_data[a] = getattr(pattern, a)

    # Extract quality score
    quality = pat_data.get("quality") or pat_data.get("quality_score") or 0.0
    
    # Extract support and support percentage
    support = pat_data.get("support") or pat_data.get("support_count") or 0
    support_pct = pat_data.get("support_percentage") or ((support / total_data_size) * 100.0 if total_data_size else 0.0)
    
    # Extract sequence descriptor
    desc_raw = pat_data.get("descriptor") or pat_data.get("pattern_descriptor") or []
    
    # Format sequence descriptor as string and list of dicts for visualization
    if isinstance(desc_raw, str):
        pattern_str = desc_raw
        sequence = [{"itemset": [desc_raw], "gap_before": 0}]
    else:
        try:
            pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in desc_raw])
        except Exception:
            pattern_str = str(desc_raw)
            
        sequence = []
        for idx, itemset in enumerate(desc_raw):
            sequence.append({
                "itemset": list(itemset),
                "gap_before": 0 if idx == 0 else int(max_gap)
            })

    # Extract class-specific errors/sizes
    err_c0 = pat_data.get("error_class_0") or 0.0
    err_c1 = pat_data.get("error_class_1") or 0.0
    std_c0 = pat_data.get("std_class_0") or 0.05
    std_c1 = pat_data.get("std_class_1") or 0.05
    size_c0 = pat_data.get("size_class_0") or 0
    size_c1 = pat_data.get("size_class_1") or 0
    
    sup = support or (size_c0 + size_c1)
    class_balance = pat_data.get("class_balance") or ((size_c0 / sup) if sup > 0 else 0.5)
    
    # Calculate delta_g and separation dynamically
    delta_g = pat_data.get("delta_g") or abs(err_c0 - err_c1)
    max_std = max(std_c0, std_c1)
    separation = pat_data.get("separation") or (delta_g / (1.0 + max_std**2))
    
    deviation = pat_data.get("deviation") or max(abs(err_c0 - 0.3), abs(err_c1 - 0.32))
    support_penalty = pat_data.get("support_penalty") or pat_data.get("support_penalty_pgB") or 1.0

    # Generate normal-distribution errors around class means for visual KDE plot compatibility
    errors_c0 = [random.gauss(err_c0, std_c0) for _ in range(min(size_c0 or 50, 100))]
    errors_c1 = [random.gauss(err_c1, std_c1) for _ in range(min(size_c1 or 50, 100))]

    return {
        "id": pattern_str or f"p-{random.randint(1000, 9999)}",
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
            "p_value_bh": float(pat_data.get("p_value_bh") or 0.0),
            "support_percentage": float(support_pct)
        },
        "example_slice": {
            "errors_class_0": errors_c0,
            "errors_class_1": errors_c1,
            "sequence": sequence
        }
    }

def update_connector_params(params):
    """
    Updates the global configuration variables dynamically based on AuditLens ack/current configuration.
    """
    if not params:
        return
    
    # 1. gamma -> SUPPORT_PENALTY
    if "gamma" in params:
        val = float(params["gamma"])
        if getattr(conf, "SUPPORT_PENALTY", None) != val:
            conf.SUPPORT_PENALTY = val
            print(f"  [Config] SUPPORT_PENALTY updated dynamically to: {val}")
            
    # 2. max_gap -> MAX_GAP
    if "max_gap" in params:
        val = int(params["max_gap"])
        if getattr(conf, "MAX_GAP", None) != val:
            conf.MAX_GAP = val
            print(f"  [Config] MAX_GAP updated dynamically to: {val}")
            
    # 3. uct_factor -> UCT_FACTOR
    if "uct_factor" in params:
        val = float(params["uct_factor"])
        if getattr(conf, "UCT_FACTOR", None) != val:
            conf.UCT_FACTOR = val
            print(f"  [Config] UCT_FACTOR updated dynamically to: {val}")

def send_model_snapshot(mcts_worker, status, consume_amount, total_data_size, global_errors_c0, global_errors_c1):
    """
    Sends the structured snapshot to AuditLens and handles the dynamic updates returned in parameters.
    """
    stats = mcts_worker.queue_stats()
    patterns_raw = mcts_worker.patterns
    
    # Limit to top-10 for chart performance
    serialized_patterns = []
    max_gap = getattr(conf, "MAX_GAP", 1)
    for p in patterns_raw[:10]:
        try:
            serialized_patterns.append(serialize_pattern(p, max_gap, total_data_size))
        except Exception as e:
            print(f"Error serializing pattern: {e}")
            
    avg_error = 0.0
    try:
        from seqscout.global_var import Model
        avg_error = float(Model.get_global_mean_error() or 0.0)
    except Exception:
        pass
        
    top_quality = 0.0
    if serialized_patterns:
        top_quality = serialized_patterns[0]["quality_score"]
        
    explored_nodes = stats.get("num_patterns", 0)
    
    metrics = {
        "iteration_count": stats.get("iteration_count", 0),
        "avg_error": avg_error,
        "tree_progress": min(1.0, explored_nodes / 50000.0),
        "top_quality": top_quality,
        "explored_nodes": explored_nodes,
        "search_space": 50000,
        "explored_rate": 0.0,
        "stability": 0,
        "rollout_success_rate": 1.0,
        "global_errors_class_0": global_errors_c0,
        "global_errors_class_1": global_errors_c1
    }
    
    payload = {
        "metrics": metrics,
        "patterns": serialized_patterns,
        "status": status,
        "consume": consume_amount
    }
    
    try:
        resp = requests.post(f"{AUDITLENS_API_BASE}/api/snapshots", json=payload, timeout=2)
        if resp.status_code == 200:
            resp_data = resp.json()
            params = resp_data.get("params", {})
            update_connector_params(params)
            print(f"Snapshot sent! Status: {status}, Iteration: {metrics['iteration_count']}, Remaining budget: {resp_data.get('remaining_budget')}")
            return resp_data.get("remaining_budget", 0.0), resp_data.get("run_status", "running")
        else:
            print(f"Failed to send snapshot. Status code: {resp.status_code}, Response: {resp.text}")
    except Exception as e:
        print(f"Error sending snapshot to AuditLens: {e}")
        
    return 0.0, "paused"

def main():
    mcts_worker = MCTS(
        filename="synth_temp",
        top_k=50,
        iterations_limit=1000
    )
    
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
        print(f"Error retrieving global baseline data: {e}")

    last_sent_iteration = 0
    last_check_time = time.time()
    is_paused = True

    print("Starting MCTS model worker...")
    
    try:
        while True:
            remaining_budget = 0.0
            
            # Fetch current config/status to determine if we should start/resume or remain paused
            try:
                resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=2)
                if resp.status_code == 200:
                    config_data = resp.json()
                    remaining_budget = config_data.get("remaining_budget", 0.0)
                    update_connector_params(config_data)
            except Exception as e:
                print(f"Failed to query AuditLens config (server might be starting...): {e}")
                time.sleep(1.0)
                continue

            current_time = time.time()
            elapsed = current_time - last_check_time
            last_check_time = current_time

            stats = mcts_worker.queue_stats()
            current_iter = stats.get('iteration_count', 0)
            model_status = mcts_worker.status

            if not is_paused:
                # Running loop
                budget_left, run_status = send_model_snapshot(
                    mcts_worker, 
                    "running", 
                    elapsed, 
                    total_data_size, 
                    global_errors_c0, 
                    global_errors_c1
                )
                
                # Check for termination
                if budget_left <= 0:
                    print("Budget exhausted. Pausing MCTS worker...")
                    mcts_worker.pause()
                    is_paused = True
                    send_model_snapshot(mcts_worker, "paused", 0.0, total_data_size, global_errors_c0, global_errors_c1)
                elif model_status in (RunStatus.STOPPED, RunStatus.ABORTED):
                    print("MCTS worker finished or aborted.")
                    send_model_snapshot(mcts_worker, "finished", 0.0, total_data_size, global_errors_c0, global_errors_c1)
                    break
                else:
                    # Normal iteration check
                    if (current_iter - last_sent_iteration) >= UPDATE_INTERVAL:
                        last_sent_iteration = current_iter
            else:
                # Paused loop - waiting for budget to be added
                if remaining_budget > 0:
                    print("Budget available! Resuming MCTS worker...")
                    mcts_worker.run()
                    is_paused = False
                    last_check_time = time.time()
                    send_model_snapshot(mcts_worker, "running", 0.0, total_data_size, global_errors_c0, global_errors_c1)
                else:
                    # Still paused, wait
                    time.sleep(0.5)
                    continue

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nInterrupted by user! Aborting...")
        mcts_worker.abort()
        try:
            send_model_snapshot(mcts_worker, "paused", 0.0, total_data_size, global_errors_c0, global_errors_c1)
        except Exception:
            pass

    # Finalization and saving results
    if mcts_worker.status != RunStatus.ABORTED:
        print("\nMCTS finalized. Processing results...")
        resultados = mcts_worker.finalize_results()
        print(f"\nCompleted! Total patterns found: {len(resultados)}")

if __name__ == "__main__":
    main()