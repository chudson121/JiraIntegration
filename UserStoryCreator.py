from jira import JIRA
from typing import List, Dict

class JiraStoryCreator:
    def __init__(self, jira_url: str, email: str, api_token: str):
        """
        Initialize Jira connection
        
        Args:
            jira_url: Your Jira instance URL (e.g., 'https://your-domain.atlassian.net')
            email: Your Jira email
            api_token: Your Jira API token
        """
        self.jira = JIRA(
            server=jira_url,
            basic_auth=(email, api_token)
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
        # Format the description with acceptance criteria
        formatted_description = f"""
{description}

h3. Acceptance Criteria:
{acceptance_criteria}
"""
        
        # Define the issue fields
        issue_dict = {
            'project': {'key': project_key},
            'summary': title,
            'description': formatted_description,
            'issuetype': {'name': issue_type},
            'customfield_10014': epic_link  # This is commonly used for Epic Link, but might be different in your instance
        }
        
        # Create the issue
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
    # Initialize the creator
    creator = JiraStoryCreator(
        jira_url="https://your-domain.atlassian.net",
        email="your-email@example.com",
        api_token="your-api-token"
    )
    
    # Example stories to create
    stories_to_create = [
        {
            "title": "Migrate Endpoint X",
            "description": "As a developer, I need to migrate endpoint X to the new API version",
            "acceptance_criteria": """
* Endpoint is fully migrated to new version
* All existing functionality is preserved
* Tests are updated and passing
* Documentation is updated
"""
        },
        # Add more stories as needed
    ]
    
    # Create the stories
    created_stories = creator.create_multiple_stories(
        stories=stories_to_create,
        epic_link="EPIC-123",  # Replace with your epic ID
        project_key="PROJ"     # Replace with your project key
    )
    
    print(f"Created stories: {created_stories}")