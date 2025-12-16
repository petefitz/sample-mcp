"""GitHub Service class for performing common GitHub operations using GitHubClientFactory."""

from typing import List, Optional

from github import Github, InputGitTreeElement, Issue, PullRequest, Repository

from github_client_factory import GitHubClientFactory


class GitHubService:
    """Service class for interacting with GitHub API using GitHubClientFactory."""
    
    def __init__(self, client_factory: GitHubClientFactory):
        """
        Initialize the GitHub service with a client factory.
        
        Args:
            client_factory: GitHubClientFactory instance for creating authenticated clients
        """
        self._client_factory = client_factory
        self._client: Optional[Github] = None
    
    def _get_client(self) -> Github:
        """
        Get or create an authenticated GitHub client.
        
        Returns:
            Github: Authenticated GitHub client instance
        """
        if self._client is None:
            self._client = self._client_factory.get_app_authenticated_client_sync()
        return self._client
    
    def get_repository(self, owner: str, repo_name: str) -> Repository:
        """
        Get a repository by owner and name.
        
        Args:
            owner: Repository owner (username or organization)
            repo_name: Repository name
            
        Returns:
            Repository: The repository object
        """
        client = self._get_client()
        return client.get_repo(f"{owner}/{repo_name}")
    
    def list_organization_repos(self, org_name: str, max_repos: Optional[int] = None) -> List[Repository]:
        """
        List repositories in an organization.
        
        Args:
            org_name: Organization name
            max_repos: Maximum number of repositories to return (None for all)
            
        Returns:
            List[Repository]: List of repository objects
        """
        client = self._get_client()
        org = client.get_organization(org_name)
        repos = org.get_repos()
        
        if max_repos:
            return list(repos[:max_repos])
        return list(repos)
    
    def get_open_issues(self, owner: str, repo_name: str, max_issues: Optional[int] = None) -> List[Issue]:
        """
        Get open issues from a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            max_issues: Maximum number of issues to return (None for all)
            
        Returns:
            List[Issue]: List of issue objects
        """
        repo = self.get_repository(owner, repo_name)
        issues = repo.get_issues(state='open')
        
        if max_issues:
            return list(issues[:max_issues])
        return list(issues)
    
    def create_issue(self, owner: str, repo_name: str, title: str, body: str, 
                    labels: Optional[List[str]] = None) -> Issue:
        """
        Create a new issue in a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            title: Issue title
            body: Issue body/description
            labels: Optional list of label names
            
        Returns:
            Issue: The created issue object
        """
        repo = self.get_repository(owner, repo_name)
        
        if labels:
            return repo.create_issue(title=title, body=body, labels=labels)
        return repo.create_issue(title=title, body=body)
    
    def get_pull_requests(self, owner: str, repo_name: str, 
                         state: str = 'open', max_prs: Optional[int] = None) -> List[PullRequest]:
        """
        Get pull requests from a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            state: PR state ('open', 'closed', or 'all')
            max_prs: Maximum number of PRs to return (None for all)
            
        Returns:
            List[PullRequest]: List of pull request objects
        """
        repo = self.get_repository(owner, repo_name)
        pulls = repo.get_pulls(state=state)
        
        if max_prs:
            return list(pulls[:max_prs])
        return list(pulls)
    
    def add_issue_comment(self, owner: str, repo_name: str, issue_number: int, comment: str) -> None:
        """
        Add a comment to an issue.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number
            comment: Comment text
        """
        repo = self.get_repository(owner, repo_name)
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment)
    
    def close_issue(self, owner: str, repo_name: str, issue_number: int, 
                   comment: Optional[str] = None) -> None:
        """
        Close an issue with an optional comment.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number
            comment: Optional comment to add before closing
        """
        repo = self.get_repository(owner, repo_name)
        issue = repo.get_issue(issue_number)
        
        if comment:
            issue.create_comment(comment)
        
        issue.edit(state='closed')
    
    def get_repository_stats(self, owner: str, repo_name: str) -> dict:
        """
        Get statistics about a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            dict: Dictionary containing repository statistics
        """
        repo = self.get_repository(owner, repo_name)
        
        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'open_issues': repo.open_issues_count,
            'watchers': repo.watchers_count,
            'language': repo.language,
            'created_at': repo.created_at,
            'updated_at': repo.updated_at,
            'default_branch': repo.default_branch,
            'archived': repo.archived,
            'private': repo.private
        }
    
    def search_issues(self, query: str, max_results: Optional[int] = None) -> List[Issue]:
        """
        Search for issues across GitHub.
        
        Args:
            query: Search query (GitHub search syntax)
            max_results: Maximum number of results to return
            
        Returns:
            List[Issue]: List of matching issues
        """
        client = self._get_client()
        issues = client.search_issues(query)
        
        if max_results:
            return list(issues[:max_results])
        return list(issues)
    
    def get_user_info(self) -> dict:
        """
        Get information about the authenticated user/app.
        
        Returns:
            dict: Dictionary containing user/app information
        """
        client = self._get_client()
        user = client.get_user()
        
        return {
            'login': user.login,
            'name': user.name,
            'type': user.type,
            'company': user.company,
            'blog': user.blog,
            'location': user.location,
            'email': user.email,
            'bio': user.bio
        }
    
    def update_file_in_branch(self, owner: str, repo_name: str, branch_name: str, 
                             file_path: str, file_content: str, 
                             commit_message: str) -> dict:
        """
        Update a file in a specific branch of a repository.
        
        This method will create the file if it doesn't exist, or update it if it does.
        Uses PyGithub's high-level update_file method which handles the Git operations internally.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            branch_name: Branch name where the file should be updated
            file_path: Path to the file within the repository (e.g., 'src/main.py')
            file_content: New content for the file
            commit_message: Commit message for the update
            
        Returns:
            dict: Dictionary containing commit information and file details
            
        Raises:
            Exception: If the file doesn't exist (use create_file_in_branch for new files)
        """
        repo = self.get_repository(owner, repo_name)
        
        try:
            # Get the file to retrieve its SHA (required for updates)
            file_contents = repo.get_contents(file_path, ref=branch_name)
            
            # Update the file
            result = repo.update_file(
                path=file_path,
                message=commit_message,
                content=file_content,
                sha=file_contents.sha,
                branch=branch_name
            )
            
            return {
                'commit_sha': result['commit'].sha,
                'commit_message': commit_message,  # Use the original message passed in
                'file_sha': result['content'].sha,
                'file_path': result['content'].path,
                'branch': branch_name
            }
        except Exception as e:
            raise Exception(f"Failed to update file '{file_path}' in branch '{branch_name}': {str(e)}")
    
    def create_or_update_file_in_branch(self, owner: str, repo_name: str, branch_name: str, 
                                       file_path: str, file_content: str, 
                                       commit_message: str) -> dict:
        """
        Create or update a file in a specific branch of a repository.
        
        This method will create the file if it doesn't exist, or update it if it does.
        This is the recommended method when you're not sure if the file exists.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            branch_name: Branch name where the file should be created/updated
            file_path: Path to the file within the repository (e.g., 'src/main.py')
            file_content: Content for the file
            commit_message: Commit message for the create/update
            
        Returns:
            dict: Dictionary containing commit information and file details
        """
        repo = self.get_repository(owner, repo_name)
        
        try:
            # Try to get the file (to see if it exists)
            file_contents = repo.get_contents(file_path, ref=branch_name)
            file_sha = file_contents.sha
            operation = 'updated'
        except Exception:
            # File doesn't exist, so we'll create it
            file_sha = None
            operation = 'created'
        
        # Create or update the file
        if file_sha:
            result = repo.update_file(
                path=file_path,
                message=commit_message,
                content=file_content,
                sha=file_sha,
                branch=branch_name
            )
        else:
            result = repo.create_file(
                path=file_path,
                message=commit_message,
                content=file_content,
                branch=branch_name
            )
        
        return {
            'operation': operation,
            'commit_sha': result['commit'].sha,
            'commit_message': commit_message,  # Use the original message passed in
            'file_sha': result['content'].sha,
            'file_path': result['content'].path,
            'branch': branch_name
        }
    
    def update_file_using_git_api(self, owner: str, repo_name: str, branch_name: str,
                                  file_path: str, file_content: str,
                                  commit_message: str) -> dict:
        """
        Update a file using low-level Git API methods (create_git_tree, create_git_commit, update reference).
        
        This is an alternative approach using the lower-level Git API that you mentioned.
        The high-level methods (update_file_in_branch, create_or_update_file_in_branch) are 
        generally easier to use, but this demonstrates the Git plumbing approach.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            branch_name: Branch name where the file should be updated
            file_path: Path to the file within the repository
            file_content: New content for the file
            commit_message: Commit message
            
        Returns:
            dict: Dictionary containing commit and reference information
        """
        repo = self.get_repository(owner, repo_name)
        
        # Get the branch reference
        ref = repo.get_git_ref(f"heads/{branch_name}")
        
        # Get the commit that the branch currently points to
        base_commit = repo.get_git_commit(ref.object.sha)
        
        # Create a blob with the file content
        blob = repo.create_git_blob(file_content, "utf-8")
        
        # Create a tree with the file
        tree_element = InputGitTreeElement(
            path=file_path,
            mode='100644',  # File mode (regular file)
            type='blob',
            sha=blob.sha
        )
        
        tree = repo.create_git_tree([tree_element], base_commit.tree)
        
        # Create a commit with the new tree
        commit = repo.create_git_commit(
            message=commit_message,
            tree=tree,
            parents=[base_commit]
        )
        
        # Update the branch reference to point to the new commit
        ref.edit(sha=commit.sha)
        
        return {
            'commit_sha': commit.sha,
            'commit_message': commit.message,
            'tree_sha': tree.sha,
            'blob_sha': blob.sha,
            'branch': branch_name,
            'file_path': file_path
        }
