import subprocess
import argparse
import json
import re
import pexpect
import sys
from iotlabcli import auth

# Utility function to run shell commands
def run_command(command):
    """Utility function to run shell commands and return output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}\n{result.stderr}")
    return result.stdout.strip()

# Function to get available sites
def get_available_sites():
    """Fetch the list of available sites."""
    print("\n Fetching available sites...\n")
    sites_output = run_command("iotlab status --sites")
    try:
        sites_data = json.loads(sites_output)
        sites = [site['site'] for site in sites_data.get('items', [])]
        return sites
    except json.JSONDecodeError:
        print("Failed to fetch or parse available sites.")
        return []

# Check all nodes for the selected site
def check_all_nodes(site):
    """Check all nodes at the given site."""
    #print(f"Checking all nodes at site: {site}...")
    all_nodes = run_command(f"iotlab status --nodes --site {site}")
    try:
        data = json.loads(all_nodes)
        return data.get('items', [])
    except json.JSONDecodeError:
        print("Failed to parse the all nodes output as JSON.")
        return []

# Check available nodes for the selected site
def check_available_nodes(site):
    """Check available nodes at the given site."""
    print(f"\n Checking available nodes at site: {site}...")
    available_nodes = run_command(f"iotlab status --nodes --site {site} --state Alive")
    try:
        data = json.loads(available_nodes)
        return data.get('items', [])
    except json.JSONDecodeError:
        print("Failed to parse the available nodes output as JSON.")
        return []

def parse_node_info(node):
    """Parse node info to extract architecture and ID for submission format."""
    archi_type = node['archi'].split(':')[0]  # Extract architecture prefix
    network_address = node['network_address']
    match_pattern = rf"{archi_type}-(\d+)\."  # Regex for extracting numeric ID

    node_id_match = re.search(match_pattern, network_address)
    if node_id_match:
        node_id = node_id_match.group(1)
        return archi_type, node_id
    else:
        print(f"Warning: Unable to parse node: {network_address}")
        return None, None

def launch_experiment(available_nodes, site, username, duration=70):
    """Launch an experiment with available nodes."""
    print(f"Launching experiment at site {site}...")

    # Prepare node list in the required format
    experiment_nodes = []
    for node in available_nodes:
        archi_type, node_id = parse_node_info(node)
        if archi_type and node_id:
            experiment_nodes.append(f"{site},{archi_type},{node_id}")

    if not experiment_nodes:
        print("No valid nodes found to launch the experiment. Exiting.")
        return None

    # Construct the command
    nodes_list_string = ' -l '.join(experiment_nodes)
    experiment_name = f"{site}_Experiment"
    submit_command = f"iotlab experiment submit -n '{experiment_name}' -d {duration} -l {nodes_list_string}"

    # Run the command
    result = run_command(submit_command)
    print(result)
    if "id" in result:
        try:
            experiment_info = json.loads(result)
            experiment_id = experiment_info.get('id')
            print(f"Experiment launched successfully! Experiment ID: {experiment_id}")
            return experiment_id
        except json.JSONDecodeError:
            print("Failed to parse experiment ID.")
    else:
        print("Error submitting experiment.")
    return None

def deploy_firmware(available_nodes, firmware_paths, site):
    """Deploy firmware to nodes based on their architecture."""
    for archi, firmware_path in firmware_paths.items():
        print(f"\nDeploying firmware for {archi} nodes...")

        # Get nodes with the current architecture
        archi_nodes = [node for node in available_nodes if node['archi'].startswith(archi)]
        if not archi_nodes:
            print(f"No {archi} nodes available. Skipping firmware deployment.")
            continue

        # Format node IDs
        node_ids = [parse_node_info(node)[1] for node in archi_nodes if parse_node_info(node)]
        if not node_ids:
            print(f"No valid nodes found for {archi}.")
            continue

        node_list = "+".join(node_ids)
        flash_command = f"iotlab node --flash {firmware_path} -l {site},{archi},{node_list}"
        result = run_command(flash_command)

        if "Error" in result:
            print(f"Error deploying firmware for {archi}: {result}")
        else:
            print(f"Firmware deployed successfully on {archi} nodes.")

def summarize_experiment(experiment_id, available_nodes, suspected_nodes):
    """Summarize experiment results, including suspected nodes."""
    # Display the experiment summary
    print("\n--- Experiment Summary ---")
    print(f"Experiment ID: {experiment_id}")
    print(f"Number of available nodes: {len(available_nodes)}")
    
    # Display suspected nodes information
    total_suspected_nodes = len(suspected_nodes)
    print(f"Number of suspected nodes: {total_suspected_nodes}")
    
    if total_suspected_nodes > 0:
        print("\nSuspected Nodes:")
        print("{:<25} {:<40} {:<15}{:<10}".format("Architecture", "Network Address", "UID", "State"))
        print("-" * 100)
        
        # Display suspected nodes' information
        for node in suspected_nodes:
            archi = node.get("archi", "N/A")
            network_address = node.get("network_address", "N/A")
            uid = node.get("uid", "N/A")
            state = node.get("state", "N/A")
            print("{:<25} {:<40} {:<15}{:<10}".format(archi, network_address, uid, state))
    
    print("--- End of Summary ---")


def wait_for_experiment(experiment_id):
    """Wait for the experiment to start."""
    print(f"Waiting for experiment {experiment_id} to start...")
    wait_command = f"iotlab experiment wait -i {experiment_id}"
    result = run_command(wait_command)
    if "Running" in result or "Terminated" in result:
        print("Experiment has started.")
    else:
        print("Error or timeout while waiting for the experiment.")
    print(result)

def get_suspected_nodes(nodes):
    """Get suspected or error nodes based on their state."""
    # Filter nodes that are either 'Suspected' or 'Error'
    suspected_nodes = [node for node in nodes if node.get("state") in ["Suspected", "Error"]]
    
    if not suspected_nodes:
        print("\nNo suspected or error nodes found.")
    
    return suspected_nodes
def display_selected_fields(available_nodes):
    """Display selected fields from the available nodes data, limited to 5 nodes."""
    
    # Display the total number of available nodes
    total_nodes = len(available_nodes)
    print(f"\nTotal Available Nodes: {total_nodes}\n")

    # Display the selected node information
    print("Selected Node Information:")
    print("{:<25} {:<40} {:<15}{:<10}".format("Architecture", "Network Address", "UID", "State"))
    print("-" * 100)

    # Limit to first 10 nodes
    for idx, node in enumerate(available_nodes[:10]):  # Slice the list to only the first 5 nodes
        archi = node.get("archi", "N/A")
        network_address = node.get("network_address", "N/A")
        uid = node.get("uid", "N/A")
        state = node.get("state", "N/A")  # Get the state of the node
        print("{:<25} {:<40} {:<15}{:<10}".format(archi, network_address, uid, state))

    # If there are more than 10 nodes, indicate that only the first 5 are displayed
    if total_nodes > 10:
        print("\nNote: Only the first 10 nodes are displayed. There are more nodes available.")

def get_user_choice(options, prompt="Choose an option: "):
    """
    Generic function to display options and get user choice, including an 'All Nodes' option.
    """
    print("\nOptions:")
    print("0. All Nodes")  # Add 'All Nodes' option at the start
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    choice = input(prompt).strip()
    try:
        choice_index = int(choice)
        if choice_index == 0:  # 'All Nodes' option
            return "all"
        elif 1 <= choice_index <= len(options):  # Valid range for options
            return options[choice_index - 1]
        else:
            print("Invalid choice. Please try again.")
            return get_user_choice(options, prompt)
    except ValueError:
        print("Invalid input. Please enter a number corresponding to your choice.")
        return get_user_choice(options, prompt)


def filter_nodes_by_architecture(available_nodes):
    """Extract and display available architectures, then let the user choose one."""
    architectures = {node.get("archi", "").split(":")[0] for node in available_nodes}
    architectures = sorted(architectures)  # Sort architectures for consistent display
    if not architectures:
        print("No architectures found in the available nodes.")
        return None, []
    
     # Prompt the user to select an architecture or "All Nodes"
    print("\nAvailable Architectures:")
    chosen_archi = get_user_choice(architectures, prompt="Choose an architecture to test: ")

    # Handle the "All Nodes" option
    if chosen_archi == "all":
        return "all", available_nodes

    # Otherwise, filter nodes by the selected architecture
    filtered_nodes = [node for node in available_nodes if node.get("archi", "").startswith(chosen_archi)]

    return chosen_archi, filtered_nodes

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="IoT-LAB Automation Script")
    parser.add_argument("--username", required=True, help="IoT-LAB username")
    parser.add_argument("--password", required=True, help="IoT-LAB password")
    parser.add_argument("--site", help="IoT-LAB site (optional, dynamic selection if omitted)")
    parser.add_argument("--duration", type=int, default=10, help="Experiment duration in seconds")
    args = parser.parse_args()

    username = args.username
    password = args.password
    site = args.site
    duration = args.duration
    # Step  1: Authenticate
    if auth.check_user_credentials(username=username, password=password):
        print(f"\n User '{username}' authenticated successfully.")
    else:
        print("Authentication failed. Check your credentials.")
        return
    # Step 2: Get site
    if not site:
        sites = get_available_sites()
        if not sites:
            print("No sites available. Exiting.")
            return
        print("Available sites:", ", ".join(sites))
        site = input("Please select a site: ").strip()
        if site not in sites:
            print(f"Invalid site: {site}. Exiting.")
            return



    # Step 3: Check nodes
    all_nodes = check_all_nodes(site)
    if not all_nodes:
        print(f"No nodes found at site {site}. Exiting.")
        return

    suspected_nodes = get_suspected_nodes(all_nodes)
    available_nodes = check_available_nodes(site)
    if not available_nodes:
        print(f"No available nodes at site {site}. Exiting.")
        return

    # Display available nodes
    display_selected_fields(available_nodes)
    # Step 4: Let the user choose a node architecture to test
    chosen_archi, filtered_nodes = filter_nodes_by_architecture(available_nodes)
    if not filtered_nodes:
        print(f"No nodes found for the chosen architecture '{chosen_archi}'. Exiting.")
        return
      # Step 5: Launch experiment
    experiment_id = launch_experiment(filtered_nodes, site, username, duration)
    if not experiment_id:
        print("Failed to launch experiment. Exiting.")
        return

    # Step 5: Wait for experiment
    wait_for_experiment(experiment_id)

    # Step 6: Deploy firmware
    firmware_paths = {
        "nrf51dk": "Firmwares/nrf51dk_test.elf",
        "nrf52dk": "Firmwares/nrf52dk_test.elf",
        "nrf52840dk": "Firmwares/nrf52840dk_test.elf",
        "samr21": "Firmwares/samr21_test.elf",
        "m3": "Firmwares/m3_test.elf",
        "arduino-zero": "Firmwares/arduino-zero_test.elf",
    }
    deploy_firmware(filtered_nodes, firmware_paths, site)

    # Step 7: Summarize experiment
    summarize_experiment(experiment_id, available_nodes ,suspected_nodes)

if __name__ == "__main__":
    main()
