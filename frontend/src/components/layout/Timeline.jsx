import React from 'react';
import { Clock, Info, CheckCircle2, AlertTriangle, Play, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Timeline = ({ events }) => {
    if (!events || events.length === 0) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-panel"
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '30px',
                    borderRadius: '16px',
                    border: '1px solid var(--border-primary)',
                    minHeight: '200px'
                }}
            >
                <div style={{
                    padding: '24px',
                    borderRadius: '50%',
                    background: 'var(--surface)',
                    border: '1px solid var(--border-secondary)',
                    marginBottom: '16px',
                    boxShadow: 'var(--shadow-inner)'
                }}>
                    <Activity size={24} color="var(--text-muted)" />
                </div>
                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Waiting for workflow events...</p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>Run a workflow to see the live Kafka stream</p>
            </motion.div>
        );
    }

    const getIcon = (type) => {
        if (type.includes('error') || type.includes('failed')) return <AlertTriangle size={14} color="var(--error)" />;
        if (type.includes('complete') || type.includes('success')) return <CheckCircle2 size={14} color="var(--success)" />;
        if (type.includes('start')) return <Play size={14} fill="var(--accent)" color="var(--accent)" />;
        return <Info size={14} color="var(--accent)" />;
    };

    return (
        <div className="glass-panel" style={{ borderRadius: '16px', padding: '20px', border: '1px solid var(--border-primary)', display: 'flex', flexDirection: 'column', maxHeight: '300px' }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
                paddingBottom: '16px',
                borderBottom: '1px solid var(--border-secondary)'
            }}>
                <h4 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
                    <Activity size={14} color="var(--accent)" /> Live Activity Stream
                </h4>
                <div className="mono" style={{ fontSize: '11px', color: 'var(--accent)', background: 'var(--surface-active)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-secondary)' }}>
                    {events.length} EVENTS
                </div>
            </div>

            <div style={{
                display: 'flex',
                flexDirection: 'column', // Changed to vertical for better readability in side panel
                gap: '0',
                overflowY: 'auto',
                paddingRight: '4px',
                height: '100%'
            }}>
                <AnimatePresence initial={false}>
                    {events.slice().reverse().map((event, idx) => ( // Show newest first
                        <motion.div
                            key={events.length - idx} // Stable key
                            initial={{ opacity: 0, x: -20, height: 0 }}
                            animate={{ opacity: 1, x: 0, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 25 }}
                            style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '12px',
                                paddingBottom: '16px',
                                position: 'relative'
                            }}
                        >
                            {/* Connector Line (Vertical now) */}
                            {idx < events.length - 1 && (
                                <div style={{
                                    position: 'absolute',
                                    top: '24px',
                                    left: '14px',
                                    bottom: -4,
                                    width: '2px',
                                    background: 'var(--border-secondary)',
                                    zIndex: 0
                                }} />
                            )}

                            {/* Dot */}
                            <div style={{
                                width: '30px',
                                height: '30px',
                                borderRadius: '50%',
                                background: 'var(--surface)',
                                border: '1px solid var(--border-secondary)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                zIndex: 1,
                                flexShrink: 0,
                                boxShadow: event.type.includes('start') ? '0 0 15px rgba(109, 92, 255, 0.2)' : 'none'
                            }}>
                                {getIcon(event.type)}
                            </div>

                            {/* Content */}
                            <div style={{ flex: 1, paddingTop: '4px' }}>
                                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', lineHeight: '1.4' }}>
                                    {event.message || event.type}
                                </div>
                                <div className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                                    {event.time}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default Timeline;
