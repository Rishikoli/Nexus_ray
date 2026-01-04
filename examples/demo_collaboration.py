"""
Example: Multi-agent collaboration for protein-drug analysis.

Demonstrates:
- Agent registration with capabilities
- Task delegation
- Consensus voting
- Shared context
- Result aggregation
"""

from src.collaboration import (
    AgentRegistry,
    AgentCapability,
    MessageProtocol,
    CollaborationCoordinator,
    ConsensusStrategy
)

def demo_multi_agent_collaboration():
    """Demo multi-agent collaboration"""
    
    print("\n🤝 Multi-Agent Collaboration Demo\n")
    print("="*70)
    
    # 1. Initialize registry and coordinator
    print("\n1️⃣ Initializing Collaboration System")
    registry = AgentRegistry()
    coordinator = CollaborationCoordinator(registry)
    
    # 2. Register agents with different capabilities
    print("\n2️⃣ Registering Agents")
    
    agents = [
        {
            "id": "llm_analyzer_1",
            "name": "LLM Analyzer Alpha",
            "capabilities": [AgentCapability.LLM_ANALYSIS, AgentCapability.DECISION_MAKING]
        },
        {
            "id": "llm_analyzer_2",
            "name": "LLM Analyzer Beta",
            "capabilities": [AgentCapability.LLM_ANALYSIS, AgentCapability.DECISION_MAKING]
        },
        {
            "id": "data_processor",
            "name": "Data Processor",
            "capabilities": [AgentCapability.DATA_PROCESSING]
        },
        {
            "id": "validator",
            "name": "Result Validator",
            "capabilities": [AgentCapability.VALIDATION]
        },
        {
            "id": "coordinator_agent",
            "name": "Task Coordinator",
            "capabilities": [AgentCapability.COORDINATION]
        }
    ]
    
    for agent_data in agents:
        agent = registry.register(
            agent_id=agent_data["id"],
            name=agent_data["name"],
            capabilities=agent_data["capabilities"]
        )
        print(f"   ✓ Registered: {agent.name} [{', '.join(c.value for c in agent.capabilities)}]")
    
    # 3. Create shared context
    print("\n3️⃣ Creating Shared Context")
    context_id = "drug_analysis_context"
    context = coordinator.create_shared_context(context_id)
    
    # Add initial data
    coordinator.update_shared_context(
        context_id=context_id,
        key="protein_sequence",
        value="MENFQKVEKIGEGTYGVVYKARNKLTGEVV",
        agent_id="coordinator_agent"
    )
    coordinator.update_shared_context(
        context_id=context_id,
        key="drug_smiles",
        value="CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)",
        agent_id="coordinator_agent"
    )
    
    print(f"   ✓ Context created: {context_id}")
    print(f"   ✓ Data keys: {list(context.data.keys())}")
    
    # 4. Delegate tasks to agents
    print("\n4️⃣ Delegating Tasks")
    
    # Delegate data processing
    processor_agent = coordinator.delegate_task(
        task_description="Process protein sequence data",
        required_capabilities=[AgentCapability.DATA_PROCESSING],
        task_data={"sequence": context.data["protein_sequence"]},
        from_agent="coordinator_agent"
    )
    
    if processor_agent:
        print(f"   ✓ Data processing delegated to: {processor_agent.name}")
        
        # Simulate processing result
        coordinator.update_shared_context(
            context_id=context_id,
            key="sequence_length",
            value=len(context.data["protein_sequence"]),
            agent_id=processor_agent.agent_id
        )
    
    # Delegate LLM analysis (finds best available LLM agent)
    llm_agent = coordinator.delegate_task(
        task_description="Analyze drug-protein interaction",
        required_capabilities=[AgentCapability.LLM_ANALYSIS],
        task_data={
            "protein": context.data["protein_sequence"],
            "drug": context.data["drug_smiles"]
        },
        from_agent="coordinator_agent"
    )
    
    if llm_agent:
        print(f"   ✓ LLM analysis delegated to: {llm_agent.name}")
    
    # 5. Consensus voting
    print("\n5️⃣ Initiating Consensus Vote")
    
    question = "What is the predicted drugability score?"
    options = ["high", "moderate", "low"]
    
    correlation_id = coordinator.initiate_consensus(
        question=question,
        options=options,
        from_agent="coordinator_agent",
        strategy=ConsensusStrategy.MAJORITY_VOTE
    )
    
    print(f"   ✓ Consensus request initiated: {correlation_id[:8]}...")
    print(f"   ✓ Question: {question}")
    print(f"   ✓ Options: {options}")
    
    # Simulate votes from LLM agents
    coordinator.submit_vote(
        correlation_id=correlation_id,
        agent_id="llm_analyzer_1",
        vote="high",
        reasoning="Strong binding affinity and low toxicity"
    )
    
    coordinator.submit_vote(
        correlation_id=correlation_id,
        agent_id="llm_analyzer_2",
        vote="high",
        reasoning="Excellent ADMET properties"
    )
    
    coordinator.submit_vote(
        correlation_id=correlation_id,
        agent_id="validator",
        vote="moderate",
        reasoning="Need more clinical data"
    )
    
    print(f"   ✓ Collected 3 votes")
    
    # Evaluate consensus
    result = coordinator.evaluate_consensus(correlation_id)
    
    if result:
        print(f"\n   📊 Consensus Result:")
        print(f"      Winning option: {result.winning_option}")
        print(f"      Vote distribution: {result.vote_counts}")
        print(f"      Confidence: {result.confidence:.2%}")
        print(f"      Strategy: {result.strategy.value}")
    
    # 6. Result aggregation
    print("\n6️⃣ Aggregating Results")
    
    agent_results = [
        {"drugability_score": 0.85, "confidence": 0.90, "agent": "llm_analyzer_1"},
        {"drugability_score": 0.88, "confidence": 0.92, "agent": "llm_analyzer_2"},
        {"drugability_score": 0.75, "confidence": 0.80, "agent": "validator"}
    ]
    
    aggregated = coordinator.aggregate_results(agent_results, "average")
    print(f"   ✓ Aggregated drugability score: {aggregated.get('drugability_score', 0):.2f}")
    print(f"   ✓ Aggregated confidence: {aggregated.get('confidence', 0):.2f}")
    
    # 7. Statistics
    print("\n7️⃣ Collaboration Statistics")
    stats = coordinator.get_statistics()
    registry_stats = registry.get_statistics()
    
    print(f"   Registry:")
    print(f"      Total agents: {registry_stats['total_agents']}")
    print(f"      Available: {registry_stats['available_agents']}")
    print(f"      Active tasks: {registry_stats['total_active_tasks']}")
    
    print(f"\n   Coordinator:")
    print(f"      Active contexts: {stats['active_contexts']}")
    print(f"      Active consensus: {stats['active_consensus']}")
    print(f"      Context updates: {stats['total_context_updates']}")
    
    print("\n" + "="*70)
    print("🎉 Multi-Agent Collaboration Demo Complete!")
    print("="*70)
    
    print("\n✅ Demonstrated:")
    print("   • Agent registration with capabilities")
    print("   • Task delegation based on capabilities")
    print("   • Shared context management")
    print("   • Consensus voting (majority)")
    print("   • Result aggregation")
    print("   • Load balancing (automatic)")
    print()


if __name__ == "__main__":
    demo_multi_agent_collaboration()
