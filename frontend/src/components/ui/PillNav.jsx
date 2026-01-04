import React from 'react';
import { motion } from 'framer-motion';

const PillNav = ({ items, activeId, onSelect }) => {
    // Legacy implementation - prefer SimplePillNav
    return <SimplePillNav items={items} activeId={activeId} onSelect={onSelect} />;
};

export const SimplePillNav = ({ items, activeId, onSelect }) => {
    return (
        <div style={{
            padding: '4px',
            background: 'var(--surface)',
            borderRadius: '999px',
            border: '1px solid var(--border-primary)',
            display: 'inline-flex',
            gap: '2px'
        }}>
            {items.map((item) => (
                <div
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    style={{
                        position: 'relative',
                        zIndex: 2,
                        padding: '6px 16px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 500,
                        color: activeId === item.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                        transition: 'color 0.2s',
                        borderRadius: '999px',
                        userSelect: 'none'
                    }}
                >
                    {activeId === item.id && (
                        <motion.div
                            layoutId="pill-bg"
                            style={{
                                position: 'absolute',
                                top: 0,
                                bottom: 0,
                                left: 0,
                                right: 0,
                                width: '100%',
                                height: '100%',
                                borderRadius: '999px',
                                background: 'var(--surface-active)',
                                boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                border: '1px solid var(--border-secondary)',
                                zIndex: -1
                            }}
                            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                        />
                    )}
                    {item.label}
                </div>
            ))}
        </div>
    );
};

export default PillNav;
