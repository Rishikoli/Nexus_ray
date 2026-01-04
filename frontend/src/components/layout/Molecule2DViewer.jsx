import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

const Molecule2DViewer = ({ smiles = "C8H11NO2", width = "100%", height = 200 }) => {
    // Deterministic pseudo-random generation based on input string
    const generateStructure = (seedStr) => {
        let seed = 0;
        for (let i = 0; i < seedStr.length; i++) seed = (seed << 5) - seed + seedStr.charCodeAt(i);

        const random = () => {
            const x = Math.sin(seed++) * 10000;
            return x - Math.floor(x);
        };

        const numAtoms = Math.floor(random() * 8) + 6; // 6-14 atoms
        const atoms = [];
        const bonds = [];

        // Center
        const cx = 50;
        const cy = 50;

        // Generate Atoms
        for (let i = 0; i < numAtoms; i++) {
            const angle = random() * Math.PI * 2;
            const dist = random() * 30 + 10; // 10-40% radius
            atoms.push({
                id: i,
                x: cx + Math.cos(angle) * dist,
                y: cy + Math.sin(angle) * dist,
                size: random() * 4 + 4, // 4-8 radius
                element: ['C', 'N', 'O', 'H'][Math.floor(random() * 4)],
                color: ['#6D5CFF', '#00D2FF', '#FF3B30', '#34C759'][Math.floor(random() * 4)]
            });
        }

        // Generate Bonds (MST-ish)
        for (let i = 1; i < numAtoms; i++) {
            const target = Math.floor(random() * i);
            bonds.push({ source: i, target: target });
        }
        // Extra random bonds for rings
        if (random() > 0.5) bonds.push({ source: 0, target: numAtoms - 1 });

        return { atoms, bonds };
    };

    const { atoms, bonds } = useMemo(() => generateStructure(smiles), [smiles]);

    return (
        <motion.div
            className="molecule-2d-container"
            style={{
                width: width,
                height: height,
                background: 'rgba(0,0,0,0.2)',
                borderRadius: '12px',
                position: 'relative',
                overflow: 'hidden',
                border: '1px solid var(--border-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
        >
            <motion.svg
                width="100%"
                height="100%"
                viewBox="0 0 100 100"
                preserveAspectRatio="xMidYMid meet"
                animate={{ rotate: 360 }}
                transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
            >
                {/* Bonds */}
                {bonds.map((bond, i) => {
                    const s = atoms[bond.source];
                    const t = atoms[bond.target];
                    return (
                        <motion.line
                            key={`bond-${i}`}
                            x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                            stroke="rgba(255,255,255,0.2)"
                            strokeWidth="1.5"
                            initial={{ pathLength: 0, opacity: 0 }}
                            animate={{ pathLength: 1, opacity: 1 }}
                            transition={{ duration: 1, delay: i * 0.1 }}
                        />
                    );
                })}

                {/* Atoms */}
                {atoms.map((atom, i) => (
                    <motion.g
                        key={`atom-${i}`}
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: [1, 1.2, 1], opacity: 1 }}
                        transition={{
                            scale: { duration: 3, repeat: Infinity, repeatType: "reverse", delay: i * 0.2 },
                            opacity: { duration: 0.5 }
                        }}
                    >
                        <circle
                            cx={atom.x}
                            cy={atom.y}
                            r={atom.size}
                            fill={atom.color}
                            fillOpacity="0.8"
                            stroke="rgba(255,255,255,0.4)"
                            strokeWidth="1"
                        />
                        <text
                            x={atom.x}
                            y={atom.y}
                            dy=".3em"
                            textAnchor="middle"
                            fill="white"
                            fontSize="4px"
                            fontFamily="Arial"
                            fontWeight="bold"
                            style={{ pointerEvents: 'none' }}
                        >
                            {atom.element}
                        </text>
                    </motion.g>
                ))}
            </motion.svg>
            <div style={{ position: 'absolute', bottom: '8px', right: '12px', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                2D LIVE VIEW
            </div>
        </motion.div>
    );
};

export default Molecule2DViewer;
