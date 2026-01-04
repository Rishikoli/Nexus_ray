import { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { Play, RotateCw } from 'lucide-react';
import { motion } from 'framer-motion'; // Import framer-motion

// Components
import { SimplePillNav as PillNav } from './components/ui/PillNav';
import TaskNode from './components/flow/TaskNode';
import DetailPanel from './components/layout/DetailPanel';
import LogPanel from './components/layout/LogPanel'; // UPDATED
import MetricCards from './components/layout/MetricCards';
import HITLModal from './components/layout/HITLModal';
import WorkflowInput from './components/layout/WorkflowInput';
import SpeedToggle from './components/layout/SpeedToggle';
import WorkflowStatusPanel from './components/layout/WorkflowStatusPanel';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

const nodeTypes = { taskNode: TaskNode };

// --- Configurations ---
const WORKFLOWS = [
    { id: 'protein', label: '🧬 Protein-Drug Discovery' },
    { id: 'semiconductor', label: '💎 Semiconductor Yield' }
];

const PROTEIN_NODES = [
    { id: '1', type: 'taskNode', position: { x: 50, y: 50 }, data: { label: 'Input Validator', agentType: 'Validator', status: 'pending', isLLM: false } },
    { id: '2', type: 'taskNode', position: { x: 300, y: 50 }, data: { label: 'Structure Predictor', agentType: 'Predictor', status: 'pending', isLLM: false } },
    { id: '3', type: 'taskNode', position: { x: 550, y: 50 }, data: { label: 'Quality Assessor', agentType: 'Analyst', status: 'pending', isLLM: false } },
    { id: '4', type: 'taskNode', position: { x: 50, y: 200 }, data: { label: 'Binding Site ID', agentType: 'Locator', status: 'pending', isLLM: false } },
    { id: '5', type: 'taskNode', position: { x: 300, y: 200 }, data: { label: 'Molecular Docker', agentType: 'Simulator', status: 'pending', isLLM: false } },
    { id: '6', type: 'taskNode', position: { x: 550, y: 200 }, data: { label: 'Safety Evaluator', agentType: 'Auditor', status: 'pending', isLLM: false } },
    { id: '7', type: 'taskNode', position: { x: 300, y: 350 }, data: { label: 'Drugability Scorer', agentType: 'LLM Reasoner', status: 'pending', isLLM: true } },
];

const SEMI_NODES = [
    { id: '1', type: 'taskNode', position: { x: 50, y: 50 }, data: { label: 'Defect Analyzer', agentType: 'Vision', status: 'pending', isLLM: false } },
    { id: '2', type: 'taskNode', position: { x: 300, y: 50 }, data: { label: 'Defect Classifier', agentType: 'Classifier', status: 'pending', isLLM: false } },
    { id: '3', type: 'taskNode', position: { x: 550, y: 50 }, data: { label: 'Process Intelligence', agentType: 'Analyst', status: 'pending', isLLM: false } },
    { id: '4', type: 'taskNode', position: { x: 50, y: 200 }, data: { label: 'Yield Predictor', agentType: 'Regressor', status: 'pending', isLLM: false } },
    { id: '5', type: 'taskNode', position: { x: 300, y: 200 }, data: { label: 'Root Cause Analyzer', agentType: 'LLM Reasoner', status: 'pending', isLLM: true } },
    { id: '6', type: 'taskNode', position: { x: 550, y: 200 }, data: { label: 'Yield Aggregator', agentType: 'aggregator', status: 'pending', isLLM: false } },
    { id: '7', type: 'taskNode', position: { x: 300, y: 350 }, data: { label: 'Recipe Optimizer', agentType: 'Optimizer', status: 'pending', isLLM: false } },
];

const EDGES = [
    { id: 'e1-2', source: '1', target: '2', type: 'smoothstep', animated: true },
    { id: 'e2-3', source: '2', target: '3', type: 'smoothstep', animated: true },
    { id: 'e3-4', source: '3', target: '4', type: 'smoothstep', animated: true },
    { id: 'e4-5', source: '4', target: '5', type: 'smoothstep', animated: true },
    { id: 'e5-6', source: '5', target: '6', type: 'smoothstep', animated: true },
    { id: 'e6-7', source: '6', target: '7', type: 'smoothstep', animated: true },
];

// Animation Variants
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            when: "beforeChildren",
            staggerChildren: 0.1
        }
    }
};

const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
};

function App() {
    const [activeWorkflow, setActiveWorkflow] = useState('protein');
    const [nodes, setNodes, onNodesChange] = useNodesState(PROTEIN_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(EDGES);
    const [selectedNode, setSelectedNode] = useState(null);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [workflowId, setWorkflowId] = useState(null);
    const [workflowResult, setWorkflowResult] = useState(null);

    // Real Metrics State
    const [metrics, setMetrics] = useState({
        avg_latency: 0,
        success_rate: 100,
        active_agents: 14,
        memory_usage: 0,
        hitl_pending: 0
    });

    // HITL State
    const [pendingHITL, setPendingHITL] = useState(null);

    // Fetch Metrics
    const fetchMetrics = useCallback(async () => {
        try {
            const res = await axios.get(`${API_BASE}/metrics`);
            setMetrics(res.data);
        } catch (e) {
            console.error("Metric fetch failed", e);
        }
    }, []);

    // Poll HITL
    const pollHITL = useCallback(async () => {
        // Poll for ANY pending HITL requests (global queue)
        try {
            const res = await axios.get(`${API_BASE}/hitl/pending`);

            // Just take the first one if it exists
            const nextReq = res.data[0];

            if (nextReq) {
                console.log("⚡ HITL FOUND (Global Queue):", nextReq);
                setPendingHITL(nextReq);
            } else {
                setPendingHITL(null);
            }
        } catch (e) {
            console.error("HITL Poll Error:", e);
        }
    }, []);

    // Set up polling intervals
    useEffect(() => {
        const interval = setInterval(() => {
            fetchMetrics();
            pollHITL();
        }, 2000);
        return () => clearInterval(interval);
    }, [fetchMetrics, pollHITL]);


    const handleHITLDecision = async (action) => {
        if (!pendingHITL) return;
        try {
            await axios.post(`${API_BASE}/hitl/${pendingHITL.request_id}/decision`, {
                action: action
            });
            setPendingHITL(null); // Close modal

            setEvents(prev => [...prev, {
                type: action === 'approve' ? 'hitl_approved' : 'hitl_rejected',
                message: `Human ${action}d request: ${pendingHITL.description}`,
                time: new Date().toLocaleTimeString()
            }]);
        } catch (e) {
            alert("Failed to submit decision: " + e.message);
        }
    };


    // Tab State
    const [activeTab, setActiveTab] = useState('feed'); // 'feed', 'results', 'inspect'

    // Switch Workflow Logic
    const handleWorkflowChange = (id) => {
        setActiveTab('feed'); // Reset to feed
        setActiveWorkflow(id);
        setNodes(id === 'protein' ? PROTEIN_NODES : SEMI_NODES);
        setSelectedNode(null);
        setEvents([]);
        setWorkflowId(null);
        setWorkflowResult(null); // Clear previous results
    };

    const onNodeClick = (_, node) => {
        setSelectedNode(node);
        setActiveTab('inspect'); // Auto-switch to inspect
    };

    const [speed, setSpeed] = useState(1); // 1 = Normal, 5 = Turbo, 99 = Instant
    const [ws, setWs] = useState(null);

    // WebSocket Connection
    useEffect(() => {
        const hostname = window.location.hostname;
        const socket = new WebSocket(`ws://${hostname}:8000/ws`);

        socket.onopen = () => {
            console.log('✅ WebSocket Connected');
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'workflow_complete' && speed === 99) {
                // INSTANT COMPLETION logic
                setLoading(false);
                setNodes((nds) => nds.map(n => ({
                    ...n,
                    data: {
                        ...n.data,
                        status: 'completed',
                        executionTime: (Math.random() * 1.5 + 0.5).toFixed(2),
                        memoryUsage: (Math.random() * 400 + 100).toFixed(0) + 'MB'
                    }
                })));
                setEvents(prev => [...prev, {
                    type: 'workflow_complete',
                    message: '⚡ Instant Workflow Completion (WebSocket)',
                    time: new Date().toLocaleTimeString()
                }]);
                fetchMetrics();

                // Set full result for DetailPanel
                const result = data.result;
                setWorkflowResult(result);
                setActiveTab('results'); // Auto-switch to results

            } else if (data.type === 'agent_update') {
                // LIVE STREAM LOGIC
                const agentName = data.payload.agent;

                setEvents(prev => [...prev, {
                    type: data.payload.type || 'info',
                    message: data.payload.message,
                    agent: agentName,
                    time: new Date().toLocaleTimeString()
                }]);

                // Update Graph Nodes (Systematic Flow)
                // Only status updates, not reasoning events
                if (data.payload.type !== 'reasoning') {
                    setNodes(nds => {
                        // Find index of the active agent
                        const activeIndex = nds.findIndex(n =>
                            n.data.label.replace(/\s/g, '').toLowerCase() === agentName.replace(/\s/g, '').toLowerCase()
                        );

                        if (activeIndex === -1) return nds; // No match (e.g. ProcessGate)

                        return nds.map((node, index) => {
                            if (index < activeIndex) {
                                // Completed nodes get simulated token usage
                                return {
                                    ...node,
                                    data: {
                                        ...node.data,
                                        status: 'completed',
                                        tokens: (Math.random() * 200 + 50).toFixed(0) + ' tkns',
                                        executionTime: (Math.random() * 0.5 + 0.1).toFixed(2)
                                    }
                                };
                            } else if (index === activeIndex) {
                                return { ...node, data: { ...node.data, status: 'active' } };
                            } else {
                                return { ...node, data: { ...node.data, status: 'pending' } };
                            }
                        });
                    });
                }
            }
        };

        socket.onclose = () => console.log('❌ WebSocket Disconnected');
        setWs(socket);

        return () => socket.close();
    }, [speed, activeWorkflow, fetchMetrics]);

    const runWorkflow = async (customPayload) => {
        setLoading(true);
        setEvents([]);
        setWorkflowResult(null);
        setActiveTab('feed');

        try {
            let endpoint = '';
            let payload = {};

            if (activeWorkflow === 'protein') {
                endpoint = `${API_BASE}/reference/protein-drug`;
                payload = customPayload || {
                    protein_sequence: "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR",
                    drug_smiles: "CC(=O)OC1=CC=CC=C1C(=O)O"
                };
            } else if (activeWorkflow === 'semiconductor') {
                endpoint = `${API_BASE}/reference/semiconductor`;
                payload = customPayload || {
                    wafer_id: "WAF-" + Math.floor(Math.random() * 10000),
                    defect_data: { total: Math.floor(Math.random() * 200) + 50 }
                };
            }

            // Add start event
            setEvents([{
                type: 'workflow_start',
                message: `Starting ${activeWorkflow} workflow...`,
                time: new Date().toLocaleTimeString()
            }]);

            const res = await axios.post(endpoint, payload);
            const { workflow_id } = res.data;
            setWorkflowId(workflow_id); // Enable HITL polling

            // Start polling for final status
            pollStatus(workflow_id, null);

        } catch (error) {
            console.error(error);
            setLoading(false);
            setEvents(prev => [...prev, {
                type: 'error',
                message: 'Failed to start workflow: ' + (error.response?.data?.detail || error.message),
                time: new Date().toLocaleTimeString()
            }]);
        }
    };

    const pollStatus = async (id, simInterval) => {
        const poll = setInterval(async () => {
            try {
                const res = await axios.get(`${API_BASE}/reference/status/${id}`);
                if (res.data.status === 'complete') {
                    clearInterval(poll);
                    clearInterval(simInterval);
                    setLoading(false);

                    // Force all nodes complete
                    setNodes((nds) => nds.map(n => ({ ...n, data: { ...n.data, status: 'completed' } })));

                    setEvents(prev => [...prev, {
                        type: 'workflow_complete',
                        message: 'Workflow completed successfully',
                        time: new Date().toLocaleTimeString()
                    }]);

                    // Refresh metrics
                    fetchMetrics();

                    // Update LLM Node with result
                    const result = res.data.result;
                    setWorkflowResult(result);
                    setActiveTab('results'); // Auto-switch to results

                    // ... (update node data logic)
                }
            } catch (e) {
                clearInterval(poll);
            }
        }, 2000);
    };

    // WebSocket Connection
    useEffect(() => {
        // (Duplicate socket logic block removed - optimization)
    }, []);


    return (
        <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--app-bg)', color: 'var(--text-primary)' }}>

            {/* Header */}
            <div style={{
                height: '64px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 24px',
                borderBottom: '1px solid var(--glass-border)',
                background: 'rgba(5, 5, 8, 0.6)',
                backdropFilter: 'blur(12px)',
                zIndex: 50
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: '32px', height: '32px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, var(--accent), #4facfe)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                        <RotateCw size={18} color="#fff" className={loading ? "spin" : ""} />
                    </div>
                    <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0, fontFamily: 'Outfit, sans-serif' }}>Nexus Ray</h2>
                </div>

                <PillNav items={WORKFLOWS} activeId={activeWorkflow} onSelect={handleWorkflowChange} />

                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <SpeedToggle speed={speed} setSpeed={setSpeed} />
                    <MetricCards metrics={metrics} />
                </div>
            </div>

            <motion.main
                initial="hidden"
                animate="visible"
                variants={containerVariants}
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) 700px',
                    gap: '20px',
                    flex: 1,
                    overflow: 'hidden',
                    padding: '20px'
                }}
            >
                {/* 1. Main Canvas (Graph) */}
                <motion.div variants={itemVariants} style={{
                    position: 'relative',
                    height: '100%'
                }}>
                    {/* Graph Container with Clipping */}
                    <div style={{
                        width: '100%',
                        height: '100%',
                        borderRadius: '16px',
                        border: '1px solid var(--glass-border)',
                        overflow: 'hidden',
                        background: 'rgba(255, 255, 255, 0.02)',
                    }}>
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onNodeClick={onNodeClick}
                            nodeTypes={nodeTypes}
                            fitView
                            className="react-flow-dark"
                        >
                            <Background color="#333" gap={20} variant="dots" size={1} />
                            <Controls style={{ fill: 'white' }} />
                        </ReactFlow>
                    </div>

                    <div style={{ position: 'absolute', top: 24, left: 24, zIndex: 100 }}>
                        <WorkflowInput activeWorkflow={activeWorkflow} onRun={runWorkflow} isDisabled={loading} />
                    </div>
                </motion.div>
                <motion.div
                    variants={itemVariants}
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gridColumn: '2 / 3',
                        gridRow: '1 / -1',
                        minWidth: 0,
                        height: '100%',
                        gap: '20px', // Spacing between the two panels
                        overflow: 'hidden'
                    }}
                >
                    {/* TOP HALF: Logs & Results */}
                    <div style={{
                        flex: '1.5', // Takes up 60% of space
                        display: 'flex',
                        flexDirection: 'column',
                        background: 'rgba(5, 5, 8, 0.4)',
                        backdropFilter: 'blur(10px)',
                        borderRadius: '16px',
                        border: '1px solid var(--glass-border)',
                        overflow: 'hidden'
                    }}>
                        {/* Tab Header */}
                        <div style={{
                            display: 'flex',
                            borderBottom: '1px solid var(--border-primary)',
                            padding: '0 4px',
                            height: '48px',
                            alignItems: 'center'
                        }}>
                            {/* Tabs: Feed and Results (Inspect moved to bottom) */}
                            {['feed', 'results'].map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    style={{
                                        flex: 1,
                                        background: 'none',
                                        border: 'none',
                                        borderBottom: activeTab === tab ? '2px solid var(--accent)' : '2px solid transparent',
                                        color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-muted)',
                                        fontWeight: 600,
                                        fontSize: '13px',
                                        height: '100%',
                                        cursor: 'pointer',
                                        textTransform: 'capitalize',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {tab === 'feed' ? 'Logs & Activity' : tab}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content Area */}
                        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: '16px' }}>

                            {activeTab === 'results' && (
                                workflowResult ? (
                                    <WorkflowStatusPanel workflowResult={workflowResult} />
                                ) : (
                                    <div style={{
                                        flex: 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'var(--text-muted)',
                                        fontSize: '14px'
                                    }}>
                                        Run workflow to see results
                                    </div>
                                )
                            )}

                            {activeTab === 'feed' && (
                                <LogPanel events={events} />
                            )}
                        </div>
                    </div>

                    {/* BOTTOM HALF: Inspect / Node Details */}
                    <div style={{
                        flex: '1', // Takes up 40% of space
                        overflow: 'hidden',
                        borderRadius: '16px',
                        display: 'flex', flexDirection: 'column',
                        background: 'rgba(5, 5, 8, 0.4)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid var(--glass-border)'
                    }}>
                        <div style={{
                            padding: '12px 16px', borderBottom: '1px solid var(--border-primary)',
                            fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)'
                        }}>
                            Selection Details
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', padding: '0' }}>
                            {selectedNode ? (
                                <DetailPanel selectedNode={selectedNode} />
                            ) : (
                                <div style={{
                                    height: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'var(--text-muted)',
                                    fontSize: '14px',
                                    fontStyle: 'italic',
                                    padding: '20px', textAlign: 'center'
                                }}>
                                    Select a node in the graph to inspect its details
                                </div>
                            )}
                        </div>
                    </div>

                </motion.div>

            </motion.main >

            {/* HITL Modal */}
            <HITLModal
                request={pendingHITL}
                onDecision={handleHITLDecision}
            />
        </div>
    );
}

export default App;
