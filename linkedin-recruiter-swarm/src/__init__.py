"""
LinkedIn Recruiter Swarm - Multi-Agent Recruiting System
"""

__version__ = "1.0.0"
__author__ = "OSSU Computer Science"

from .linkedin_hunter_interface import LinkedInHunterInterface
from .swarm_coordinator import RecruiterSwarm

__all__ = ['LinkedInHunterInterface', 'RecruiterSwarm']
