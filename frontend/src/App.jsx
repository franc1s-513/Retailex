import React, { useEffect, useState, useMemo } from 'react';
import { ChartLine, Store, RefreshCw } from 'lucide-react';
import BriefingCard from './components/BriefingCard';
import ChatPanel from './components/ChatPanel';

const STORES = [
  { id: 'ALL', label: 'All Stores' },
  { id: 'S001', label: 'Store S001' },
  { id: 'S002', label: 'Store S002' },
  { id: 'S003', label: 'Store S003' },
];

function App() {
  const [briefing, setBriefing] = useState({
    stockout_risks: [],
    dead_stock: [],
    sales_anomalies: []
  });
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadBriefing = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/morning-briefing');
      if (!res.ok) throw new Error('Briefing request failed');
      const data = await res.json();
      setBriefing(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBriefing();
  }, []);

  const filteredStockouts = useMemo(() => {
    if (selectedStore === 'ALL') return briefing.stockout_risks;
    return briefing.stockout_risks.filter(item => item.store_id === selectedStore);
  }, [briefing.stockout_risks, selectedStore]);

  const filteredDeadStock = useMemo(() => {
    if (selectedStore === 'ALL') return briefing.dead_stock;
    return briefing.dead_stock.filter(item => item.store_id === selectedStore);
  }, [briefing.dead_stock, selectedStore]);

  return (
    <div className="min-h-screen bg-background text-text font-sans selection:bg-primary-light selection:text-primary">
      {/* Grid lines background simulation */}
      <div className="fixed inset-0 pointer-events-none grid grid-cols-1 md:grid-cols-3 md:gap-0 z-0">
        <div className="border-r border-dashed border-border h-full"></div>
        <div className="border-r border-dashed border-border h-full"></div>
        <div className="h-full"></div>
      </div>

      <header className="relative z-10 border-b border-dashed border-border py-6 px-8">
        <div className="max-w-[1200px] mx-auto flex items-center justify-between">
          <div>
            <h1 className="m-0 text-3xl font-display font-bold uppercase tracking-tight text-text">Optikka <span className="text-primary">Retail</span></h1>
            <p className="m-0 mt-1 text-muted text-xs uppercase tracking-widest font-semibold">Autonomous Store Briefing & Conversational Copilot</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={loadBriefing}
              disabled={loading}
              title="Refresh Briefing"
              className="p-2 border border-text text-text hover:bg-text hover:text-background transition-colors disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <div className="text-primary hidden sm:block">
              <ChartLine className="w-8 h-8" strokeWidth={1.5} />
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-[1200px] mx-auto p-8 pb-16 flex flex-col gap-16">
        
        <section>
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 border-b border-text pb-4 gap-4">
            <div>
              <h2 className="m-0 text-2xl font-display font-bold text-text uppercase tracking-wide">
                Morning Briefing
              </h2>
              <span className="text-xs font-semibold uppercase tracking-widest text-muted">Daily Automated Exceptions</span>
            </div>

            {/* Store Filter Selector */}
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-xs font-bold uppercase tracking-wider text-muted mr-2 flex items-center gap-1">
                <Store className="w-3.5 h-3.5" /> Scope:
              </span>
              {STORES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStore(s.id)}
                  className={`text-xs font-bold uppercase tracking-wider px-3 py-1.5 transition-colors cursor-pointer border ${
                    selectedStore === s.id
                      ? 'bg-text text-background border-text'
                      : 'bg-transparent text-text border-border hover:border-text'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
          
          {loading ? (
            <div className="text-muted animate-pulse font-display text-xl py-12">Computing operational insights...</div>
          ) : error ? (
            <div className="text-primary bg-primary-light p-4 border border-primary font-medium">{error}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-t border-l border-dashed border-border">
              <BriefingCard 
                title="Stockout Risks" 
                count={filteredStockouts.length} 
                data={filteredStockouts} 
                type="stockout" 
              />
              <BriefingCard 
                title="Dead Stock" 
                count={filteredDeadStock.length} 
                data={filteredDeadStock} 
                type="deadstock" 
              />
              <BriefingCard 
                title="Sales Anomalies" 
                count={briefing.sales_anomalies.length} 
                data={briefing.sales_anomalies} 
                type="anomaly" 
              />
            </div>
          )}
        </section>

        <section>
          <div className="flex items-center justify-between mb-8 border-b border-text pb-2">
            <div>
              <h2 className="m-0 text-2xl font-display font-bold text-text uppercase tracking-wide">
                Interact & Analyze
              </h2>
              <span className="text-xs font-semibold uppercase tracking-widest text-muted">Text-to-SQL Grounded Assistant</span>
            </div>
          </div>
          <ChatPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
