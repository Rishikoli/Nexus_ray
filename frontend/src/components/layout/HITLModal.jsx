import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

const HITLModal = ({ request, onDecision }) => {
    if (!request) return null;

    return (
        <AnimatePresence>
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0,0,0,0.7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                backdropFilter: 'blur(4px)'
            }}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="glass-panel"
                    style={{
                        background: 'var(--card-bg)',
                        borderRadius: '20px',
                        width: '500px',
                        border: '1px solid var(--border-primary)',
                        overflow: 'hidden',
                        boxShadow: 'var(--shadow-hover)'
                    }}
                >
                    {/* Header */}
                    <div style={{
                        padding: '24px',
                        background: request.severity === 'critical' ? 'rgba(229, 83, 61, 0.15)' : 'rgba(250, 204, 21, 0.1)',
                        borderBottom: '1px solid var(--border-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px'
                    }}>
                        <div style={{
                            background: 'var(--card-bg)',
                            padding: '10px',
                            borderRadius: '50%',
                            boxShadow: 'var(--shadow-card)',
                            border: '1px solid var(--border-secondary)'
                        }}>
                            <ShieldAlert size={28} color={request.severity === 'critical' ? 'var(--error)' : 'var(--warning)'} />
                        </div>
                        <div>
                            <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>Human Approval Required</h3>
                            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                Workflow <span className="mono" style={{ color: 'var(--accent)' }}>{request.workflow_id.slice(0, 8)}...</span> paused for review
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div style={{ padding: '24px' }}>
                        <div style={{ marginBottom: '24px' }}>
                            <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', letterSpacing: '0.05em' }}>
                                Trigger Reason
                            </h4>
                            <div style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text-primary)', lineHeight: '1.5' }}>
                                {request.description}
                            </div>
                        </div>

                        <div style={{ marginBottom: '28px' }}>
                            <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', letterSpacing: '0.05em' }}>
                                Context Payload
                            </h4>
                            <div style={{
                                background: 'var(--surface)',
                                padding: '16px',
                                borderRadius: '12px',
                                fontSize: '13px',
                                color: 'var(--text-secondary)',
                                border: '1px solid var(--border-secondary)',
                                maxHeight: '200px',
                                overflowY: 'auto'
                            }}>
                                <pre style={{ margin: 0, fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'pre-wrap' }}>
                                    {JSON.stringify(request.context, null, 2)}
                                </pre>
                            </div>
                        </div>

                        {/* Actions */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <button
                                onClick={() => onDecision('reject')}
                                style={{
                                    padding: '14px',
                                    borderRadius: '12px',
                                    border: '1px solid var(--border-primary)',
                                    background: 'transparent',
                                    color: 'var(--text-primary)',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px',
                                    transition: 'all 0.2s',
                                    ':hover': { background: 'var(--surface-hover)' }
                                }}
                            >
                                <XCircle size={18} color="var(--error)" />
                                Reject
                            </button>

                            <button
                                onClick={() => onDecision('approve')}
                                style={{
                                    padding: '14px',
                                    borderRadius: '12px',
                                    border: 'none',
                                    background: 'var(--accent)',
                                    color: 'white',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px',
                                    boxShadow: 'var(--accent-glow)'
                                }}
                            >
                                <CheckCircle2 size={18} />
                                Approve Action
                            </button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default HITLModal;
