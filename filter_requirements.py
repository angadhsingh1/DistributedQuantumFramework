# Define the packages that should be kept
required_packages = {
    'numpy',
    'qiskit',
    'qiskit-aer',
    'qiskit-ibm-runtime',
    'scipy',
    'matplotlib',
    'dask',
    'redis'
}

# Read the current requirements.txt file
input_file = 'requirements.txt'
output_file = 'filtered_requirements.txt'

# Function to filter the requirements
def filter_requirements(input_file, output_file, required_packages):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Filter lines to only keep the required packages
    filtered_lines = []
    for line in lines:
        # Get the package name before any version specifier
        package_name = line.split('==')[0].split('>=')[0].strip().lower()
        
        # Keep only the required packages
        if any(pkg in package_name for pkg in required_packages):
            filtered_lines.append(line)

    # Write the filtered packages to a new output file
    with open(output_file, 'w') as f:
        f.writelines(filtered_lines)

    print(f"Filtered requirements written to '{output_file}'")

# Run the filtering function
filter_requirements(input_file, output_file, required_packages)
