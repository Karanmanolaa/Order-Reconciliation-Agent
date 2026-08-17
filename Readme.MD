# Order Reconciliation Agent

## Overview

This project implements an order reconciliation system that compares two different sources of order data:

- A live event stream containing order changes (create, update, cancel)
- A warehouse snapshot containing the current stored state

The purpose of the system is to identify differences between these sources, decide which state should be accepted, store the final reconciled state, and ensure the same reconciliation is not applied more than once.

---

## Problem

In real systems, the same business data is usually stored across multiple services.

For example, an order may appear in:

- A live operational system receiving events immediately
- A warehouse database updated periodically

Because these systems do not update at exactly the same time, differences can occur.

Examples:

- An order exists in the live system but is missing from the warehouse snapshot.
- The warehouse contains an order that never appeared in the event stream.
- Both systems contain the order but disagree on the current status.
- The same reconciliation job runs multiple times.

This project focuses on building a simple and explainable process for resolving these situations.

---

# How the system works

The reconciliation flow is:

```
Live Events
     |
     v
Build Current Order State
     |
     v
Compare with Warehouse Snapshot
     |
     v
Apply Reconciliation Rules
     |
     v
Save Final State and Reconciliation History
```

---

# Reconciliation Strategy

The system first classifies each order into one of four categories.

## 1. MATCH

The live system and warehouse snapshot contain the same order information.

Example:

```
Live:
ORD001 - PROCESSING

Warehouse:
ORD001 - PROCESSING
```

Action:

```
NO_ACTION
```

No update is required.

---

## 2. LIVE_ONLY

The order exists in the live event stream but not in the warehouse snapshot.

Example:

```
Live:
ORD003 - PROCESSING

Warehouse:
Not found
```

Decision:

```
ACCEPT_LIVE
```

The live state is accepted because the order was most likely created after the previous warehouse snapshot.

---

## 3. SNAPSHOT_ONLY

The order exists in the warehouse snapshot but no matching live event exists.

Example:

```
Warehouse:
ORD004 - PROCESSING

Live:
Not found
```

Decision:

```
ACCEPT_SNAPSHOT
```

The snapshot is accepted to avoid losing existing data.

This case is treated as suspicious because it may indicate a missing event in the live pipeline.

---

## 4. CONFLICT

Both sources contain the order but have different states.

Example:

```
Live:
ORD001 - SHIPPED
Updated: 15:00


Warehouse:
ORD001 - PROCESSING
Snapshot: 12:00
```

For conflicts, the system compares timestamps.

Rules:

- If the live update happened after the warehouse snapshot, the live state is accepted.
- If the warehouse contains a newer state, the snapshot is accepted and the case is flagged for review.

This avoids blindly trusting one source and keeps the decision explainable.

---

# Idempotency

A reconciliation process should be safe to run multiple times.

To handle this, every reconciliation creates an input fingerprint based on:

- Order ID
- Selected action
- Live order state
- Warehouse order state

Before applying a reconciliation, the system checks whether that fingerprint has already been processed.

Example:

First run:

```
ORD001 → ACCEPT_LIVE
Saved
```

Second run:

```
ORD001 → Skipped (already reconciled)
```

This prevents duplicate corrections and keeps the reconciliation history consistent.

---

# Database

SQLite is used as the persistent ledger.

## Orders table

Stores the final accepted order state.

Fields:

```
order_id
status
amount
source
last_updated
```

## Reconciliation history table

Stores every reconciliation decision.

Fields:

```
order_id
action
reason
input_hash
processed_time
```

This provides an audit trail showing why a particular state was selected.

---

# Project Structure

```
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
```

---

# Running the Project

## Create virtual environment

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the reconciliation agent:

```bash
python3 main.py
```

Example output:

```
ORD001 | CONFLICT | ACCEPT_LIVE
ORD002 | CONFLICT | ACCEPT_LIVE
ORD003 | LIVE_ONLY | ACCEPT_LIVE
ORD004 | SNAPSHOT_ONLY | ACCEPT_SNAPSHOT
```

---

# Running Tests

The project includes tests for:

- Live-only orders
- Snapshot-only orders
- Conflict resolution using timestamps
- Idempotent reconciliation processing

Run:

```bash
pytest
```

Expected output:

```
5 passed
```

---

# Design Decisions

## Why timestamp-based conflict resolution?

Neither source can always be considered correct.

A live system may contain updates that have not reached the warehouse yet.

A warehouse snapshot may contain information that was missed by the event stream.

Using timestamps provides a simple rule that is easy to understand and explain.

---

## Why SQLite?

For a production system, a larger database would likely be used.

SQLite was chosen because it provides:

- Persistent storage
- Transactions
- Simple local setup

while still demonstrating the core behaviour of a reconciliation ledger.

---

# Possible Improvements

If this was extended into a production system, the next improvements would be:

- Replace JSON files with a real event stream
- Add a message queue such as Kafka
- Create a manual review workflow for flagged conflicts
- Add monitoring and reconciliation metrics
- Add retry handling for failed processing

---

# Summary

This project demonstrates a complete reconciliation workflow:

- Detecting differences between data sources
- Applying explainable resolution rules
- Maintaining a persistent ledger
- Recording reconciliation history
- Preventing duplicate processing through idempotencySNAPSHOT_ONLY
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
