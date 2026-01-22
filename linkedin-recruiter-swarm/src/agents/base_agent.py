"""
Base Agent class for all specialized agents in the swarm
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging


class BaseAgent(ABC):
    """
    Base class for all agents in the recruiter swarm.
    Provides common functionality and enforces interface.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        """
        Initialize base agent

        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.logger = self._setup_logger()
        self.state = {
            'status': 'idle',
            'tasks_completed': 0,
            'tasks_failed': 0,
            'created_at': datetime.now(),
            'last_active': None
        }

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this agent"""
        logger = logging.getLogger(f"{self.__class__.__name__}:{self.agent_id}")
        logger.setLevel(logging.INFO)
        return logger

    @abstractmethod
    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task. Must be implemented by subclasses.

        Args:
            task: Task dictionary with type and parameters

        Returns:
            Result dictionary with status and data
        """
        pass

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with error handling and state management

        Args:
            task: Task to execute

        Returns:
            Result dictionary
        """
        self.logger.info(f"Executing task: {task.get('type', 'unknown')}")
        self.state['status'] = 'working'
        self.state['last_active'] = datetime.now()

        try:
            result = self.process(task)
            self.state['tasks_completed'] += 1
            self.state['status'] = 'idle'
            self.logger.info(f"Task completed successfully")
            return {
                'success': True,
                'agent_id': self.agent_id,
                'result': result,
                'completed_at': datetime.now()
            }
        except Exception as e:
            self.state['tasks_failed'] += 1
            self.state['status'] = 'error'
            self.logger.error(f"Task failed: {str(e)}")
            return {
                'success': False,
                'agent_id': self.agent_id,
                'error': str(e),
                'failed_at': datetime.now()
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__,
            'state': self.state.copy(),
            'config': self.config
        }

    def reset(self) -> None:
        """Reset agent state"""
        self.state = {
            'status': 'idle',
            'tasks_completed': 0,
            'tasks_failed': 0,
            'created_at': self.state['created_at'],
            'last_active': None
        }
        self.logger.info("Agent reset")

    def can_handle(self, task: Dict[str, Any]) -> bool:
        """
        Check if this agent can handle a given task

        Args:
            task: Task to check

        Returns:
            True if agent can handle this task
        """
        # Default implementation - subclasses should override
        return True
