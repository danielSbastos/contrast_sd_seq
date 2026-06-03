import cProfile
import pstats
from mctsextent.main import prepare_mcts_from_files, launch_mcts

def main():
    filename = 'synth_temp'
    print("Loading data...")
    data, target_class, log_losses, extra, encoding_to_items = prepare_mcts_from_files(filename)
    
    print("Profiling 5 iterations of MCTS...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run MCTS with limit of 5 iterations
    results = launch_mcts(
        data, target_class, log_losses, 
        time_budget=600, top_k=10, theta=0.0,
        iterations_limit=5, extra=extra, max_length=3
    )
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(30)

if __name__ == '__main__':
    main()
