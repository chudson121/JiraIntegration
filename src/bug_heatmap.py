# First-time use (will prompt for credentials)
# python .\src\bug_heatmap.py --jql "project = CID AND issuetype = Bug AND \"environment[dropdown]\" = Production and status != Declined and createdDate >= startOfYear() ORDER BY created DESC"

# Using existing config
# python .\src\bug_heatmap.py --config my_config.ini --output my_heatmap.png

import os
import pandas as pd
import numpy as np
import requests
from jira import JIRA
import matplotlib.pyplot as plt
import seaborn as sns
from github import Github
from collections import defaultdict
import argparse
import configparser
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BugHeatmapGenerator:
    def __init__(self, config_file='config.ini'):
        """Initialize with configuration from a config file."""
        self.config = configparser.ConfigParser()
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            self.setup_config(config_file)
        
        # Initialize connections to Jira and GitHub
        self.setup_jira()
        self.setup_github()
        
    def setup_config(self, config_file):
        """Create a new configuration file with user input."""
        self.config['JIRA'] = {
            'server': input("Enter Jira server URL (e.g., https://your-domain.atlassian.net): "),
            'username': input("Enter Jira username (email): "),
            'api_token': input("Enter Jira API token: "),
            'project_key': input("Enter Jira project key (e.g., PROJ): ")
        }
        
        self.config['GITHUB'] = {
            'token': input("Enter GitHub personal access token: "),
            'organization': input("Enter GitHub organization or username: ")
        }
        
        with open(config_file, 'w') as f:
            self.config.write(f)
        logger.info(f"Configuration saved to {config_file}")
    
    def setup_jira(self):
        """Set up connection to Jira."""
        try:
            self.jira = JIRA(
                server=self.config['JIRA']['server'],
                basic_auth=(self.config['JIRA']['username'], self.config['JIRA']['api_token'])
            )
            logger.info("Successfully connected to Jira")
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            raise
    
    def setup_github(self):
        """Set up connection to GitHub."""
        try:
            self.github = Github(self.config['GITHUB']['token'])
            self.org = self.github.get_organization(self.config['GITHUB']['organization'])
            logger.info("Successfully connected to GitHub")
        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise
    
    def get_jira_issues(self, custom_jql=None, max_results=1000):
        """Fetch bug issues from Jira with GitHub references using custom JQL if provided."""
        if custom_jql:
            jql_query = custom_jql
        else:
            jql_query = f'project = {self.config["JIRA"]["project_key"]} AND issuetype = Bug'
        
        logger.info(f"Fetching Jira issues with query: {jql_query}")
        issues = self.jira.search_issues(jql_query, maxResults=max_results)
        logger.info(f"Found {len(issues)} issues")
        
        return issues
    
    def extract_github_references(self, issues):
        """Extract GitHub repository and file references from Jira issues."""
        bug_data = []
        
        for issue in issues:
            # Look for GitHub links in issue description and comments
            description = issue.fields.description or ""
            comments = self.jira.comments(issue.key)
            
            repo_refs = self.find_github_references(description)
            
            for comment in comments:
                repo_refs.extend(self.find_github_references(comment.body))
            
            # Add the discovered references
            for ref in repo_refs:
                bug_data.append({
                    'issue_key': issue.key,
                    'summary': issue.fields.summary,
                    'repository': ref.get('repository', ''),
                    'file_path': ref.get('file_path', ''),
                    'directory': self.get_directory(ref.get('file_path', '')),
                    'status': issue.fields.status.name
                })
        
        return pd.DataFrame(bug_data)
    
    def find_github_references(self, text):
        """Find GitHub repository and file references in text.
        
        This is a simplified implementation. In a real scenario, you might want to use
        regex patterns to detect GitHub links or specific formats used in your organization.
        """
        if not text:
            return []
        
        references = []
        # Simple detection for GitHub links
        # Format: https://github.com/org/repo/blob/branch/path/to/file.ext
        lines = text.split('\n')
        for line in lines:
            if 'github.com' in line and '/blob/' in line:
                parts = line.split('github.com/')[1].split('/blob/')
                if len(parts) >= 2:
                    org_repo = parts[0].strip()
                    file_path = parts[1].split('/', 1)[1] if '/' in parts[1] else parts[1]
                    references.append({
                        'repository': org_repo,
                        'file_path': file_path
                    })
        
        return references
    
    def get_directory(self, file_path, depth=2):
        """Get directory from file path up to specified depth."""
        if not file_path:
            return ""
        
        parts = file_path.split('/')
        if len(parts) <= depth:
            return '/'.join(parts[:-1]) if len(parts) > 1 else ""
        else:
            return '/'.join(parts[:depth])
    
    def scan_repositories(self):
        """Scan GitHub repositories to get file structure."""
        repo_data = {}
        
        logger.info(f"Scanning repositories in {self.config['GITHUB']['organization']}")
        for repo in self.org.get_repos():
            repo_name = repo.name
            repo_data[repo_name] = self.scan_repository_structure(repo)
        
        return repo_data
    
    def scan_repository_structure(self, repo, max_depth=3):
        """Scan repository to get its structure up to max_depth."""
        try:
            contents = repo.get_contents("")
            structure = defaultdict(int)
            
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    # Count directories up to max_depth
                    path_parts = file_content.path.split('/')
                    if len(path_parts) <= max_depth:
                        structure[file_content.path] += 1
                    
                    # Get contents of this directory
                    if len(path_parts) < max_depth:
                        try:
                            directory_contents = repo.get_contents(file_content.path)
                            contents.extend(directory_contents)
                        except Exception as e:
                            logger.warning(f"Error getting contents of {file_content.path}: {e}")
                else:
                    # For files, track their parent directories
                    path_parts = file_content.path.split('/')
                    if len(path_parts) > 1:
                        for depth in range(1, min(len(path_parts), max_depth + 1)):
                            dir_path = '/'.join(path_parts[:depth])
                            structure[dir_path] += 1
            
            return dict(structure)
        except Exception as e:
            logger.error(f"Error scanning repository {repo.name}: {e}")
            return {}
    
    def generate_heatmap_data(self, bugs_df, repo_structure=None):
        """Generate data for the heatmap."""
        # Group bugs by repository and directory
        if bugs_df.empty:
            logger.warning("No bug data to generate heatmap")
            return None
        
        # Count bugs by repository and directory
        bug_counts = bugs_df.groupby(['repository', 'directory']).size().reset_index(name='bug_count')
        
        # If we have repository structure, we can enhance the heatmap
        if repo_structure:
            # Create a more complete matrix including directories without bugs
            all_repos = list(repo_structure.keys())
            all_dirs = set()
            for repo, dirs in repo_structure.items():
                for dir_path in dirs:
                    all_dirs.add(dir_path)
            
            # Create a complete DataFrame
            complete_data = []
            for repo in all_repos:
                for dir_path in all_dirs:
                    bug_row = bug_counts[(bug_counts['repository'] == repo) & 
                                        (bug_counts['directory'] == dir_path)]
                    bug_count = bug_row['bug_count'].values[0] if not bug_row.empty else 0
                    complete_data.append({
                        'repository': repo,
                        'directory': dir_path,
                        'bug_count': bug_count
                    })
            
            return pd.DataFrame(complete_data)
        else:
            return bug_counts
    
    def plot_heatmap(self, heatmap_data, output_file="bug_heatmap.png"):
        """Plot the heatmap and save to file."""
        if heatmap_data is None or heatmap_data.empty:
            logger.warning("No data to plot heatmap")
            return
        
        # Pivot the data for the heatmap
        pivot_data = heatmap_data.pivot(index='repository', columns='directory', values='bug_count')
        pivot_data = pivot_data.fillna(0)
        
        # Set up the plot
        plt.figure(figsize=(15, 10))
        
        # Create heatmap
        ax = sns.heatmap(
            pivot_data, 
            annot=True, 
            fmt="g", 
            cmap="YlOrRd",
            linewidths=0.5,
            cbar_kws={'label': 'Bug Count'}
        )
        
        plt.title('Bug Heatmap by Repository and Directory')
        plt.xlabel('Directory')
        plt.ylabel('Repository')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Heatmap saved to {output_file}")
        plt.close()
    
    def run(self, jql_query=None, output_file="bug_heatmap.png"):
        """Run the full process to generate the heatmap."""
        # Get Jira issues using the provided JQL query if available
        issues = self.get_jira_issues(custom_jql=jql_query)
        
        # Extract GitHub references
        bugs_df = self.extract_github_references(issues)
        
        # If no GitHub references are found, log a warning
        if bugs_df.empty:
            logger.warning("No GitHub references found in the Jira issues. Check if your issues contain links to GitHub files.")
            return None
        
        # If limited GitHub references are found in Jira, scan repositories
        repo_structure = None
        if len(bugs_df) < 20:  # Arbitrary threshold, adjust as needed
            logger.info("Few GitHub references found in Jira, scanning repositories structure")
            repo_structure = self.scan_repositories()
        
        # Generate heatmap data
        heatmap_data = self.generate_heatmap_data(bugs_df, repo_structure)
        
        # Plot and save the heatmap
        self.plot_heatmap(heatmap_data, output_file)
        
        return heatmap_data

def main():
    parser = argparse.ArgumentParser(description='Generate bug heatmap from Jira and GitHub data')
    parser.add_argument('--config', type=str, default='config.ini', help='Configuration file')
    parser.add_argument('--output', type=str, default='bug_heatmap.png', help='Output file name')
    parser.add_argument('--jql', type=str, help='Custom JQL query to fetch specific issues')
    args = parser.parse_args()
    
    jql = "project = CID AND issuetype = Bug AND \"environment[dropdown]\" = Production and status != Declined and createdDate >= startOfYear() ORDER BY created DESC"
        
    generator = BugHeatmapGenerator(config_file=args.config)
    generator.run(jql_query=args.jql, output_file=args.output)

if __name__ == "__main__":
    main()