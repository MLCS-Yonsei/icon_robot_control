import numpy as np
import matplotlib.pyplot as plt


# Calculate the average
aluminum_mean = 56.45
copper_mean = 21.56

# Calculate the standard deviation
aluminum_std = 20.37
copper_std = 10.58

# Create lists for the plot
materials = ['(a)', '(b)']
x_pos = np.arange(len(materials))
CTEs = [aluminum_mean, copper_mean]
error = [aluminum_std, copper_std]

# Build the plot
fig, ax = plt.subplots()
ax.bar(x_pos, CTEs, yerr=error, align='center', alpha=0.5, ecolor='black', capsize=10)
ax.set_ylabel('Time spent with the robot $(seconds)$', fontsize=13)
ax.set_xticks(x_pos)
ax.set_xticklabels(materials, fontsize=13)
# ax.set_title('Coefficent of Thermal Expansion (CTE) of Three Metals')
plt.yticks(size = 12)
ax.yaxis.grid(True)
fig.set_figwidth(3)
# Save the figure and show
plt.tight_layout()
plt.savefig('bar_plot_with_error_bars.png')
plt.show()