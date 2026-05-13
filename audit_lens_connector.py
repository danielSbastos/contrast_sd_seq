import time
import requests
from api import MCTS, RunStatus

AUDITLENS_API_BASE = "http://localhost:8001"
UPDATE_INTERVAL = 10  # Enviar dados a cada X iterações

def sync_with_auditlens(stats, force_send=False):
    """
    Busca o budget atual. Se houver budget e force_send for True (ou atingiu o intervalo),
    envia o melhor padrão atual para a API do AuditLens.
    Retorna o remaining_budget.
    """
    remaining_budget = 0.0
    try:
        resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=2)
        if resp.status_code == 200:
            remaining_budget = resp.json().get("remaining_budget", 0.0)
    except Exception as e:
        print(f"Erro ao conectar com AuditLens (config): {e}")
        return remaining_budget

    if force_send and remaining_budget > 0 and stats.get('top10_patterns'):
        best = stats['top10_patterns'][0]
        sup = (best.get("size_class_0") or 0) + (best.get("size_class_1") or 0)
        
        desc_raw = best.get("pattern_descriptor", [])
        try:
            pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in desc_raw])
        except Exception:
            pattern_str = str(desc_raw)
            
        payload = {
            "pattern_descriptor": pattern_str,
            "error_class_0": best.get("error_class_0") or 0.0,
            "error_class_1": best.get("error_class_1") or 0.0,
            "top10_avg_quality": stats.get("top10_avg_quality", 0.0),
            "top10_avg_support": stats.get("top10_avg_support", 0.0),
            "soft_error": best.get("error_class_0") or 0.0,
            "quality_score_phi": best.get("quality") or 0.0,
            "separation_sg": 0.0,
            "baseline_deviation_dgB": 0.0,
            "class_balance_bg": (best.get("size_class_0") or 0) / sup if sup > 0 else 0.5,
            "support_penalty_pgB": 0.0,
            "delta_g": 0.0,
            "mean_error_mu": best.get("error_class_0") or 0.0,
            "std_error_sigma": best.get("std_class_0") or 0.0,
            "p_value_bh": 0.0,
            "support_count": sup,
            "support_percentage": (sup / 10000.0) * 100,
            "search_metrics": {
                "explored_patterns": stats.get("iteration_count", 0),
                "filtered_similarity": 0.0,
                "search_space_coverage": 0.0
            }
        }
        
        try:
            post_resp = requests.post(f"{AUDITLENS_API_BASE}/api/slices", json=payload, timeout=2)
            if post_resp.status_code == 200:
                print(f"  -> AuditLens atualizado! (Budget restante: {post_resp.json().get('remaining_budget')})")
        except Exception as e:
            print(f"Erro ao enviar dados para AuditLens: {e}")

    return remaining_budget

# 1. Inicializa o MCTS passando o nome do dataset (arquivo) e outras configurações opcionais
# Certifique-se de usar o caminho correto para o seu arquivo .dat
mcts_worker = MCTS(
    filename="synth_temp",
    top_k=50,
    # time_budget=3600, # 1 hora de limite
    iterations_limit=1000
)

# 2. Inicia o worker em background
print("Iniciando MCTS...")
mcts_worker.run()

# 3. Monitoramento "ao vivo" (Main thread fica livre para fazer outras coisas)
last_sent_iteration = 0
last_check_time = time.time()
try:
    while mcts_worker.status not in (RunStatus.STOPPED, RunStatus.ABORTED):
        # Pega as estatísticas do top 10 atual
        stats = mcts_worker.queue_stats()
        current_iter = stats['iteration_count']
        
        print(f"\nStatus: {mcts_worker.status.name}")
        print(f"Iterações: {current_iter}")
        print(f"Qualidade Média (Top 10): {stats['top10_avg_quality']:.4f}")
        
        current_time = time.time()
        elapsed = current_time - last_check_time
        last_check_time = current_time
        
        budget = 0.0
        if mcts_worker.status.name.startswith("RUNNING"):
            try:
                resp = requests.post(f"{AUDITLENS_API_BASE}/api/config/consume", json={"amount": elapsed}, timeout=2)
                if resp.status_code == 200:
                    budget = resp.json().get("remaining_budget", 0.0)
                    if budget <= 0:
                        print("Budget esgotado (Tempo finalizado). Pausando MCTS...")
                        mcts_worker.pause()
            except Exception:
                pass
        else:
            try:
                resp = requests.get(f"{AUDITLENS_API_BASE}/api/config/current", timeout=2)
                if resp.status_code == 200:
                    budget = resp.json().get("remaining_budget", 0.0)
                    if budget > 0:
                        print("Budget disponível. Retomando MCTS...")
                        mcts_worker.run()
                        last_check_time = time.time()
            except Exception:
                pass
        
        # Sincroniza com AuditLens
        should_send = (current_iter - last_sent_iteration) >= UPDATE_INTERVAL
        if should_send and budget > 0:
            sync_with_auditlens(stats, force_send=True)
            last_sent_iteration = current_iter
                
        # Dorme por um tempo curtinho
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nInterrompido pelo usuário! Abortando...")
    mcts_worker.abort()

# 4. Finalização e extração dos resultados
if mcts_worker.status != RunStatus.ABORTED:
    print("\nProcessamento concluído. Finalizando resultados...")
    # Isso aplica a filtragem, validação estatística e também cria/grava os arquivos
    resultados = mcts_worker.finalize_results()
    
    print(f"\nTotal de padrões encontrados: {len(resultados)}")