# CircuitSage

## Agentic AI for Embedded Systems Diagnostics

CircuitSage is an agentic diagnostic prototype for troubleshooting embedded-system projects using a combination of technical-document retrieval, deterministic code validation, engineering evidence, and evidence-constrained LLM reasoning.

It is designed to answer a more useful engineering question than a generic chatbot:

> **What can be established from the available evidence, what cannot yet be established, and what should be checked next?**

CircuitSage currently focuses on Arduino-oriented embedded projects and uses a curated canonical corpus of 89 projects as its retrieval knowledge base.

---

## What CircuitSage Does

A user can provide an embedded-system problem together with available evidence such as firmware/code and serial-output information.

CircuitSage then:

1. Determines whether the requested component or diagnostic scenario is within the supported scope.
2. Retrieves technically relevant projects from its canonical knowledge base.
3. Runs deterministic code-level validation when a supported validator is available.
4. Packages the available evidence and known unknowns.
5. Uses constrained LLM reasoning where appropriate.
6. Validates the reasoning output.
7. Returns a concise engineering-oriented diagnosis and recommended next verification steps.

The system is intentionally designed **not to treat an LLM's free-form answer as ground truth**.

---

# Diagnostic Philosophy

CircuitSage separates three different outcomes:

### PASS

Deterministic evidence supports the expected implementation.

This does **not** prove that the physical hardware is working.

### FAIL

A deterministic validator has identified a known code-level contradiction or implementation problem.

This is a software/code-level finding, not automatic proof of a physical hardware failure.

### UNKNOWN

The available evidence is insufficient to establish a reliable result.

CircuitSage should prefer an explicit **UNKNOWN** over inventing a diagnosis.

---

# System Architecture

```text
User
 │
 ▼
Frontend
 │
 ▼
FastAPI API
 │
 ▼
Scope Gate
 │
 ├── Unsupported
 │
 ├── Insufficient Evidence
 │
 └── Supported
        │
        ▼
   Retrieval Layer
        │
        ▼
Deterministic Validator
        │
        ▼
   Evidence Package
        │
        ▼
Reasoning Pipeline
        │
        ▼
Evidence-Constrained LLM
        │
        ▼
Reasoning Output Validation
        │
        ▼
Diagnostic Response
