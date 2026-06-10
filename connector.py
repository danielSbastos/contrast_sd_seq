"""
MCTSExtent to AuditLens Integration Middleware (Connector) Server.
This server acts as a bridge, translating AuditLens configurations and control calls
into interactive MCTS search loops, and converting queue stats/diagnostics to
visualizable AuditLens snapshots.
"""
from __future__ import annotations

import sys
import os
import json
import time
import threading
import random
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# Insert repository path to resolve imports correctly
sys.path.insert(0, '/home/vitor/projetos/contrast_sd_seq')

from api import MCTS, RunStatus
from general.utils import decode_sequence


def get_transition_feature_importance(mcts_instance):
    """
    Computes prevalence score of event transitions or individual items
    amongst the top 5% highest quality nodes in the search space.
    """
    with mcts_instance._lock:
        if not mcts_instance._node_hashmap:
            return {}

        nodes = [
            node for node in mcts_instance._node_hashmap.values()
            if node._quality is not None and node._quality > 0
        ]
        if not nodes:
            return {}

        nodes.sort(key=lambda x: x._quality, reverse=True)
        k = max(5, int(len(nodes) * 0.05))
        top_nodes = nodes[:k]

        from collections import Counter
        transition_counts = Counter()

        for node in top_nodes:
            if not node.intent:
                continue

            desc = decode_sequence(node.intent, mcts_instance.encoding_to_items)
            itemsets = [list(itemset) for itemset in desc]

            flat_items = []
            for itemset in itemsets:
                for item in itemset:
                    flat_items.append(str(item))

            for idx in range(len(flat_items) - 1):
                transition = f"{flat_items[idx]}->{flat_items[idx+1]}"
                transition_counts[transition] += 1

            if len(flat_items) == 1:
                transition_counts[flat_items[0]] += 1

        importance = {}
        for trans, count in transition_counts.items():
            importance[trans] = count / len(top_nodes)

        importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)[:20]
        )
        return importance


class MCTSConnector:
    """
    Manages MCTS instance life cycle and keeps track of active streaming loop.
    """
    def __init__(self):
        self.mcts = None
        self.domain = None
        self.dataset_path = None
        self.config = {}
        self.identity_filters = []
        self.auditlens_url = os.environ.get("AUDITLENS_URL", "http://127.0.0.1:8001")
        self.lock = threading.RLock()
        self.last_elapsed_time = 0.0

    def get_budget(self, config=None):
        if config is None:
            config = self.config or {}
        if "remaining_budget" in config:
            return float(config["remaining_budget"])
        budgets = config.get("budgets")
        if isinstance(budgets, dict):
            search_budget = budgets.get("search")
            if search_budget is not None:
                return float(search_budget)
        budget = config.get("budget")
        if budget is not None:
            return float(budget)
        return 120.0

    def prepare(self, domain, dataset_path, config, identity_filters):
        with self.lock:
            self.domain = domain
            self.dataset_path = dataset_path
            self.config = config
            self.identity_filters = identity_filters
            self.last_elapsed_time = 0.0

            # Default dataset matching based on domain
            filename = "emm_dynamic_api_call_sequence_per_malware_100_0_306"
            if domain == "toxicity":
                filename = "emm_toxicity"
            elif dataset_path:
                base = os.path.basename(dataset_path)
                stem, ext = os.path.splitext(base)
                filename = stem
                
                # Check if data files exist for this filename. If not, resolve prefix match in data/
                if not os.path.exists(f"data/{filename}.dat") and not os.path.exists(f"data/{filename}_train.dat"):
                    prefix = stem
                    if "_" in prefix:
                        parts = prefix.split("_")
                        if parts[-1] in ("test", "train", "val", "validation"):
                            prefix = "_".join(parts[:-1])
                    
                    found = False
                    for f in sorted(os.listdir("data")):
                        if f.startswith(prefix) and f.endswith(".dat"):
                            filename = f[:-4]  # strip .dat extension
                            if filename.endswith("_train"):
                                filename = filename[:-6]
                            found = True
                            break
                    
                    if not found:
                        filename = stem

            print(f"[INFO] Preparing MCTS tree using filename: {filename}")

            # Prevent double loading of dataset on initialization by setting conf values early
            import general.conf as conf_module
            if "min_support" in config:
                conf_module.MIN_SUPPORT = int(config["min_support"])
            if "max_gap" in config:
                conf_module.MAX_GAP = int(config["max_gap"])
            if "gamma" in config:
                conf_module.SUPPORT_PENALTY = float(config["gamma"])
            if "uct_factor" in config:
                conf_module.UCT_FACTOR = float(config["uct_factor"])

            self.mcts = MCTS(
                filename=filename,
                top_k=100,
                time_budget=self.get_budget(config),
                theta=float(config.get("theta", 0.1)),
                iterations_limit=int(config.get("max_iterations", 10000)),
                max_length=6,
                max_gap=config.get("max_gap", 5),
                support_penalty=config.get("gamma", 0.5),
                snapshot_callback=self.on_mcts_snapshot,
            )

            self.mcts.apply_focus(params=config)
            print(f"[DEBUG prepare] self.mcts type: {type(self.mcts)}, id: {id(self.mcts)}")
            print("[INFO] Preparation phase completed successfully.")
            return {"status": "prepared", "filename": filename}

    def start(self, config):
        with self.lock:
            if not self.mcts:
                self.prepare(
                    self.domain or "malware",
                    self.dataset_path,
                    config,
                    self.identity_filters
                )

            print(f"[DEBUG start] self.mcts type: {type(self.mcts)}, id: {id(self.mcts)}")
            self.mcts.apply_focus(params=config)
            time_budget = self.get_budget(config)
            print(f"[INFO] Triggering MCTS loop with time limit: {time_budget}s")
            self.mcts.run(time_budget=time_budget)
            return {"status": "started"}

    def control(self, action, additional_budget=None, config=None):
        if action == "update_config":
            with self.lock:
                if self.mcts:
                    self.config.update(config or {})
                    self.mcts.apply_focus(params=config)
                    return {"status": "config_updated"}
                return {"status": "error", "message": "MCTS instance not found"}

        with self.lock:
            if not self.mcts:
                return {"status": "error", "message": "MCTS instance not found"}
            mcts_instance = self.mcts

        print(f"[DEBUG control] self.mcts type: {type(mcts_instance)}, id: {id(mcts_instance)}, repr: {repr(mcts_instance)}, dir: {dir(mcts_instance)}")
        print(f"[INFO] Executing life cycle action: {action}")
        if action == "pause":
            mcts_instance.pause()
        elif action == "resume":
            try:
                if additional_budget is not None:
                    print(f"[INFO] Resuming MCTS with additional budget: {additional_budget}s")
                    mcts_instance.resume_with_budget(additional_budget, config=config)
                else:
                    budget = self.get_budget()
                    print(f"[INFO] Resuming MCTS with budget: {budget}s")
                    mcts_instance.resume_with_budget(budget, config=config)
            except Exception as e:
                print(f"[DEBUG ERROR] Exception in control resume: {e}")
                try:
                    print(f"[DEBUG info] self.mcts dict: {mcts_instance.__dict__}")
                except Exception as de:
                    print(f"[DEBUG info] self.mcts dict failed: {de}")
                import sys, traceback
                traceback.print_exc()
                raise e
        elif action == "stop":
            print("[INFO] MCTS Finalizing: compiling final results and clearing memory.")
            try:
                # 1. Stop worker (joins worker thread) and compile final results
                mcts_instance.finalize_results(stop_worker=True)
                
                # 2. Build final snapshot with finished status
                final_snapshot = self.build_snapshot(mcts_instance, "finished")
                
                # 3. Post the final snapshot to AuditLens
                url = f"{self.auditlens_url}/api/snapshots"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(final_snapshot).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=5.0) as res:
                        res.read()
                except Exception as e:
                    print(f"[WARNING] Failed sending final snapshot to AuditLens: {e}")
            except Exception as e:
                print(f"[ERROR] Failed during finalization sequence: {e}")
            finally:
                # 4. Safe memory cleanup
                with self.lock:
                    if self.mcts is mcts_instance:
                        self.mcts = None
                import gc
                gc.collect()
                print("[INFO] Safe memory cleanup completed.")
        elif action == "clear":
            mcts_instance.stop()
            with self.lock:
                if self.mcts is mcts_instance:
                    self.mcts = None
            self.last_elapsed_time = 0.0
            print("[INFO] Cleared operational state.")

        status_str = "paused"
        if mcts_instance:
            status_str = self.get_mapped_status(mcts_instance.status)
        return {"status": status_str}

    def resume_with_budget(self, additional_budget, config=None):
        with self.lock:
            if not self.mcts:
                return {"status": "error", "message": "MCTS instance not found"}

            print(f"[DEBUG resume_with_budget] self.mcts type: {type(self.mcts)}, id: {id(self.mcts)}")
            print(f"[INFO] Injecting additional budget: {additional_budget} seconds.")
            self.mcts.resume_with_budget(additional_budget, config=config)
            self.start_streaming()

            status_str = self.get_mapped_status(self.mcts.status)
            return {"status": status_str, "budget": self.mcts.time_budget}

    def get_mapped_status(self, run_status):
        status_map = {
            RunStatus.IDLE: "paused",
            RunStatus.PAUSED: "paused",
            RunStatus.STOPPED: "finished",
            RunStatus.ABORTED: "finished",
            RunStatus.RUNNING_MAIN: "running",
            RunStatus.RUNNING_ROLLOUT: "running",
            RunStatus.RUNNING_BACKPROP: "running",
            RunStatus.RUNNING_SIM: "running",
            RunStatus.RUNNING_STATS: "running",
        }
        return status_map.get(run_status, "paused")



    def on_mcts_snapshot(self, mcts_instance, status_str=None):
        if status_str is None:
            status_str = self.get_mapped_status(mcts_instance.status)
        try:
            snapshot = self.build_snapshot(mcts_instance, status_str)
            url = f"{self.auditlens_url}/api/snapshots"
            req = urllib.request.Request(
                url,
                data=json.dumps(snapshot).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3.0) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                params = response_data.get("params", {})
                if params:
                    with self.lock:
                        if self.mcts is mcts_instance:
                            self.mcts.apply_focus(params=params, weights=params.get("weights"))
        except Exception as e:
            print(f"[ERROR] Failed dispatching event-driven snapshot: {e}")

    def build_snapshot(self, mcts_instance, status_str):
        stats = mcts_instance.queue_stats()
        iteration = stats.get("iteration_count", 0)

        current_elapsed = 0.0
        if mcts_instance._stats:
            current_elapsed = mcts_instance._stats.get("total_elapsed_time", 0.0)
        consume_val = max(0.0, current_elapsed - self.last_elapsed_time)
        self.last_elapsed_time = current_elapsed

        patterns_raw = mcts_instance.get_non_redundant_patterns()

        total_samples = 1
        if mcts_instance._data:
            total_samples = len(mcts_instance._data)

        from seqscout.global_var import Model
        import numpy as np
        global_errors_c0 = []
        global_errors_c1 = []
        global_err_c0_mean = 0.3
        global_err_c1_mean = 0.32
        soft_errors = Model.get_soft_errors()
        target_class = Model.get_target_class()
        if soft_errors is not None and target_class is not None:
            y_true = target_class[:, 0]
            errs_c0 = soft_errors[y_true == 0]
            errs_c1 = soft_errors[y_true == 1]
            if len(errs_c0) > 0:
                global_err_c0_mean = float(np.mean(errs_c0))
            if len(errs_c1) > 0:
                global_err_c1_mean = float(np.mean(errs_c1))
            errs_c0_list = errs_c0.tolist()
            errs_c1_list = errs_c1.tolist()
            global_errors_c0 = random.sample(errs_c0_list, min(100, len(errs_c0_list)))
            global_errors_c1 = random.sample(errs_c1_list, min(100, len(errs_c1_list)))

        import general.conf as conf
        gamma = getattr(conf, "SUPPORT_PENALTY", 0.5)
        min_support = getattr(conf, "MIN_SUPPORT", 10)

        serialized_patterns = []
        for p in patterns_raw:
            desc = p.descriptor
            pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in desc])
            sup_pct = (p.support / total_samples) * 100.0

            err_c0 = float(p.error_class_0) if p.error_class_0 is not None else 0.0
            err_c1 = float(p.error_class_1) if p.error_class_1 is not None else 0.0
            std_c0 = float(p.std_class_0) if p.std_class_0 is not None else 0.05
            std_c1 = float(p.std_class_1) if p.std_class_1 is not None else 0.05
            size_c0 = int(p.size_class_0 or 0)
            size_c1 = int(p.size_class_1 or 0)
            
            delta_g = abs(err_c0 - err_c1)
            max_std = max(std_c0, std_c1)
            separation = delta_g / (1.0 + max_std**2)
            deviation = max(abs(err_c0 - global_err_c0_mean), abs(err_c1 - global_err_c1_mean))
            class_balance = float(size_c0 / p.support) if p.support > 0 else 0.5
            
            # Simple approximation for frontend visualization purposes
            support_penalty = min(1.0, (p.support / min_support) ** gamma) if p.support > 0 else 0.0

            errors_class_0 = [random.gauss(err_c0, max(0.01, std_c0)) for _ in range(50)]
            errors_class_1 = [random.gauss(err_c1, max(0.01, std_c1)) for _ in range(50)]

            seq_repr = [{"itemset": list(itemset), "gap_before": 0} for itemset in desc]

            serialized_patterns.append({
                "id": pattern_str,
                "quality_score": float(p.quality),
                "attributes": {
                    "support": int(p.support),
                    "support_percentage": float(sup_pct),
                    "delta_g": float(p.pattern_delta),
                    "separation": float(separation),
                    "deviation": float(deviation),
                    "class_balance": float(class_balance),
                    "support_penalty_pgB": float(support_penalty),
                    "mean_error_mu": float((err_c0 + err_c1) / 2.0),
                    "std_error_sigma": float((std_c0 + std_c1) / 2.0),
                    "std_class_0": float(std_c0),
                    "std_class_1": float(std_c1),
                    "p_value_bh": float(p.p_value_bh),
                    "error_class_0": float(err_c0),
                    "error_class_1": float(err_c1),
                    "size_class_0": int(size_c0),
                    "size_class_1": int(size_c1)
                },
                "example_slice": {
                    "errors_class_0": errors_class_0,
                    "errors_class_1": errors_class_1,
                    "sequence": seq_repr
                }
            })

        feat_importance = get_transition_feature_importance(mcts_instance)
        pareto = mcts_instance.get_pareto_frontier()
        depth_hist = mcts_instance.get_depth_histogram()
        anytime = mcts_instance.get_anytime_quality()
        diversity = mcts_instance.get_path_diversity()
        diagnostics = mcts_instance.get_search_space_diagnostics()

        # global_errors pre-calculated above

        import general.conf as conf

        return {
            "metrics": {
                "iteration_count": iteration,
                "avg_error": Model.get_global_mean_error() or 0.3,
                "tree_progress": iteration / 10000.0,
                "top_quality": serialized_patterns[0]["quality_score"] if serialized_patterns else 0.0,
                "explored_nodes": stats.get("explored_nodes", 0),
                "search_space": 10000,
                "explored_rate": iteration / max(1.0, current_elapsed),
                "stability": (
                    mcts_instance._stats.get("iteration_count", 0) -
                    mcts_instance._stats.get("last_gain_iteration", 0)
                    if mcts_instance._stats else 0
                ),
                "rollout_success_rate": (
                    mcts_instance._stats.get("rollout_success_count", 0) /
                    max(1, mcts_instance._stats.get("rollout_count", 1))
                    if mcts_instance._stats else 1.0
                ),
                "global_errors_class_0": global_errors_c0,
                "global_errors_class_1": global_errors_c1,

                "uct_factor": getattr(conf, "UCT_FACTOR", 0.5),
                "support_penalty": getattr(conf, "SUPPORT_PENALTY", 0.0),
                "max_gap": getattr(conf, "MAX_GAP", 1),
                "max_depth": mcts_instance._stats.get("max_depth_reached", 0) if mcts_instance._stats else 0,
                "total_elapsed_time": current_elapsed,

                "pareto_frontier": pareto,
                "feature_importance": feat_importance,
                "depth_histogram": depth_hist,
                "anytime_quality": anytime,
                "path_diversity": diversity,
                "search_space_diagnostics": diagnostics
            },
            "patterns": serialized_patterns,
            "status": status_str,
            "consume": consume_val
        }


connector = MCTSConnector()


class MCTSConnectorHandler(BaseHTTPRequestHandler):
    """
    Standard request handler mapping HTTP routes to model adapter functions.
    """
    def log_message(self, format, *args):
        # Professional standard logs to stdout
        sys.stdout.write(f"[HTTP] {format % args}\n")

    def send_json_response(self, status_code, data):
        try:
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError) as e:
            sys.stdout.write(f"[WARN] Client disconnected prematurely. Aborting response. Error: {e}\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"[WARN] Error sending response: {e}\n")
            sys.stdout.flush()

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError) as e:
            sys.stdout.write(f"[WARN] Client disconnected prematurely during OPTIONS. Error: {e}\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"[WARN] Error in OPTIONS handler: {e}\n")
            sys.stdout.flush()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_json_response(200, {"status": "online"})
        elif self.path == "/metadata":
            metadata = {
                "status": "online",
                "parameters": [
                    {
                        "name": "budget",
                        "label": "Search Budget (seconds)",
                        "type": "int",
                        "default_value": 50,
                        "required": True,
                        "constraints": {
                            "min": 5,
                            "max": 3600
                        }
                    },
                    {
                        "name": "max_gap",
                        "label": "Max Sequence Gap",
                        "type": "int",
                        "default_value": 5,
                        "required": True,
                        "constraints": {
                            "min": 1,
                            "max": 20
                        }
                    },
                    {
                        "name": "gamma",
                        "label": "Support Penalty (Gamma)",
                        "type": "float",
                        "default_value": 0.5,
                        "required": False,
                        "constraints": {
                            "min": 0.0,
                            "max": 1.0
                        }
                    },
                    {
                        "name": "theta",
                        "label": "Similarity Threshold (Theta)",
                        "type": "float",
                        "default_value": 0.1,
                        "required": True,
                        "constraints": {
                            "min": 0.0,
                            "max": 1.0
                        }
                    },
                    {
                        "name": "min_support",
                        "label": "Minimum Support",
                        "type": "int",
                        "default_value": 10,
                        "required": True,
                        "constraints": {
                            "min": 1
                        }
                    },
                    {
                        "name": "uct_factor",
                        "label": "UCT Exploration Factor",
                        "type": "float",
                        "default_value": 0.5,
                        "required": True,
                        "constraints": {
                            "min": 0.0
                        }
                    },
                    {
                        "name": "max_iterations",
                        "label": "Max Iterations",
                        "type": "int",
                        "default_value": 10000,
                        "required": True,
                        "constraints": {
                            "min": 1
                        }
                    },
                ]
            }
            self.send_json_response(200, metadata)
        else:
            self.send_json_response(404, {"error": "Not Found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self.send_json_response(400, {"error": "Invalid JSON payload"})
            return

        try:
            if self.path == "/prepare":
                domain = payload.get("domain", "malware")
                dataset_path = payload.get("dataset_path")
                config = payload.get("config", {}) or {}
                identity_filters = payload.get("identity_filters", [])

                res = connector.prepare(domain, dataset_path, config, identity_filters)
                self.send_json_response(200, res)

            elif self.path == "/start":
                config = payload.get("config", {}) or {}
                res = connector.start(config)
                self.send_json_response(200, res)

            elif self.path == "/control":
                action = payload.get("action")
                additional_budget = payload.get("additional_budget")
                config = payload.get("config")
                res = connector.control(action, additional_budget=additional_budget, config=config)
                self.send_json_response(200, res)

            elif self.path == "/api/mcts/resume":
                additional_budget = payload.get("additional_budget", 120.0)
                config = payload.get("config")
                res = connector.resume_with_budget(additional_budget, config=config)
                self.send_json_response(200, res)

            else:
                self.send_json_response(404, {"error": "Not Found"})
        except (BrokenPipeError, ConnectionResetError) as e:
            sys.stdout.write(f"[WARN] Client disconnected prematurely. Aborting POST handler. Error: {e}\n")
            sys.stdout.flush()
        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            self.send_json_response(500, {"error": str(e), "traceback": traceback.format_exc()})


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """
    Handle requests in separate threads to allow responsive concurrent lifecycle triggers.
    """
    daemon_threads = True


def run_server(port=8002):
    server_address = ("127.0.0.1", port)
    httpd = ThreadedHTTPServer(server_address, MCTSConnectorHandler)
    print(f"[INFO] Integration Middleware server listening on http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Shutting down Integration Middleware server.")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCTS Integration Middleware Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind the server")
    args = parser.parse_args()
    run_server(args.port)
