"""
Config Routes - API endpoints for configuration management
"""

from flask import Blueprint, jsonify, request
from pathlib import Path

from models.app_profile import ApplicationProfile
from config.settings import get_settings
from utils.helpers import load_yaml
from utils.logger import get_logger

logger = get_logger(__name__)

config_bp = Blueprint('config', __name__)
settings = get_settings()


@config_bp.route('/profiles', methods=['GET'])
def get_profiles():
    """Get all application profiles"""
    try:
        profiles_path = Path("config/app_profiles.yaml")

        if not profiles_path.exists():
            return jsonify({
                'success': True,
                'profiles': []
            })

        profiles_data = load_yaml(str(profiles_path))
        applications = profiles_data.get('applications', {})

        profiles_list = []
        for app_name, app_config in applications.items():
            profiles_list.append({
                'name': app_name,
                'app_type': app_config.get('app_type', 'N/A'),
                'adapter': app_config.get('adapter', 'N/A'),
                'base_url': app_config.get('base_url', 'N/A'),
                'test_framework': app_config.get('test_framework', 'N/A'),
                'description': app_config.get('description', 'N/A')
            })

        return jsonify({
            'success': True,
            'count': len(profiles_list),
            'profiles': profiles_list
        })

    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/profiles/<profile_name>', methods=['GET'])
def get_profile(profile_name):
    """Get a specific application profile"""
    try:
        profiles_path = Path("config/app_profiles.yaml")

        if not profiles_path.exists():
            return jsonify({'error': 'Profiles file not found'}), 404

        profiles_data = load_yaml(str(profiles_path))
        applications = profiles_data.get('applications', {})

        if profile_name not in applications:
            return jsonify({'error': 'Profile not found'}), 404

        return jsonify({
            'success': True,
            'profile': applications[profile_name]
        })

    except Exception as e:
        logger.error(f"Error getting profile {profile_name}: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/settings', methods=['GET'])
def get_settings_info():
    """Get current framework settings (non-sensitive)"""
    try:
        return jsonify({
            'success': True,
            'settings': {
                'llm_provider': settings.llm_provider,
                'llm_model': settings.llm_model,
                'vector_store': settings.vector_store,
                'hitl_mode': settings.hitl_mode,
                'approval_timeout': settings.approval_timeout,
                'test_framework': settings.test_framework,
                'parallel_execution': settings.parallel_execution,
                'max_workers': settings.max_workers,
                'headless_mode': settings.headless_mode,
                'enable_web_interface': settings.enable_web_interface
            }
        })

    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': str(e)}), 500
