# EDITH AI OS - Implementation Roadmap

## Overview of Roadmap
- **Phase 1: Stabilization, Error Remediation, Truthful Execution, and Host Grounding (COMPLETED)**
- **Phase 2: Persistent Memory and Session Recovery (COMPLETED)**
- **Phase 3: Expanded Cyber Operations & Hardware Instrumentation (Future Scope)**

---

## Phase 1: Stabilization & Truthful Operations (COMPLETED)

### Objectives
Make the existing application stable, truthful, and fully functional on Kali Linux without rebuilding or breaking existing UI/UX.

### Phase 1 Task Tracker
- [x] **1.1 Project & Architecture Audit:** Document baseline architecture, components, and security boundary (`docs/PROJECT_AUDIT.md`, `docs/ARCHITECTURE.md`).
- [x] **1.2 Truthful System Tool Execution:**
  - Replaced mock application launcher with real host discovery (`which`), headless detection, and spawn handling.
  - Replaced mock folder opener with path expansion (`os.homedir()`) and `xdg-open` / fallback directory listing.
  - Replaced static `[22, 80, 443, 3000]` mock in `run_security_scan` with real socket-based connection probing.
  - Implemented real Python & Bash evaluation with strict timeouts (5s) in `run_code_simulation`.
  - Connected real host process monitor in `system_monitor.ts` on Linux (`ps -eo ...`).
- [x] **1.3 AI Provider Configuration & Error Hardening:**
  - Supported `AI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, and `API_KEY`.
  - Enforced timeout safety across all provider calls (`AI_TIMEOUT_SECONDS`).
  - Added graceful fallbacks for unavailable AI services and search grounding timeout race.
- [x] **1.4 Database & Persistence Verification:**
  - Verified SQLite schema initialization, safe migrations, and persistence across restarts in `edith.db`.
  - Verified foreign key cascades, atomic transaction commits, and added performance indexes.
- [x] **1.5 Git & Environment Security Hygiene:**
  - Excluded `.env*`, `edith.db`, `*.db`, `*.sqlite*`, and `workspace/*` from source control via `.gitignore`.
- [x] **1.6 Automated Verification Suite:**
  - Created automated test runner `tests/phase1.test.ts` verifying database persistence, API routes, tool truthful execution, and timeout handling.
  - Verified zero TypeScript or lint errors (`npm run lint` & `npm run build` passed).

---

## Phase 2: Persistent Memory and Session Recovery (COMPLETED)

### Objectives
Enable EDITH to remember projects, task progress, previous sessions, and unfinished work across application and computer restarts, maintaining strict memory safety invariants and preserving existing conversation data.

### Phase 2 Task Tracker
- [x] **2.1 Persistent Schema & Safe Migrations (`server/database.ts`):**
  - **Projects (`projects` table):** Persistent storage of project workspaces, status, and metadata.
  - **Tasks (`tasks` table):** Persistent task records supporting ID, title, description, category, project association, status (`pending`, `in_progress`, `waiting_for_approval`, `completed`, `failed`, `interrupted`), progress (0-100), PID, last completed step, next planned step, relevant file paths, error info, checkpoint data JSON, and completion evidence JSON.
  - **Execution Steps (`task_steps` table):** Detailed granular steps with execution status and output logs.
  - **Checkpoints (`task_checkpoints` table):** State snapshots captured during long-running background tasks.
  - **Sessions (`sessions` table):** Lifecycle tracking of every application start, shutdown, and unexpected interruption.
  - **Workspace Activity (`workspace_activity` table):** Audit trail distinguishing verified system actions from unverified inference.
  - **Memory Records (`memory_records` table):** Long-term knowledge store with strict secret redaction.
  - Maintained complete backwards compatibility: existing `conversations` and `messages` tables were unmodified and verified intact.
- [x] **2.2 Startup Session Recovery Engine (`server/database.ts`):**
  - Detects tasks left in `in_progress` state upon previous application termination/crash and marks them as `interrupted`.
  - Records previous session status and generates a contextual `resumeSummary` and `suggestedNextAction`.
  - Provides instant recovery methods: `resumeInterruptedTask(id)` and `dismissInterruptedTask(id)`.
  - Creates a new active session on boot with reference to the previous active project and task.
- [x] **2.3 Memory Safety & Secret Sanitization (`server/database.ts`):**
  - Implemented `sanitizeMemoryContent()` to strip Gemini API keys (`AIzaSy...`), OpenAI/Anthropic keys (`sk-...`), Bearer tokens, and password/credential assignments prior to persistent memory storage.
  - Memory records are kept strictly local in `edith.db`.
  - Enforced completion evidence invariant: tasks cannot be marked `completed` without verifiable completion evidence.
- [x] **2.4 REST API Endpoints (`server.ts`):**
  - `GET /api/projects`, `POST /api/projects`, `GET /api/projects/:id`, `PUT /api/projects/:id`
  - `GET /api/persistent-tasks`, `POST /api/persistent-tasks`, `GET /api/persistent-tasks/:id`, `PUT /api/persistent-tasks/:id`
  - `POST /api/persistent-tasks/:id/complete` (verifies evidence payload)
  - `POST /api/persistent-tasks/:id/resume`, `POST /api/persistent-tasks/:id/dismiss`
  - `GET /api/persistent-tasks/:id/steps`, `POST /api/persistent-tasks/:id/steps`, `PUT /api/persistent-tasks/:id/steps/:stepId`
  - `GET /api/persistent-tasks/:id/checkpoints`, `POST /api/persistent-tasks/:id/checkpoints`
  - `GET /api/session/recovery`, `POST /api/session/recovery/dismiss`
  - `GET /api/memory`, `POST /api/memory`
  - `GET /api/activity`, `POST /api/activity`
- [x] **2.5 Frontend Persistence & Session Recovery Interface:**
  - **Session Recovery Card (`TaskManager.tsx` & `Dashboard.tsx`):** Prominently displays recovery alerts when interrupted tasks are detected on startup, with 1-click "Resume" or "Dismiss" actions.
  - **Workspace Project Selector:** Allows users to filter tasks by project workspace or view all workspaces.
  - **Task State Tabs:** Filters by All, Unfinished, Interrupted, and Completed tasks.
  - **Task Detail Cards:** Displays progress percentage, last completed step, next planned step, checkpoint data, and verified completion evidence.
  - **Completion Evidence Modal:** Requires user to provide a verifiable result note or artifact reference before marking tasks complete.
- [x] **2.6 Automated Verification Suite (`tests/phase2.test.ts`):**
  - 1. A project can be created, retrieved, and updated.
  - 2. A task can be created with steps, checkpoints, and updated.
  - 3. Progress survives restart & interrupted tasks are detected and recovered.
  - 4. Completed tasks require evidence and are not presented as unfinished.
  - 5. Memory safety: API keys, tokens, and credentials are scrubbed before storage.
  - 6. Existing conversations and messages remain completely intact.
  - 7. Workspace activities distinguish verified system action from unverified.

---

## Test Results

### Phase 1 & Phase 2 Test Summary (`npm test`): 16 Passed, 0 Failed
```
====================================================
   EDITH AI OS - PHASE 1 VERIFICATION TEST SUITE   
====================================================
 [PASS] Database connects and pings successfully
 [PASS] Database saves and reloads conversations across simulated restarts
 [PASS] Settings persistence and default values work properly
 [PASS] open_application returns truthful status instead of fake success
 [PASS] open_folder validates path and inspects contents truthfully
 [PASS] run_security_scan performs real TCP connect probes and measures latency
 [PASS] run_code_simulation executes code truthfully with timeout limits
 [PASS] System monitor queries real host telemetry
 [PASS] Environment variable key resolution is resilient
====================================================
 RESULTS: 9 PASSED, 0 FAILED
====================================================

====================================================
   EDITH AI OS - PHASE 2 VERIFICATION TEST SUITE   
====================================================
 [PASS] 1. A project can be created, retrieved, and updated
 [PASS] 2. A task can be created with steps, checkpoints, and updated
 [PASS] 3. Progress survives restart & interrupted tasks are detected and recovered
 [PASS] 4. Completed tasks require evidence and are not presented as unfinished
 [PASS] 5. Memory safety: API keys, tokens, and credentials are scrubbed before storage
 [PASS] 6. Existing conversations and messages remain completely intact
 [PASS] 7. Workspace activities distinguish verified system action from unverified
====================================================
Phase 2 Tests Finished: 7 Passed, 0 Failed
====================================================
```

- **Static Typing & Linting:** `tsc --noEmit` passed with 0 errors.
- **Production Build:** `vite build` completed successfully.

---

## Local Execution on Kali Linux

### 1. Prerequisites
- Node.js (v18+ or v20+)
- npm

### 2. Configuration (`.env`)
```bash
cp .env.example .env
# Edit .env with your Google Gemini or AI API key:
# AI_API_KEY=your_key_here
# AI_PROVIDER=gemini
# AI_MODEL=gemini-3.8-flash
```

### 3. Run Automated Tests
```bash
# Run both Phase 1 and Phase 2 test suites
npm test

# Run individual test suites
npm run test:phase1
npm run test:phase2
```

### 4. Start the Application
```bash
npm start
# Server listens on http://localhost:3000
```

### Remaining Manual Tests (Requires Physical/GUI Kali Linux Environment)
1. **Microphone Audio Input:** Approve the browser Web Audio / MediaDevices prompt to vocalize commands.
2. **Desktop Application Spawning:** Requires an active Kali Linux GUI session (`DISPLAY=:0`) to open applications like Firefox or Wireshark.
3. **Hardware Network Adapter Probing:** Connect a physical Wi-Fi adapter (e.g. `wlan0mon`) to capture live wireless packets in Kali Linux.
