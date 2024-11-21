
---

# IoT-LAB Automation Script

This Python script automates various tasks in the IoT-LAB environment, including:
- Authenticating with IoT-LAB
- Checking available nodes on a specific site
- Filtering nodes by architecture
- Launching experiments
- Deploying firmware to selected nodes
- Summarizing experiment results

## Requirements

Before using this script, make sure you have the following dependencies installed:

1. **Python 3.x**: This script is written in Python 3.
2. **IoT-LAB CLI**: The IoT-LAB CLI (`iotlabcli`) is required for interacting with the IoT-LAB platform. You can install it using the following command:
    ```bash
    pip install iotlabcli
    ```
3. **Pexpect**: This library is used for handling interactive commands (like password entry).
    ```bash
    pip install pexpect
    ```

4. **Other Required Libraries**: The script also uses `subprocess`, `argparse`, `json`, `re`, and `sys`, which should already be available in standard Python installations.

## Setup

1. **Authentication**: The script requires your IoT-LAB username and password for authentication. You can supply them via the command line or let the script prompt you.

2. **Firmware Files**: The script assumes that you have firmware files for different architectures stored in the `Firmwares/` folder. These files should be named according to the architecture (e.g., `nrf51dk_test.elf`, `nrf52dk_test.elf`, etc.).

## Usage

### Command-Line Arguments

The script accepts the following arguments:

- `--username`: Your IoT-LAB username (required).
- `--password`: Your IoT-LAB password (required).
- `--site`: The IoT-LAB site to work with (optional; if omitted, it will list available sites and prompt you to choose one).
- `--duration`: The duration of the experiment in seconds (optional; default is 10 seconds).

### Running the Script

You can run the script using the following command:

```bash
python iotlab_automation.py --username <your_username> --password <your_password> --site <site_name> --duration <experiment_duration>
```

### Example:

```bash
python iotlab_automation.py --username john_doe --password mypassword123 --site lyon --duration 120
```

If you don't provide a site, the script will fetch available sites and ask you to choose one.

## Workflow

1. **Authentication**: The script authenticates you with IoT-LAB using the provided username and password.
   
2. **Site Selection**: If no site is provided, the script will fetch and display available IoT-LAB sites. You will then be prompted to select one.

3. **Node Check**: The script checks the nodes at the selected site and lists them. It will display all nodes and their statuses (Alive, Suspected, Error, etc.).

4. **Architecture Filtering**: You will be prompted to choose an architecture for the experiment, or you can select "All Nodes".

5. **Experiment Launch**: After selecting nodes, the script will launch an experiment using the selected nodes.

6. **Firmware Deployment**: Once the experiment is running, the script deploys firmware to the selected nodes according to their architecture.

7. **Summary**: After the experiment, a summary is displayed, including information about the available nodes, suspected nodes, and experiment status.

## Functions

### Utility Functions

- `run_command(command)`: Runs a shell command and returns the output.
- `get_available_sites()`: Fetches available IoT-LAB sites.
- `check_all_nodes(site)`: Checks all nodes at a given site.
- `check_available_nodes(site)`: Checks available nodes (in "Alive" state) at a given site.
- `parse_node_info(node)`: Parses the architecture and node ID from node information.
- `launch_experiment(available_nodes, site, username, duration)`: Launches an experiment with selected nodes.
- `deploy_firmware(available_nodes, firmware_paths, site)`: Deploys firmware to nodes based on their architecture.
- `summarize_experiment(experiment_id, available_nodes, suspected_nodes)`: Summarizes the experiment and displays relevant node information.
- `wait_for_experiment(experiment_id)`: Waits for the experiment to start.
- `get_suspected_nodes(nodes)`: Returns a list of suspected or error nodes based on their state.
- `display_selected_fields(available_nodes)`: Displays selected fields (Architecture, Network Address, UID, State) of available nodes, limited to 5 nodes.
- `get_user_choice(options, prompt)`: Displays a list of options for the user to choose from, with an option to select "All Nodes".
- `filter_nodes_by_architecture(available_nodes)`: Filters nodes based on their architecture.

### Example Workflow:

1. **Authenticate**: The user authenticates using the `iotlabcli` API.
2. **Get Available Sites**: The script fetches available sites and prompts the user to select one.
3. **Get Available Nodes**: The script fetches available nodes at the selected site.
4. **Node Selection**: The user selects an architecture, and the script filters nodes accordingly.
5. **Launch Experiment**: The script launches an experiment with the selected nodes.
6. **Deploy Firmware**: The firmware is deployed to the nodes based on their architecture.
7. **Summary**: The experiment summary, including the status of suspected or error nodes, is displayed.



---

### Note:
- This script is primarily for use with IoT-LAB and assumes you have access to an IoT-LAB account. It interacts with the IoT-LAB platform using the `iotlabcli` tool.
- The script uses `iotlabcli` commands, so make sure you have it installed and properly configured.
