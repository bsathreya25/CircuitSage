import { useState } from "react";
import "./App.css";

type ValidatorCheck = {
  check_id?: string;
  name?: string;
  status?: string;
  evidence?: string;
};

type DiagnosticResponse = {
  status: string;
  accepted: boolean;
  component?: string | null;
  diagnosis?: string;
  evidence?: Array<Record<string, unknown>>;
  unknowns?: string[];
  verification_steps?: string[];
  retrieved_projects?: Array<Record<string, unknown>>;
  validator?: {
    validator_id?: string;
    component?: string;
    overall_status?: string;
    summary?: {
      total?: number;
      passed?: number;
      failed?: number;
      unknown?: number;
    };
    checks?: ValidatorCheck[];
  };
  limitations?: string[];
  error?: string | null;
};

type Message = {
  role: "user" | "assistant";
  content?: string;
  result?: DiagnosticResponse;
};

function extractSection(
  diagnosis: string | undefined,
  startPattern: RegExp,
  endPattern?: RegExp,
) {
  if (!diagnosis) return "";

  const startMatch = diagnosis.match(startPattern);

  if (!startMatch || startMatch.index === undefined) {
    return "";
  }

  const contentStart =
    startMatch.index + startMatch[0].length;

  const remaining = diagnosis.slice(contentStart);

  if (!endPattern) {
    return remaining.trim();
  }

  const endMatch = remaining.match(endPattern);

  return (
    endMatch?.index !== undefined
      ? remaining.slice(0, endMatch.index)
      : remaining
  ).trim();
}

function extractVerification(diagnosis?: string) {
  const section = extractSection(
    diagnosis,
    /6\.\s*NEXT ENGINEERING VERIFICATION/i,
  );

  if (!section) return [];

  return section
    .split("\n")
    .map((line) =>
      line
        .replace(/^\s*[-•]\s*/, "")
        .trim(),
    )
    .filter(Boolean);
}

function cleanIssue(text: string) {
  return text
    .replace(/^\s*[-:]\s*/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function App() {
  const [problem, setProblem] = useState("");
  const [code, setCode] = useState("");
  const [serialOutput, setSerialOutput] = useState("");

  const [showCode, setShowCode] = useState(false);
  const [showSerial, setShowSerial] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const [detailsOpen, setDetailsOpen] = useState<number | null>(
    null,
  );

  const diagnose = async () => {
    if (!problem.trim() || loading) return;

    const problemText = problem.trim();
    const submittedCode = code.trim();
    const submittedSerial = serialOutput.trim();

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: problemText,
      },
    ]);

    setProblem("");
    setShowCode(false);
    setShowSerial(false);
    setLoading(true);

    try {
      const response = await fetch("/api/diagnose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          problem_description: problemText,
          code: submittedCode || undefined,
          serial_output: submittedSerial || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Diagnostic request failed");
      }

      const data: DiagnosticResponse =
        await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          result: data,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't connect to the CircuitSage diagnostic engine. Make sure the backend is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      diagnose();
    }
  };

  const statusClass = (status?: string) => {
    switch (status) {
      case "SUPPORTED":
        return "supported";

      case "INSUFFICIENT_EVIDENCE":
        return "insufficient";

      case "UNSUPPORTED":
        return "unsupported";

      default:
        return "";
    }
  };

  const renderDiagnosticResult = (
    result: DiagnosticResponse,
    index: number,
  ) => {
    const validatorStatus =
      result.validator?.overall_status;

    const validatorSummary =
      result.validator?.summary;

    const validatorChecks =
      result.validator?.checks?.filter(
        (check) => check.status === "PASS",
      ) ?? [];

    let primaryDiagnosis = "";

    if (validatorStatus === "PASS") {
      primaryDiagnosis =
        "Code-level validation passed. No software-side fault was identified by the available deterministic checks.";
    } else if (validatorStatus === "FAIL") {
      const failedChecks =
        result.validator?.checks?.filter(
          (check) => check.status === "FAIL",
        ) ?? [];

      if (failedChecks.length > 0) {
        primaryDiagnosis =
          `A code-level issue was detected during deterministic validation: ${
            failedChecks[0].name ??
            failedChecks[0].check_id ??
            "validation check failed"
          }.`;
      } else {
        primaryDiagnosis =
          "A code-level issue was detected during deterministic validation.";
      }
    } else {
      const confirmedIssue = cleanIssue(
        extractSection(
          result.diagnosis,
          /1\.\s*CONFIRMED ISSUE/i,
          /2\.\s*CONFIRMED EVIDENCE/i,
        ),
      );

      primaryDiagnosis =
        confirmedIssue ||
        "No confirmed malfunction has been established from the available evidence.";
    }

    const meaningfulUnknowns =
      result.unknowns?.filter(
        (item) =>
          !item
            .toLowerCase()
            .includes("schematic analysis"),
      ) ?? [];

    let verification: string[] = [];

    if (validatorStatus === "PASS") {
      verification = [
        "Verify TRIG and ECHO wiring directly against the circuit schematic.",
        "Verify the sensor has stable power and a common ground with the Arduino.",
        "Open Serial Monitor at 9600 baud and capture the actual distance readings.",
        "Test the sensor against a known physical distance and compare the measured value.",
      ];
    } else if (result.verification_steps?.length) {
      verification = result.verification_steps;
    } else {
      verification = extractVerification(
        result.diagnosis,
      );
    }

    const isDetailsOpen =
      detailsOpen === index;

    return (
      <div className="diagnostic-result">
        <div className="result-status-row">
          <span
            className={`result-status ${statusClass(
              result.status,
            )}`}
          >
            {result.status?.replaceAll("_", " ")}
          </span>

          {result.component && (
            <span className="result-component">
              · {result.component}
            </span>
          )}
        </div>

        <div className="diagnosis">
          {primaryDiagnosis}
        </div>

        {validatorChecks.length > 0 && (
          <section className="result-section">
            <div className="result-heading">
              Confirmed evidence
            </div>

            <ul className="evidence-list">
              {validatorChecks.map(
                (check, checkIndex) => (
                  <li key={checkIndex}>
                    <strong>
                      {check.name ??
                        check.check_id ??
                        "Validation check"}
                    </strong>

                    {check.evidence && (
                      <span className="evidence-detail">
                        {" "}
                        — {check.evidence}
                      </span>
                    )}
                  </li>
                ),
              )}
            </ul>

            {validatorSummary && (
              <div className="validation-summary">
                {validatorSummary.passed ?? 0}/
                {validatorSummary.total ?? 0} checks passed
              </div>
            )}
          </section>
        )}

        {meaningfulUnknowns.length > 0 && (
          <section className="result-section">
            <div className="result-heading">
              What we don't know
            </div>

            <ul className="evidence-list">
              {meaningfulUnknowns.map(
                (item, itemIndex) => (
                  <li key={itemIndex}>{item}</li>
                ),
              )}
            </ul>
          </section>
        )}

        {verification.length > 0 && (
          <section className="result-section">
            <div className="result-heading">
              Next verification
            </div>

            <ul className="evidence-list">
              {verification.map(
                (item, itemIndex) => (
                  <li key={itemIndex}>{item}</li>
                ),
              )}
            </ul>
          </section>
        )}

        <div className="details">
          <button
            className="details-toggle"
            onClick={() =>
              setDetailsOpen(
                isDetailsOpen ? null : index,
              )
            }
          >
            {isDetailsOpen
              ? "Hide details"
              : "Details"}
          </button>

          {isDetailsOpen && (
            <div className="details-content">
              {result.validator && (
                <div className="detail-block">
                  <span>Validator</span>

                  <pre>
                    {JSON.stringify(
                      result.validator,
                      null,
                      2,
                    )}
                  </pre>
                </div>
              )}

              {result.retrieved_projects &&
                result.retrieved_projects.length > 0 && (
                  <div className="detail-block">
                    <span>
                      Retrieved projects
                    </span>

                    <ul>
                      {result.retrieved_projects.map(
                        (project, projectIndex) => (
                          <li key={projectIndex}>
                            {String(
                              project.project_name ??
                                "Unknown project",
                            )}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}

              {result.limitations &&
                result.limitations.length > 0 && (
                  <div className="detail-block">
                    <span>Limitations</span>

                    <ul>
                      {result.limitations.map(
                        (
                          item,
                          limitationIndex,
                        ) => (
                          <li
                            key={
                              limitationIndex
                            }
                          >
                            {item}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          CircuitSage
        </div>

        <div className="status">
          <span className="status-dot" />
          Ready
        </div>
      </header>

      <main className="chat">
        {messages.length === 0 ? (
          <section className="welcome">
            <h1>
              What’s wrong with your circuit?
            </h1>

            <p>
              Describe the problem and
              CircuitSage will investigate it.
            </p>
          </section>
        ) : (
          <section className="messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${message.role}`}
              >
                {message.role === "assistant" && (
                  <div className="assistant-label">
                    CircuitSage
                  </div>
                )}

                {message.role === "user" ? (
                  <div className="message-content">
                    {message.content}
                  </div>
                ) : message.result ? (
                  renderDiagnosticResult(
                    message.result,
                    index,
                  )
                ) : (
                  <div className="message-content">
                    {message.content}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="assistant-label">
                  CircuitSage
                </div>

                <div className="thinking">
                  Investigating
                  <span>...</span>
                </div>
              </div>
            )}
          </section>
        )}

        <section className="composer-wrapper">
          {showCode && (
            <textarea
              className="attachment-input"
              placeholder="Paste your Arduino code..."
              value={code}
              onChange={(event) =>
                setCode(event.target.value)
              }
            />
          )}

          {showSerial && (
            <textarea
              className="attachment-input serial"
              placeholder="Paste serial monitor output..."
              value={serialOutput}
              onChange={(event) =>
                setSerialOutput(
                  event.target.value,
                )
              }
            />
          )}

          <div className="composer">
            <textarea
              value={problem}
              onChange={(event) =>
                setProblem(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Describe your circuit problem..."
              rows={1}
            />

            <div className="composer-bottom">
              <div className="tools">
                <button
                  className={
                    showCode
                      ? "tool active"
                      : "tool"
                  }
                  onClick={() =>
                    setShowCode(!showCode)
                  }
                >
                  + Code
                </button>

                <button
                  className={
                    showSerial
                      ? "tool active"
                      : "tool"
                  }
                  onClick={() =>
                    setShowSerial(!showSerial)
                  }
                >
                  + Serial
                </button>

                <button
                  className="tool disabled"
                  title="Coming soon"
                >
                  + Schematic
                </button>
              </div>

              <button
                className="send"
                onClick={diagnose}
                disabled={
                  !problem.trim() || loading
                }
                aria-label="Send"
              >
                ↑
              </button>
            </div>
          </div>

          <div className="hint">
            CircuitSage can make mistakes. Verify
            findings against your hardware.
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;