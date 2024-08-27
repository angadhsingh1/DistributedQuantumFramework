# compile_results.py

# Read the outputs from both machines
with open('results/output_machine_1.txt', 'r') as file:
    output1 = file.read()

with open('results/output_machine_2.txt', 'r') as file:
    output2 = file.read()

# Combine or analyze the outputs
combined_output = f"Output from Machine 1:\n{output1}\n\nOutput from Machine 2:\n{output2}"

# Save the combined results
with open('results/combined_output.txt', 'w') as file:
    file.write(combined_output)

# Print or log the combined results
print("Compiled Output: ", combined_output)
