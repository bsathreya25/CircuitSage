# CircuitSage

## Agentic AI for Embedded Systems Diagnostics

### Technical Project Report

# 1. Executive Summary

CircuitSage is an agentic diagnostic prototype designed to assist with troubleshooting embedded-system projects.

The system combines:

- Technical-document retrieval
- A curated embedded-systems knowledge base
- Deterministic code-level validation
- Structured engineering evidence
- Evidence-constrained LLM reasoning
- Explicit uncertainty handling
- Diagnostic verification steps

The central design principle is:

> **The system should establish what can be supported by available evidence before asking an LLM to reason about the problem.**

This distinguishes CircuitSage from a conventional chatbot architecture in which a user submits a problem directly to a language model and receives a generated answer.

CircuitSage instead follows a multi-stage diagnostic workflow:

User Problem
     ↓
Scope Gate
     ↓
Technical Retrieval
     ↓
Deterministic Validation
     ↓
Evidence Package
     ↓
Reasoning
     ↓
Output Validation
     ↓
Diagnostic Response
The current MVP focuses primarily on Arduino-oriented embedded projects and uses a curated canonical corpus of 89 projects.

## Problem Statement
   
Embedded-system troubleshooting frequently requires combining several forms of evidence.
A developer may need to inspect:
- Firmware source code
- Component configuration
- Sensor libraries
- Pin assignments
- Serial output
- Known reference implementations
- Schematics
- Physical wiring
- Power conditions
- Hardware behavior
A conventional LLM can generate technically plausible explanations, but a plausible explanation is not necessarily an established diagnosis.
This creates a fundamental problem:
Plausible explanation
        ≠
Evidence-supported diagnosis

CircuitSage was designed to explore a different approach.
Instead of asking:
"What is wrong with my circuit?"

the system is designed around:
"What can be established from the available evidence, what remains unknown, and what should be checked next?"

## Project Objective
The primary objective of CircuitSage is to develop an MVP that demonstrates evidence-driven troubleshooting for embedded systems.
The system aims to:
1. Determine whether a diagnostic request is within supported scope.
2. Retrieve technically relevant embedded-system evidence.
3. Apply deterministic validation where explicit rules exist.
4. Separate confirmed findings from unknown conditions.
5. Use LLM reasoning only after evidence collection.
6. Produce structured diagnostic explanations.
7. Recommend engineering verification steps.
8. Avoid fabricated diagnoses for unsupported scenarios.
4. Design Hypothesis
The project is based on the following design hypothesis:
A diagnostic system can produce more grounded troubleshooting guidance when deterministic engineering checks and retrieved technical evidence are established before generative reasoning.

The architecture therefore separates:
Evidence Collection
        ↓
Deterministic Analysis
        ↓
Reasoning
        ↓
Response Validation

This allows the LLM to operate as part of a larger engineering workflow rather than as the sole diagnostic mechanism.
## System Overview
CircuitSage consists of several cooperating layers.
┌──────────────────────────┐
│          User            │
│ Problem + Code + Output  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      React Frontend      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       FastAPI API        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│        Scope Gate        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│     Retrieval Layer      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Deterministic Validators │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Evidence Package    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    Reasoning Pipeline    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Output Validation      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    Diagnostic Response   │
└──────────────────────────┘


## Why the LLM Is Not the Diagnostic Authority

A conventional chatbot may follow:
User
  ↓
LLM
  ↓
Answer

CircuitSage instead follows:
User
  ↓
Scope
  ↓
Retrieval
  ↓
Deterministic Validation
  ↓
Evidence Package
  ↓
Reasoning
  ↓
Output Validation
  ↓
Response

The LLM is therefore one component of the diagnostic workflow.
The system attempts to establish deterministic findings before relying on generative reasoning.

## Agentic Workflow:

CircuitSage is described as an agentic diagnostic prototype because it coordinates multiple stages toward a common diagnostic objective.
The workflow is:
Observe
   ↓
Evaluate Scope
   ↓
Retrieve Evidence
   ↓
Run Engineering Validation
   ↓
Accumulate Evidence
   ↓
Reason
   ↓
Validate Output
   ↓
Respond

The system combines:
- Retrieval
- Deterministic tools
- Evidence accumulation
- Reasoning
- Output validation
- Verification-oriented response generation
  
## Engineering Safety Through Uncertainty
CircuitSage deliberately preserves uncertainty when the evidence is insufficient.
Source code may establish:
TRIG configured as OUTPUT

but it cannot automatically establish:
TRIG wire physically connected

Similarly, a retrieved project may provide:
Reference implementation

without proving:
User's hardware behaves identically

This distinction is central to the system's diagnostic philosophy.

## Current Limitations:
    
CircuitSage V1.0 has several limitations.
Limited validator coverage
Only a defined set of components has dedicated deterministic validators.
Physical hardware cannot be directly verified
The software cannot independently inspect:
- Wiring
- Power delivery
- Hardware damage
- Loose connections
- Real-world electrical measurements
Limited visual reasoning
Schematic artifacts are stored/indexed, but complete visual schematic interpretation is not part of the current diagnostic path.
Retrieval is not correctness
A relevant retrieved project does not prove that the implementation is correct.
Dataset scope
The corpus is primarily Arduino-oriented and should not be presented as universal embedded-system coverage.

## Project Status
    
CircuitSage is an: MVP / hackathon prototype

The current system demonstrates an evidence-driven architecture for embedded-system diagnostics.
Its major implemented layers are:
Technical Retrieval
        +
Scope Management
        +
Deterministic Validation
        +
Evidence Packaging
        +
Constrained Reasoning
        +
Output Validation

The system is intended as a technical prototype rather than a production-grade hardware diagnostic platform.

## Future Development
    
Potential future development areas include:
Expanded Validator Coverage
Add deterministic validators for additional embedded components and communication systems.
Deeper Schematic Analysis
Introduce stronger visual reasoning for schematic and wiring artifacts.

Additional Engineering Tools
Integrate more tools for analyzing:
- Serial communication
- Sensor behavior
- Protocols
- Timing
- Pin configuration
- Component interfaces
Hardware-in-the-Loop Validation
Future versions could incorporate actual hardware measurements and test equipment.
Broader Platform Support
The system could eventually expand beyond Arduino-oriented projects to additional embedded platforms.

More Structured Evidence
Future versions could incorporate richer engineering evidence and confidence/uncertainty representations.

## Technical Contribution

The main technical contribution of CircuitSage is the combination of deterministic engineering validation with evidence-constrained AI reasoning.
The system does not attempt to eliminate LLM reasoning.
Instead, it attempts to place reasoning inside a structured engineering workflow:
Engineering Evidence
        ↓
Deterministic Findings
        ↓
Explicit Unknowns
        ↓
AI Reasoning
        ↓
Verification-Oriented Response

This architecture provides a framework in which generative AI can assist embedded troubleshooting while maintaining explicit boundaries around what the available evidence can establish.

## Project Outcome

The CircuitSage MVP demonstrates a complete prototype workflow from user interaction to evidence-driven diagnostic response.
The implemented system provides:
User Interface
      ↓
API Layer
      ↓
Scope Management
      ↓
Technical Retrieval
      ↓
Deterministic Validation
      ↓
Evidence Package
      ↓
Constrained Reasoning
      ↓
Validated Diagnostic Response

The project also establishes a structured foundation for future expansion through:
- Additional validators
- Additional datasets
- Additional evidence sources
- Additional engineering tools
- More advanced reasoning
- Hardware integration

## Conclusion
  
CircuitSage explores an evidence-first approach to AI-assisted embedded-system troubleshooting.
The central idea is simple:
Do not ask an LLM to guess what is wrong. First establish what the available engineering evidence can support.

The current MVP implements this idea through:
Scope
  ↓
Retrieval
  ↓
Deterministic Validation
  ↓
Evidence
  ↓
Reasoning
  ↓
Validation
  ↓
Diagnostic Response

The result is an embedded-systems diagnostic prototype that explicitly separates:
- What is known
- What is unknown
- What is technically possible
- What should be verified next
  
This evidence-driven architecture forms the foundation for future versions of CircuitSage with broader component coverage, richer engineering evidence, deeper schematic analysis, and eventual hardware-integrated diagnostics.
