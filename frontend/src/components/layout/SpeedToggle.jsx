import React from 'react';
import { Zap, FastForward, PlayCircle } from 'lucide-react';

const SpeedToggle = ({ speed, setSpeed, disabled }) => {
    return (
        <div className="glass-panel" style={{
            display: 'flex',
            borderRadius: '10px',
            padding: '4px',
            gap: '2px',
            background: 'var(--surface)'
        }}>
            <button
                onClick={() => setSpeed(1)}
                disabled={disabled}
                title="Normal Speed (Demo Mode)"
                style={{
                    background: speed === 1 ? 'var(--surface-active)' : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    color: speed === 1 ? 'var(--text-primary)' : 'var(--text-muted)',
                    boxShadow: speed === 1 ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    transition: 'all 0.2s ease'
                }}
            >
                <PlayCircle size={14} color={speed === 1 ? 'var(--accent)' : 'currentColor'} /> 1x
            </button>

            <button
                onClick={() => setSpeed(5)}
                disabled={disabled}
                title="Turbo Mode (5x speed)"
                style={{
                    background: speed === 5 ? 'var(--surface-active)' : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    color: speed === 5 ? 'var(--text-primary)' : 'var(--text-muted)',
                    boxShadow: speed === 5 ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    transition: 'all 0.2s ease'
                }}
            >
                <FastForward size={14} color={speed === 5 ? 'var(--running)' : 'currentColor'} /> 5x
            </button>

            <button
                onClick={() => setSpeed(99)}
                disabled={disabled}
                title="Instant Mode (Wait for WebSocket)"
                style={{
                    background: speed === 99 ? 'var(--surface-active)' : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    color: speed === 99 ? 'var(--text-primary)' : 'var(--text-muted)',
                    boxShadow: speed === 99 ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    transition: 'all 0.2s ease'
                }}
            >
                <Zap size={14} color={speed === 99 ? 'var(--warning)' : 'currentColor'} fill={speed === 99 ? 'var(--warning)' : 'none'} /> Instant
            </button>
        </div>
    );
};

export default SpeedToggle;
