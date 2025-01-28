from jira import JIRA
from typing import List, Dict
import os
from dotenv import load_dotenv
from dataclasses import dataclass

class JiraConfig:
    def __init__(self, url, email, api_key):
        self.url = url
        self.email = email
        self.api_key = api_key
    
    def __post_init__(self):
        """Validate the configuration"""
        if not all([self.url, self.email, self.api_key]):
            missing = []
            if not self.url: missing.append('JIRA_URL')
            if not self.email: missing.append('JIRA_EMAIL')
            if not self.api_key: missing.append('JIRA_APIKEY')
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

class JiraStoryCreator:
    def __init__(self, config: JiraConfig):
        """
        Initialize Jira connection using configuration
        
        Args:
            config: Optional JiraConfig instance. If not provided, will load from environment variables
        """
        print('program initiated')
        
        # Use provided config or create from environment variables
        self.config = config
        
        self.jira = JIRA(
            server=self.config.url,
            basic_auth=(self.config.email, self.config.api_key)
        )
    
    def create_user_story(self, 
                         title: str, 
                         description: str, 
                         acceptance_criteria: str,
                         epic_link: str,
                         project_key: str,
                         issue_type: str = "Story") -> str:
        """
        Create a user story and link it to an epic
        
        Args:
            title: Story title
            description: Story description
            acceptance_criteria: Acceptance criteria for the story
            epic_link: Epic ID to link the story to
            project_key: The project key where the story should be created
            issue_type: The issue type (default is "Story")
            
        Returns:
            str: The key of the created issue
        """
    
        issue_dict = {
            'project': {'key': project_key},
            'summary': title,
            'description': description,
            'customfield_10155' : acceptance_criteria,
            'issuetype': {'name' : issue_type},
            'parent':  {'key': epic_link}  # customfield_10014 This is commonly used for Epic Link, but might be different in your instance    'type': {'type': issue_type},
        }
        
        new_issue = self.jira.create_issue(fields=issue_dict)
        return new_issue.key
    
    def create_multiple_stories(self, 
                              stories: List[Dict[str, str]], 
                              epic_link: str,
                              project_key: str) -> List[str]:
        """
        Create multiple user stories linked to the same epic
        
        Args:
            stories: List of dictionaries containing story details
                    Each dict should have 'title', 'description', and 'acceptance_criteria'
            epic_link: Epic ID to link all stories to
            project_key: The project key where stories should be created
            
        Returns:
            List[str]: List of created issue keys
        """
        created_issues = []
        
        for story in stories:
            try:
                issue_key = self.create_user_story(
                    title=story['title'],
                    description=story['description'],
                    acceptance_criteria=story['acceptance_criteria'],
                    epic_link=epic_link,
                    project_key=project_key
                )
                created_issues.append(issue_key)
            except Exception as e:
                print(f"Error creating story '{story['title']}': {str(e)}")
        
        return created_issues

# Example usage
if __name__ == "__main__":
    load_dotenv()
    
    config = JiraConfig(os.getenv('JIRA_URL'), os.getenv('JIRA_EMAIL'), os.getenv('JIRA_APIKEY'))
    creator = JiraStoryCreator(config)
        
    # Example stories to create
    
    #loop through these endpoint urls
    endpoints = [
        "scheduled_texts.php",
        "rest/v1/ricochet/syncleads"
    ]

    # Template for the story
    story_template = {
        "title": "Migrate PHP Endpoints to Node.js - {endpoint}",
        "description": """As a software director,
    I want to migrate our PHP endpoints to Node.js,
    So that we can improve performance and support real-time capabilities.

    Business Rationale:
    Migrating to Node.js will leverage its event-driven, non-blocking I/O model to enhance performance and support real-time capabilities, which are crucial for our automation tasks.
    """,
        "acceptance_criteria": """
    Given the existing PHP endpoints, when they are migrated to Node.js, then the system behaviors should remain unchanged. (inputs and outputs remain same)
    Given the new Node.js endpoints, when they are deployed, then they should handle the same load and performance requirements as the current system.
    Given the new Node.js endpoints, when they are monitored using Enterprise Logging (AWS CloudWatch), then performance timings and errors should be tracked and reported accurately.
    Given the API endpoints, when they are added to the automated QA integration tests, then any regressions should be detected and addressed promptly.

    Notes: Ensure that the code follows SOLID principles, has unit tests and is maintainable and scalable.
    """
    }

    # Generate stories
    stories_to_create = []
    for endpoint in endpoints:
        story = {
            "title": story_template["title"].format(endpoint=endpoint),
            "description": story_template["description"],
            "acceptance_criteria": story_template["acceptance_criteria"]
        }
        stories_to_create.append(story)
    
    print (stories_to_create)

    created_stories = creator.create_multiple_stories(
        stories=stories_to_create,
        epic_link="CID-4532",  # Replace with your epic ID
        project_key="CID"     # Replace with your project key
    )
    
    print(f"Created stories: {created_stories}")