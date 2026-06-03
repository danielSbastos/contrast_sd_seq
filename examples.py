"""
Exemplo de uso manual da integração MCTS + AuditLens.
Útil para notebooks e testes interativos.
"""

import sys
sys.path.insert(0, '/home/vitor/projetos/contrast_sd_seq')

from api import MCTS
from auditlens_weights import focus_on_region, focus_on_attributes, reset_weights
import requests
import time

# ============================================================================
# Exemplo 1: Iniciar MCTS com estado anterior
# ============================================================================

def example_load_and_continue():
    """Carregar árvore anterior e continuar."""
    print("Exemplo 1: Carregando estado anterior...")
    
    mcts = MCTS(filename="synth_temp", iterations_limit=10000, time_budget=600)
    
    # Tentar carregar estado anterior
    if mcts.load_state():
        print(f"✓ Árvore carregada com {mcts.iteration_count} iterações")
    else:
        print("→ Iniciando nova árvore")
    
    # Continuar execução
    mcts.run()
    
    # Executar por 10 segundos
    time.sleep(10)
    
    print(f"Iterações após 10s: {mcts.iteration_count}")
    print(f"Padrões descobertos: {len(mcts.patterns)}")
    
    # Pausar e salvar
    mcts.pause()
    mcts.save_state()
    print("✓ Estado salvo")


# ============================================================================
# Exemplo 2: Aplicar pesos por atributo
# ============================================================================

def example_focus_by_attributes():
    """Focar exploração em padrões específicos."""
    print("\nExemplo 2: Aplicando pesos por atributos...")
    
    mcts = MCTS(filename="synth_temp", iterations_limit=10000, time_budget=60)
    
    # Aplicar pesos ANTES de iniciar
    focus_on_attributes({
        "support>50": 1.5,        # Explorar padrões com suporte > 50
        "quality>0.7": 2.0,       # Explorar padrões de alta qualidade
        "class_balance>0.4": 1.2  # Explorar padrões balanceados
    })
    print("✓ Pesos aplicados")
    
    # Executar
    mcts.run()
    time.sleep(5)
    mcts.pause()
    
    # Verificar padrões descobertos
    patterns = mcts.patterns[:3]
    for i, p in enumerate(patterns, 1):
        print(f"  Pattern {i}: quality={p.quality:.3f}, support={p.support}, "
              f"error_c0={p.error_class_0:.3f}, error_c1={p.error_class_1:.3f}")


# ============================================================================
# Exemplo 3: Integração com AuditLens (enviar snapshots)
# ============================================================================

def example_send_snapshot_to_auditlens():
    """Enviar dados ao AuditLens em tempo real."""
    print("\nExemplo 3: Enviando snapshot para AuditLens...")
    
    # Verificar se AuditLens está rodando
    try:
        resp = requests.get("http://localhost:8001/api/config/current", timeout=1)
        if resp.status_code != 200:
            print("❌ AuditLens não está respondendo")
            print("   Inicie com: cd ~/projetos/AuditLens && python main.py")
            return
    except Exception as e:
        print(f"❌ Não conseguiu conectar ao AuditLens: {e}")
        return
    
    mcts = MCTS(filename="synth_temp", iterations_limit=1000, time_budget=10)
    mcts.run()
    
    # Executar algumas iterações
    time.sleep(3)
    
    # Preparar dados para enviar
    stats = mcts.queue_stats()
    patterns_raw = mcts.patterns[:5]
    
    # Serializar padrões
    def serialize_pattern(pattern):
        return {
            "id": str(pattern.descriptor) if hasattr(pattern, 'descriptor') else "p-unknown",
            "quality_score": float(pattern.quality),
            "attributes": {
                "support": int(pattern.support),
                "error_class_0": float(pattern.error_class_0 or 0.0),
                "error_class_1": float(pattern.error_class_1 or 0.0),
                "size_class_0": int(pattern.size_class_0 or 0),
                "size_class_1": int(pattern.size_class_1 or 0),
            }
        }
    
    serialized_patterns = [serialize_pattern(p) for p in patterns_raw]
    
    # Enviar snapshot
    payload = {
        "metrics": {
            "iteration_count": stats.get("iteration_count", 0),
            "avg_error": 0.3,
            "tree_progress": 0.1,
            "top_quality": serialized_patterns[0]["quality_score"] if serialized_patterns else 0.0,
            "explored_nodes": len(patterns_raw),
            "search_space": 50000,
        },
        "patterns": serialized_patterns,
        "status": "running",
        "consume": 3.0
    }
    
    try:
        resp = requests.post("http://localhost:8001/api/snapshots", json=payload, timeout=2)
        if resp.status_code == 200:
            print("✓ Snapshot enviado com sucesso!")
            print(f"  Iterações: {payload['metrics']['iteration_count']}")
            print(f"  Padrões: {len(serialized_patterns)}")
            resp_data = resp.json()
            print(f"  Budget restante: {resp_data.get('remaining_budget', 0):.1f}s")
        else:
            print(f"❌ AuditLens retornou {resp.status_code}")
    except Exception as e:
        print(f"❌ Erro enviando snapshot: {e}")
    
    mcts.pause()


# ============================================================================
# Exemplo 4: Ciclo completo com budget
# ============================================================================

def example_budget_cycle():
    """Demonstrar ciclo de run/pause com budget."""
    print("\nExemplo 4: Ciclo completo run/pause com budget...")
    
    mcts = MCTS(filename="synth_temp", iterations_limit=10000, time_budget=300)
    
    # Carregar estado anterior se houver
    mcts.load_state()
    
    budget_available = 30.0  # 30 segundos de budget
    
    print(f"Budget inicial: {budget_available:.1f}s")
    print("Começando exploração...")
    
    # Executar com budget
    mcts.run()
    start = time.time()
    
    while time.time() - start < budget_available:
        time.sleep(1)
        elapsed = time.time() - start
        iters = mcts.iteration_count
        print(f"  [{elapsed:.1f}s] {iters} iterações, {len(mcts.patterns)} padrões")
    
    # Budget esgotado
    print("\nBudget esgotado!")
    mcts.pause()
    
    # Salvar estado
    mcts.save_state()
    print(f"✓ Estado salvo ({mcts.iteration_count} iterações)")
    
    # Simular novo budget
    print("\nRecebendo novo budget (+20s)...")
    time.sleep(1)
    
    print("Retomando exploração...")
    mcts.run()
    
    new_budget = 20.0
    start = time.time()
    while time.time() - start < new_budget:
        time.sleep(1)
        elapsed = time.time() - start
        iters = mcts.iteration_count
        print(f"  [{elapsed:.1f}s] {iters} iterações, {len(mcts.patterns)} padrões")
    
    mcts.pause()
    mcts.save_state()
    print(f"✓ Total de iterações: {mcts.iteration_count}")
    print(f"✓ Total de padrões: {len(mcts.patterns)}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("EXEMPLOS DE INTEGRAÇÃO MCTS + AuditLens")
    print("="*70)
    
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "1":
            example_load_and_continue()
        elif example == "2":
            example_focus_by_attributes()
        elif example == "3":
            example_send_snapshot_to_auditlens()
        elif example == "4":
            example_budget_cycle()
        else:
            print(f"Exemplo desconhecido: {example}")
    else:
        print("\nUso: python examples.py [1|2|3|4]")
        print("  1 - Carregar estado anterior e continuar")
        print("  2 - Aplicar pesos por atributos")
        print("  3 - Enviar snapshot para AuditLens")
        print("  4 - Ciclo completo com budget")
        print("\nOu importe diretamente em Python:")
        print("  from examples import example_load_and_continue")
        print("  example_load_and_continue()")
