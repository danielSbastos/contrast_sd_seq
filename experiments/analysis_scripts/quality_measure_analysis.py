import numpy as np
import matplotlib.pyplot as plt

auc = np.linspace(0, 1, 401)
support = np.linspace(0.001, 1, 401)
X, Y = np.meshgrid(auc, support)
Q = (X**2) * np.sqrt(Y)
plt.figure(figsize=(8, 6))
plt.imshow(
    Q, origin='lower', aspect='auto',
    extent=[auc.min(), auc.max(), support.min(), support.max()],
    cmap='viridis'
)
plt.colorbar(label='qm')
plt.xlabel('auc_diff')
plt.ylabel('relative_support')
plt.title('qm = auc_diff^2 * relative_support^0.5')


x = np.linspace(0, 1, 200)
y = np.linspace(0, 1, 200)
X, Y = np.meshgrid(x, y)

Z1 = (X) * (Y**0.5)
Z2 = (X**2) * (Y**0.5)
Z3 = (X**1.5) * (Y**0.5)
Z4 = (X**2) * (Y**0.3)

fig = plt.figure(figsize=(14, 10))

ax1 = fig.add_subplot(2, 2, 1, projection='3d')
surf1 = ax1.plot_surface(X, Y, Z1, cmap='viridis', edgecolor='none')
ax1.set_title(f"qm = auc_diff * rel_sup^0.5")
ax1.set_xlabel('auc_diff')
ax1.set_ylabel('rel_sup')
ax1.set_zlabel('qm')
fig.colorbar(surf1, ax=ax1, shrink=0.6)

ax2 = fig.add_subplot(2, 2, 2, projection='3d')
surf2 = ax2.plot_surface(X, Y, Z2, cmap='viridis', edgecolor='none')
ax2.set_title(f"qm = auc_diff^2 * rel_sup^0.5")
ax2.set_xlabel('auc_diff')
ax2.set_ylabel('rel_sup')
ax2.set_zlabel('qm')
fig.colorbar(surf2, ax=ax2, shrink=0.6)

ax3 = fig.add_subplot(2, 2, 3, projection='3d')
surf3 = ax3.plot_surface(X, Y, Z3, cmap='viridis', edgecolor='none')
ax3.set_title(f"qm = auc_diff^1.5 * rel_sup^0.5")
ax3.set_xlabel('auc_diff')
ax3.set_ylabel('rel_sup')
ax3.set_zlabel('qm')
fig.colorbar(surf3, ax=ax3, shrink=0.6)

ax4 = fig.add_subplot(2, 2, 4, projection='3d')
surf4 = ax4.plot_surface(X, Y, Z4, cmap='viridis', edgecolor='none')
ax4.set_title(f"qm = auc_diff^2 * rel_sup^0.3")
ax4.set_xlabel('auc_diff')
ax4.set_ylabel('rel_sup')
ax4.set_zlabel('qm')
fig.colorbar(surf4, ax=ax4, shrink=0.6)

plt.tight_layout()
plt.show()
