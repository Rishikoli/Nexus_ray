import React, { useState } from 'react';
import { Settings, X, ChevronDown, ChevronUp, Play } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const WorkflowInput = ({ activeWorkflow, onRun, isDisabled }) => {
    const [isOpen, setIsOpen] = useState(false);

    // Protein State
    const [proteinSeq, setProteinSeq] = useState("MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRL");
    const [drugSmiles, setDrugSmiles] = useState("CC(=O)Oc1ccccc1C(=O)O");

    // Semiconductor State
    const [waferId, setWaferId] = useState("WAFER_2024_001");
    const [defectCount, setDefectCount] = useState(150);

    const handleSubmit = () => {
        const payload = activeWorkflow === 'protein'
            ? { protein_sequence: proteinSeq, drug_smiles: drugSmiles }
            : { wafer_id: waferId, defect_data: { total: parseInt(defectCount) } };

        onRun(payload);
        setIsOpen(false);
    };

    return (
        <div style={{ position: 'relative' }}>
            {/* Toggle / Quick Action */}
            <div style={{ display: 'flex', gap: '8px' }}>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="glass-panel"
                    style={{
                        padding: '8px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '13px',
                        fontWeight: 500,
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        borderRadius: '10px',
                        background: 'var(--surface)'
                    }}
                >
                    <Settings size={14} />
                    Configure
                    {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                <button
                    onClick={handleSubmit}
                    disabled={isDisabled}
                    style={{
                        background: isDisabled ? 'var(--surface)' : 'var(--accent)',
                        color: isDisabled ? 'var(--text-disabled)' : 'white',
                        border: 'none',
                        borderRadius: '10px',
                        padding: '8px 16px',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: isDisabled ? 'not-allowed' : 'pointer',
                        boxShadow: isDisabled ? 'none' : 'var(--accent-glow)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s ease'
                    }}
                >
                    {isDisabled ? 'Processing...' : (
                        <>
                            <Play size={14} fill="currentColor" /> Run Analysis
                        </>
                    )}
                </button>
            </div>

            {/* Dropdown Panel */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        className="glass-panel"
                        style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            marginTop: '12px',
                            borderRadius: '16px',
                            padding: '20px',
                            width: '320px',
                            zIndex: 150
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', alignItems: 'center' }}>
                            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Run Configuration</h4>
                            <div
                                onClick={() => setIsOpen(false)}
                                style={{
                                    cursor: 'pointer',
                                    padding: '4px',
                                    borderRadius: '50%',
                                    background: 'var(--surface-hover)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}
                            >
                                <X size={14} color="var(--text-secondary)" />
                            </div>
                        </div>

                        {activeWorkflow === 'protein' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>Target Protein Sequence</label>
                                    <textarea
                                        value={proteinSeq}
                                        onChange={(e) => setProteinSeq(e.target.value)}
                                        className="mono"
                                        style={{
                                            width: '100%',
                                            height: '80px',
                                            padding: '10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--border-secondary)',
                                            fontSize: '11px',
                                            background: 'var(--surface-active)',
                                            color: 'var(--text-secondary)',
                                            resize: 'none',
                                            outline: 'none'
                                        }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>Drug SMILES String</label>
                                    <input
                                        type="text"
                                        value={drugSmiles}
                                        onChange={(e) => setDrugSmiles(e.target.value)}
                                        className="mono"
                                        style={{
                                            width: '100%',
                                            padding: '10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--border-secondary)',
                                            fontSize: '11px',
                                            background: 'var(--surface-active)',
                                            color: 'var(--text-secondary)',
                                            outline: 'none'
                                        }}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>Wafer ID</label>
                                    <input
                                        type="text"
                                        value={waferId}
                                        onChange={(e) => setWaferId(e.target.value)}
                                        style={{
                                            width: '100%',
                                            padding: '10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--border-secondary)',
                                            fontSize: '13px',
                                            background: 'var(--surface-active)',
                                            color: 'var(--text-secondary)',
                                            outline: 'none'
                                        }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', textTransform: 'uppercase' }}>Defect Count</label>
                                    <input
                                        type="number"
                                        value={defectCount}
                                        onChange={(e) => setDefectCount(e.target.value)}
                                        style={{
                                            width: '100%',
                                            padding: '10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--border-secondary)',
                                            fontSize: '13px',
                                            background: 'var(--surface-active)',
                                            color: 'var(--text-secondary)',
                                            outline: 'none'
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-secondary)', display: 'flex', justifyContent: 'flex-end' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                Ready to process
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default WorkflowInput;
