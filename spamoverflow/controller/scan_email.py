import subprocess
import json
import os
import re

def scan_spam(json_data):
    current_directory = os.path.dirname(os.path.abspath(__file__))

    spamhammer_path = os.path.abspath(os.path.join(current_directory, "../spamhammer"))

    if not os.path.exists(spamhammer_path):
        print("Error: SpamHammer executable not found.")

    command = [spamhammer_path, "scan", "--input", "-", "--output", "-"]

    json_string = json.dumps(json_data)

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    output, _ = process.communicate(input=json_string)

    output_json = json.loads(output)

    return output_json

def extract_urls(text):
    
    urls = re.findall(r'https?://[^?\s]+', text)
    extracted_urls = []

    for url in urls:
        match = re.search(r'//([^/?]+)', url)
        if match:
            domain = match.group(1)
            extracted_urls.append(domain)

    return extracted_urls
