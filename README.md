TRACK_ID=PS03
# Retail Copilot (Optikka Retail)

Retail Copilot is an autonomous conversational dashboard for store operations and retail analytics. It combines **deterministic operational analytics** (automated Morning Briefing flagging stockout hazards, dead stock capital, and demand anomalies) with a **grounded GenAI assistant** that translates natural language inquiries into read-only SQL queries with visible data evidence and citations.

---

## Key Features

1. **Automated Morning Briefing:**
   - **Stockout Risks:** Real-time detection of zero-inventory items, sub-reorder levels, and velocity-based depletion risks (< 7 days of stock).
   - **Dead Stock Analysis:** Tracks tied-up working capital on dormant stock (`current_stock >= 30` with 0 sales in 14 days).
   - **Sales Anomalies:** Flags demand volume spikes (e.g. Day 16 promotions) and sudden sales drops vs. historical baselines.
   - **Multi-Store Filtering:** Instant scoping across all stores or isolated to Store `S001`, `S002`, or `S003`.

2. **Grounded Conversational Copilot (GenAI):**
   - **Dynamic Schema Injection:** Queries live SQLite PRAGMA schema to construct precise SQL.
   - **Data Citations & SQL Transparency:** Evaluators and managers can expand the **"Evidence: Generated SQL"** accordion under any AI response to view the executed SQLite query and retrieved row count.
   - **Discipline Against Hallucinations:** Two-stage prompting ensures the LLM bases every figure strictly on query output rows, refusing or clarifying when data is unavailable.
   - **Interactive Prompt Suggestions:** 1-click suggested prompts for rapid investigation.

3. **Enterprise Sound Engineering:**
   - Strict read-only database connections (`mode=ro`) preventing data modification.
   - 100% automated test coverage across deterministic analytics, database safety, and API endpoints.

---

## How to Run

Following the hackathon constraints, the entire application (compiled React frontend + FastAPI backend) runs from a single command on port `8000`:

### 1. Prerequisites
Ensure Python 3.10+ is installed. Clone the repository and configure your environment:
```bash
# Copy environment template
cp .env.example .env

# Set your Gemini API key in .env
# GEMINI_API_KEY="your_api_key_here"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python app.py
```

### 4. Access the Application
Open your browser and navigate to:
```
http://localhost:8000
```

---

## Running the Automated Test Suite

Run the built-in unit and integration test suite with zero external test runners:
```bash
python -m unittest discover tests -v
```

---

## Architecture & Technology Stack

- **Backend:** FastAPI (Python 3.11+), Uvicorn, SQLite 3, Pydantic, Pandas.
- **Frontend:** React 19, Vite, Tailwind CSS 3.4, Framer Motion, Lucide React.
- **AI Model:** Google Gemini (`gemini-3.6-flash`).
- **Database:** Local read-only SQLite database (`database/retail.db`) with synthetic data modeling realistic multi-store edge cases.

---

## Demo Video

[Link to 5-minute evaluation demo video]
