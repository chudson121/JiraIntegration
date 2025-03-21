from jira import JIRA
from typing import List, Dict
import os
from dotenv import load_dotenv
from dataclasses import dataclass
import json

class JiraConfig:
    def __init__(self, url, email, api_key, project_key):
        self.url = url
        self.email = email
        self.api_key = api_key
        self.project_key = project_key
    
    def __post_init__(self):
        """Validate the configuration"""
        if not all([self.url, self.email, self.api_key]):
            missing = []
            if not self.url: missing.append('JIRA_URL')
            if not self.email: missing.append('JIRA_EMAIL')
            if not self.api_key: missing.append('JIRA_APIKEY')
            if not self.project_key: missing.append('PROJECT_KEY')
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
    

    
    def get_parent_id(self) -> str:
        # Prompt the user for the parent_id
        parent_id = input("Please enter the parent_id: ")
        return parent_id


    def create_user_story(self, 
                         title: str, 
                         description: str, 
                         acceptance_criteria: str,
                         parent_id: str,
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
    
        issue_MapObjToJira = {
            'project': {'key': project_key},
            'summary': title,
            'description': description,
            'customfield_10155' : acceptance_criteria,
            'issuetype': {'name' : issue_type},
            'parent':  {'key': parent_id}  # customfield_10014 This is commonly used for Epic Link, but might be different in your instance    'type': {'type': issue_type},
        }
        
        new_issue = self.jira.create_issue(fields=issue_MapObjToJira)
        return new_issue.key


    def create_epic(self, title: str, description: str, project_key: str, parent_id) -> str:
        """
        Create an epic in Jira
        
        Args:
            title: Epic title
            description: Epic description
            project_key: The project key where the epic should be created
            
        Returns:
            str: The key of the created epic
        """
        issue_dict = {
            'project': {'key': project_key},
            'summary': title,
            'description': description,
            'issuetype': {'name': 'Epic'},
            'parent':  {'key': parent_id}
        }
        
        new_issue = self.jira.create_issue(fields=issue_dict)
        return new_issue.key

    def parse_json_and_create_tickets(self, json_data):
        # Parse the JSON data
        
        created_issues = []
        parent_id = self.get_parent_id()
        
        # Iterate over each epic
        for epic in json_data['epics']:
            epic_title = epic['title']
            epic_description = epic['description']
            print(f"Creating Epic: {epic_title}")
            
            # Create the epic
            epic_link = self.create_epic(epic_title, epic_description, config.project_key, parent_id)
            created_issues.append(epic_link)
            
            # Iterate over each user story in the epic
            for user_story in epic['user_stories']:
                user_story_title = user_story['title']
                user_story_description = user_story['description']
                acceptance_criteria = user_story['acceptance_criteria']
                
                print(f"  Creating User Story: {user_story_title}")
                #print(f"    Description: {user_story_description}")
                #print(f"    Acceptance Criteria: {acceptance_criteria}")
                
                # Create the User story
                issue_key = self.create_user_story(user_story_title, user_story_description, acceptance_criteria, epic_link, 'CID', 'Story')
                created_issues.append(issue_key)
            
        return created_issues


# Example usage
if __name__ == "__main__":
    load_dotenv()
    
    config = JiraConfig(os.getenv('JIRA_URL'), os.getenv('JIRA_EMAIL'), os.getenv('JIRA_APIKEY'), os.getenv('PROJECT_KEY'))
    
    # Get json file
    file_path = 'project.json'
    json_data = ''
    creator = JiraStoryCreator(config)
    
    try:
        # Open the JSON file
        with open(file_path, 'r') as file:
            # Check if the file is empty
            if file.readable() and file.read(1):
                file.seek(0)  # Reset file pointer to the beginning
                # Load the JSON data
                json_data = json.load(file)
                print("JSON data loaded successfully.")
                # print(json_data)
                issues = creator.parse_json_and_create_tickets(json_data)
                print(f"Created stories: {issues}")
    
            else:
                print("The file is empty.")
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print("Program completed.")