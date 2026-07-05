import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { CheckCircle2, MessageSquareText, Plus, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [cases, setCases] = useState([]);
  const [caseId, setCaseId] = useState("resident-avery");
  const [caseData, setCaseData] = useState(null);
  const [handoff, setHandoff] = useState(null);
  const [traces, setTraces] = useState([]);
  const [noteText, setNoteText] = useState("");
  const [noteType, setNoteType] = useState("shift");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);

  const memories = caseData?.memories || [];
  const importantCount = useMemo(() => memories.filter((item) => item.important).length, [memories]);

  async function api(path, options = {}) {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async function loadAll() {
    const [caseList, selectedCase, traceList] = await Promise.all([
      api("/v1/cases"),
      api(`/v1/cases/${caseId}`),
      api(`/v1/cases/${caseId}/trace`),
    ]);
    setCases(caseList.cases);
    setCaseData(selectedCase);
    setTraces(traceList.traces);
  }

  async function run(action) {
    setBusy(true);
    try {
      await action();
      await loadAll();
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, [caseId]);

  async function addNote(event) {
    event.preventDefault();
    if (!noteText.trim()) return;
    await run(async () => {
      await api(`/v1/cases/${caseId}/notes`, {
        method: "POST",
        body: JSON.stringify({ type: noteType, text: noteText, source: "local shift note" }),
      });
      setNoteText("");
    });
  }

  async function generateHandoff() {
    await run(async () => {
      const data = await api(`/v1/cases/${caseId}/handoff`, {
        method: "POST",
        body: JSON.stringify({ focus: "morning handoff risks tasks family preferences" }),
      });
      setHandoff(data.handoff);
    });
  }

  async function askQuestion(event) {
    event.preventDefault();
    if (!question.trim()) return;
    await run(async () => {
      const data = await api(`/v1/cases/${caseId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      setAnswer(data.answer);
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
      if (handoff) await generateHandoff();
    });
  }

  return (
    <div className="app">
      <header className="shell-header">
        <div>
          <span className="eyebrow">Phase 1 local MVP</span>
          <h1>ShiftMemory</h1>
          <p>One shared memory for shift notes, handoffs, questions, corrections, and deletion.</p>
        </div>
        <div className="status-pill">
          <ShieldCheck size={17} />
          Local memory adapter
        </div>
      </header>

      <main className="workspace">
        <aside className="side-panel">
          <label>
            Case
            <select value={caseId} onChange={(event) => setCaseId(event.target.value)}>
              {cases.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <div className="metrics">
            <div>
              <strong>{memories.length}</strong>
              <span>remembered</span>
            </div>
            <div>
              <strong>{importantCount}</strong>
              <span>improved</span>
            </div>
          </div>

          <form className="composer" onSubmit={addNote}>
            <label>
              Type
              <select value={noteType} onChange={(event) => setNoteType(event.target.value)}>
                <option value="shift">Shift note</option>
                <option value="risk">Risk</option>
                <option value="task">Task</option>
                <option value="family">Family</option>
                <option value="preference">Preference</option>
              </select>
            </label>
            <label>
              New memory
              <textarea
                value={noteText}
                onChange={(event) => setNoteText(event.target.value)}
                placeholder="Example: Family asked for a callback before 10."
              />
            </label>
            <button type="submit" disabled={busy}>
              <Plus size={17} />
              Remember
            </button>
          </form>
        </aside>

        <section className="main-panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">Current case</span>
              <h2>{caseData?.name || "Loading"}</h2>
            </div>
            <button className="secondary" onClick={generateHandoff} disabled={busy}>
              <RefreshCw size={17} />
              Generate handoff
            </button>
          </div>

          <section className="handoff">
            <h3>Morning handoff</h3>
            {!handoff && <p className="empty">Generate a handoff from remembered notes.</p>}
            {handoff && (
              <div className="handoff-grid">
                <HandoffList title="Start here" items={handoff.start_here} />
                <HandoffList title="Watch" items={handoff.watch} />
                <HandoffList title="Tasks" items={handoff.tasks} />
                <HandoffList title="Preferences" items={handoff.preferences} />
              </div>
            )}
          </section>

          <section className="memory-list">
            <h3>Case memory</h3>
            {memories.map((memory) => (
              <article key={memory.id} className={memory.important ? "memory important" : "memory"}>
                <div>
                  <span className="tag">{memory.type}</span>
                  {memory.important && <span className="tag important-tag">high signal</span>}
                </div>
                <p>{memory.text}</p>
                <small>{memory.source}</small>
                <div className="memory-actions">
                  <button className="icon-action" onClick={() => improve(memory.id)} title="Improve">
                    <CheckCircle2 size={16} />
                  </button>
                  <button className="icon-action danger" onClick={() => forget(memory.id)} title="Forget">
                    <Trash2 size={16} />
                  </button>
                </div>
              </article>
            ))}
          </section>
        </section>

        <aside className="right-panel">
          <form className="ask-box" onSubmit={askQuestion}>
            <h3>Ask this case</h3>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What should morning shift know about family requests?"
            />
            <button type="submit" disabled={busy}>
              <MessageSquareText size={17} />
              Recall answer
            </button>
            {answer && <p className="answer">{answer}</p>}
          </form>

          <label className="feedback-box">
            Supervisor feedback
            <textarea
              value={feedback}
              onChange={(event) => setFeedback(event.target.value)}
              placeholder="Example: prioritize family calls in the next handoff"
            />
          </label>

          <section className="trace">
            <h3>Memory trace</h3>
            {traces.slice(0, 8).map((trace) => (
              <div key={trace.id} className="trace-row">
                <strong>{trace.operation}</strong>
                <span>{trace.memory_ids.length} source(s)</span>
                <small>{trace.latency_ms} ms</small>
              </div>
            ))}
          </section>
        </aside>
      </main>
    </div>
  );
}

function HandoffList({ title, items }) {
  return (
    <div className="handoff-list">
      <h4>{title}</h4>
      {items?.length ? (
        items.map((item, index) => (
          <p key={`${title}-${index}`}>
            {item.text}
            {item.source_ids?.length ? <span> source: {item.source_ids.join(", ")}</span> : null}
          </p>
        ))
      ) : (
        <p className="empty">No recalled memory.</p>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
