import React from 'react';
import { Activity } from 'lucide-react';
import Molecule2DViewer from './Molecule2DViewer';

const WorkflowStatusPanel = ({ workflowResult }) => {
    if (!workflowResult) return null;

    return (
        <div className="glass-panel" style={{ borderRadius: '16px', display: 'flex', flexDirection: 'column', flex: 1, minHeight: '0', overflow: 'hidden', border: '1px solid var(--border-primary)' }}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-primary)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Activity size={16} color="var(--accent)" />
                    Workflow Results
                </h3>
            </div>

            <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }} className="custom-scrollbar">
                {/* 2D Visualization Section */}
                {(workflowResult.drug || workflowResult.protein) && (
                    <section style={{ marginBottom: '24px' }}>
                        <h4 style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '8px', letterSpacing: '0.05em' }}>
                            Structure Visualization
                        </h4>
                        <Molecule2DViewer
                            smiles={workflowResult.drug || "DEFAULT"}
                            height={160}
                        />
                    </section>
                )}

                {Object.entries(workflowResult).map(([key, value]) => {
                    if (key === 'info' || key === 'message' || key === 'success') return null;
                    if (typeof value !== 'object' || value === null) return null;

                    return (
                        <section key={key} style={{ marginBottom: '20px' }}>
                            <h4 style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '8px', letterSpacing: '0.05em' }}>
                                {key.replace(/_/g, ' ')}
                            </h4>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', background: 'var(--surface)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border-secondary)' }}>
                                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'JetBrains Mono, monospace' }}>
                                    {JSON.stringify(value, null, 2)}
                                </pre>
                            </div>
                        </section>
                    );
                })}
            </div>
        </div>
    );
};

export default WorkflowStatusPanel;
