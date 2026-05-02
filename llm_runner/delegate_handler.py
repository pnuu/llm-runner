"""Delegate mode handler for autonomous agent-driven task execution"""
from llm_runner.agent_orchestrator import AgentOrchestrator
from llm_runner.agents.plan_agent import PlanAgent
from llm_runner.llm import OllamaClient, check_ollama_connection
from llm_runner.plan_handler import read_agents_context


def handle_delegate_mode(
    request: str,
    config: dict,
    use_context: bool = False,
    workspace_dir: str = "."
) -> str:
    """
    Handle delegate mode - spawn agent to autonomously delegate and execute tasks.
    
    Args:
        request: The complex task to delegate
        config: Configuration dict with model, ollama_url
        use_context: Whether to include AGENTS.md context
        workspace_dir: Workspace directory for agents
        
    Returns:
        Result string with execution summary
    """
    if not check_ollama_connection(config.get("ollama_url")):
        return "Error: Cannot connect to Ollama server"
    
    # Initialize LLM client
    llm_client = OllamaClient(
        url=config.get("ollama_url", "http://localhost:11434")
    )
    
    # Set model on client
    llm_client.model = config.get("model", "mistral:7b")
    
    # Get context if requested
    context = ""
    if use_context:
        context = read_agents_context(".")
    
    # Create initial planning agent
    prompt = f"""You are an autonomous agent orchestrator.
Your task: {request}

{f"Project context: {context}" if context else ""}

First, decompose this task into specific sub-tasks that can be executed by specialized agents.
Format: 
- AgentType: task description

Available agent types: CodeAgent, TestAgent, PlanAgent, ResearchAgent, BuildAgent
"""
    
    plan_agent = PlanAgent(
        task=request,
        llm_client=llm_client,
        workspace_dir=workspace_dir
    )
    
    # Get decomposition from LLM
    decomposition = plan_agent.decompose_task()
    plan_agent.execute()
    
    # Parse sub-tasks
    sub_tasks = plan_agent._parse_decomposition(decomposition)
    
    if not sub_tasks:
        return "No sub-tasks identified. Task may be too simple or unclear."
    
    # Create orchestrator and execute tasks
    orchestrator = AgentOrchestrator()
    
    # Execute sequentially by default (can add parallel logic later)
    result = orchestrator.execute_sequential(sub_tasks, on_error="skip")
    
    # Generate execution tree
    execution_tree = orchestrator.generate_execution_tree()
    
    # Aggregate results
    aggregated = orchestrator.aggregate_results()
    
    # Format output
    output = f"""
Delegation Complete!
====================

Original Request: {request}

Sub-tasks Identified: {len(sub_tasks)}
{chr(10).join(f"  - {s['agent_type']}: {s['task']}" for s in sub_tasks)}

Execution Status: {result['status']}

Execution Tree:
{_format_execution_tree(execution_tree)}

Summary:
- Total agents spawned: {len(execution_tree)}
- Status: {result['status']}
- Tasks completed: {result.get('tasks_completed', 0)}/{len(sub_tasks)}
"""
    
    return output


def _format_execution_tree(tree: dict) -> str:
    """Format execution tree for display"""
    lines = []
    for agent_id, info in tree.items():
        status = info.get("status", "unknown")
        agent_type = info.get("type", "Unknown")
        lines.append(f"  [{status}] {agent_id} ({agent_type})")
    return "\n".join(lines) if lines else "  (no agents executed)"
