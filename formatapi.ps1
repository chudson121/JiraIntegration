# .\script.ps1 -filename "input.txt"
param (
    [string]$filename
)

# Read the content of the file
$inputString = Get-Content -Path $filename -Raw

# Split the input string into lines
$lines = $inputString -split "`n"


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



# Initialize variables
$currentCategory = ""
$outputLines = @()

# Process each line
foreach ($line in $lines) {
    $line = $line.Trim()
    if ($line.StartsWith("####")) {
        $currentCategory = $line.Replace("####", "").Trim()
    } elseif ($line.StartsWith("-")) {
        $outputLines += "$currentCategory, $($line.Replace('-', '').Trim())"
    }
}

# Join the output lines into a single string
$outputString = $outputLines -join "`n"

# Output the result to a new file called output.txt
$outputString | Out-File -FilePath "output.txt"

# Print a message indicating the output file has been created
Write-Output "The results have been written to output.txt"