import React from 'react';
import {
    Activity,
    ShieldCheck,
    Brain,
    Clock,
    CheckCircle2,
    AlertTriangle
} from 'lucide-react';

const DetailPanel = ({ selectedNode }) => {
    if (!selectedNode) {
        return (
            <div className="glass-panel" style={{ borderRadius: '16px', display: 'flex', flexDirection: 'column', height: '200px', flexShrink: 0, minHeight: '0', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)' }}>
                <div style={{
                    padding: '16px',
                    borderRadius: '50%',
                    background: 'var(--surface)',
                    border: '1px solid var(--border-primary)',
                    marginBottom: '12px',
                    boxShadow: 'inset 0 0 20px rgba(0,0,0,0.2)'
                }}>
                    <Activity size={24} style={{ opacity: 0.5 }} />
                </div>
                <p style={{ fontWeight: 500, fontSize: '14px' }}>Select a task node to view details</p>
                <p style={{ fontSize: '11px', marginTop: '4px', opacity: 0.7 }}>(Node metadata & logs)</p>
            </div>
        );
    }

    const { data } = selectedNode;

    return (
        <div className="glass-panel" style={{ borderRadius: '16px', display: 'flex', flexDirection: 'column', flex: 1, minHeight: '0', overflow: 'hidden' }}>
            {/* Header */}
            <div style={{ padding: '24px', borderBottom: '1px solid var(--border-primary)', background: 'linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 100%)' }}>
                <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>{data.label}</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                        fontSize: '12px',
                        padding: '4px 10px',
                        borderRadius: '12px',
                        background: 'var(--surface-active)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-secondary)'
                    }}>
                        {data.agentType}
                    </span>
                    <span style={{
                        fontSize: '12px',
                        padding: '4px 10px',
                        borderRadius: '12px',
                        background: data.status === 'completed' ? 'rgba(0, 240, 144, 0.1)' : 'var(--surface)',
                        color: data.status === 'completed' ? 'var(--success)' : 'var(--text-secondary)',
                        border: '1px solid transparent',
                        borderColor: data.status === 'completed' ? 'rgba(0, 240, 144, 0.2)' : 'var(--border-secondary)'
                    }}>
                        {data.status}
                    </span>
                </div>
            </div>

            {/* Content */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>

                {/* Agent Info Section */}
                <section style={{ marginBottom: '28px' }}>
                    <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', letterSpacing: '0.05em' }}>
                        Performance Metrics
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div style={{ background: 'var(--surface)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-secondary)' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Context Tokens</div>
                            <div className="mono" style={{ fontSize: '15px', fontWeight: 600 }}>{data.tokens || '--'}</div>
                        </div>
                        <div style={{ background: 'var(--surface)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-secondary)' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Latency</div>
                            <div className="mono" style={{ fontSize: '15px', fontWeight: 600 }}>{data.executionTime ? `${(data.executionTime * 1000).toFixed(0)}ms` : '--'}</div>
                        </div>
                    </div>
                </section>

                {/* Safety Score */}
                <section style={{ marginBottom: '28px' }}>
                    <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', letterSpacing: '0.05em' }}>
                        Safety & Guardrails
                    </h4>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '16px',
                        background: 'rgba(0, 240, 144, 0.05)',
                        border: '1px solid rgba(0, 240, 144, 0.2)',
                        borderRadius: '12px'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <ShieldCheck size={18} color="var(--success)" />
                            <span style={{ fontSize: '14px', fontWeight: 500 }}>Safety Score</span>
                        </div>
                        <span className="mono" style={{ fontSize: '18px', fontWeight: 700, color: 'var(--success)' }}>
                            {data.safetyScore || '98/100'}
                        </span>
                    </div>
                </section>

                {/* LLM Reasoning */}
                {data.isLLM && (
                    <section>
                        <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', letterSpacing: '0.05em' }}>
                            LLM Reasoning Trace
                        </h4>
                        <div style={{
                            background: 'var(--surface)',
                            padding: '16px',
                            borderRadius: '12px',
                            border: '1px solid var(--border-secondary)',
                            fontSize: '13px',
                            lineHeight: '1.6',
                            color: 'var(--text-secondary)'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: 'var(--accent)' }}>
                                <Brain size={16} />
                                <span style={{ fontWeight: 600 }}>Cortex.Analysis</span>
                            </div>
                            {data.llmOutput || (
                                <span style={{ fontStyle: 'italic', opacity: 0.7 }}>Waiting for agent execution...</span>
                            )}
                        </div>
                    </section>
                )}

            </div>
        </div>
    );
};

export default DetailPanel;
