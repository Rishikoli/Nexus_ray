import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import SmilesDrawer from 'smiles-drawer';

const Molecule2DViewer = ({ smiles = "C8H11NO2", width = "100%", height = 200 }) => {
    // Generate a unique ID for the canvas to ensure robust targeting
    const canvasId = useRef(`molecule-canvas-${Math.random().toString(36).substr(2, 9)}`);
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!canvasRef.current || !smiles) return;

        // Ensure canvas has dimensions
        const rect = canvasRef.current.parentElement.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        // Update canvas logical size to match display size (prevents blur)
        canvasRef.current.width = rect.width;
        canvasRef.current.height = rect.height;

        try {
            // WORKAROUND: Use SvgDrawer directly because Drawer.js has an argument mismatch bug
            // causing it to skip initialization (interprets infoOnly as an empty array).
            const drawer = new SmilesDrawer.SvgDrawer({
                width: rect.width,
                height: rect.height,
                compactDrawing: false,
                experimentalSSSR: true,
                kkThreshold: 0.1,
                fill: false,
                padding: 5.0,
                scale: 1.0,
                bondThickness: 2.0,
                bondLength: 15,
                shortBondLength: 0.85,
                bondSpacing: 0.18 * 15,
                explicitHydrogens: false,
                overlapResolutionIterations: 1
            });

            SmilesDrawer.parse(smiles, (tree) => {
                if (tree) {
                    // Create a detached SVG element for the drawer to populate
                    // Pass null/false for weights/infoOnly to ensure correct argument alignment
                    // SvgDrawer.draw(data, target, themeName, weights, infoOnly, highlight_atoms)
                    const svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    svgElement.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                    svgElement.setAttribute('width', rect.width);
                    svgElement.setAttribute('height', rect.height);

                    // explicit explicit high contrast theme
                    const theme = {
                        root: '#ffffff',
                        bond: '#ffffff',
                        text: '#ffffff',
                        BACKGROUND: '#000000',
                        C: '#ffffff', O: '#ff4d4d', N: '#4d94ff', F: '#00cc00',
                        Cl: '#00cc00', Br: '#a52a2a', I: '#9400d3', S: '#ffd700', P: '#ffa500'
                    };

                    // Draw to SVG first
                    drawer.draw(tree, svgElement, 'dark', null, false);

                    // Then converting to canvas
                    if (drawer.svgWrapper) {
                        drawer.svgWrapper.toCanvas(canvasRef.current, rect.width, rect.height);
                        console.log('[Molecule2DViewer] Rendered via SvgDrawer workaround');
                    } else {
                        console.error('[Molecule2DViewer] svgWrapper not initialized');
                    }
                } else {
                    console.error('[Molecule2DViewer] Parsed tree is null');
                }
            }, (err) => {
                console.error('[Molecule2DViewer] Parse error:', err);
            });
        } catch (e) {
            console.error('[Molecule2DViewer] Initialization error:', e);
        }

    }, [smiles, width, height]);

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
            <canvas
                id={canvasId.current}
                ref={canvasRef}
                width={typeof width === 'number' ? width : 400}
                height={typeof height === 'number' ? height : 180}
                style={{ width: '100%', height: '100%' }}
            />

            <div style={{ position: 'absolute', bottom: '8px', right: '12px', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                LIVE RENDER (SmilesDrawer)
            </div>
        </motion.div>
    );
};

export default Molecule2DViewer;
