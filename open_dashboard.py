import webbrowser
import os

# Get the absolute path to the dashboard file
dashboard_path = os.path.abspath("simple_dashboard.html")

# Convert the file path to a URL
file_url = f"file://{dashboard_path}"

print(f"Opening dashboard at: {file_url}")

# Open the dashboard in the default browser
webbrowser.open(file_url)

print("If the browser doesn't open automatically, please open this URL manually:")
print(file_url) 