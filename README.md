# CircuitSage

## Agentic AI for Embedded Systems Diagnostics 

CircuitSage is an agentic diagnostic prototype for debugging embedded-system projects using a combination of document retrieval,code validation, engineering evidence, and evidence-constrained LLM reasoning.

It is designed to answer a more useful engineering question than a generic chatbot:

> **What can be established from the available evidence, what cannot yet be established, and what should be checked next?**

CircuitSage currently focuses on **Arduino-oriented** embedded projects and uses a curated corpus of 89 projects as its retrieval knowledge base.

## What CircuitSage Does

A user can provide an Arduino Based Embedded-system problem together with available evidence such as firmware/code and serial-output information.

CircuitSage then:

1. Determines whether the requested component or diagnostic scenario is within the supported scope.
2. Retrieves technically relevant projects from its canonical knowledge base.
3. Runs deterministic code-level validation when a supported validator is available.
4. Packages the available evidence and known unknowns.
5. Uses constrained LLM reasoning where appropriate.
6. Validates the reasoning output.
7. Returns a concise engineering-oriented diagnosis and recommended next verification steps.

The system is intentionally designed **not to treat an LLM's free-form answer as ground truth**.

# Diagnostic Philosophy

CircuitSage separates three different outcomes.

**PASS**

Deterministic evidence supports the expected implementation.

This does **not** prove that the physical hardware is working.

**FAIL**

A deterministic validator has identified a known code-level contradiction or implementation problem.

This is a software/code-level finding, not automatic proof of a physical hardware failure.

**UNKNOWN**

The available evidence is insufficient to establish a reliable result.

CircuitSage should prefer an explicit **UNKNOWN** over inventing a diagnosis.


## System Architecture

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

The architecture is based on the principle that evidence collection and deterministic validation should happen before generative reasoning.

## **Scope Gate**

The Scope Gate determines whether CircuitSage has enough relevant technical evidence to proceed with a diagnostic request.

CircuitSage distinguishes between three situations:

Supported :
The requested diagnostic scenario has relevant evidence and sufficient information to proceed.

Insufficient Evidence
CircuitSage recognizes relevant technical evidence, but the available information is not sufficient to establish a grounded diagnosis.

Unsupported
The requested component or diagnostic scenario is not currently supported by the available CircuitSage knowledge and diagnostic capabilities.
The system should not fabricate a diagnosis for unsupported scenarios.

## **Retrieval Layer**
CircuitSage uses a curated canonical corpus of 89 projects as its retrieval knowledge base.
The retrieval layer searches this corpus for technically relevant evidence associated with the user's diagnostic request.
Retrieved information can provide context such as:
- Relevant components
- Libraries
- Diagnostic signals
- Source files
- Artifact files
- Project names
- Interfaces
- Project categories
Retrieval establishes technical relevance. It does not by itself establish that an implementation is correct.

**Deterministic Validation**

Where a supported validator exists, CircuitSage performs explicit code-level checks before relying on generative reasoning.
The current deterministic validator coverage includes:
Component	Validator
HC-SR04	hcsr04_v1
DHT11	dht_v1
DHT22	dht_v1
MPU6050	mpu6050_v1
nRF24L01	nrf24_v1


The validator layer is intended to identify concrete implementation evidence rather than generate speculative explanations.
HC-SR04 Validation
The HC-SR04 validator performs eight deterministic checks:
Check	Description
HC001	TRIG pin is defined
HC002	ECHO pin is defined
HC003	TRIG is configured as OUTPUT
HC004	ECHO is configured as INPUT
HC005	Trigger pulse is generated
HC006	pulseIn() measurement is present
HC007	Distance calculation is present
HC008	Serial output is present


These checks allow CircuitSage to distinguish between:
Known implementation evidence and Information that cannot be established from the source code.

Evidence Package
After scope evaluation, retrieval, and deterministic validation, CircuitSage organizes the available information into an evidence package.
The evidence package can contain:
- User query
- Scope status
- Component
- Retrieved projects
- Validator result
- Schematic evidence
- Engineering parameters
- Known unknowns

The purpose of this layer is to provide the reasoning system with a structured representation of the evidence collected during diagnosis.

## **Evidence-Constrained Reasoning**

CircuitSage uses LLM reasoning as one part of the diagnostic pipeline rather than treating the LLM as the diagnostic authority.
The reasoning process is constrained by the evidence available to the system.

Important principles include:
- Do not invent physical measurements.
- Do not treat the user's problem report as proof of malfunction.
- Do not treat UNKNOWN as FAIL.
- Do not claim physical observations that have not been established.
- Distinguish confirmed findings from possible explanations.
- Provide engineering verification steps when evidence is incomplete.
Conceptually:
User Problem
     │
     ▼
Evidence Retrieval
     │
     ▼
Deterministic Validation
     │
     ▼
Evidence Package
     │
     ▼
Constrained Reasoning
     │
     ▼
Diagnostic Explanation

## **Reasoning Output**

The reasoning layer is structured around the following information:
- confirmed_issue
- confirmed_evidence
- unknown_information
- possible_explanations
- potential_consequences
- next_engineering_verification
This structure helps separate established evidence from uncertainty and possible explanations.

## **Schematic and Artifact Handling**

CircuitSage includes schematic/image/PDF artifacts associated with projects in its knowledge base.
However, storing or indexing an artifact does not mean that the system has fully interpreted its visual contents.
The current diagnostic architecture should therefore distinguish between:
Artifact available and Visual schematic reasoning established

Full visual schematic reasoning is outside the current diagnostic scope.

## **Frontend :**

CircuitSage provides a conversational frontend for interacting with the diagnostic system.
The frontend is responsible for:
- Accepting diagnostic requests
- Sending requests to the backend
- Displaying diagnostic results
- Presenting evidence and uncertainty
- Presenting recommended next verification steps

The interface is designed around a concise conversational diagnostic workflow rather than a generic chatbot experience.

## **Backend :**

The backend exposes the diagnostic system through a FastAPI API.
The primary endpoints include:
GET  /health
POST /diagnose
GET /health
Provides a basic service health response.
POST /diagnose
Accepts a diagnostic request and runs it through the CircuitSage diagnostic pipeline.
Repository Structure

The major project areas are organized around the diagnostic system, frontend, and knowledge base.
CircuitSage/
│
├── README.md
│
├── src/
│   ├── api/
│   ├── ...
│
├── frontend/
│
├── knowledge_base/
│
└── data/
    └── canonical/

The exact implementation may contain additional modules and supporting files.

## **Diagnostic Flow Example**

Consider an HC-SR04 project where the user reports an unexpected distance reading.
CircuitSage can process the request approximately as follows:
User reports problem
        │
        ▼
Identify diagnostic scope
        │
        ▼
Retrieve relevant HC-SR04 evidence
        │
        ▼
Run deterministic HC-SR04 validation
        │
        ▼
Construct evidence package
        │
        ▼
Separate confirmed findings from unknowns
        │
        ▼
Apply constrained reasoning
        │
        ▼
Return diagnosis + next verification

For example, if the source code contains a contradictory configuration such as:
pinMode(trigPin, INPUT);
the deterministic validator can identify that the TRIG pin configuration does not match the expected implementation.
The resulting diagnosis can then distinguish the confirmed software-side finding from physical conditions that remain unverified.

## **What CircuitSage Does Not Claim**

CircuitSage does not claim that source-code analysis can directly establish physical hardware conditions.
For example, software evidence alone cannot establish:
- Whether a wire is physically connected
- Whether a sensor is electrically damaged
- Whether a breadboard connection is loose
- Whether the required power supply is physically present
- Whether a real-world electrical measurement is correct

These conditions remain unknown unless appropriate evidence is provided.

## **Design Principles**

CircuitSage follows several core engineering principles.
1. Evidence before inference
Collect available technical evidence before generating conclusions.
2. Deterministic checks before generative reasoning
Known software conditions should be checked explicitly whenever possible.
3. UNKNOWN is not FAILURE
Missing evidence should not automatically be interpreted as a fault.
4. Scope before diagnosis
Unsupported scenarios should not receive fabricated diagnoses.
5. Separate relevance from correctness
Retrieval identifies technically relevant evidence; deterministic validation establishes implementation findings.
6. Never invent physical measurements
The system must distinguish source-code evidence from physical-world observations.
7. Verification over speculation
When evidence is insufficient, the system should identify what should be checked next.

## **Current Limitations**
CircuitSage V1.0 has several deliberate limitations.

1. Limited validator coverage
2. Only a defined set of components currently has dedicated deterministic validators.
3. Physical hardware cannot be directly verified
4. The diagnostic system primarily works with the evidence supplied to it and cannot independently inspect physical wiring or hardware condition.
5. Visual schematic reasoning is limited
6. Schematic and other artifacts may be available in the knowledge base, but complete visual interpretation is not part of the current diagnostic path.
7. Retrieval does not equal correctness
8. A retrieved project can be technically relevant without being proof that the user's implementation is correct.
9. Diagnostic scope is limited
10. CircuitSage should not be presented as a universal embedded-systems troubleshooting system.

## **Project Status**

CircuitSage is an MVP / hackathon prototype focused on demonstrating an evidence-driven approach to embedded-system diagnostics.
The current system combines:
Technical Retrieval
        +
Deterministic Validation
        +
Evidence Packaging
        +
Constrained Reasoning
        +
Diagnostic Verification Steps

The architecture is intentionally designed so that additional validators, evidence sources, and diagnostic capabilities can be added incrementally.

## **Future Directions**

Potential future development areas include:
- Additional deterministic component validators
- Expanded embedded-system coverage
- Deeper schematic interpretation
- Additional engineering evidence sources
- More diagnostic tools
- Expanded verification workflows
- More structured hardware-test integration

These are future directions rather than claims about the current V1.0 implementation.

## **Core Idea**

CircuitSage is built around one central principle:
**Do not ask an LLM to guess what is wrong. Build the available engineering evidence first, determine what can actually be established, and use reasoning to explain that evidence and identify what should be verified next.**
