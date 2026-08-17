A small reconciliation system that keeps order data consistent between a live event stream and a warehouse snapshot.
The system detects missing records and conflicting states, decides which source should be trusted, stores the resolved state in SQLite, and prevents the same reconciliation from being applied multiple times.
Problem
In distributed systems, the same piece of data often exists in multiple places.
For this project:
The live event stream contains order events such as create, update, and cancel.
The warehouse snapshot contains a periodic view of order states.
Because these sources update independently, they can disagree.
Examples:
An order exists in live data but not in the warehouse.
An order exists in both systems but has different statuses.
A previous reconciliation is accidentally executed again.
The goal was to build a simple reconciliation process that can resolve these situations in a predictable and explainable way.
How it works
The workflow is:
Live Events
      |
      ↓
Build Current Order State
      |
      ↓
Compare Against Warehouse Snapshot
      |
      ↓
Apply Reconciliation Rules
      |
      ↓
Save Final State + Audit History
Reconciliation Strategy
The system first classifies every order.
MATCH
Both systems contain the same status and amount.
Action:
NO_ACTION
Nothing needs to be changed.
LIVE_ONLY
The order exists in the live event stream but not in the warehouse snapshot.
Example:
Live:
ORD003 - PROCESSING

Warehouse:
Missing
Decision:
ACCEPT_LIVE
Reason:
The order most likely appeared after the warehouse snapshot was created.
SNAPSHOT_ONLY
The order exists in the warehouse snapshot but no live event exists.
Example:
Warehouse:
ORD004 - PROCESSING

Live:
Missing
Decision:
ACCEPT_SNAPSHOT
Reason:
The data is preserved, but this case is treated as suspicious because it could indicate a missing event.
CONFLICT
Both sources contain the order but disagree.
Example:
Live:
ORD001 - SHIPPED
Updated: 15:00


Warehouse:
ORD001 - PROCESSING
Snapshot: 12:00
The system does not blindly trust either source.
It compares timestamps:
If live was updated after the snapshot → accept live.
If the warehouse contains a newer state → accept snapshot and flag for review.
This keeps the decision explainable.
Idempotency
A reconciliation process should be safe to run multiple times.
To achieve this, each reconciliation generates a fingerprint based on:
order ID
action taken
live state
warehouse state
Before applying a correction, the system checks whether that exact reconciliation has already been processed.
Example:
First run:
ORD001 → ACCEPT_LIVE
Saved
Second run:
ORD001 → Already reconciled
Skipped
This prevents duplicate corrections and keeps the reconciliation history consistent.
Storage
SQLite is used as a lightweight persistent ledger.
Orders table
Stores the final accepted state:
order_id
status
amount
source
last_updated
Reconciliation history table
Stores why a decision was made:
order_id
action
reason
input_hash
processed_time
This provides an audit trail for every reconciliation.
Project Structure
lec_order_reconciliation/

├── data/
│   ├── live_events.json
│   └── warehouse_snapshot.json
│
├── tests/
│   ├── test_reconciliation.py
│   └── test_idempotency.py
│
├── main.py
├── reconciliation.py
├── database.py
├── check_database.py
├── requirements.txt
└── README.md
Running the project
Create environment:
python3 -m venv venv
Activate:
source venv/bin/activate
Install dependencies:
pip install -r requirements.txt
Run:
python3 main.py
Example:
ORD001 | CONFLICT | ACCEPT_LIVE
ORD002 | CONFLICT | ACCEPT_LIVE
ORD003 | LIVE_ONLY | ACCEPT_LIVE
ORD004 | SNAPSHOT_ONLY | ACCEPT_SNAPSHOT
Running Tests
Tests cover:
live-only records
snapshot-only records
conflict resolution
idempotent processing
Run:
pytest
Expected:
5 passed
Design Decisions
Why timestamp comparison?
Neither source is always guaranteed to be correct.
A live stream can miss events.
A warehouse snapshot can become stale.
Using timestamps gives a simple rule that can be explained during review.
Why SQLite?
A production implementation would likely use a larger database, but SQLite provides:
persistent storage
transactions
simple local execution
which is sufficient for demonstrating the reconciliation workflow.
Possible Improvements
With more time, I would add:
real event ingestion instead of JSON files
a queue-based architecture
a manual review queue for flagged conflicts
monitoring metrics for reconciliation failures
retry handling for failed processing
