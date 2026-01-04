"""
Semiconductor Yield Optimization Reference Agent.

Multi-agent workflow for analyzing wafer defects and optimizing fabrication yield.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import random
from loguru import logger


@dataclass
class WaferDefect:
    """Wafer defect data"""
    defect_id: str
    x_coord: float
    y_coord: float
    defect_type: str
    severity: str
    size_um: float


@dataclass
class ProcessData:
    """Process sensor data"""
    temperature: float
    pressure: float
    gas_flow: float
    power: float
    timestamp: str


class DefectAnalyzer:
    """Analyzes wafer defects from images"""
    
    def analyze(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze defect images"""
        wafer_id = inputs.get("wafer_id", "unknown")
        
        # Simulate defect detection (in production: use OpenVINO vision model)
        logger.info(f"Analyzing defects for wafer {wafer_id}")
        
        num_defects = random.randint(5, 25)
        defects = []
        
        defect_types = ["particle", "scratch", "residue", "void", "bridging"]
        severities = ["low", "medium", "high", "critical"]
        
        for i in range(num_defects):
            defects.append({
                "defect_id": f"D-{wafer_id}-{i+1:03d}",
                "x_coord": round(random.uniform(0, 300), 2),
                "y_coord": round(random.uniform(0, 300), 2),
                "defect_type": random.choice(defect_types),
                "severity": random.choice(severities),
                "size_um": round(random.uniform(0.1, 50.0), 2)
            })
        
        # Defectdensity
        wafer_area = 300 * 300  # mm²
        defect_density = (num_defects / wafer_area) * 1000  # defects per cm²
        
        return {
            "wafer_id": wafer_id,
            "total_defects": num_defects,
            "defect_density_per_cm2": round(defect_density, 3),
            "defects": defects,
            "critical_defects": len([d for d in defects if d["severity"] == "critical"])
        }


class DefectClassifier:
    """Classifies defects by type and root cause"""
    
    def classify(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Classify defects"""
        defects = inputs.get("defects", [])
        
        # Group by type
        type_counts = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for defect in defects:
            defect_type = defect["defect_type"]
            severity = defect["severity"]
            
            type_counts[defect_type] = type_counts.get(defect_type, 0) + 1
            severity_counts[severity] += 1
        
        # Identify dominant defect
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "unknown"
        
        # Spatial clustering (simplified)
        clusters = random.randint(2, 5)
        
        return {
            "classification_complete": True,
            "defect_distribution": type_counts,
            "severity_distribution": severity_counts,
            "dominant_defect_type": dominant_type,
            "spatial_clusters": clusters,
            "clustered_defects": round(random.uniform(0.4, 0.8), 2),  # Fraction clustered
            "root_cause_candidates": [
                "contamination" if dominant_type == "particle" else "process_drift",
                "equipment_malfunction" if clusters > 3 else "material_quality"
            ]
        }


class ProcessIntelligence:
    """Analyzes process sensor data"""
    
    def analyze(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze process parameters"""
        wafer_id = inputs.get("wafer_id", "unknown")
        
        # Simulate process data collection
        logger.info(f"Analyzing process data for wafer {wafer_id}")
        
        # Generate mock process data
        process_data = {
            "temperature": {
                "mean": round(random.uniform(380, 420), 1),
                "std": round(random.uniform(2, 8), 2),
                "out_of_spec": random.random() < 0.2
            },
            "pressure": {
                "mean": round(random.uniform(4.5, 5.5), 2),
                "std": round(random.uniform(0.1, 0.3), 2),
                "out_of_spec": random.random() < 0.15
            },
            "gas_flow": {
                "mean": round(random.uniform(95, 105), 1),
                "std": round(random.uniform(1, 5), 2),
                "out_of_spec": random.random() < 0.1
            },
            "power": {
                "mean": round(random.uniform(1800, 2200), 0),
                "std": round(random.uniform(10, 50), 1),
                "out_of_spec": random.random() < 0.25
            }
        }
        
        # Calculate process stability score
        out_of_spec_count = sum(1 for p in process_data.values() if p["out_of_spec"])
        stability_score = round(1.0 - (out_of_spec_count / len(process_data)), 2)
        
        return {
            "process_data": process_data,
            "stability_score": stability_score,
            "out_of_spec_parameters": out_of_spec_count,
            "drift_detected": stability_score < 0.7,
            "recommended_action": "calibrate" if stability_score < 0.7 else "monitor"
        }


class YieldImpactPredictor:
    """Predicts yield impact from defects"""
    
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Predict yield impact"""
        defect_density = inputs.get("defect_density_per_cm2", 0.0)
        critical_defects = inputs.get("critical_defects", 0)
        total_defects = inputs.get("total_defects", 0)
        
        # Simplified yield model
        base_yield = 0.95
        
        # Defect density impact
        density_impact = min(defect_density * 0.02, 0.3)
        
        # Critical defect impact
        critical_impact = critical_defects * 0.015
        
        # Predicted yield
        predicted_yield = max(base_yield - density_impact - critical_impact, 0.1)
        
        # Yield loss
        yield_loss = round((base_yield - predicted_yield) * 100, 2)
        
        # Calculate financial impact (simplified)
        wafers_per_lot = 25
        dies_per_wafer = 500
        value_per_die = 150  # USD
        
        dies_lost = int(dies_per_wafer * (base_yield - predicted_yield) * wafers_per_lot)
        financial_impact = dies_lost * value_per_die
        
        return {
            "predicted_yield": round(predicted_yield, 4),
            "yield_loss_percent": yield_loss,
            "baseline_yield": base_yield,
            "impact_severity": "critical" if yield_loss > 10 else "high" if yield_loss > 5 else "moderate",
            "estimated_dies_lost": dies_lost,
            "financial_impact_usd": financial_impact
        }


class RootCauseAnalyzer:
    """LLM-powered root cause analysis"""
    
    def __init__(self):
        """Initialize with LLM"""
        from src.llm import PromptBuilder, ResponseParser
        self.llm = None
        self.prompt_builder = PromptBuilder()
        self.parser = ResponseParser()
    
    def _get_llm(self):
        """Lazy load LLM"""
        if self.llm is None:
            try:
                from src.llm import get_llm
                self.llm = get_llm()
            except Exception as e:
                logger.warning(f"LLM not available: {e}. Using fallback logic.")
        return self.llm
    
    def analyze(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis with LLM"""
        dominant_defect = inputs.get("dominant_defect_type", "unknown")
        process_stability = inputs.get("stability_score", 1.0)
        clusters = inputs.get("spatial_clusters", 0)
        drift_detected = inputs.get("drift_detected", False)
        defect_distribution = inputs.get("defect_distribution", {})
        
        # Build LLM prompt
        prompt_text = f"""Analyze the root cause of semiconductor wafer defects based on the following data:
           

Defect Pattern:
- Dominant defect type: {dominant_defect}
- Distribution: {defect_distribution}
- Spatial clusters: {clusters}

Process Metrics:
- Stability score: {process_stability} (0-1 scale)
- Drift detected: {drift_detected}

Provide:
1. Top 3 most likely root causes with confidence scores (0-1)
2. Primary root cause
3. Detailed technical reasoning
4. Correlation factors

Format as JSON with keys: root_causes (list of {{cause, confidence}}), primary_cause, reasoning"""
        
        # Get LLM analysis
        llm = self._get_llm()
        if llm:
            try:
                response = llm.generate(prompt_text, max_tokens=400, temperature=0.2)
                
                # Try to parse  JSON from response
                try:
                    analysis = self.parser.extract_json(response, strict=False)
                    ranked_causes = [(c["cause"], c["confidence"]) for c in analysis.get("root_causes", [])]
                    primary_cause = analysis.get("primary_cause", ranked_causes[0][0] if ranked_causes else "unknown")
                    reasoning = analysis.get("reasoning", response)
                except:
                    # Fallback parsing
                    primary_cause, ranked_causes, reasoning = self._parse_llm_response(response, dominant_defect)
                
                logger.info(f"LLM root cause analysis: {primary_cause}")
                
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}. Using fallback.")
                primary_cause, ranked_causes, reasoning = self._fallback_analysis(
                    dominant_defect, process_stability, clusters, drift_detected
                )
        else:
            primary_cause, ranked_causes, reasoning = self._fallback_analysis(
                dominant_defect, process_stability, clusters, drift_detected
            )
        
        return {
            "root_causes": ranked_causes,
            "primary_cause": primary_cause,
            "confidence": ranked_causes[0][1] if ranked_causes else 0,
            "reasoning": reasoning,
            "llm_powered": llm is not None,
            "correlation_factors": {
                "defect_type": dominant_defect,
                "process_stability": process_stability,
                "clustering": clusters
            }
        }
    
    def _fallback_analysis(self, dominant_defect, process_stability, clusters, drift_detected):
        """Fallback when LLM unavailable"""
        root_causes = []
        confidence_scores = {}
        
        if dominant_defect == "particle":
            confidence_scores["contamination"] = 0.85
            confidence_scores["inadequate_cleaning"] = 0.65
        elif dominant_defect == "scratch":
            confidence_scores["wafer_handling"] = 0.80
        else:
            confidence_scores["process_drift"] = 0.70
        
        if process_stability < 0.7 and "process_drift" not in confidence_scores:
            confidence_scores["process_drift"] = 0.75
        
        if clusters > 3:
            confidence_scores["equipment_malfunction"] = 0.60
        
        ranked_causes = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
        primary_cause = ranked_causes[0][0] if ranked_causes else "unknown"
        
        reasoning = f"Root cause analysis indicates {primary_cause} based on {dominant_defect} defects and process stability of {process_stability}."
        
        return primary_cause, ranked_causes, reasoning
    
    def _parse_llm_response(self, response, dominant_defect):
        """Parse LLM response when JSON parsing fails"""
        # Simple keyword extraction
        causes = ["contamination", "process_drift", "equipment_malfunction", "wafer_handling"]
        found_causes = [(cause, 0.7) for cause in causes if cause in response.lower()]
        
        if not found_causes:
            found_causes = [("unknown", 0.5)]
        
        return found_causes[0][0], found_causes, response[:200]


class YieldAggregator:
    """LLM-powered yield analysis aggregation"""
    
    def aggregate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate and synthesize yield analysis"""
        yield_loss = inputs.get("yield_loss_percent", 0)
        financial_impact = inputs.get("financial_impact_usd", 0)
        primary_cause = inputs.get("primary_cause", "unknown")
        
        # Priority level
        if yield_loss > 10 or financial_impact > 50000:
            priority = "P0_CRITICAL"
        elif yield_loss > 5 or financial_impact > 20000:
            priority = "P1_HIGH"
        else:
            priority = "P2_MEDIUM"
        
        # Synthesis
        summary = f"""
Yield Optimization Analysis Summary:
- Yield Loss: {yield_loss}%
- Financial Impact: ${financial_impact:,}
- Root Cause: {primary_cause}
- Priority: {priority}

Immediate attention required to prevent further yield degradation.
"""
        
        return {
            "priority": priority,
            "summary": summary.strip(),
            "yield_metrics": {
                "loss_percent": yield_loss,
                "financial_impact": financial_impact
            },
            "actionable": True
        }


class RecipeOptimizer:
    """LLM-powered recipe optimization"""
    
    def optimize(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend recipe optimizations"""
        primary_cause = inputs.get("primary_cause", "unknown")
        process_data = inputs.get("process_data", {})
        
        # Generate optimizations based on root cause
        optimizations = []
        
        if primary_cause == "contamination":
            optimizations.extend([
                {"parameter": "clean_cycle_time", "current": 120, "recommended": 180, "unit": "seconds"},
                {"parameter": "chamber_purge_cycles", "current": 3, "recommended": 5, "unit": "cycles"}
            ])
        
        if primary_cause == "process_drift":
            optimizations.extend([
                {"parameter": "temperature_setpoint", "current": 400, "recommended": 395, "unit": "C"},
                {"parameter": "pressure_tolerance", "current": 0.5, "recommended": 0.3, "unit": "Torr"}
            ])
        
        # Generic optimizations
        for param, data in process_data.items():
            if data.get("out_of_spec"):
                optimizations.append({
                    "parameter": param,
                    "current": data["mean"],
                    "recommended": data["mean"] * 0.95,  # Adjust by 5%
                    "unit": "varied"
                })
        
        # Trade-off analysis
        trade_offs = {
            "throughput_impact": "-5%" if len(optimizations) > 3 else "-2%",
            "cost_impact": "+$500/lot" if len(optimizations) > 3 else "+$200/lot",
            "yield_improvement": f"+{random.randint(3, 8)}%"
        }
        
        return {
            "optimizations": optimizations[:5],  # Top 5
            "total_parameters": len(optimizations),
            "trade_off_analysis": trade_offs,
            "estimated_roi": "positive",
            "implementation_risk": "low" if len(optimizations) <= 3 else "medium"
        }


import asyncio
from concurrent.futures import ThreadPoolExecutor

# Create a thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

async def run_semiconductor_yield_optimization_async(wafer_id: str, workflow_id: str = None, on_update = None) -> Dict[str, Any]:
    """
    Run complete semiconductor yield optimization workflow (ASYNC PARALLEL).
    """
    logger.info(f"⚡ Starting ASYNC Semiconductor Workflow for {wafer_id}")

    # Helper to send updates safely
    async def send_update(agent, message, type="info"):
        if on_update:
            try:
                await on_update({
                    "agent": agent,
                    "message": message,
                    "type": type,
                    "workflow_id": workflow_id
                })
            except Exception as e:
                logger.warning(f"Failed to send update: {e}")
    
    data = {"wafer_id": wafer_id}
    loop = asyncio.get_event_loop()
    
    # --- PHASE 1: Parallel Data Collection ---
    await send_update("DefectAnalyzer", f"Analyzing defects for wafer {wafer_id}...", "info")
    await send_update("ProcessIntelligence", "Collecting sensor data (Temp, Pressure, RF)...", "info")

    # Run Defect Analysis and Process Intelligence concurrently
    # These are independent CPU-bound tasks, so we run them in thread pool
    
    async def run_defect_analysis():
        analyzer = DefectAnalyzer()
        res = await loop.run_in_executor(executor, analyzer.analyze, data)
        await send_update("DefectAnalyzer", f"Analysis complete: {res['total_defects']} defects found", "success")
        return res

    async def run_process_analysis():
        intel = ProcessIntelligence()
        res = await loop.run_in_executor(executor, intel.analyze, data)
        status = "Stable" if res['stability_score'] > 0.7 else "Unstable"
        await send_update("ProcessIntelligence", f"Process Analysis: {status} (Score: {res['stability_score']})", "success")
        return res

    # Launch parallel tasks
    results = await asyncio.gather(run_defect_analysis(), run_process_analysis())
    
    # Merge results
    data.update(results[0]) # Defect data
    data.update(results[1]) # Process data
    
    # --- PHASE 2: Parallel Classification & Prediction ---
    # Now that we have defect data, we can run Classifier and Yield Predictor concurrently
    
    async def run_classifier():
        await send_update("DefectClassifier", "Classifying defect types and clusters...", "info")
        classifier = DefectClassifier()
        res = await loop.run_in_executor(executor, classifier.classify, data)
        await send_update("DefectClassifier", f"Dominant type: {res['dominant_defect_type']}", "success")
        return res
        
    async def run_yield_predictor():
        await send_update("YieldImpactPredictor", "Predicting financial & yield impact...", "info")
        predictor = YieldImpactPredictor()
        res = await loop.run_in_executor(executor, predictor.predict, data)
        await send_update("YieldImpactPredictor", f"Predicted Loss: {res['yield_loss_percent']}% (${res['financial_impact_usd']:,})", "success")
        return res

    results_p2 = await asyncio.gather(run_classifier(), run_yield_predictor())
    
    data.update(results_p2[0]) # Classification
    data.update(results_p2[1]) # Yield prediction
    
    # --- PROCESS CONTROL GATE --- 
    # Intermediate check for significant yield excursions (> 3.0% loss)
    # Requires human verification of defect classification before proceeding to RCA.
    if workflow_id and data.get("yield_loss_percent", 0) > 3.0:
        loss = data['yield_loss_percent']
        await send_update("ProcessGate", f"🛑 Yield Excursion: {loss}% loss. Requesting verification.", "warning")

        from src.api.routes.hitl import hitl_store
        import uuid
        import time
        
        req_id = str(uuid.uuid4())
        logger.info(f"🛑 Yield Gate Active: Significant Loss Detected ({loss}%)")
        
        hitl_store[req_id] = {
            "request_id": req_id,
            "workflow_id": workflow_id,
            "task_id": "process-verification",
            "description": f"Yield Excursion Warning: {loss}% loss. Verify defect classification?",
            "severity": "medium",
            "context": {
                "yield_loss": loss,
                "defects": data.get("total_defects"),
                "dominant_type": data.get("dominant_defect_type")
            },
            "status": "pending",
            "created_at": time.time(),
            "decision": None
        }
        
        # Wait for decision
        while hitl_store[req_id]["status"] == "pending":
            await asyncio.sleep(1)
            
        decision = hitl_store[req_id]["decision"]
        if decision["action"] == "reject":
            await send_update("ProcessGate", "Optimization rejected by operator", "error")
            return {"error": "Process Gate Rejection: Optimization stopped", "details": data}
            
        logger.info("✅ Yield Gate passed. Proceeding to RCA.")
        await send_update("ProcessGate", "Classification verified. Proceeding to RCA.", "success")
    
    # --- PHASE 3: Sequential & LLM (Convergence) ---
    
    # Root Cause Analysis (Needs all previous data)
    await send_update("RootCauseAnalyzer", "Running AI Root Cause Analysis...", "info")
    rca_analyzer = RootCauseAnalyzer()
    # LLM might be IO bound (network/generation), allow async if native support exists, 
    # but here we wrap in executor to be safe/consistent
    rca = await loop.run_in_executor(executor, rca_analyzer.analyze, data)
    data.update(rca)
    await send_update("RootCauseAnalyzer", f"Root Cause Identified: {rca['primary_cause']}", "success")
    
    # Aggregation
    aggregator = YieldAggregator()
    aggregation = aggregator.aggregate(data)
    data.update(aggregation)
    
    # Optimization
    await send_update("RecipeOptimizer", "Generating process optimizations...", "info")
    optimizer = RecipeOptimizer()
    recommendations = optimizer.optimize(data)
    await send_update("RecipeOptimizer", f"Generated {len(recommendations['optimizations'])} recipe adjustments", "success")
    
    return {
        "success": True,
        "wafer_id": wafer_id,
        "defects": {
            "total": data.get("total_defects", 0),
            "critical": data.get("critical_defects", 0),
            "dominant_type": data.get("dominant_defect_type", "unknown")
        },
        "yield_impact": data.get("impact_severity", "unknown"),
        "root_cause": rca.get("primary_cause", "unknown"),
        "priority": aggregation.get("priority", "P2_MEDIUM"),
        "optimizations": recommendations
    }

# Legacy Sync Wrapper
def run_semiconductor_yield_optimization(wafer_id: str) -> Dict[str, Any]:
    return asyncio.run(run_semiconductor_yield_optimization_async(wafer_id))
