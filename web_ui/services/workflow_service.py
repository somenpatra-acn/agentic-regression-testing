"""
Workflow Service - Business logic for monitoring workflow state

This service handles:
- Retrieving current workflow status
- Getting stage details
- Workflow history
- Progress tracking
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.helpers import load_json
from utils.logger import get_logger

logger = get_logger(__name__)

# Workflow state file (in-memory for now, could be persisted)
WORKFLOW_STATE: Dict[str, Any] = {
    'status': 'idle',
    'current_stage': None,
    'completed_stages': [],
    'start_time': None,
    'elapsed_time': 0,
    'app_name': None,
    'feature_description': None,
    'stages': {
        'discovery': {
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'elements_found': 0,
            'pages_found': 0,
            'error': None
        },
        'planning': {
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'test_cases_created': 0,
            'error': None
        },
        'generation': {
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'scripts_generated': 0,
            'scripts_validated': 0,
            'error': None
        },
        'execution': {
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'pass_rate': 0,
            'error': None
        },
        'reporting': {
            'status': 'pending',
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'reports_generated': 0,
            'report_formats': [],
            'error': None
        }
    }
}


class WorkflowService:
    """Service for managing workflow monitoring"""

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """
        Get current workflow status

        Returns:
            Workflow status dictionary
        """
        status = WORKFLOW_STATE.copy()

        # Calculate elapsed time if workflow is running
        if status['status'] == 'in_progress' and status['start_time']:
            start = datetime.fromisoformat(status['start_time'])
            status['elapsed_time'] = (datetime.now() - start).total_seconds()

        return status

    @staticmethod
    def update_status(updates: Dict[str, Any]) -> None:
        """
        Update workflow status

        Args:
            updates: Dictionary of updates to apply
        """
        global WORKFLOW_STATE

        # Update top-level fields
        for key, value in updates.items():
            if key == 'stages':
                # Merge stage updates
                for stage_name, stage_data in value.items():
                    if stage_name in WORKFLOW_STATE['stages']:
                        WORKFLOW_STATE['stages'][stage_name].update(stage_data)
            else:
                WORKFLOW_STATE[key] = value

        logger.debug(f"Workflow status updated: {updates}")

    @staticmethod
    def start_workflow(app_name: str, feature_description: str) -> None:
        """
        Mark workflow as started

        Args:
            app_name: Application name
            feature_description: Feature being tested
        """
        global WORKFLOW_STATE

        WORKFLOW_STATE.update({
            'status': 'in_progress',
            'current_stage': 'discovery',
            'completed_stages': [],
            'start_time': datetime.now().isoformat(),
            'elapsed_time': 0,
            'app_name': app_name,
            'feature_description': feature_description
        })

        # Reset all stages to pending
        for stage in WORKFLOW_STATE['stages'].values():
            stage['status'] = 'pending'
            stage['start_time'] = None
            stage['end_time'] = None
            stage['duration'] = 0
            stage['error'] = None

        logger.info(f"Workflow started for {app_name}: {feature_description}")

    @staticmethod
    def start_stage(stage_name: str) -> None:
        """
        Mark a stage as started

        Args:
            stage_name: Name of the stage
        """
        if stage_name in WORKFLOW_STATE['stages']:
            WORKFLOW_STATE['current_stage'] = stage_name
            WORKFLOW_STATE['stages'][stage_name].update({
                'status': 'in_progress',
                'start_time': datetime.now().isoformat()
            })

            logger.info(f"Stage started: {stage_name}")

    @staticmethod
    def complete_stage(stage_name: str, results: Dict[str, Any]) -> None:
        """
        Mark a stage as completed

        Args:
            stage_name: Name of the stage
            results: Stage results to store
        """
        if stage_name in WORKFLOW_STATE['stages']:
            end_time = datetime.now()
            stage = WORKFLOW_STATE['stages'][stage_name]

            # Calculate duration
            if stage['start_time']:
                start = datetime.fromisoformat(stage['start_time'])
                duration = (end_time - start).total_seconds()
            else:
                duration = 0

            # Update stage
            stage.update({
                'status': 'completed',
                'end_time': end_time.isoformat(),
                'duration': duration
            })

            # Update stage-specific results
            stage.update(results)

            # Add to completed stages
            if stage_name not in WORKFLOW_STATE['completed_stages']:
                WORKFLOW_STATE['completed_stages'].append(stage_name)

            logger.info(f"Stage completed: {stage_name} (duration: {duration:.2f}s)")

    @staticmethod
    def fail_stage(stage_name: str, error: str) -> None:
        """
        Mark a stage as failed

        Args:
            stage_name: Name of the stage
            error: Error message
        """
        if stage_name in WORKFLOW_STATE['stages']:
            end_time = datetime.now()
            stage = WORKFLOW_STATE['stages'][stage_name]

            # Calculate duration
            if stage['start_time']:
                start = datetime.fromisoformat(stage['start_time'])
                duration = (end_time - start).total_seconds()
            else:
                duration = 0

            # Update stage
            stage.update({
                'status': 'failed',
                'end_time': end_time.isoformat(),
                'duration': duration,
                'error': error
            })

            # Update workflow status
            WORKFLOW_STATE['status'] = 'failed'

            logger.error(f"Stage failed: {stage_name} - {error}")

    @staticmethod
    def complete_workflow() -> None:
        """Mark workflow as completed"""
        WORKFLOW_STATE['status'] = 'completed'

        # Calculate total duration
        if WORKFLOW_STATE['start_time']:
            start = datetime.fromisoformat(WORKFLOW_STATE['start_time'])
            WORKFLOW_STATE['elapsed_time'] = (datetime.now() - start).total_seconds()

        logger.info(f"Workflow completed (duration: {WORKFLOW_STATE['elapsed_time']:.2f}s)")

    @staticmethod
    def reset_workflow() -> None:
        """Reset workflow to initial state"""
        global WORKFLOW_STATE

        WORKFLOW_STATE['status'] = 'idle'
        WORKFLOW_STATE['current_stage'] = None
        WORKFLOW_STATE['completed_stages'] = []
        WORKFLOW_STATE['start_time'] = None
        WORKFLOW_STATE['elapsed_time'] = 0
        WORKFLOW_STATE['app_name'] = None
        WORKFLOW_STATE['feature_description'] = None

        # Reset all stages
        for stage in WORKFLOW_STATE['stages'].values():
            stage['status'] = 'pending'
            stage['start_time'] = None
            stage['end_time'] = None
            stage['duration'] = 0
            stage['error'] = None

        logger.info("Workflow reset")

    @staticmethod
    def get_stage_details(stage_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific stage

        Args:
            stage_name: Name of the stage

        Returns:
            Stage details or None if not found
        """
        return WORKFLOW_STATE['stages'].get(stage_name)

    @staticmethod
    def get_all_stages() -> Dict[str, Any]:
        """
        Get details for all stages

        Returns:
            Dictionary of all stage details
        """
        return WORKFLOW_STATE['stages'].copy()
