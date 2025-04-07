import logging
from pathlib import Path
from jira import JIRA, JIRAError
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
import json
from getpass import getpass
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    """Jira configuration with validation"""
    url: str
    email: str
    api_key: str
    project_key: str
    epic_link_field: str = field(default="customfield_10014")
    acceptance_criteria_field: str = field(default="customfield_10155")
    max_retries: int = field(default=3)
    retry_delay: int = field(default=5)

    def __post_init__(self):
        """Validate configuration parameters"""
        required = {
            'url': self.url,
            'email': self.email,
            'api_key': self.api_key,
            'project_key': self.project_key
        }
        
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

class JiraDataParser:
    """Handles parsing and validation of input data"""
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict:
        """
        Load and validate JSON data from file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            ValueError: On invalid JSON or file structure
            FileNotFoundError: If file doesn't exist
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                if not isinstance(data, dict) or 'epics' not in data:
                    raise ValueError("Invalid JSON structure - missing 'epics' key")
                    
                return data
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error reading file: {e}")

class JiraClient:
    """Handles Jira API interactions with retry logic"""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.jira = self._connect()
        
    def _connect(self) -> JIRA:
        """Establish Jira connection with retry logic"""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                return JIRA(
                    server=self.config.url,
                    basic_auth=(self.config.email, self.config.api_key),
                    timeout=10
                )
            except JIRAError as e:
                if attempt == self.config.max_retries:
                    raise
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                time.sleep(self.config.retry_delay)
                
        raise RuntimeError("Failed to establish Jira connection")

    def _create_issue_with_retry(self, issue_dict: Dict) -> str:
        """Create issue with retry logic"""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                issue = self.jira.create_issue(fields=issue_dict)
                return issue.key
            except JIRAError as e:
                if attempt == self.config.max_retries:
                    raise
                logger.warning(f"Create issue attempt {attempt} failed: {e}")
                time.sleep(self.config.retry_delay)
                
        raise RuntimeError("Failed to create issue after retries")

class JiraStoryCreator(JiraClient):
    """Handles creation of Jira epics and user stories"""
    
    def get_parent_id(self) -> str:
        """Prompt user for parent ID with validation"""
        while True:
            parent_id = input("Please enter the parent ID (Epic/Initiative key): ").strip()
            if parent_id and self._validate_issue(parent_id):
                return parent_id
            logger.error("Invalid parent ID or inaccessible issue")
            
    def _validate_issue(self, issue_key: str) -> bool:
        """Validate if issue exists and is accessible"""
        try:
            return bool(self.jira.issue(issue_key))
        except JIRAError:
            return False

    def create_epic(self, title: str, description: str, parent_key: str) -> str:
        """
        Create a Jira epic
        
        Args:
            title: Epic title
            description: Epic description
            parent_key: Parent issue key
            
        Returns:
            Created epic key
        """
        issue_dict = {
            'project': {'key': self.config.project_key},
            'summary': title,
            'description': description,
            'issuetype': {'name': 'Epic'},
            'parent': {'key': parent_key}
        }
        
        try:
            return self._create_issue_with_retry(issue_dict)
        except JIRAError as e:
            logger.error(f"Failed to create epic '{title}': {e}")
            raise

    def create_user_story(self, 
                         title: str, 
                         description: str, 
                         acceptance_criteria: str,
                         epic_key: str) -> str:
        """
        Create a user story linked to an epic
        
        Args:
            title: Story title
            description: Story description
            acceptance_criteria: Acceptance criteria
            epic_key: Linked epic key
            
        Returns:
            Created story key
        """
        issue_dict = {
            'project': {'key': self.config.project_key},
            'summary': title,
            'description': description,
            self.config.acceptance_criteria_field: acceptance_criteria,
            'issuetype': {'name': 'Story'},
            self.config.epic_link_field: epic_key
        }
        
        try:
            return self._create_issue_with_retry(issue_dict)
        except JIRAError as e:
            logger.error(f"Failed to create story '{title}': {e}")
            raise

    def create_from_json(self, json_data: Dict) -> List[str]:
        """
        Create hierarchy from JSON data
        
        Args:
            json_data: Structured data containing epics and stories
            
        Returns:
            List of created issue keys
        """
        created_issues = []
        parent_key = self.get_parent_id()
        
        try:
            for epic in json_data['epics']:
                epic_key = self.create_epic(
                    epic['title'],
                    epic['description'],
                    parent_key
                )
                created_issues.append(epic_key)
                logger.info(f"Created epic: {epic_key}")
                
                for story in epic['user_stories']:
                    story_key = self.create_user_story(
                        story['title'],
                        story['description'],
                        story['acceptance_criteria'],
                        epic_key
                    )
                    created_issues.append(story_key)
                    logger.info(f"Created story: {story_key} under {epic_key}")
                    
        except Exception as e:
            logger.error(f"Aborting due to error: {e}")
            raise
        
        return created_issues

def load_config() -> JiraConfig:
    """Load configuration from environment with fallback prompts"""
    # load_dotenv()
    load_dotenv(Path('.env'))
    
    print(os.getenv('JIRA_API_KEY'))
    
    return JiraConfig(
        api_key=os.getenv('JIRA_API_KEY') or getpass("Jira API Key: "),
        url=os.getenv('JIRA_URL') or input("Jira URL: "),
        email=os.getenv('JIRA_EMAIL') or input("Jira Email: "),
        project_key=os.getenv('PROJECT_KEY') or input("Project Key: "),
        epic_link_field=os.getenv('EPIC_LINK_FIELD', 'customfield_10014'),
        acceptance_criteria_field=os.getenv('ACCEPTANCE_CRITERIA_FIELD', 'customfield_10155')
    )

if __name__ == "__main__":
    try:
        config = load_config()
        creator = JiraStoryCreator(config)
        
        data = JiraDataParser.load_from_file('project.json')
        created_issues = creator.create_from_json(data)
        
        logger.info(f"Successfully created {len(created_issues)} issues:")
        logger.info("\n".join(created_issues))
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        exit(1)