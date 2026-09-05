import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, ArrowRight, Database, ChevronDown, ChevronUp, Copy, Check, Sparkles } from 'lucide-react';

// Basic markdown-to-html renderer
function renderMarkdown(text) {
  if (!text) return '';
  const lines = text.split('\n');
  let html = [];
  let inList = false;

  for (const line of lines) {
    const bullet = line.match(/^\s*(?:[-*])\s+(.*)$/);
    if (bullet) {
      if (!inList) {
        html.push('<ul class="list-disc pl-4 my-2">');
        inList = true;
      }
      html.push('<li>' + bullet[1] + '</li>');
    } else {
      if (inList) {
        html.push('</ul>');
        inList = false;
      }
      if (line.trim()) {
        html.push('<p class="mb-2">' + line + '</p>');
      }
    }
  }
  if (inList) html.push('</ul>');

  return html.join('')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold uppercase tracking-wider text-xs">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-card px-1 font-mono text-xs">$1</code>');
}

const PROMPT_SUGGESTIONS = [
  "What are the top 5 selling products by revenue?",
  "Which products are completely out of stock?",
  "What is our total dead stock value across all stores?",
  "Analyze the sales spike on Day 16 for Bluetooth Speaker"
];

function SqlEvidenceViewer({ sql, rowCount }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!sql) return null;

  return (
    <div className="mt-3 border-t border-dashed border-border pt-2">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary hover:text-primary-dark transition-colors py-1 cursor-pointer"
      >
        <Database className="w-3.5 h-3.5" />
        <span>Evidence: Generated SQL ({rowCount || 0} rows)</span>
        {isOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {isOpen && (
        <div className="mt-2 p-3 bg-text text-background font-mono text-xs relative rounded-none border border-text">
          <div className="flex items-center justify-between border-b border-background/20 pb-1 mb-2">
            <span className="text-[10px] uppercase tracking-widest opacity-60 font-sans font-bold">Read-Only SQLite Query</span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 text-[10px] uppercase tracking-widest text-primary hover:text-white transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap leading-relaxed select-all">
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      role: 'ai', 
      content: 'INITIALIZING COPILOT...\n\nAsk me anything about your stores, inventory levels, or transaction trends. Every response is grounded in real database queries.',
      sql: null,
      rowCount: 0
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendQuery = async (queryText) => {
    const text = (queryText || input).trim();
    if (!text || isLoading) return;

    const userMessage = { id: Date.now(), role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      let data = {};
      try { data = await res.json(); } catch (_) {}

      if (!res.ok) {
        throw new Error(data.detail || `Chat request failed (${res.status})`);
      }

      const aiMessage = { 
        id: Date.now() + 1, 
        role: 'ai', 
        content: data.response || '',
        sql: data.sql || null,
        rowCount: data.row_count || 0
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'ai', 
        content: "ERROR: " + err.message,
        sql: null,
        rowCount: 0 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendQuery();
  };

  return (
    <section className="border border-text p-6 flex flex-col min-h-[550px] bg-background relative z-10">
      <div className="flex-1 overflow-y-auto mb-4 pr-2 flex flex-col gap-6 max-h-[460px]">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`flex flex-col gap-1 max-w-[95%] md:max-w-[85%] ${msg.role === 'user' ? 'self-end items-end' : 'self-start'}`}
            >
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text opacity-70 mb-1">
                {msg.role === 'user' ? 'STORE MANAGER' : 'RETAIL COPILOT AGENT'}
              </div>
              <div 
                className={`px-5 py-4 text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'bg-text text-background border border-text' 
                    : 'bg-transparent border border-text text-text'
                }`}
              >
                <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                {msg.role === 'ai' && <SqlEvidenceViewer sql={msg.sql} rowCount={msg.rowCount} />}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-1 self-start">
             <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text opacity-70 mb-1">
                RETAIL COPILOT AGENT
              </div>
            <div className="px-5 py-4 border border-text text-text flex items-center gap-2 h-12">
              <span className="text-xs uppercase tracking-widest font-bold">Querying & Synthesizing</span>
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </motion.div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="mb-3 pt-3 border-t border-dashed border-border flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-muted">
          <Sparkles className="w-3 h-3 text-primary" /> Suggested:
        </span>
        {PROMPT_SUGGESTIONS.map((suggestion, idx) => (
          <button
            key={idx}
            type="button"
            disabled={isLoading}
            onClick={() => sendQuery(suggestion)}
            className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 bg-transparent hover:bg-text hover:text-background border border-text transition-colors disabled:opacity-50 cursor-pointer"
          >
            {suggestion.length > 32 ? suggestion.slice(0, 32) + '...' : suggestion}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-0 border-t border-text pt-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="ASK ABOUT STOCKS, SALES, REVENUE..."
          className="flex-1 bg-transparent px-4 py-3 outline-none text-text text-sm uppercase tracking-wider placeholder:text-muted placeholder:tracking-widest font-semibold border border-text border-r-0 focus:bg-white transition-colors"
          disabled={isLoading}
          autoComplete="off"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="flex items-center justify-center px-6 py-3 bg-primary hover:bg-primary-dark disabled:opacity-50 text-white font-bold uppercase tracking-widest transition-colors border border-primary cursor-pointer"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowRight className="w-5 h-5" />}
        </button>
      </form>
    </section>
  );
}
