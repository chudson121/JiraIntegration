# .\formatAPIToUserStory.ps1 -inputFilePath "NodeAPI.txt"
# Define the input file path
# $inputFilePath = "input.txt"
param (
    [string]$inputFilePath
)


# Read the content of the input file
$inputContent = Get-Content -Path $inputFilePath

# Initialize the JSON schema
$jsonSchema = @{
    epics = @()
}

# Define the common description and acceptance criteria for user stories
$commonDescription = "As a software director, I want to migrate our PHP endpoints to Node.js, So that we can improve performance and support real-time capabilities."
$commonAcceptanceCriteria = @"
Given the existing PHP endpoints,
when they are migrated to Node.js,
then the system behaviors should remain unchanged. (inputs and outputs remain same)
Given the new Node.js endpoints,
when they are deployed,
then they should handle the same or better load and performance requirements as the current system.
Given the new Node.js endpoints,
when they are monitored using Enterprise Logging (AWS CloudWatch),
then performance timings and errors should be tracked and reported accurately.
Given the API endpoints,
when they are added to the automated QA integration tests,
then any regressions should be detected and addressed promptly.
Notes: Ensure that the code follows SOLID principles, has unit tests and is maintainable and scalable.
"@

# Initialize variables to store current epic details
$currentEpicTitle = ""
$currentEpicDescription = ""
$currentUserStories = @()

# Process the input content and add user stories to the JSON schema
foreach ($line in $inputContent) {
    $line = $line.Trim()
    if ($line.StartsWith("####")) {
        # If there is an existing epic, add it to the JSON schema
        if ($currentEpicTitle -ne "") {
            $jsonSchema.epics += @{
                title = $currentEpicTitle
                description = $currentEpicDescription
                user_stories = $currentUserStories
            }
        }
        # Start a new epic
        $currentEpicTitle = "Node Migration - " + $line.Substring(5).Trim()
        $currentEpicDescription = "Node Migration - " + $line.Substring(5).Trim()
        $currentUserStories = @()
    } elseif ($line.StartsWith("-")) {
        # Add user story to the current epic
        $currentUserStories += @{
            title = $line.Substring(2).Trim()
            description = $commonDescription
            acceptance_criteria = $commonAcceptanceCriteria
        }
    }
}

# Add the last epic to the JSON schema
if ($currentEpicTitle -ne "") {
    $jsonSchema.epics += @{
        title = $currentEpicTitle
        description = $currentEpicDescription
        user_stories = $currentUserStories
    }
}

# Convert the JSON schema to a JSON string
$jsonOutput = $jsonSchema | ConvertTo-Json -Depth 4

# Define the output file path
$outputFilePath = "output.json"

# Save the JSON output to the output file
$jsonOutput | Out-File -FilePath $outputFilePath

Write-Host "The JSON schema has been successfully created and saved to $outputFilePath."