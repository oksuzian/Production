# plot the distributions
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np
output_csv_file_name = "output_data.csv"
df = pd.read_csv(output_csv_file_name)

processes = ['CRYCosmic','DIO','IPAMichel','RMCExternal','RMCInternal','RPCExternal','RPCInternal']
colors = ['green','black','orange','red','blue','cyan','violet']
weight = [0.792365,0.0268767,0.058688,0.0387817,0.0130446,0.0337845,0.0366466]
plot = 'fraction_sampled'
for i in range(0,len(processes)):
  data = df[df['Dataset'] == str(processes[i])]

  # Extract the 'fraction_sampled' column for plotting (this is the 3rd column, index 2)
  fraction_sampled_values = data[str(plot)]
  print(processes[i],np.mean(fraction_sampled_values))
  # Create the plot
  plt.figure(figsize=(10, 6)) 
  #plt.axvline(weight[i], color='red', linestyle='dashed', linewidth=2, label=f'weight')

  plt.hist(fraction_sampled_values, bins=50, color=colors[i], label=str(processes[i])) # Line plot with markers
  plt.title(str(processes[i]))
  plt.xlabel(str(plot))
  plt.ylabel('Occurances')
  plt.grid(True)
  plt.show()
  #plt.savefig(str(processes[i])+'.pdf')
