# CircuitSage Architecture

## Agentic AI for Embedded Systems Diagnostics

CircuitSage is an agentic diagnostic prototype for embedded systems Debugging

**The architecture is built around one central principle:**

> **The LLM should reason over engineering evidence, not invent the evidence itself.**

Instead of sending a user's problem directly to an LLM and asking it to guess the fault, CircuitSage first evaluates the diagnostic scope, retrieves relevant technical evidence, performs code-level validation where supported, constructs an evidence package, and then applies constrained reasoning.

# 1. High-Level Architecture

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

The architecture separates evidence collection, deterministic analysis, reasoning, and response generation.

**Architectural Philosophy**
   
CircuitSage does not treat the language model as the sole source of truth.

The diagnostic workflow is:
User Input
    ↓
Scope Evaluation
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

This separation is intended to reduce unsupported conclusions and make diagnostic reasoning traceable to available engineering evidence.

## End-to-End Request Flow

A diagnostic request passes through several stages.

**Stage 1 — User Input :**

The user provides a diagnostic problem and available evidence.
Available evidence can include:
- Component information
- Problem description
- Embedded firmware/code
- Serial-output information

The request is submitted through the frontend.

**Stage 2 — API Layer**

The frontend communicates with the FastAPI backend.
The primary diagnostic endpoint is:
POST /diagnose

The API layer receives the request and passes it into the diagnostic pipeline.
The API layer itself is not responsible for determining the engineering fault.

**Stage 3 — Scope Evaluation :**

The Scope Gate determines whether CircuitSage can meaningfully process the request.

The system distinguishes between:
SUPPORTED
INSUFFICIENT_EVIDENCE
UNSUPPORTED

This prevents the system from treating every incoming question as automatically diagnosable.

## Retrieval Evidence Weighting

The retrieval layer uses different weights for different evidence fields.
Evidence Field	Weight
Component	10
Library	10
Diagnostic signal	10
Source file	7
Artifact file	5
Project name	4
Interface	3
Category	1


These weights are used for retrieval ranking.
They should not be interpreted as correctness or physical-confidence scores.

Conceptually:
Higher retrieval score
        ↓
More technically relevant evidence
        ↓
Not necessarily correct implementation

## Deterministic Validation Layer
After retrieval, CircuitSage can run deterministic component-specific validation where a validator exists.

The current supported deterministic validators are:
Component	Validator
HC-SR04	hcsr04_v1
DHT11	dht_v1
DHT22	dht_v1
MPU6050	mpu6050_v1
nRF24L01	nrf24_v1

The purpose of deterministic validation is to identify concrete implementation evidence through explicit rules.
This reduces the need to ask a generative model to infer known code-level conditions.

Missing evidence should not automatically become a fault.

## HC-SR04 Validator

The HC-SR04 validator performs eight deterministic checks.
Check	Description
HC001	TRIG pin is defined
HC002	ECHO pin is defined
HC003	TRIG is configured as OUTPUT
HC004	ECHO is configured as INPUT
HC005	Trigger pulse is generated
HC006	pulseIn() measurement is present
HC007	Distance calculation is present
HC008	Serial output is present


The validator therefore evaluates concrete implementation conditions rather than asking the LLM to infer them.
For example:

pinMode(trigPin, INPUT);
can produce a deterministic contradiction when the expected HC-SR04 implementation requires the TRIG pin to be configured as an output.

## Evidence Package

After scope evaluation, retrieval, and deterministic validation, CircuitSage constructs an evidence package.
The EvidencePackage contains structured diagnostic information such as:
user_query
scope_status
component
retrieved_projects
validator_result
schematic_evidence
engineering_parameters
known_unknowns

The evidence package acts as the boundary between evidence collection and reasoning.
Conceptually:
┌──────────────────────────┐
│      Evidence Package    │
├──────────────────────────┤
│ User query               │
│ Scope status             │
│ Component                │
│ Retrieved projects       │
│ Validator result         │
│ Schematic evidence       │
│ Engineering parameters   │
│ Known unknowns           │
└────────────┬─────────────┘
             │
             ▼
        Reasoning

## Engineering Parameters
Where available, CircuitSage can extract engineering parameters relevant to the diagnostic problem.

For example, an HC-SR04 diagnostic may contain information such as:
Sensor: HC-SR04
TRIG pin: 11
ECHO pin: 12
Serial baud rate: 9600
Loop delay: 250 ms
Trigger pulse: 10 µs

These values provide concrete engineering context for the diagnostic reasoning.

## Known & Unknowns: 

A central architectural feature of CircuitSage is explicit uncertainty tracking.
Source-code analysis can establish certain software conditions.
It cannot automatically establish physical conditions.

For example:
Source-code evidence:
TRIG is configured as OUTPUT

does not establish:
Physical evidence:
The TRIG wire is actually connected.

Therefore the diagnostic system can distinguish between:
Confirmed evidence

and:
Unknown information
This prevents unsupported physical claims.

## Reasoning Pipeline
Once the evidence package has been constructed, CircuitSage applies its reasoning pipeline.
The reasoning process can combine:
Deterministic reasoning
        +
Constrained LLM reasoning

The deterministic evidence is established first.
The LLM is then used where generative reasoning can help interpret and communicate the available evidence.

## Evidence-Constrained LLM Reasoning
The LLM is explicitly constrained by the evidence available to CircuitSage.

Important reasoning rules include:
- Do not invent physical measurements.
- Do not treat the user's problem report as proof of malfunction.
- Do not treat UNKNOWN as FAIL.
- Do not claim unsupported hardware observations.
- Distinguish confirmed findings from possible explanations.
- Provide engineering verification steps when evidence is incomplete.
- 
Conceptually:

User Problem
     ↓
Retrieved Evidence
     ↓
Deterministic Findings
     ↓
Evidence Package
     ↓
Constrained LLM Reasoning
     ↓
Structured Diagnostic Explanation

The LLM therefore operates as a reasoning and explanation component rather than the entire diagnostic system.

## Reasoning Output Structure

The reasoning pipeline is structured around six major fields:
confirmed_issue
confirmed_evidence
unknown_information
possible_explanations
potential_consequences
next_engineering_verification

This structure separates:
- What has been established
- What evidence supports it
- What remains unknown
- What explanations are possible
- What consequences could follow
- What should be verified next
16. Output Validation
Reasoning output is validated before the final diagnostic response is returned.
The intended flow is:
LLM reasoning output
        ↓
Schema validation
        ↓
Required fields
        ↓
Reasoning constraints
        ↓
Diagnostic response

This prevents malformed or structurally invalid reasoning from being blindly returned to the frontend.

## Frontend Architecture

CircuitSage uses a React frontend.
The frontend is responsible for:
- Accepting diagnostic requests
- Sending requests to the backend
- Displaying diagnostic results
- Displaying evidence
- Displaying uncertainty
- Displaying recommended next verification steps
During development, the frontend communicates with the backend through the Vite development proxy.

Conceptually:

Browser
   │
   │ /api
   ▼
Vite Development Proxy
   │
   ▼
FastAPI
   │
   ▼
Diagnostic Engine

The proxy allows the frontend to communicate with the local FastAPI service during development.

## Backend Architecture

The backend is implemented using FastAPI.
Primary endpoints:
GET  /health
POST /diagnose
Health Endpoint
GET /health

Provides a basic service health response.
Diagnostic Endpoint
POST /diagnose

Accepts a diagnostic request and sends it through the CircuitSage diagnostic pipeline.

## Knowledge Base Architecture

The raw Arduino dataset and the curated CircuitSage corpus are treated as separate layers.
The raw dataset remains the original source material.
CircuitSage operates on a curated canonical subset for its diagnostic knowledge base.
The current canonical corpus contains:
89 canonical projects

The repository also contains indexed technical source and artifact information associated with these projects.
This separation prevents the diagnostic pipeline from depending directly on the uncurated raw dataset.
20. Artifact and Schematic Layer
CircuitSage stores and indexes project artifacts such as:
- Schematic images
- PDFs
- Other project files
The current canonical corpus contains:
143 image/PDF artifacts

However:
Artifact stored/indexed
        ≠
Complete visual schematic reasoning

The current V1.0 diagnostic path does not perform complete visual interpretation of every schematic artifact.
Visual schematic reasoning remains a future extension of the architecture.

## Failure and Uncertainty Handling

CircuitSage intentionally avoids converting missing evidence into automatic failure.
For example:
No serial output found does not automatically establish:
Sensor is broken

Instead, the system can report the condition as unknown and identify what should be verified.
This produces a diagnostic distinction between:
Confirmed
Possible and Unknown

## Unsupported Diagnostic Scenarios

CircuitSage is deliberately scoped.
When the system cannot establish sufficient technical evidence for a requested component or diagnostic scenario, it should not generate a fabricated diagnosis.

The intended behavior is to communicate that the requested scenario is currently outside the supported CircuitSage V1.0 scope.
This scope control is an important part of maintaining evidence-grounded behavior.
24. Why This Is More Than a Simple LLM Chatbot

A simple LLM chatbot could follow:
User
  ↓
LLM
  ↓
Answer

CircuitSage instead follows:
User
  ↓
Scope Gate
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
Diagnostic Response

The difference is the presence of explicit evidence collection, deterministic tools, state/evidence accumulation, reasoning constraints, and output validation.
The LLM is therefore one component of the overall system.

# Why the Workflow Is Agentic

CircuitSage coordinates multiple steps toward a diagnostic objective:
Observe
   ↓
Evaluate scope
   ↓
Retrieve
   ↓
Validate
   ↓
Collect evidence
   ↓
Reason
   ↓
Validate output
   ↓
Respond

The workflow combines:

- Knowledge retrieval
- Deterministic engineering tools
- Evidence accumulation
- Reasoning
- Output validation
- Engineering verification steps
This multi-stage workflow is the basis for describing CircuitSage as an agentic diagnostic prototype.

## Current Supported Validators
Component	Validator
HC-SR04	hcsr04_v1
DHT11	dht_v1
DHT22	dht_v1
MPU6050	mpu6050_v1
nRF24L01	nrf24_v1


The validator registry is designed so additional component-specific validators can be added without redesigning the entire diagnostic workflow.
27. Current Architectural Limitations
CircuitSage V1.0 has several deliberate limitations.
Limited deterministic validator coverage
Only a defined set of components currently has dedicated validators.
Physical hardware cannot be directly verified
Source-code analysis cannot establish:
- Actual wiring
- Physical power delivery
- Sensor damage
- Breadboard faults
- Loose connections
- Real-world electrical measurements
  
Full visual schematic reasoning is not active
Schematic artifacts are stored and indexed, but complete visual schematic interpretation is not currently part of the main diagnostic path.
Retrieval relevance is not correctness
A highly ranked retrieved project indicates technical relevance but does not prove that the implementation is correct.
Dataset scope limits diagnostic scope
CircuitSage should not claim universal embedded-system diagnostic coverage.

# Architectural Summary

CircuitSage can be summarized as:
┌─────────────────────────────────────────┐
│             CIRCUITSAGE                 │
├─────────────────────────────────────────┤
│                                         │
│  User Input                             │
│       ↓                                 │
│  Scope Gate                             │
│       ↓                                 │
│  Knowledge Retrieval                    │
│       ↓                                 │
│  Deterministic Validation               │
│       ↓                                 │
│  Evidence Package                       │
│       ↓                                 │
│  Evidence-Constrained Reasoning         │
│       ↓                                 │
│  Output Validation                      │
│       ↓                                 │
│  Diagnostic + Verification Steps        │
│                                         │
└─────────────────────────────────────────┘

## The central architectural idea is:
CircuitSage does not ask an LLM to guess what is wrong. It builds an evidence package first and uses reasoning to interpret that evidence.
