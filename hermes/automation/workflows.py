"""
HERMES Automated Workflows and Bulk Operations
Legal process automation with intelligent workflow orchestration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class WorkflowPriority(Enum):
    """Workflow execution priority"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    retry_count: int = 3
    timeout_seconds: int = 300

@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: str

@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    priority: WorkflowPriority
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    current_step: Optional[str]
    context: Dict[str, Any]
    results: Dict[str, Any]
    error_log: List[str]
    tenant_id: str

class WorkflowEngine:
    """Automated workflow execution engine"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        
        # Built-in workflow definitions
        self.register_builtin_workflows()
        
        # Action registry for workflow steps
        self.action_registry = {
            "clio_sync": self.action_clio_sync,
            "analytics_report": self.action_generate_analytics_report,
            "client_intake": self.action_client_intake_process,
            "data_backup": self.action_backup_data,
        }
    
    def register_builtin_workflows(self):
        """Register built-in legal workflow templates"""
        
        # Daily Clio Synchronization Workflow
        clio_sync_workflow = WorkflowDefinition(
            workflow_id="daily_clio_sync",
            name="Daily Clio Synchronization",
            description="Automated daily synchronization with Clio CRM",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="backup_before_sync",
                    name="Backup Data Before Sync",
                    description="Create backup before Clio sync",
                    action_type="data_backup",
                    parameters={"backup_type": "pre_sync", "retention_days": 7}
                ),
                WorkflowStep(
                    step_id="sync_contacts",
                    name="Sync Contacts",
                    description="Synchronize contacts from Clio",
                    action_type="clio_sync",
                    parameters={"sync_type": "contacts", "batch_size": 100}
                ),
                WorkflowStep(
                    step_id="generate_sync_report",
                    name="Generate Sync Report",
                    description="Generate synchronization analytics report",
                    action_type="analytics_report",
                    parameters={"report_type": "sync_summary"}
                )
            ],
            metadata={"category": "data_sync", "criticality": "high"},
            created_at=datetime.utcnow(),
            created_by="system"
        )
        
        self.workflows[clio_sync_workflow.workflow_id] = clio_sync_workflow
        logger.info(f"Registered {len(self.workflows)} built-in workflows")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        tenant_id: str = "default"
    ) -> str:
        """Execute a workflow and return execution ID"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            priority=priority,
            started_at=None,
            completed_at=None,
            current_step=None,
            context=context or {},
            results={},
            error_log=[],
            tenant_id=tenant_id
        )
        
        self.executions[execution_id] = execution
        
        # Start workflow execution
        task = asyncio.create_task(self._run_workflow_execution(execution_id))
        self.running_workflows[execution_id] = task
        
        logger.info(f"Started workflow execution {execution_id} for workflow {workflow_id}")
        return execution_id
    
    async def _run_workflow_execution(self, execution_id: str) -> None:
        """Run workflow execution"""
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            logger.info(f"Executing workflow {workflow.name} (ID: {execution_id})")
            
            # Execute each step in sequence
            for step in workflow.steps:
                execution.current_step = step.step_id
                
                try:
                    logger.info(f"Executing step: {step.name}")
                    step_result = await self._execute_step_with_retry(step, execution)
                    execution.results[step.step_id] = step_result
                except Exception as e:
                    error_msg = f"Step {step.step_id} failed: {str(e)}"
                    execution.error_log.append(error_msg)
                    logger.error(error_msg)
                    raise
            
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            logger.info(f"Workflow {workflow.name} completed successfully")
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            error_msg = f"Workflow execution failed: {str(e)}"
            execution.error_log.append(error_msg)
            logger.error(error_msg)
        
        finally:
            if execution_id in self.running_workflows:
                del self.running_workflows[execution_id]
    
    async def _execute_step_with_retry(self, step: WorkflowStep, execution: WorkflowExecution) -> Any:
        """Execute workflow step with retry logic"""
        last_exception = None
        
        for attempt in range(step.retry_count + 1):
            try:
                if step.action_type not in self.action_registry:
                    raise ValueError(f"Unknown action type: {step.action_type}")
                
                action_func = self.action_registry[step.action_type]
                result = await asyncio.wait_for(
                    action_func(step.parameters, execution.context),
                    timeout=step.timeout_seconds
                )
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < step.retry_count:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    # Workflow Action Implementations
    
    async def action_clio_sync(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Clio synchronization action"""
        sync_type = parameters.get("sync_type", "all")
        return {"status": "completed", "records_synced": 100, "sync_type": sync_type}
    
    async def action_generate_analytics_report(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analytics report action"""
        report_type = parameters.get("report_type", "general")
        return {"status": "completed", "report_generated": True, "report_type": report_type}
    
    async def action_client_intake_process(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Client intake processing action"""
        stage = parameters.get("stage", "initial_contact")
        return {"status": "completed", "stage": stage, "client_id": f"client_{int(time.time())}"}
    
    async def action_backup_data(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Data backup action"""
        return {"status": "completed", "backup_created": True}
    
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        if execution_id not in self.executions:
            return None
        
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        
        return {
            "execution_id": execution_id,
            "workflow_name": workflow.name,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "progress": len(execution.results) / len(workflow.steps) if workflow.steps else 0,
            "error_log": execution.error_log
        }
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows"""
        return [
            {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "steps_count": len(workflow.steps),
                "category": workflow.metadata.get("category", "general")
            }
            for workflow in self.workflows.values()
        ]

# Global workflow engine instance
workflow_engine: Optional[WorkflowEngine] = None

def get_workflow_engine() -> WorkflowEngine:
    """Get global workflow engine instance"""
    global workflow_engine
    if workflow_engine is None:
        workflow_engine = WorkflowEngine()
    return workflow_engine