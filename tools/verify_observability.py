#!/usr/bin/env python3
"""
Quick verification test for observability components.
"""

import sys
sys.path.insert(0, '/home/aditya/Nexus-ray1')

from src.observability.metrics import get_metrics_collector, WorkflowMetrics
from src.observability.llm_insights import (
    get_llm_tracker,
    LLMCall,
    TokenUsage,
    LLMProvider
)
from src.observability.activity_feed import get_activity_feed, ActivityType
from datetime import datetime
import uuid

def test_metrics():
    """Test metrics collection"""
    print("1️⃣  Testing Metrics Collection...")
    
    collector = get_metrics_collector()
    
    # Test counter
    collector.inc_counter("workflows_started_total")
    collector.inc_counter("workflows_started_total")
    
    # Test gauge
    collector.set_gauge("hitl_pending", 3)
    
    # Test histogram
    collector.observe_histogram("task_duration_seconds", 1.5)
    collector.observe_histogram("task_duration_seconds", 2.3)
    
    # Get summary
    summary = collector.get_summary()
    print(f"   ✓ Total metrics: {summary['total_metrics']}")
    print(f"   ✓ Workflows started: {summary['metrics'].get('workflows_started_total', {}).get('value', 0)}")
    
    # Test Prometheus export
    prom_output = collector.export_prometheus()
    print(f"   ✓ Prometheus export: {len(prom_output)} characters")
    
    print("   ✅ Metrics collection working!")
    return True

def test_llm_insights():
    """Test LLM insights tracking"""
    print("\n2️⃣  Testing LLM Insights...")
    
    tracker = get_llm_tracker()
    
    # Create test LLM call
    call = LLMCall(
        call_id=str(uuid.uuid4()),
        workflow_id="test-wf-1",
        task_id="test-task-1",
        model="mistral-7b-ov",
        provider=LLMProvider.OPENVINO,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        prompt="Test prompt",
        response="Test response",
        tokens=TokenUsage(input_tokens=50, output_tokens=100)
    )
    call.calculate_duration()
    
    # Track it
    tracker.track_call(call)
    
    # Get analytics
    analytics = tracker.get_global_analytics()
    print(f"   ✓ Total calls: {analytics['total_calls']}")
    print(f"   ✓ Total tokens: {analytics['total_tokens']}")
    print(f"   ✓ Estimated cost: ${analytics['estimated_cost_usd']}")
    
    # Workflow analytics
    workflow_analytics = tracker.get_workflow_analytics("test-wf-1")
    print(f"   ✓ Workflow calls: {workflow_analytics['total_calls']}")
    
    print("   ✅ LLM insights tracking working!")
    return True

def test_activity_feed():
    """Test activity feed"""
    print("\n3️⃣  Testing Activity Feed...")
    
    feed = get_activity_feed()
    
    # Add activities
    feed.add_activity(
        activity_type=ActivityType.WORKFLOW_STARTED,
        title="Test workflow started",
        description="Testing activity feed",
        workflow_id="test-wf-1"
    )
    
    feed.add_activity(
        activity_type=ActivityType.TASK_COMPLETED,
        title="Test task completed",
        workflow_id="test-wf-1",
        task_id="task-1",
        severity="info"
    )
    
    feed.add_activity(
        activity_type=ActivityType.TASK_FAILED,
        title="Test task failed",
        description="Simulated error",
        workflow_id="test-wf-1",
        task_id="task-2",
        severity="error"
    )
    
    # Get activities
    recent = feed.get_recent(10)
    print(f"   ✓ Recent activities: {len(recent)}")
    
    workflow_activities = feed.get_for_workflow("test-wf-1")
    print(f"   ✓ Workflow activities: {len(workflow_activities)}")
    
    errors = feed.get_errors(10)
    print(f"   ✓ Error activities: {len(errors)}")
    
    # Test export
    exported = feed.export(limit=5)
    print(f"   ✓ Exported {len(exported)} activities")
    
    print("   ✅ Activity feed working!")
    return True

def test_workflow_helpers():
    """Test workflow helper classes"""
    print("\n4️⃣  Testing Workflow Helpers...")
    
    # WorkflowMetrics
    wf_metrics = WorkflowMetrics("helper-test-wf")
    wf_metrics.workflow_started()
    wf_metrics.task_executed("task-1", 1000, "success")
    wf_metrics.llm_call("mistral-7b-ov", 50, 100, 500)
    wf_metrics.workflow_completed()
    
    print("   ✓ WorkflowMetrics helper working")
    
    # WorkflowActivityTracker
    from src.observability.activity_feed import WorkflowActivityTracker
    
    wf_activity = WorkflowActivityTracker("helper-test-wf")
    wf_activity.workflow_started("Test Workflow", 3)
    wf_activity.task_started("task-1", "Test Task")
    wf_activity.task_completed("task-1", "Test Task", 1000)
    
    print("   ✓ WorkflowActivityTracker helper working")
    print("   ✅ Workflow helpers working!")
    return True

def main():
    """Run all tests"""
    print("🧪 Observability Components Verification")
    print("=" * 50)
    
    try:
        results = [
            test_metrics(),
            test_llm_insights(),
            test_activity_feed(),
            test_workflow_helpers()
        ]
        
        if all(results):
            print("\n" + "=" * 50)
            print("✅ ALL TESTS PASSED!")
            print("=" * 50)
            print("\n📊 Components verified:")
            print("   • Metrics Collection (Prometheus)")
            print("   • LLM Insights & Analytics")
            print("   • Activity Feed System")
            print("   • Workflow Helper Classes")
            print("\n🚀 Ready to proceed to next phase!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
