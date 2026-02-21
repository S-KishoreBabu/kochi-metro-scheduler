# Kochi Metro AI-Powered Scheduling Assistant

## 1. Project Overview

This is a full-stack web application that serves as an AI-powered decision support system for the Operations Supervisor at Kochi Metro. The tool provides a daily, optimized schedule for deploying trains based on a variety of operational and commercial constraints, helping to maximize revenue from branding contracts while ensuring operational efficiency.

---

## 2. Core Features

* **Automated Ranking:** An AI engine that uses a Weighted Sum Model to score and rank each train's suitability for service.
* **Interactive Dashboard:** A professional, multi-tab web interface built with Flask and JavaScript for intuitive data visualization.
* **Data-Driven Insights:** Provides clear views on:
    * Train Eligibility (Certified, Clean, Available)
    * Ranked Schedule with XAI Explanations
    * Detailed Branding Contract Status
    * Suitability Scores (Visualized as battery levels)
    * Physical Depot Layout (Color-coded by priority)
* **Schedule History:** Allows supervisors to look up and review past schedule recommendations for any given date.



---

## 3. System Architecture

The application is built on a classic three-tier architecture:

1.  **Presentation Layer (Frontend):** `HTML`, `CSS`, `JavaScript`
2.  **Logic Layer (Backend):** `Python`, `Flask` (Web Server), `Pandas` (Data Manipulation)
3.  **Data Layer (Database):** `PostgreSQL`

---

## 4. Setup and Installation

### Prerequisites

* Python 3.10+
* PostgreSQL

### Instructions

1.  **Clone the Repository:**
    ```bash
    git clone [<your-repo-url>](https://github.com/S-KishoreBabu/kochi-metro-scheduler.git)
    cd kochi_metro_scheduler
    ```

2.  **Set Up a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up the Database:**
    * Start your PostgreSQL server.
    * Create a database named `kochi_metro_db`.
    * Connect to it using `psql` and run the SQL scripts located in the `database_setup/` directory to create and populate the tables.

5.  **Run the Application:**
    ```bash
    python app/main.py
    ```
    Open your web browser and navigate to `http://127.0.0.1:5000`.
