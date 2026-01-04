import {
    Activity,
    Brain,
    Database,
    Play,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    Clock,
    Zap
} from 'lucide-react';
import { Handle, Position } from 'reactflow';
import { motion } from 'framer-motion';

const nodeStyles = {
    default: {
        background: 'rgba(30, 32, 40, 0.85)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px', // Tighter radius
        padding: '8px 10px', // Micro padding
        minWidth: '140px', // Micro width
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        fontFamily: 'Outfit, sans-serif',
        color: 'var(--text-primary)',
        transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
    },
    selected: {
        border: '1px solid var(--accent)',
        boxShadow: 'var(--accent-glow)',
    },
    running: {
        border: '1px solid var(--running)',
        // Shadow handled by animation
    }
};

const statusColors = {
    pending: 'var(--text-muted)',
    running: 'var(--running)',
    completed: 'var(--success)',
    failed: 'var(--error)',
    warning: 'var(--warning)',
};

const TaskNode = ({ data, selected }) => {
    const statusColor = statusColors[data.status] || statusColors.pending;
    const isRunning = data.status === 'running';

    // Dynamic style based on state
    let activeStyle = { ...nodeStyles.default };
    if (selected) activeStyle = { ...activeStyle, ...nodeStyles.selected };
    if (isRunning) activeStyle = { ...activeStyle, ...nodeStyles.running };

    const StatusIcon = () => {
        switch (data.status) {
            case 'running': return <Zap size={10} fill="currentColor" />; // Micro icon
            case 'completed': return <CheckCircle2 size={10} />;
            case 'failed': return <XCircle size={10} />;
            default: return <Clock size={10} />;
        }
    };

    return (
        <motion.div
            style={activeStyle}
            animate={isRunning ? {
                boxShadow: [
                    "0 0 0 rgba(59, 130, 246, 0)",
                    "0 0 10px rgba(59, 130, 246, 0.4)", // Tighter glow
                    "0 0 0 rgba(59, 130, 246, 0)"
                ]
            } : {}}
            transition={isRunning ? {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
            } : {}}
        >
            {/* Top Handle */}
            <Handle type="target" position={Position.Top} style={{ background: 'var(--text-secondary)', width: '6px', height: '6px' }} />

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, marginBottom: '0px', letterSpacing: '-0.01em', lineHeight: '1.2' }}>{data.label}</div>
                    <div style={{ fontSize: '9px', color: 'var(--text-secondary)' }}>{data.agentType}</div>
                </div>

                {/* Status Badge */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    fontSize: '9px',
                    padding: '2px 4px',
                    borderRadius: '8px',
                    background: isRunning ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255,255,255,0.05)',
                    color: statusColor,
                    fontWeight: 500,
                    border: '1px solid transparent',
                    borderColor: isRunning ? 'rgba(59, 130, 246, 0.2)' : 'transparent'
                }}>
                    <StatusIcon />
                    {/* Hide text on micro node if needed, but keeping for now */}
                    {/* <span style={{ textTransform: 'capitalize' }}>{data.status}</span> */}
                </div>
            </div>

            {/* Meta Content */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '9px', // Micro meta text
                color: 'var(--text-muted)',
                borderTop: '1px solid var(--border-primary)',
                paddingTop: '6px',
                marginTop: '6px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                    <Brain size={10} color={data.isLLM ? 'var(--accent)' : 'currentColor'} />
                    <span style={{ color: data.isLLM ? 'var(--text-secondary)' : 'currentColor' }}>
                        {data.isLLM ? 'LLM' : 'Det.'}
                    </span>
                </div>
                <div className="mono" style={{ opacity: 0.8 }}>
                    {data.executionTime ? `${Number(data.executionTime).toFixed(2)}s` : '--'}
                </div>
            </div>

            {/* Bottom Handle */}
            <Handle type="source" position={Position.Bottom} style={{ background: 'var(--text-secondary)', width: '6px', height: '6px' }} />
        </motion.div>
    );
};

export default TaskNode;
