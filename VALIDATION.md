# CircuitSage Validation

## Validation Strategy and Test Results

CircuitSage is designed as an evidence-driven diagnostic system, so validation focuses on more than whether the application starts successfully.

The validation process evaluates:

1. Scope handling
2. Retrieval behavior
3. Deterministic validators
4. PASS / FAIL / UNKNOWN semantics
5. Evidence construction
6. Reasoning behavior
7. API behavior
8. Frontend behavior
9. Unsupported and insufficient-evidence cases

The goal is to verify that CircuitSage produces diagnostics that remain grounded in the evidence available to the system.

# Validation Philosophy

CircuitSage follows a layered validation approach.

Application
    ↓
API Validation
    ↓
Scope Validation
    ↓
Retrieval Validation
    ↓
Deterministic Validation
    ↓
Evidence Validation
    ↓
Reasoning Validation
    ↓
Frontend Validation

Each layer tests a different part of the diagnostic workflow.
A successful application build alone is therefore not considered sufficient evidence that the diagnostic system is functioning correctly.

## Validation Objectives

The validation process is intended to establish that CircuitSage can:
- Recognize supported diagnostic scenarios
- Reject unsupported scenarios
- Distinguish insufficient evidence from unsupported scope
- Retrieve technically relevant projects
- Execute supported deterministic validators
- Produce PASS, FAIL, and UNKNOWN findings correctly
- Preserve uncertainty instead of inventing faults
- Construct structured diagnostic evidence
- Produce constrained reasoning where appropriate
- Return valid API responses
- Render diagnostic results through the frontend
  
## Backend Test Suite
   
The CircuitSage backend was validated using the project's automated test suite.
The final backend test result was:
53 tests passed

This represents the current automated backend validation baseline for the MVP.
The test suite covers multiple parts of the diagnostic pipeline rather than testing only the API surface.

## Scope Gate Validation

The Scope Gate was tested to ensure that CircuitSage does not treat every request as automatically diagnosable.
The expected states are:
SUPPORTED
INSUFFICIENT_EVIDENCE
UNSUPPORTED

Supported Case
A request should be classified as SUPPORTED when:
- Relevant evidence is retrieved
- The retrieval evidence is sufficiently strong
- Appropriate code or serial-output evidence is available
This allows the request to continue into the diagnostic pipeline.

## Insufficient Evidence Case

A request should be classified as INSUFFICIENT_EVIDENCE when CircuitSage recognizes the relevant technical area but cannot establish enough evidence for a grounded diagnosis.
This prevents the system from treating missing information as proof of a fault.
Unsupported Case
A request should be classified as UNSUPPORTED when the requested component or diagnostic scenario does not have sufficient matching technical support.
The system should explicitly identify the unsupported scope rather than fabricate a diagnosis.

## Retrieval Validation

The retrieval layer was validated using representative embedded-system projects and component queries.
Representative validation targets included:
HC-SR04
DHT11 / DHT22
MPU6050
nRF24L01
GSM
Stepper motor systems

The objective was not to require a particular project to always appear as the first result.
Instead, retrieval was evaluated for whether it could surface technically relevant evidence from the canonical corpus.

## Retrieval Ranking Interpretation

Retrieval scores are used for relevance ranking.
They are not treated as correctness scores.
The current weighting system gives greater importance to fields such as:
Component
Library
Diagnostic signal

followed by:
Source file
Artifact file
Project name
Interface
Category

Therefore:
High retrieval relevance
        ≠
Confirmed implementation correctness

Correctness is established separately through deterministic validation and evidence-based reasoning.

## Representative Retrieval Validation

Representative corpus checks included known projects associated with:
Component / System	Representative Project ID
HC-SR04	8
DHT11 / DHT22	1
MPU6050	50
nRF24L01	15
GSM	22
Stepper	145

These cases were used to verify that the retrieval system could identify technically relevant project evidence.
The retrieval system is not required to return the expected project as the first result in every case.
The validation objective is technical relevance rather than a rigid ranking position.

## Deterministic Validator Validation

CircuitSage currently provides dedicated deterministic validation for:
Component	Validator
HC-SR04	hcsr04_v1
DHT11	dht_v1
DHT22	dht_v1
MPU6050	mpu6050_v1
nRF24L01	nrf24_v1

These validators operate through explicit rules rather than relying entirely on LLM interpretation.

## HC-SR04 Validation

The HC-SR04 validator contains eight checks.
Check	Validation
HC001	TRIG pin is defined
HC002	ECHO pin is defined
HC003	TRIG is configured as OUTPUT
HC004	ECHO is configured as INPUT
HC005	Trigger pulse is generated
HC006	pulseIn() is used
HC007	Distance calculation is present
HC008	Serial output is present


These checks provide deterministic evidence about the implementation.

## HC-SR04 Healthy Implementation

A healthy implementation should satisfy the expected software-side checks.
For example:
TRIG defined
      ↓
ECHO defined
      ↓
TRIG OUTPUT
      ↓
ECHO INPUT
      ↓
Trigger pulse
      ↓
pulseIn()
      ↓
Distance calculation
      ↓
Serial output

When the expected conditions are present, the validator can return PASS findings for the corresponding checks.
This establishes consistency with the expected software implementation.
It does not establish that the physical sensor or wiring is functional.


## HC-SR04 Failure Detection

The validator can also identify explicit code-level contradictions.
For example:
pinMode(trigPin, INPUT);

contradicts the expected HC-SR04 implementation when the TRIG pin should be configured as an output.
The validator can therefore identify:
HC003 — FAIL

This is a deterministic software finding.
It should not automatically be interpreted as proof that the physical HC-SR04 module is damaged.

## UNKNOWN Validation

A major part of CircuitSage validation is ensuring that missing evidence does not automatically become failure.
For example:
Physical wiring cannot be inspected from source code.

should remain an unknown condition rather than being converted into:
FAIL

The system therefore follows:
UNKNOWN ≠ FAIL

This behavior is important because embedded-system failures frequently involve physical conditions that cannot be established from firmware alone.

## Deterministic Validator Registry

The validator registry maps supported component names to deterministic validation functions.
Conceptually:
Component
    ↓
Validator Registry
    ↓
Component-specific validator
    ↓
PASS / FAIL / UNKNOWN findings

The current registry supports:
HC-SR04
HCSR04
DHT11
DHT22
MPU6050
nRF24L01
nRF24

Aliases are supported where appropriate so that equivalent component naming does not prevent the correct validator from being selected.

## Evidence Package Validation

The diagnostic pipeline constructs an evidence package containing structured information such as:
user_query
scope_status
component
retrieved_projects
validator_result
schematic_evidence
engineering_parameters
known_unknowns

Validation of this layer focuses on ensuring that reasoning receives structured evidence rather than only the original user question.
This creates a clear separation:
Evidence Collection
        ↓
Evidence Package
        ↓
Reasoning

## Engineering Parameter Validation

Representative engineering parameters were validated during diagnostic testing.
For HC-SR04 examples, the evidence package can contain values such as:
Sensor: HC-SR04
TRIG pin: 11
ECHO pin: 12
Serial baud rate: 9600
Loop delay: 250 ms
Trigger pulse: 10 µs

These values provide concrete technical context for downstream reasoning.

## Reasoning Validation

The reasoning pipeline is constrained by the evidence collected earlier in the workflow.
The reasoning structure includes:
confirmed_issue
confirmed_evidence
unknown_information
possible_explanations
potential_consequences
next_engineering_verification

The reasoning layer is expected to preserve the distinction between:
Confirmed evidence and Possible explanation

This prevents speculative explanations from being presented as established faults.

## LLM Safety and Evidence Constraints

The reasoning layer follows explicit constraints.
Important rules include:
Never invent physical measurements.
Never treat the user problem report as proof of malfunction.
Never treat UNKNOWN as FAILURE.

The LLM is therefore expected to reason from the evidence package rather than generate unsupported hardware observations.

## Deterministic Reasoning Path

When deterministic evidence is sufficient to establish the relevant conclusion, the system can avoid unnecessary generative reasoning.
This is particularly useful for:
- Known code-level contradictions
- Explicit validator failures
- Cases where the available evidence is insufficient and the correct response is uncertainty
The intended behavior is:
Deterministic evidence
        ↓
Can conclusion be established?
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   ▼         ▼
Reason      Continue
directly    with appropriate
            evidence/reasoning

This reduces unnecessary dependence on generative output.

## Unsupported Component Validation

CircuitSage was tested with unsupported diagnostic scenarios.
A representative unsupported case is a component or system for which the current CircuitSage diagnostic pipeline has no sufficient supported evidence.
The expected result is:
UNSUPPORTED
rather than a fabricated technical diagnosis.
For example, an unsupported Raspberry Pi camera diagnostic should not be presented as though CircuitSage has a dedicated camera diagnostic model.

## API Validation

The backend API was validated through its primary endpoints.
Health
GET /health

The expected response indicates that the CircuitSage API service is operational.
A representative response is:
{
  "status": "ok",
  "service": "CircuitSage API",
  "version": "1.0.0"
}

Diagnosis
POST /diagnose

The diagnostic endpoint was validated through the backend test suite and representative frontend diagnostic flows.

## Frontend Validation

The frontend was validated using the production build process.
The frontend build completed successfully using:
npm run build

The build used the project's Vite-based React frontend.
The production build completed successfully without build errors.

## Frontend Diagnostic Cases

Representative frontend diagnostic cases included:
Healthy HC-SR04
The interface displayed a supported diagnostic result with deterministic validation evidence.
The result indicated that the available software evidence did not establish a confirmed software-side malfunction.
Physical conditions such as actual wiring and hardware condition remained unknown

Broken HC-SR04 Code Configuration
A deliberately incorrect HC-SR04 implementation was used to verify that deterministic validation could identify a concrete code-level contradiction.
The resulting diagnostic reflected the failed validator check rather than claiming an unverified physical hardware failure.

Unsupported Component
An unsupported Raspberry Pi camera scenario was used to verify scope control.
The expected result was:
UNSUPPORTED
with no fabricated malfunction diagnosis.

## Validation of Physical Unknowns
    
CircuitSage deliberately preserves uncertainty around conditions that source-code analysis cannot establish.
The following should remain unverified unless additional evidence is provided:
- Physical wiring
- Power delivery
- Hardware damage
- Loose connections
- Actual sensor output
- Real-world electrical measurements
This is an intentional validation requirement rather than an implementation defect.

## Artifact Validation

The dataset contains image/PDF artifacts associated with projects.
Validation confirms that these artifacts exist within the curated dataset and are represented by the artifact/indexing layer.
However, artifact presence does not imply complete visual interpretation.
Therefore the validation claim is:
Artifact availability

rather than:
Complete automated schematic validation

## Regression Testing

The automated backend test suite provides the main regression baseline for the MVP.
Current baseline:
53 tests passed

Whenever diagnostic logic is modified, the test suite should be rerun to detect regressions in:
- Scope behavior
- Retrieval
- Validators
- Evidence construction
- Reasoning
- API behavior
Frontend changes should additionally be checked with:
npm run build

## Validation Boundaries

The current validation system does not establish that:
- Every possible Arduino project can be diagnosed
- Every physical hardware fault can be detected
- Every schematic is visually interpreted
- Every retrieved project is correct
- Every possible component has a deterministic validator
- Every LLM explanation is independently verified against physical hardware
The validation results apply to the implemented CircuitSage V1.0 MVP and its supported evidence/validator scope.

## Validation Summary

The current validation baseline can be summarized as:
Area	Current Validation
Backend automated tests	53 passed
Scope handling	Validated

Retrieval	Representative corpus tests
HC-SR04 validation	Deterministic checks
DHT11 / DHT22	Deterministic validator
MPU6050	Deterministic validator
nRF24L01	Deterministic validator
Evidence package	Structured validation

LLM reasoning constraints	Validated
API health	Validated
Diagnostic API	Tested
Frontend production build	Passed
Healthy diagnostic flow	Tested
Code-level failure flow	Tested
Unsupported scenario	Tested
Physical hardware verification	Not claimed
Full visual schematic reasoning	Not claimed

# Final Validation Principle
**The central validation principle of CircuitSage is:**
A diagnostic system should be evaluated not only on whether it produces an answer, but on whether the answer remains consistent with the evidence available to the system.
