# Autonomous AI Maintenance Analyst

This project implements an **Autonomous AI Agent** that acts as a predictive maintenance analyst for vehicle fleets.

It processes raw prediction data (simulated in this project) to:
- 🔍 **Detect Anomalies**: Identify abnormal regional failure patterns.
- 🚨 **flag Critical Risks**: Warn about vehicles under warranty likely to fail soon.
- 📦 **Predict Supply Chain Needs**: Estimate upcoming demand for spare parts.
- 📢 **Dispatch Alerts**: Automatically route insights to Warranty, Logistics, and Operations teams.

## Prerequisites

- **Python** (3.8 or higher)
- **pip** (Python package manager)

## Installation

1.  Clone or download this repository.
2.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main script to start the analyst agent:

```bash
python main.py
```

## Output

1.  **Console Output**: The agent will print its analysis steps and "dispatch" alerts (logs) to the console.
2.  **Daily Report**: A file named `daily_briefing.md` is generated in the root directory. This contains the structured executive briefing.

## Project Structure

- `main.py`: Entry point. Generates dummy data (simulating `FACT_PREDICTION`) and runs the agent.
- `ai_agent.py`: Contains the `MaintenanceAgent` class with the core logic.
- `requirements.txt`: List of python dependencies.
- `daily_briefing.md`: The output report (generated after running).
