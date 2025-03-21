# JiraIntegration

## Installation

```python
pip install jira python-dotenv
pip freeze > requirements.txt
pip install -r requirements.txt
```
.venv\Scripts\activate

Get your Jira API token:

Go to [API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
Create an API token and save it

Make sure to add .env to your .gitignore file to keep your API key secure
Create a .env file in your project root with:
Copy JIRA_APIKEY=your-api-token-here



Update the configuration with your details:

Jira URL
Your email
Your API token
Project key


epics: An array of epic objects.
title: The title of the epic (string).
description: The description of the epic (string).
user_stories: An array of user story objects.
title: The title of the user story (string).
description: The description of the user story. Should be in the As a [type of user] I want [describe system behavior/business rule] so that [identify business value or outcome] (string).
acceptance_criteria: The acceptance criteria for the user story in the Given When Then format for each criteria (string).

{
  "epics": [
    {
      "title": "string",
      "description": "string",
      "user_stories": [
        {
          "title": "string",
          "description": "string",
          "acceptance_criteria": "string"
        }
      ]
    }
  ]
}