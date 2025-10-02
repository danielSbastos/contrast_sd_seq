from mctsextent.main import get_patterns

#[
#  {
#    "element": "X",
#    "quantity": 200,
#    "target_auc": 0.95
#  },
#  {
#    "element": "A B",
#    "quantity": 10,
#    "target_auc": 0.60
#  },
#  {
#    "element": "C",
#    "quantity": 20,
#    "target_auc": 0.70
#  }
#]

# theta, time_budget
values = [
    [1.0, 100],
    [0.5, 100],
    [0.0, 100],
    [0.5, 50],
    [0.5, 200],
    [0.5, 400],
    [0.5, 700],
    [0.5, 1000],
]
for theta, time_budget in values:
    print(f"Theta: {theta}. Budget: {time_budget}")
    print(get_patterns(path='./data/synth.dat', target_path='./data/synth.csv', time_budget=time_budget, top_k=10, theta=theta))