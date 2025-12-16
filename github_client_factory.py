"""GitHub Client Factory for creating authenticated GitHub clients using GitHub App authentication."""

import os
import time
from typing import Optional

import jwt
from dotenv import load_dotenv
from github import Auth, Github, GithubIntegration

# Load environment variables from .env file
load_dotenv()


class AppConfiguration:
    """Configuration interface for GitHub App settings."""
    
    def __init__(self, github_app_id: Optional[str] = None, 
                 github_app_name: Optional[str] = None, 
                 github_app_private_key: Optional[str] = None, 
                 github_org: Optional[str] = None):
        """
        Initialize configuration from parameters or environment variables.
        
        Environment variables used (if parameters not provided):
        - GITHUB_APP_ID: The GitHub App ID
        - GITHUB_APP_NAME: The GitHub App name
        - GITHUB_APP_PRIVATE_KEY: The GitHub App private key (RSA format)
        - GITHUB_ORG: The GitHub organization name
        
        Args:
            github_app_id: GitHub App ID (optional, reads from GITHUB_APP_ID env var if not provided)
            github_app_name: GitHub App name (optional, reads from GITHUB_APP_NAME env var if not provided)
            github_app_private_key: GitHub App private key (optional, reads from GITHUB_APP_PRIVATE_KEY env var if not provided)
            github_org: GitHub organization (optional, reads from GITHUB_ORG_NAME env var if not provided)
        
        Raises:
            ValueError: If any required configuration is missing
        """
        self.github_app_id = github_app_id or os.getenv('GITHUB_APP_ID')
        self.github_app_name = github_app_name or os.getenv('GITHUB_APP_NAME')
        self.github_app_private_key = github_app_private_key or os.getenv('GITHUB_APP_PRIVATE_KEY')
        self.github_org = github_org or os.getenv('GITHUB_ORG_NAME')
        
        # Validate required configuration
        missing = []
        if not self.github_app_id:
            missing.append('GITHUB_APP_ID')
        if not self.github_app_name:
            missing.append('GITHUB_APP_NAME')
        if not self.github_app_private_key:
            missing.append('GITHUB_APP_PRIVATE_KEY')
        if not self.github_org:
            missing.append('GITHUB_ORG_NAME')
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please provide as parameters or set environment variables."
            )
    
    @classmethod
    def from_env(cls) -> 'AppConfiguration':
        """
        Create configuration from environment variables only.
        
        Returns:
            AppConfiguration: Configuration instance loaded from environment
        """
        return cls()


class GitHubClientFactory:
    """Factory for creating authenticated GitHub clients using GitHub App authentication."""
    
    def __init__(self, app_configuration: AppConfiguration):
        """
        Initialize the GitHub client factory.
        
        Args:
            app_configuration: Configuration object containing GitHub App credentials
        """
        self._app_configuration = app_configuration
    
    async def get_app_authenticated_client(self) -> Github:
        """
        Get a GitHub client authenticated with an installation access token.
        
        Returns:
            Github: An authenticated GitHub client instance
        """
        installation_token = await self._get_installation_token()
        
        auth = Auth.Token(installation_token)
        return Github(auth=auth)
    
    def get_app_authenticated_client_sync(self) -> Github:
        """
        Get a GitHub client authenticated with an installation access token (synchronous version).
        
        Returns:
            Github: An authenticated GitHub client instance
        """
        installation_token = self._get_installation_token_sync()
        
        auth = Auth.Token(installation_token)
        return Github(auth=auth)
    
    async def _get_installation_token(self) -> str:
        """
        Get an installation access token for the GitHub App.
        
        Returns:
            str: The installation access token
        """
        return self._get_installation_token_sync()
    
    def _get_installation_token_sync(self) -> str:
        """
        Get an installation access token for the GitHub App (synchronous).
        
        Returns:
            str: The installation access token
        """
        github_integration = self._get_github_integration()
        
        # Get all installations for this GitHub App
        installations = github_integration.get_installations()
        
        # Find the installation for the configured organization
        installation = None
        for inst in installations:
            if inst.account.login.lower() == self._app_configuration.github_org.lower():
                installation = inst
                break
        
        if not installation:
            raise ValueError(
                f"No installation found for organization: {self._app_configuration.github_org}"
            )
        
        # Create an installation access token
        access_token = github_integration.get_access_token(installation.id)
        
        return access_token.token
    
    def _get_github_integration(self) -> GithubIntegration:
        """
        Create a GitHub Integration client authenticated with JWT.
        
        Returns:
            GithubIntegration: A GitHub Integration client for App-level operations
        """
        return GithubIntegration(
            integration_id=self._app_configuration.github_app_id,
            private_key=self._app_configuration.github_app_private_key
        )
    
    def _encode_jwt_token(self, expiration_seconds: int = 600) -> str:
        """
        Encode a JWT token for GitHub App authentication.
        
        Args:
            expiration_seconds: Token expiration time in seconds (default: 600)
            
        Returns:
            str: The encoded JWT token
        """
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + expiration_seconds,
            'iss': self._app_configuration.github_app_id
        }
        
        token = jwt.encode(
            payload,
            self._app_configuration.github_app_private_key,
            algorithm='RS256'
        )
        
        return token
        return token
