/**
 * components/ChatArea.jsx
 * Main chat panel: messages list + agent graph + progress.
 */
import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import AgentGraph from './AgentGraph'
import ProgressBar from './ProgressBar'
import FileDropZone from './FileDropZone'
import { useJobPolling } from '../hooks/useJobPolling'
import { uploadAndAnalyze, sendChat } from '../api/client'

const WELCOME = {
  role: 'assistant',
  agent: 'system',
  content: `Hello! I am the CRA Analyzer 👋

Send me your activity report file (PDF, DOCX, XLSX, CSV, JSON, or TXT) and I will automatically launch the multi-agent analysis pipeline:

🌐 Web search + RAG
🔧 Creation of analysis tools
📊 KPI & trend extraction

You can also ask questions in natural language about your data.`,
  timestamp: new Date().toISOString(),
}

export default function ChatArea() {
  const [messages, setMessages]         = useState([WELCOME])
  const [jobId, setJobId]               = useState(null)
  const [agentStatuses, setAgentStatuses] = useState({})
  const [uploading, setUploading]       = useState(false)
  const [progress, setProgress]         = useState(0)
  const [progressLabel, setProgressLabel] = useState('')
  const [fileInfo, setFileInfo]         = useState(null)
  const [showDrop, setShowDrop]         = useState(true)
  const bottomRef                       = useRef(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Poll job status
  const { job } = useJobPolling(jobId, (finalJob) => {
if (finalJob.status === 'completed') {
  const r = finalJob.result;
  
  // 1. Extraction des indicateurs clés (KPIs)
  // On utilise consolidated_data qui contient les moyennes et sommes calculées
  const kpiData = r.consolidated_data?.kpi_data || {};
  const kpiSection = Object.entries(kpiData).length > 0 
    ? "\n#### 📊 KPIs extracted\n" + 
      Object.entries(kpiData).map(([name, stats]) => 
        `* **${name} :** ${stats.avg.toLocaleString()} (moyenne)`
      ).join('\n')
    : "";

  // 2. Extraction de l'analyse TRIZ
  const triz = r.triz_analysis || {};
  const contradictions = triz.contradictions?.map(c => 
    `* **Contradiction ${c.type} :** ${c.improving_parameter} ↑ vs ${c.degrading_parameter} ↓`
  ).join('\n') || "Aucune identifiée.";

  const ifr = triz.ideal_final_result ? `\n\n**Résultat Final Idéal (IFR) :** ${triz.ideal_final_result}` : "";

  // 3. Extraction des recommandations avec Owners et Délais
  const recs = r.recommendations?.map((rec, idx) => 
    `${idx + 1}. **[${rec.priority}] ${rec.action}**\n    * *Propriétaire : ${rec.owner} | Échéance : ${rec.timeline}*`
  ).join('\n') || "Aucune recommandation générée.";

  // 4. Construction du message final
  const fullMessage = `🤖 **ARIA Assistant** — Analysis completed (Confidence: ${(r.confidence_score * 100).toFixed(0)}%)*

✅ **Strategic analysis completed for the domain: ${r.domain || 'Not specified'}.**

${kpiSection}

---

#### 🧠 Contradiction Analysis (TRIZ)
The AI has identified the following blockages:

${contradictions}${ifr}

---

#### 📋 Recommandations Prioritaires
${recs}

---

#### 📁 Generated Artifacts
* 📄 [Complete report available in the Reports tab]
* 📉 ${r.artifacts?.charts?.length || 0} charts generated.`;

  // 5. Envoi au chat
  addAssistantMessage(fullMessage, 'analysis');
  setProgress(100);
} else if (finalJob.status === 'failed') {
      addAssistantMessage(`❌ Analysis failed: ${finalJob.error ?? 'Unknown error'}`, 'system')
      setProgress(0)
    }
    setJobId(null)
  })

  // Keep agent graph in sync
  useEffect(() => {
    if (!job) return
    setAgentStatuses(job.agent_statuses ?? {})
    setProgress(job.progress ?? 0)
    setProgressLabel(job.current_step ?? '')
  }, [job])

  const addUserMessage = (content) =>
    setMessages((m) => [...m, { role: 'user', content, timestamp: new Date().toISOString() }])

  const addAssistantMessage = (content, agent = 'system') =>
    setMessages((m) => [...m, { role: 'assistant', agent, content, timestamp: new Date().toISOString() }])

  // File upload → analysis
const handleFile = async (file) => {
  setUploading(true);
  setShowDrop(false);
  addUserMessage(`📎 ${file.name}`);

  try {
    // 1. Upload du fichier (on suppose que cette route renvoie un identifiant/chemin)
    const up = await uploadAndAnalyze(file); 
    
    // 2. Préparation du payload respectant le schéma AnalyzeRequest
    const payload = {
      data_sources: [
        {
          source_id: file.name,
          source_type: "file",
          path_or_url: up.job_id || up.file_id, // Utilisez l'ID retourné par l'upload
          data_format: file.name.split('.').pop().toLowerCase(),
          metadata: {}
        }
      ],
      query: "Complete Analysis of the Activity Report"
    };


    setFileInfo({ name: file.name, file_id: up.job_id });
    setJobId(up.job_id); 
    // ... reste du code
  } catch (err) {
    setError(err.response?.data?.detail || "Error during analysis");
  } finally {
    setUploading(false);
  }
};

  // Free-text chat
  const handleSend = async (text) => {
    addUserMessage(text)
    try {
      const r = await sendChat(jobId, text)
      addAssistantMessage(r.answer ?? r.content ?? JSON.stringify(r), 'analysis')
    } catch (err) {
      addAssistantMessage(`I couldn't process your question: ${err.message}`, 'system')
    }
  }

  const isRunning = !!jobId

  return (
    <div className="flex flex-col h-screen flex-1 overflow-hidden bg-gray-950">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm shrink-0">
        <div>
          <h2 className="font-semibold text-white text-sm">Activity Report Analysis</h2>
          {fileInfo && <p className="text-gray-500 text-xs">{fileInfo.name}</p>}
        </div>
        {isRunning && (
          <div className="flex items-center gap-2 text-brand-400 text-xs">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-ping inline-block" />
            Pipeline in progress…
          </div>
        )}
      </header>

      {/* Main Content Area (Split Screen) */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Left Column: Messages & Input */}
        <div className="flex flex-col flex-1 border-r border-gray-800 overflow-hidden">
          {/* Progress bar (Inside Chat Column) */}
          {(isRunning || progress > 0) && (
            <div className="px-4 pt-4">
              <ProgressBar progress={progress} label={progressLabel} />
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Chat input */}
          <ChatInput onSend={handleSend} onFile={handleFile} disabled={uploading} />
        </div>

        {/* Right Column: Agent Graph (Sidebar style) */}
        <div className="w-96 bg-gray-900/30 flex flex-col overflow-hidden">
          <AgentGraph agentStatuses={agentStatuses} />
        </div>
      </div>
    </div>
  )
}
