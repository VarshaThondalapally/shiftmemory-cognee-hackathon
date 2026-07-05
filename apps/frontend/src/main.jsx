import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BadgeCheck,
  ClipboardList,
  Eye,
  MessageSquareText,
  Moon,
  Plus,
  RefreshCw,
  RotateCcw,
  Trash2,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const screens = [
  {
    id: "notes",
    label: "Night caregiver",
    icon: Moon,
    title: "End the night without losing the small details.",
    body: "Save what changed once. The morning team can open their handoff later without chasing a chat thread.",
  },
  {
    id: "handoff",
    label: "Morning lead",
    icon: ClipboardList,
    title: "Start the morning with the right context.",
    body: "The morning lead gets a clean handoff and can ask follow-up questions without asking the night caregiver to repeat everything.",
  },
  {
    id: "review",
    label: "Supervisor",
    icon: BadgeCheck,
    title: "Keep the handoff accurate.",
    body: "A supervisor can mark what matters or remove stale notes before they keep shaping future handoffs.",
  },
  {
    id: "proof",
    label: "Proof mode",
    icon: Eye,
    title: "Show what the memory layer actually did.",
    body: "This screen is for judges and engineers: it exposes the redacted remember, recall, improve, and forget traces behind the product flow.",
  },
];

const roleToScreen = {
  night: "notes",
  caregiver: "notes",
  notes: "notes",
  morning: "handoff",
  lead: "handoff",
  handoff: "handoff",
  supervisor: "review",
  review: "review",
  proof: "proof",
};

const screenToRole = {
  notes: "night",
  handoff: "morning",
  review: "supervisor",
  proof: "proof",
};

function initialViewFromUrl() {
  return initialRoleEntryFromUrl() || "notes";
}

function initialRoleEntryFromUrl() {
  if (typeof window === "undefined") return "";
  const params = new URLSearchParams(window.location.search);
  const requestedRole = params.get("role")?.toLowerCase();
  return roleToScreen[requestedRole] || "";
}

function App() {
  const [cases, setCases] = useState([]);
  const [caseId, setCaseId] = useState("resident-avery");
  const [caseData, setCaseData] = useState(null);
  const [handoff, setHandoff] = useState(null);
  const [handoffSources, setHandoffSources] = useState([]);
  const [evidence, setEvidence] = useState(null);
  const [health, setHealth] = useState(null);
  const [view, setView] = useState(initialViewFromUrl);
  const [roleEntry, setRoleEntry] = useState(initialRoleEntryFromUrl);
  const [noteText, setNoteText] = useState("");
  const [noteType, setNoteType] = useState("shift");
  const [question, setQuestion] = useState("What should I tell the family this morning?");
  const [answer, setAnswer] = useState(null);
  const [answerSources, setAnswerSources] = useState([]);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [caseLoading, setCaseLoading] = useState(true);
  const [proofLoading, setProofLoading] = useState(false);
  const [error, setError] = useState("");
  const activeCaseIdRef = useRef(caseId);

  const selectedCaseData = caseData?.id === caseId ? caseData : null;
  const memories = selectedCaseData?.memories || [];
  const currentCase = cases.find((item) => item.id === caseId);
  const importantCount = useMemo(() => memories.filter((item) => item.important).length, [memories]);
  const reviewCount = useMemo(() => memories.filter((item) => item.type === "review").length, [memories]);
  const activeScreen = screens.find((screen) => screen.id === view) || screens[0];
  const roleSpecificEntry = Boolean(roleEntry);
  const displayedCaseName = selectedCaseData?.name || currentCase?.name || "Care recipient";
  const displayedTeam = selectedCaseData?.team || currentCase?.team || "Home care handoff";

  async function api(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Request failed");
    }
    return response.json();
  }

  function clearWorkflowState() {
    setHandoff(null);
    setHandoffSources([]);
    setAnswer(null);
    setAnswerSources([]);
    setFeedback("");
  }

  async function refreshCaseData(targetCaseId = caseId) {
    const selectedCase = await api(`/v1/cases/${targetCaseId}`);
    if (activeCaseIdRef.current === targetCaseId) {
      setCaseData(selectedCase);
    }
    return selectedCase;
  }

  async function refreshProofData(targetCaseId = caseId) {
    const [healthResult, evidenceResult] = await Promise.all([
      api("/healthz"),
      api(`/v1/cases/${targetCaseId}/evidence`),
    ]);
    if (activeCaseIdRef.current === targetCaseId) {
      setHealth(healthResult);
      setEvidence(evidenceResult);
    }
  }

  async function run(action) {
    setBusy(true);
    setError("");
    const targetCaseId = caseId;
    try {
      await action();
      await refreshCaseData(targetCaseId);
      if (view === "proof") {
        await refreshProofData(targetCaseId);
      }
    } catch (err) {
      setError(cleanError(err));
    } finally {
      setBusy(false);
    }
  }

  function selectView(nextView) {
    setView(nextView);
    if (typeof window === "undefined" || !roleSpecificEntry) return;
    const role = screenToRole[nextView] || nextView;
    const url = new URL(window.location.href);
    url.searchParams.set("role", role);
    window.history.replaceState({}, "", `${url.pathname}?${url.searchParams.toString()}${url.hash}`);
  }

  function changeCase(nextCaseId) {
    if (nextCaseId === caseId) return;
    activeCaseIdRef.current = nextCaseId;
    setCaseId(nextCaseId);
    setCaseLoading(true);
    setCaseData(null);
    setEvidence(null);
    setNoteText("");
    setError("");
    clearWorkflowState();
  }

  useEffect(() => {
    function syncViewToBrowserUrl() {
      const nextRoleEntry = initialRoleEntryFromUrl();
      setRoleEntry(nextRoleEntry);
      setView(nextRoleEntry || "notes");
    }
    window.addEventListener("popstate", syncViewToBrowserUrl);
    return () => window.removeEventListener("popstate", syncViewToBrowserUrl);
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadShell() {
      try {
        const [healthResult, caseList] = await Promise.all([api("/healthz"), api("/v1/cases")]);
        if (!ignore) {
          setHealth(healthResult);
          setCases(caseList.cases);
        }
      } catch (err) {
        if (!ignore) setError(cleanError(err));
      }
    }

    loadShell();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;
    const targetCaseId = caseId;
    activeCaseIdRef.current = targetCaseId;
    setCaseLoading(true);
    setCaseData(null);
    setEvidence(null);
    clearWorkflowState();

    async function loadSelectedCase() {
      try {
        const selectedCase = await api(`/v1/cases/${targetCaseId}`);
        if (!ignore && activeCaseIdRef.current === targetCaseId) {
          setCaseData(selectedCase);
        }
      } catch (err) {
        if (!ignore && activeCaseIdRef.current === targetCaseId) setError(cleanError(err));
      } finally {
        if (!ignore && activeCaseIdRef.current === targetCaseId) setCaseLoading(false);
      }
    }

    loadSelectedCase();
    return () => {
      ignore = true;
    };
  }, [caseId]);

  useEffect(() => {
    if (view !== "proof") return;
    let ignore = false;
    const targetCaseId = caseId;
    setProofLoading(true);

    async function loadProof() {
      try {
        const [healthResult, evidenceResult] = await Promise.all([
          api("/healthz"),
          api(`/v1/cases/${targetCaseId}/evidence`),
        ]);
        if (!ignore && activeCaseIdRef.current === targetCaseId) {
          setHealth(healthResult);
          setEvidence(evidenceResult);
        }
      } catch (err) {
        if (!ignore && activeCaseIdRef.current === targetCaseId) setError(cleanError(err));
      } finally {
        if (!ignore && activeCaseIdRef.current === targetCaseId) setProofLoading(false);
      }
    }

    loadProof();
    return () => {
      ignore = true;
    };
  }, [caseId, view]);

  async function addNote(event) {
    event.preventDefault();
    if (!noteText.trim()) return;
    await run(async () => {
      await api(`/v1/cases/${caseId}/notes`, {
        method: "POST",
        body: JSON.stringify({ type: noteType, text: noteText, source: "night worker note" }),
      });
      setNoteText("");
      selectView("notes");
    });
  }

  async function generateHandoff() {
    await run(async () => {
      const data = await api(`/v1/cases/${caseId}/handoff`, {
        method: "POST",
        body: JSON.stringify({
          focus: "morning handoff before 9 family risks tasks breakfast preference review",
        }),
      });
      setHandoff(data.handoff);
      setHandoffSources(data.sources);
      selectView("handoff");
    });
  }

  async function askQuestion(event, preset) {
    event?.preventDefault();
    const text = preset || question;
    if (!text.trim()) return;
    await run(async () => {
      const data = await api(`/v1/cases/${caseId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question: text }),
      });
      setQuestion(text);
      setAnswer(data.answer);
      setAnswerSources(data.sources);
      selectView("handoff");
    });
  }

  async function improve(memoryId) {
    await run(async () => {
      await api(`/v1/cases/${caseId}/feedback`, {
        method: "POST",
        body: JSON.stringify({ memory_id: memoryId, feedback }),
      });
      setFeedback("");
    });
  }

  async function forget(memoryId) {
    await run(async () => {
      await api(`/v1/cases/${caseId}/memories/${memoryId}`, { method: "DELETE" });
      setHandoff(null);
      setHandoffSources([]);
      setAnswer(null);
      setAnswerSources([]);
    });
  }

  async function resetDemo() {
    await run(async () => {
      await api("/v1/demo/reset", { method: "POST" });
      setHandoff(null);
      setHandoffSources([]);
      setAnswer(null);
      setAnswerSources([]);
      selectView(view);
    });
  }

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-copy">
          <span className="eyebrow">{displayedTeam}</span>
          <h1>{activeScreen.title}</h1>
          <p>{activeScreen.body}</p>
        </div>

        <div className="hero-panel">
          <div className="case-switcher">
            <label>
              Care recipient
              <select value={caseId} onChange={(event) => changeCase(event.target.value)}>
                {cases.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            {(!roleSpecificEntry || view === "proof") && (
              <button className="quiet-button" type="button" onClick={resetDemo} disabled={busy} title="Reset demo notes">
                <RotateCcw size={17} />
                Reset demo
              </button>
            )}
          </div>
          {roleSpecificEntry ? (
            <div className="memory-summary role-entry-summary" aria-label="Current workspace">
              <span>Current workspace</span>
              <strong>{activeScreen.label}</strong>
              <small>{caseLoading ? `Loading ${displayedCaseName}...` : displayedCaseName}</small>
            </div>
          ) : (
            <div className="memory-summary" aria-label="Current memory summary">
              <span>Demo case context</span>
              <strong>{caseLoading ? "Loading..." : `${memories.length} notes`}</strong>
              <small>
                {importantCount} priority - {reviewCount} needs review
              </small>
            </div>
          )}
        </div>
      </header>

      {!roleSpecificEntry && (
        <nav className="screen-tabs" aria-label="Demo screens">
          {screens.map((screen) => {
            const Icon = screen.icon;
            return (
              <button
                key={screen.id}
                className={view === screen.id ? "tab active" : "tab"}
                type="button"
                onClick={() => selectView(screen.id)}
              >
                <Icon size={17} />
                {screen.label}
              </button>
            );
          })}
        </nav>
      )}

      {error && <div className="error-banner">{error}</div>}

      <main className="workspace">
        <section className="stage">
          {view === "handoff" && (
            <HandoffScreen
              busy={busy || caseLoading}
              loading={caseLoading}
              name={displayedCaseName}
              handoff={handoff}
              sources={handoffSources}
              question={question}
              answer={answer}
              answerSources={answerSources}
              setQuestion={setQuestion}
              onGenerate={generateHandoff}
              onAsk={askQuestion}
              onAskPreset={(questionText) => askQuestion(null, questionText)}
            />
          )}
          {view === "notes" && (
            <NotesScreen
              busy={busy || caseLoading}
              loading={caseLoading}
              memories={memories}
              noteText={noteText}
              noteType={noteType}
              setNoteText={setNoteText}
              setNoteType={setNoteType}
              onSubmit={addNote}
            />
          )}
          {view === "review" && (
            <ReviewScreen
              busy={busy || caseLoading}
              loading={caseLoading}
              memories={memories}
              feedback={feedback}
              setFeedback={setFeedback}
              onImprove={improve}
              onForget={forget}
            />
          )}
          {view === "proof" && <ProofScreen evidence={evidence} health={health} loading={proofLoading} />}
        </section>
      </main>
    </div>
  );
}

function HandoffScreen({
  busy,
  loading,
  name,
  handoff,
  sources,
  question,
  answer,
  answerSources,
  setQuestion,
  onGenerate,
  onAsk,
  onAskPreset,
}) {
  return (
    <div className="screen-layout">
      <div className="role-strip">
        <div>
          <span className="eyebrow">Morning lead</span>
          <h2>Build the first brief for {name}</h2>
          <p>Start from saved notes instead of asking someone to paste the night shift again.</p>
        </div>
        <button className="primary-action" type="button" onClick={onGenerate} disabled={busy}>
          <RefreshCw size={18} />
          Generate handoff
        </button>
      </div>

      <div className="morning-grid">
        <section className="handoff-area">
          {loading ? (
            <div className="empty-state">
              <ClipboardList size={38} />
              <h3>Loading {name}</h3>
              <p>Getting the latest saved notes for this care recipient.</p>
            </div>
          ) : !handoff ? (
            <div className="empty-state">
              <ClipboardList size={38} />
              <h3>No handoff generated yet</h3>
              <p>Click generate. The app will pull saved notes and turn them into the morning brief.</p>
            </div>
          ) : (
            <>
              <div className="handoff-board">
                <HandoffColumn title="Before 9 AM" items={handoff.before_9} accent="urgent" />
                <HandoffColumn title="Watch Today" items={handoff.watch_today} accent="watch" />
                <HandoffColumn title="Care Preference" items={handoff.care_preferences} accent="calm" />
                <HandoffColumn title="Later Today" items={handoff.later_today} accent="task" />
                <HandoffColumn title="Review" items={handoff.review_with_supervisor} accent="review" />
              </div>
              <div className="handoff-footer">
                <p>{handoff.safety_note}</p>
              </div>
              <SourceList title="Sources used" sources={sources} />
            </>
          )}
        </section>

        <aside className="question-panel">
          <form className="ask-form" onSubmit={onAsk}>
            <span className="eyebrow">Follow-up</span>
            <h2>Ask a follow-up</h2>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
            <div className="preset-row">
              <button type="button" className="quiet-button" onClick={() => onAskPreset("What should I tell the family this morning?")}>
                Family update
              </button>
              <button type="button" className="quiet-button" onClick={() => onAskPreset("What should I watch today?")}>
                Watch item
              </button>
              <button type="button" className="quiet-button" onClick={() => onAskPreset("What changed after 3 AM?")}>
                After 3 AM
              </button>
            </div>
            <button className="primary-action" type="submit" disabled={busy}>
              <MessageSquareText size={18} />
              Answer from saved notes
            </button>
          </form>

          {answer && (
            <section className="answer-panel">
              <span className="eyebrow">Answer</span>
              <p>{answer}</p>
              <SourceList title="Why this answer" sources={answerSources} />
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

function NotesScreen({ busy, loading, memories, noteText, noteType, setNoteText, setNoteType, onSubmit }) {
  const nightNotes = memories.filter((memory) => memory.source?.toLowerCase().includes("night"));

  return (
    <div className="screen-layout two-column">
      <form className="note-form" onSubmit={onSubmit}>
        <span className="eyebrow">Night caregiver</span>
        <h2>Save the thing the morning team must not miss</h2>
        <p>Write the note the way the caregiver would say it. It will be available when the morning handoff is opened.</p>
        <label>
          What kind of note is this?
          <select value={noteType} onChange={(event) => setNoteType(event.target.value)}>
            <option value="shift">General</option>
            <option value="risk">Watch today</option>
            <option value="task">Task</option>
            <option value="family">Family</option>
            <option value="preference">Preference</option>
            <option value="review">Needs review</option>
          </select>
        </label>
        <label>
          Note
          <textarea
            value={noteText}
            onChange={(event) => setNoteText(event.target.value)}
            placeholder="Example: Avery woke again around 3:10 AM, settled after water, and should be checked gently before breakfast."
          />
        </label>
        <button className="primary-action" type="submit" disabled={busy}>
          <Plus size={18} />
          Remember for morning
        </button>
      </form>

      <div className="timeline timeline-panel">
        <span className="eyebrow">Saved from this shift</span>
        <h2>Night notes ready for morning</h2>
        {loading ? (
          <div className="empty-state compact">
            <Moon size={28} />
            <h3>Loading notes</h3>
            <p>Getting the latest shift notes for this care recipient.</p>
          </div>
        ) : nightNotes.length ? (
          nightNotes.map((memory) => (
            <article key={memory.id} className="timeline-item">
              <span className={memory.important ? "timeline-pin important" : "timeline-pin"} />
              <div>
                <strong>{labelForType(memory.type)}</strong>
                <p>{memory.text}</p>
                <small>{memory.source}</small>
              </div>
            </article>
          ))
        ) : (
          <div className="empty-state compact">
            <Moon size={28} />
            <h3>No night notes saved yet</h3>
            <p>Add the first change from the shift. The morning lead will see it in the handoff.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ReviewScreen({ busy, loading, memories, feedback, setFeedback, onImprove, onForget }) {
  return (
    <div className="screen-layout">
      <div className="action-strip">
        <div>
          <span className="eyebrow">Supervisor review</span>
          <h2>Decide what should keep shaping future handoffs</h2>
          <p>Use this when a note is important enough to surface again, or when an old note should stop appearing.</p>
        </div>
        <label className="feedback-input">
          Optional reason
          <input
            value={feedback}
            onChange={(event) => setFeedback(event.target.value)}
            placeholder="Example: mention this before breakfast"
          />
        </label>
      </div>

      <div className="review-list">
        {loading ? (
          <div className="empty-state compact">
            <BadgeCheck size={28} />
            <h3>Loading review queue</h3>
            <p>Getting the latest notes for this care recipient.</p>
          </div>
        ) : memories.map((memory) => (
          <article key={memory.id} className={memory.important ? "review-item important" : "review-item"}>
            <div>
              <span className="type-chip">{labelForType(memory.type)}</span>
              {memory.important && <span className="type-chip priority">important</span>}
              <p>{memory.text}</p>
              <small>{memory.source}</small>
            </div>
            <div className="review-actions">
              <button type="button" className="quiet-button" onClick={() => onImprove(memory.id)} disabled={busy}>
                <BadgeCheck size={17} />
                Keep important
              </button>
              <button type="button" className="danger-button" onClick={() => onForget(memory.id)} disabled={busy}>
                <Trash2 size={17} />
                Remove
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function ProofScreen({ evidence, health, loading }) {
  const backend = evidence?.backend || health?.memory;
  const intelligence = evidence?.intelligence || health?.intelligence;
  const communicationTimeline = evidence?.communication_timeline || [];
  return (
    <div className="screen-layout">
      <div className="action-strip">
        <div>
          <span className="eyebrow">Judge proof</span>
          <h2>Memory lifecycle evidence</h2>
          <p>Normal users never need this screen. It shows the exact redacted exchange between this backend and memory.</p>
        </div>
        <div className="backend-badge">
          <strong>{backend?.name || "loading"}</strong>
          <span>{backend?.phase || "memory layer"}</span>
        </div>
        <div className="backend-badge">
          <strong>{intelligence?.name || "loading"}</strong>
          <span>{intelligence?.model || "reasoning layer"}</span>
        </div>
      </div>

      <div className="proof-grid">
        {evidence?.proof_steps?.map((step) => (
          <article key={step.operation} className={step.complete ? "proof-step complete" : "proof-step"}>
            <span>{step.operation}</span>
            <h3>{step.label}</h3>
            <p>{step.meaning}</p>
          </article>
        ))}
      </div>

      <section className="communication-log">
        <div className="section-title">
          <span className="eyebrow">Backend to memory</span>
          <h3>Communication trace</h3>
          <p>API keys are redacted. Requests, datasets, queries, status codes, and response previews stay visible.</p>
        </div>
        {loading ? (
          <div className="local-call-note">Loading the latest proof trace for this care recipient.</div>
        ) : communicationTimeline.length ? (
          communicationTimeline.map((event) => (
            <article className="communication-event" key={event.trace_id}>
              <div className="event-topline">
                <strong>{event.operation}</strong>
                <span>{event.memory_ids?.join(", ") || "no memory id"}</span>
                <small>{event.latency_ms} ms</small>
              </div>
              {event.proof && <p className="event-proof">{event.proof}</p>}
              {event.calls?.length ? (
                event.calls.map((call, index) => (
                  <div className="call-card" key={`${event.trace_id}-${index}`}>
                    <div className="call-topline">
                      <strong>
                        {call.method} {call.endpoint}
                      </strong>
                      <span className={call.status === "ok" ? "call-status ok" : "call-status"}>
                        {call.status || "unknown"}
                      </span>
                    </div>
                    <div className="call-grid">
                      <div>
                        <span className="mini-label">Request</span>
                        <pre>{formatJson(call.request || { reason: call.reason })}</pre>
                      </div>
                      <div>
                        <span className="mini-label">Response</span>
                        <pre>{formatJson(call.response || { status: call.status, reason: call.reason, error: call.error })}</pre>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="local-call-note">No Cognee HTTP call was captured for this trace. Local demo memory is active.</div>
              )}
            </article>
          ))
        ) : (
          <div className="local-call-note">Run remember, handoff, review, or remove once to create memory traces.</div>
        )}
      </section>

      <section className="trace-table">
        <div className="trace-head">
          <span>Operation</span>
          <span>Source IDs</span>
          <span>Time</span>
        </div>
        {evidence?.recent_traces?.map((trace) => (
          <div className="trace-row" key={trace.id}>
            <strong>{trace.operation}</strong>
            <span>{trace.memory_ids.join(", ") || "none"}</span>
            <small>{trace.latency_ms} ms</small>
          </div>
        ))}
      </section>

      <section className="balance-note">
        <h3>How the Cognee balance is used</h3>
        {evidence?.balance_policy?.map((item) => (
          <p key={item}>{item}</p>
        ))}
      </section>
    </div>
  );
}

function formatJson(value) {
  if (value === undefined || value === null) return "none";
  return JSON.stringify(value, null, 2);
}

function HandoffColumn({ title, items, accent }) {
  return (
    <section className={`handoff-column ${accent}`}>
      <h3>{title}</h3>
      {items?.length ? (
        items.map((item, index) => (
          <article key={`${title}-${index}`}>
            <p>{item.text}</p>
            {item.source_ids?.length ? <small>Source: {item.source_ids.join(", ")}</small> : null}
          </article>
        ))
      ) : (
        <p className="muted">No note found.</p>
      )}
    </section>
  );
}

function SourceList({ title, sources }) {
  if (!sources?.length) return null;
  return (
    <section className="source-list">
      <h3>{title}</h3>
      {sources.slice(0, 5).map((source) => (
        <article key={source.id}>
          <strong>{labelForType(source.type)}</strong>
          <p>{source.text}</p>
          <small>{source.source}</small>
        </article>
      ))}
    </section>
  );
}

function labelForType(type) {
  return (
    {
      family: "Family",
      risk: "Watch",
      task: "Task",
      preference: "Preference",
      review: "Review",
      feedback: "Feedback",
      shift: "General",
    }[type] || "Note"
  );
}

function cleanError(err) {
  const raw = err?.message || String(err);
  try {
    const parsed = JSON.parse(raw);
    return parsed.detail || raw;
  } catch {
    return raw;
  }
}

createRoot(document.getElementById("root")).render(<App />);
