import React from 'react';
import { Clock, Activity, Zap, Server } from 'lucide-react';
import { motion } from 'framer-motion';

const MetricCards = ({ metrics = {} }) => {
    // Default values if metrics is null or fields missing
    const {
        avg_latency = 0,
        llm_tokens_total = 0, // Changed from memory_usage
        active_agents = 0,
        hitl_pending = 0
    } = metrics || {};

    const cards = [
        {
            label: 'Avg Latency',
            value: avg_latency ? `${avg_latency.toFixed(2)}s` : '--',
            trend: 'Live',
            icon: Clock,
            color: 'var(--accent)'
        },
        {
            label: 'Context Usage',
            value: llm_tokens_total ? `${(llm_tokens_total / 1000).toFixed(1)}k` : '0',
            trend: 'Tokens',
            icon: Server,
            color: 'var(--success)'
        },
        {
            label: 'Active Agents',
            value: active_agents || 0,
            trend: 'Online',
            icon: Zap,
            color: 'var(--running)'
        },
        {
            label: 'Pending HITL',
            value: hitl_pending,
            trend: hitl_pending > 0 ? 'Action Req' : 'None',
            icon: Activity,
            color: hitl_pending > 0 ? 'var(--warning)' : 'var(--text-muted)'
        }
    ];

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {cards.map((card, idx) => (
                <motion.div
                    key={idx}
                    className="glass-panel"
                    whileHover={{ y: -4, boxShadow: "0 12px 30px rgba(109, 92, 255, 0.15)" }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    style={{
                        padding: '16px',
                        borderRadius: '16px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        cursor: 'default',
                        minWidth: '140px'
                    }}
                >
                    {/* Card content: label, value, trend */}
                    <div>
                        <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '6px' }}>
                            {card.label}
                        </div>
                        <motion.div
                            key={card.value} // Trigger animation on change
                            initial={{ scale: 0.9, opacity: 0.5 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="mono"
                            style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)' }}
                        >
                            {card.value}
                        </motion.div>
                        <div style={{ fontSize: '10px', color: card.trend === 'Action Req' ? 'var(--warning)' : 'var(--text-muted)', marginTop: '4px' }}>
                            {card.trend}
                        </div>
                    </div>
                    {/* Icon container */}
                    <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        background: 'var(--surface-hover)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px solid var(--border-secondary)'
                    }}>
                        <card.icon size={18} color={card.color} />
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

export default MetricCards;
