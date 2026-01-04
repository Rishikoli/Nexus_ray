import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Brain, Activity, X, ChevronDown, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LogPanel = ({ events }) => {
    const [activeTab, setActiveTab] = useState('feed');
    const logsEndRef = useRef(null);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [events, activeTab]);

    const logs = events || [];
    const reasoningEvents = logs.filter(e => e.type === 'reasoning');

    return (
        <div className="glass-panel" style={{
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden',
            background: 'rgba(5, 5, 8, 0.6)'
        }}>
            {/* Header / Tabs */}
            <div style={{
                display: 'flex',
                borderBottom: '1px solid var(--border-primary)',
                background: 'rgba(0,0,0,0.2)'
            }}>
                <button
                    onClick={() => setActiveTab('feed')}
                    style={{
                        flex: 1,
                        padding: '12px',
                        background: activeTab === 'feed' ? 'rgba(255,255,255,0.05)' : 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'feed' ? '2px solid var(--accent)' : '2px solid transparent',
                        color: activeTab === 'feed' ? 'var(--text-primary)' : 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                        fontSize: '13px', fontWeight: 600
                    }}
                >
                    <Activity size={14} /> Activity Feed
                </button>
                <button
                    onClick={() => setActiveTab('logs')}
                    style={{
                        flex: 1,
                        padding: '12px',
                        background: activeTab === 'logs' ? 'rgba(255,255,255,0.05)' : 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'logs' ? '2px solid var(--accent)' : '2px solid transparent',
                        color: activeTab === 'logs' ? 'var(--text-primary)' : 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                        fontSize: '13px', fontWeight: 600
                    }}
                >
                    <Terminal size={14} /> System Logs
                </button>
                <button
                    onClick={() => setActiveTab('reasoning')}
                    style={{
                        flex: 1,
                        padding: '12px',
                        background: activeTab === 'reasoning' ? 'rgba(255,255,255,0.05)' : 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'reasoning' ? '2px solid var(--accent)' : '2px solid transparent',
                        color: activeTab === 'reasoning' ? 'var(--text-primary)' : 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                        fontSize: '13px', fontWeight: 600
                    }}
                >
                    <Brain size={14} /> AI Reasoning
                    {reasoningEvents.length > 0 && (
                        <span style={{
                            background: 'var(--accent)', color: 'white',
                            fontSize: '10px', padding: '1px 5px', borderRadius: '4px', marginLeft: '4px'
                        }}>
                            {reasoningEvents.length}
                        </span>
                    )}
                </button>
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '0', position: 'relative' }}>

                {/* 1. Activity Feed (Classic) */}
                {activeTab === 'feed' && (
                    <div style={{ padding: '20px' }}>
                        {logs.length === 0 ? <EmptyState msg="No activity yet" /> : (
                            logs.filter(e => e.type !== 'reasoning').slice().reverse().map((event, idx) => (
                                <FeedItem key={idx} event={event} />
                            ))
                        )}
                    </div>
                )}

                {/* 2. System Logs (Terminal Style) */}
                {activeTab === 'logs' && (
                    <div style={{
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        padding: '16px',
                        color: '#a0a0a0',
                        lineHeight: '1.6'
                    }}>
                        {logs.map((log, i) => (
                            <div key={i} style={{ marginBottom: '4px', wordBreak: 'break-all' }}>
                                <span style={{ color: '#555', marginRight: '8px' }}>[{log.time}]</span>
                                <span style={{
                                    color: log.type === 'error' ? '#ff5555' :
                                        log.type === 'success' ? '#50fa7b' :
                                            log.type === 'reasoning' ? '#bd93f9' : '#f1fa8c',
                                    fontWeight: 'bold',
                                    marginRight: '8px'
                                }}>
                                    {log.agent ? `[${log.agent}]` : '[SYSTEM]'}
                                </span>
                                <span>{log.message}</span>
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                )}

                {/* 3. AI Reasoning (Cards) */}
                {activeTab === 'reasoning' && (
                    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {reasoningEvents.length === 0 ? (
                            <EmptyState msg="No reasoning thoughts captured yet. Run an agent workflow." />
                        ) : (
                            reasoningEvents.map((event, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    style={{
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid var(--border-secondary)',
                                        borderRadius: '12px',
                                        padding: '16px',
                                        borderLeft: '4px solid var(--accent)'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Brain size={16} color="var(--accent)" />
                                        <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                                            {event.agent} Thought Process
                                        </span>
                                        <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-muted)' }}>
                                            {event.time}
                                        </span>
                                    </div>
                                    <div style={{
                                        lineHeight: '1.6',
                                        fontSize: '13px',
                                        color: 'var(--text-secondary)',
                                        whiteSpace: 'pre-wrap' // Preserve newlines
                                    }}>
                                        {event.message}
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const FeedItem = ({ event }) => {
    // Reuse Timeline logic roughly
    let color = 'var(--accent)';
    if (event.type === 'error') color = 'var(--error)';
    if (event.type === 'success') color = 'var(--success)';

    return (
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{
                width: '2px', background: 'var(--border-secondary)',
                marginRight: '-6px', marginLeft: '6px'
            }} />
            <div style={{
                width: '14px', height: '14px', borderRadius: '50%', background: color,
                marginTop: '4px', flexShrink: 0, border: '2px solid rgba(0,0,0,0.5)'
            }} />
            <div>
                <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{event.message}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{event.time} • {event.agent || 'System'}</div>
            </div>
        </div>
    );
}

const EmptyState = ({ msg }) => (
    <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '200px', color: 'var(--text-muted)', textAlign: 'center'
    }}>
        <Activity size={24} style={{ marginBottom: '12px', opacity: 0.5 }} />
        <p style={{ fontSize: '13px' }}>{msg}</p>
    </div>
);

export default LogPanel;
