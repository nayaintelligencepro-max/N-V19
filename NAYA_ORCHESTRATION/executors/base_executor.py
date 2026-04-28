"""
Base Executor Interface for NAYA

Defines the contract for all executors (CloudRun, VM, Local, Kubernetes, etc)
"""

from abc import ABC
from typing import Dict, Any


class BaseExecutor(ABC):
    """
    Abstract base class for all task executors.

    Implementations should override:
    - execute(): Run a task and return result
    - validate(): Verify executor prerequisites
    - health_check(): Verify executor is ready
    """

    def __init__(self):
        self.name: str = "BaseExecutor"
        self.is_ready: bool = False

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return results.

        Args:
            task: Task specification with type, params, etc

        Returns:
            {
                'status': 'success'|'failed',
                'task_id': str,
                'output': {...},
                'execution_time': float,
                'timestamp': str
            }
        """
        return {
            'status': 'failed',
            'task_id': task.get('task_id', 'unknown'),
            'output': {'error': f'Executor {self.__class__.__name__} must implement execute()'},
            'execution_time': 0.0,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        }

    def validate(self) -> bool:
        """Validate that executor prerequisites are met."""
        return True

    def health_check(self) -> bool:
        """Check if executor is healthy and ready."""
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            'name': self.name,
            'is_ready': self.is_ready,
            'health': self.health_check()
        }


__all__ = ['BaseExecutor']
