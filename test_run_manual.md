⏺ Steps to Run End-to-End Tests

  Prerequisites

  - Python 3.8+ installed
  - Git installed
  - Clone the repository

  Step-by-Step Setup

  1. Create and activate virtual environment

  cd TrojanHacks_MITHackNation
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate

  2. Install dependencies

  pip install -r requirements.txt

  3. Set up environment variables

  Create a .env file in the project root:
  # Minimum required for testing
  ANTHROPIC_API_KEY=your-anthropic-api-key-here
  # OR
  # OPENAI_API_KEY=your-openai-api-key-here

  # Optional (will be mocked if not provided)
  # GITHUB_WEBHOOK_SECRET=  # Leave empty for local testing
  # VERCEL_TOKEN=           # Leave empty to simulate deployment
  # GITHUB_TOKEN=           # Leave empty to skip issue creation
  # SMTP_* variables        # Leave empty to log emails only

  4. Create test repository

  bash test_setup.sh
  This creates a sample Node.js app in test-sample-app/ directory with test commits.

  5. Start the API server

  # In terminal 1
  source venv/bin/activate
  uvicorn api:app --reload

  6. Run the end-to-end test

  # In terminal 2
  source venv/bin/activate
  python run_e2e_test.py

  What the Test Does

  1. ✅ Checks API health
  2. ✅ Triggers deployment via mocked GitHub webhook
  3. ✅ Clones test repository
  4. ✅ Runs agent pipeline (Architect → Deps → Tests → Deploy → Monitor)
  5. ✅ Tests replay functionality
  6. ✅ Shows which services are mocked vs real

  Expected Output

  ======================================================================
  🧪 MULTI-AGENT DEPLOYMENT ORCHESTRATOR - END-TO-END TEST
  ======================================================================
  ✅ Deployment triggered: <deployment-id>
  📡 Monitoring deployment...
     📦 [clone] Cloning repository
     🏗️ [Architect] Starting
     📚 [Deps] Starting
     🧪 [TestSuite] Starting
     🚀 [Deployment] Starting (simulated)
     🚨 [IncidentMonitor] Starting
  ✅ END-TO-END TEST COMPLETED SUCCESSFULLY!

  Troubleshooting

  If API won't start:
  - Check .env file has valid API key
  - Ensure port 8000 is free

  If test fails at webhook:
  - Leave GITHUB_WEBHOOK_SECRET empty in .env

  If GitPython error:
  - Make sure you ran pip install -r requirements.txt in the venv

  Current Known Issue:
  - Agents may crash with "Prompt missing required variables" - this is a known bug in the agent prompt template that needs fixing

  Quick Test (All Commands)

  # One-time setup
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  echo "ANTHROPIC_API_KEY=your-key-here" > .env
  bash test_setup.sh

  # Run test
  # Terminal 1:
  uvicorn api:app --reload

  # Terminal 2:
  python run_e2e_test.py