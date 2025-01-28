# JiraIntegration

## Installation

```python
pip install jira python-dotenv
pip freeze > requirements.txt
pip install -r requirements.txt
```

Get your Jira API token:

Go to [API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
Create an API token and save it

Make sure to add .env to your .gitignore file to keep your API key secure
Create a .env file in your project root with:
CopyJIRA_APIKEY=your-api-token-here



Update the configuration with your details:

Jira URL
Your email
Your API token
Project key
Epic link ID