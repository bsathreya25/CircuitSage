# CircuitSage Demo Guide

## Hackathon Demonstration Workflow

This document provides a repeatable demonstration workflow for CircuitSage.
The purpose of the demo is to show that CircuitSage is not simply an LLM chatbot.

The demonstration should make the following architecture visible:

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
Diagnostic Response

The recommended demonstration uses three scenarios:
1. A supported and healthy embedded-system implementation
2. A supported implementation containing a deterministic code-level fault
3. An unsupported diagnostic scenario
These three cases demonstrate the system's ability to:
- Diagnose within supported scope
- Identify concrete software-side problems
- Preserve uncertainty
- Refuse unsupported diagnostic scenarios rather than inventing an answer
- 
## Demo Objective
   
The main objective of the demonstration is to show the difference between:
Generic LLM response and Evidence-driven embedded-system diagnosis

CircuitSage should demonstrate that it:
- Checks diagnostic scope
- Retrieves relevant technical evidence
- Uses deterministic validators
- Separates PASS, FAIL, and UNKNOWN
- Does not treat physical assumptions as facts
- Uses reasoning to interpret collected evidence
- Provides engineering verification steps
- Does not fabricate unsupported diagnoses
  
## Recommended Demo Sequence

The recommended sequence is:
Demo 1
Healthy HC-SR04
       ↓
Demo 2
Faulty HC-SR04 code
       ↓
Demo 3
Unsupported Raspberry Pi camera

This sequence is useful because the three cases demonstrate progressively stronger behavior:
Supported + healthy
        ↓
Supported + code-level fault
        ↓
Unsupported scenario

## Demo Environment
CircuitSage consists of a frontend and backend.
The development architecture is:
Browser
   │
   ▼
React / Vite Frontend
   │
   │ /api
   ▼
FastAPI Backend
   │
   ▼
CircuitSage Diagnostic Engine

The frontend provides the user interface.
The backend performs the diagnostic workflow.

## Starting the Backend
   
The backend is provided through the FastAPI application.
The exact launch command depends on the current repository entry point and local environment.
The backend should be running before the frontend is used.
The API health endpoint can be used to confirm that the service is available:
GET /health

A healthy service returns a response indicating:
{
  "status": "ok",
  "service": "CircuitSage API",
  "version": "1.0.0"
}

## Starting the Frontend
The frontend is located in:
frontend/

From the frontend directory, install dependencies if necessary:
npm install

Then start the development server:
npm run dev

The Vite development server provides the browser interface.
The frontend communicates with the backend through the configured development proxy.

## Demo 1 — Healthy HC-SR04

Objective
Demonstrate a supported component where the available software evidence does not establish a confirmed code-level fault.
The component is:
HC-SR04

The corresponding deterministic validator is:
hcsr04_v1

What to Enter
Use a diagnostic request describing an HC-SR04 distance-reading problem and provide the relevant Arduino code.
A representative request can be:
My HC-SR04 is not giving the expected distance. Please inspect the code and identify whether there is a software-side problem.

Provide the healthy HC-SR04 implementation used by the demo dataset.
Expected Diagnostic Flow
CircuitSage should process the request through:
User Query
    ↓
Scope Gate
    ↓
HC-SR04 Retrieval
    ↓
HC-SR04 Deterministic Validator
    ↓
Evidence Package
    ↓
Reasoning
    ↓
Diagnostic Response

Expected Validation Behavior
The validator checks:
HC001 — TRIG defined
HC002 — ECHO defined
HC003 — TRIG OUTPUT
HC004 — ECHO INPUT
HC005 — Trigger pulse
HC006 — pulseIn()
HC007 — Distance calculation
HC008 — Serial output

A healthy implementation should produce evidence consistent with the expected software implementation.
What to Point Out
During the demo, emphasize:
"CircuitSage is not claiming that the sensor is physically working. It is saying that the available software evidence does not establish a confirmed software-side fault."

This demonstrates the distinction between:
Software evidence and Physical hardware verification

## Demo 2 — Faulty HC-SR04 Code
Objective
Demonstrate deterministic fault detection.
Use the same general HC-SR04 scenario, but provide code containing a known implementation contradiction.
For example:
pinMode(trigPin, INPUT);

The HC-SR04 TRIG pin is expected to be configured as an output.
Expected Diagnostic Flow
User Query
    ↓
Scope Gate
    ↓
HC-SR04 Retrieval
    ↓
HC-SR04 Validator
    ↓
Deterministic FAIL
    ↓
Evidence Package
    ↓
Reasoning
    ↓
Diagnostic Response

Expected Finding
The validator should identify:
HC003
TRIG configured as OUTPUT as a failed software-side condition when the supplied implementation configures TRIG incorrectly.
The important distinction is:
Confirmed:
The source code contains a configuration contradiction.

Not confirmed:
The physical sensor is damaged.

What to Tell the Judges
A useful explanation is:
"The LLM didn't simply guess that the sensor is broken. CircuitSage first ran a deterministic validator, found a concrete contradiction in the code, and then used reasoning to explain what that finding means."

This is one of the strongest demonstrations of the architecture.
## Demo 3 — Unsupported Raspberry Pi Camera
Objective
Demonstrate that CircuitSage has an explicit scope boundary.
Use a diagnostic request involving a Raspberry Pi camera scenario that is outside the current supported diagnostic scope.
For example:
My Raspberry Pi camera is not working. Diagnose the problem.

Expected Behavior
CircuitSage should identify the scenario as:
UNSUPPORTED

rather than inventing a detailed diagnosis.
The response should communicate that the requested component or diagnostic scenario is not currently supported by CircuitSage V1.0.
Why This Matters
This demonstrates an important architectural property:
Generic LLM
     ↓
May attempt an answer

CircuitSage
     ↓
Scope Gate
     ↓
Unsupported
     ↓
No fabricated diagnosis

This is intentional behavior.

## Demonstrating UNKNOWN
    
The demo can also be used to explain the UNKNOWN state.
For example, source code may show:
TRIG configured correctly
ECHO configured correctly
Distance calculation present

while the system still cannot establish:
Physical wiring
Sensor power
Sensor damage
Actual electrical signal

The correct interpretation is:
UNKNOWN

rather than:
FAIL

This distinction is central to CircuitSage's diagnostic philosophy.

## The Three-State Model

During the demo, explain the validation model:
             Evidence
                │
       ┌────────┼────────┐
       │        │        │
       ▼        ▼        ▼
      PASS     FAIL    UNKNOWN
       │        │        │
       ▼        ▼        ▼
   Evidence   Known    Evidence
   supports   code     insufficient
   expected   problem  to conclude
   behavior

The important rule is:
UNKNOWN ≠ FAIL

## What the Demo Proves

The demonstration is intended to establish several properties of CircuitSage.
1. Scope awareness
CircuitSage does not assume every embedded-system problem is supported.
2. Retrieval
The system retrieves technically relevant embedded-system evidence from the canonical corpus.
3. Deterministic analysis
Supported components can be checked using explicit validation rules.
4. Evidence packaging
The system organizes retrieved and deterministic findings into structured diagnostic evidence.
5. Constrained reasoning
The LLM reasons over available evidence rather than being asked to invent a fault.
6. Explicit uncertainty
The system distinguishes confirmed findings from information that remains unknown.
7. Verification-oriented output
The system identifies what should be checked next rather than stopping at a speculative diagnosis.

## What the Demo Does Not Prove
    
The demonstration does not establish that CircuitSage can:
- Diagnose every Arduino project
- Diagnose every embedded-system platform
- Detect every physical hardware failure
- Inspect physical wiring directly
- Measure electrical signals independently
- Fully interpret every schematic visually
- Guarantee that a retrieved project is correct
- Replace laboratory hardware debugging
These are outside the demonstrated V1.0 scope.

## Suggested Judge Explanation: 

If asked:
"What makes this different from simply using Gemini or ChatGPT?"

A concise explanation is:
"The language model is not the first or only step. CircuitSage first determines whether the problem is within scope, retrieves relevant embedded-system evidence, runs deterministic validators when available, packages the findings and unknowns, and only then uses constrained reasoning to explain the result."

## Suggested Architecture Explanation

If a judge asks:
"Where is the agentic part?"

Explain the workflow:
Observe
  ↓
Scope
  ↓
Retrieve
  ↓
Validate
  ↓
Collect Evidence
  ↓
Reason
  ↓
Validate Output
  ↓
Respond

The system coordinates multiple tools and reasoning stages toward the same diagnostic objective.
The LLM is therefore one component of the agentic workflow rather than the entire application.

## Suggested Dataset Explanation
    
If asked:
"Where does the technical knowledge come from?"

Explain:
"CircuitSage uses a curated canonical corpus of 89 embedded-system projects derived from a larger Arduino-oriented project collection. The raw dataset is kept separate, while the curated corpus is indexed for retrieval."

The important distinction is:
Raw Dataset
     ↓
Curated Canonical Corpus
     ↓
Retrieval Index
     ↓
Diagnostic Evidence

## Suggested Validator Explanation

If asked:
"Why use deterministic validators?"

Explain:
"Whenever we know how to check something explicitly, we prefer deterministic validation over asking the LLM to infer it."

For example, an HC-SR04 validator can explicitly check whether:
TRIG is defined
TRIG is OUTPUT
ECHO is INPUT
pulseIn() exists
Distance calculation exists

The LLM can then reason over those findings.

## Suggested Uncertainty Explanation

If asked:
"Can CircuitSage tell whether the sensor is physically broken?"

Answer:
"Not from source code alone. CircuitSage explicitly distinguishes software evidence from physical-world evidence. If the available evidence cannot establish a physical condition, it reports that information as unknown and identifies what should be verified next."

## Recommended Live Demo Timing

A concise demonstration can follow this structure:
0:00 – 1:00
Problem and motivation

1:00 – 2:00
Architecture overview

2:00 – 4:00
Healthy HC-SR04 case

4:00 – 6:00
Faulty HC-SR04 case

6:00 – 7:00
Unsupported Raspberry Pi camera case

7:00 – 8:00
Explain agentic architecture

8:00 – 10:00
Questions

The exact timing can be adjusted to the hackathon's presentation rules.

## Demo Checklist
    
Before presenting, verify:
[ ] Backend starts successfully
[ ] /health responds successfully
[ ] Frontend starts successfully
[ ] Frontend can communicate with backend
[ ] Healthy HC-SR04 case works
[ ] Faulty HC-SR04 case works
[ ] Unsupported case works
[ ] No API key or secret is exposed
[ ] Demo code is ready
[ ] Browser tab is prepared
[ ] Backup screenshots/results are available

## Demo Backup Plan
    
If the live environment fails, the demonstration should still be explainable using previously validated outputs.
Useful backup material includes:
- Healthy HC-SR04 result
- Faulty HC-SR04 result
- Unsupported-component result
- Architecture diagram
- Validator output
- Backend test result
The backup should be presented as previously validated evidence rather than as a new live execution.

## Core Demo Message
The most important message of the demonstration is CircuitSage is designed to determine what can actually be established from embedded-system evidence, rather than simply generating a plausible-sounding answer.

# Final Demo Summary

The complete demonstration is:
                CIRCUITSAGE DEMO

                     User
                       │
                       ▼
               Diagnostic Query
                       │
                       ▼
                 Scope Gate
                 /    |    \
                /     |     \
               ▼      ▼      ▼
          Supported  ...  Unsupported
               │             │
               ▼             ▼
           Retrieval       Stop
               │
               ▼
       Deterministic Validator
               │
          ┌────┴────┐
          ▼         ▼
         PASS      FAIL
          │         │
          └────┬────┘
               ▼
        Evidence Package
               │
               ▼
       Constrained Reasoning
               │
               ▼
       Output Validation
               │
               ▼
        Diagnostic Response

The three core scenarios are:
1. Healthy HC-SR04
   → Supported + software evidence consistent

2. Faulty HC-SR04 code
   → Supported + deterministic code-level finding

3. Unsupported Raspberry Pi camera
   → Unsupported + no fabricated diagnosis

Together, these cases demonstrate the central design of CircuitSage:
Retrieve evidence, validate what can be checked deterministically, preserve what remains unknown, and use AI reasoning only within those evidence boundaries.
