import requests

url = "https://api.usemotion.com/v1/tasks"
headers = {
    "X-API-Key": "EPUrPoxMRSIXNL6o1/fL2CGf7cqzo6yvyyolY6rp8Fw=",
    "Accept": "application/json"
}
response = requests.get(url, headers=headers)
print(response.status_code)
print(response.text)