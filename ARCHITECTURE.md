# CircuitSage Architecture

## Agentic AI for Embedded Systems Diagnostics

CircuitSage is an agentic diagnostic prototype for embedded systems.

Its architecture is designed around a simple principle:

> **The LLM should reason over engineering evidence, not invent the evidence itself.**

Instead of sending a user's problem directly to an LLM and asking it to guess the fault, CircuitSage first establishes whether the problem is within the system's supported scope, retrieves relevant technical evidence, performs deterministic code-level validation, constructs an evidence package, and only then invokes constrained reasoning.

---

# 1. High-Level Architecture

```text
┌──────────────────────────┐
│          User            │
│                          │
│ Problem + Code + Output │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       React Frontend     │
│                          │
│ Diagnostic Chat UI       │
└────────────┬─────────────┘
             │
             │ POST /diagnose
             ▼
┌──────────────────────────┐
│       FastAPI API        │
│                          │
│ Request / Response Layer │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│        Scope Gate        │
│                          │
│ Supported?               │
│ Sufficient evidence?     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    Retrieval Engine      │
│                          │
│ Technical Evidence       │
│ from Canonical Corpus    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Deterministic Validators │
│                          │
│ HC-SR04                  │
│ DHT11 / DHT22            │
│ MPU6050                  │
│ nRF24L01                 │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Evidence Package    │
│                          │
│ Retrieval + Validation   │
│ + Parameters + Unknowns  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    Reasoning Pipeline    │
│                          │
│ Deterministic Reasoning  │
│ + Constrained LLM        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Output Validation      │
│                          │
│ Schema + Safety Rules    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    Diagnostic Response   │
│                          │
│ Evidence + Unknowns      │
│ + Next Verification      │
└──────────────────────────┘
