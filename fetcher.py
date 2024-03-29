import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta


class Fetcher:
    
    JIRA_ISSUES_ENDPOINT = "/rest/api/3/search"
    JIRA_BOARDS_ENDPOINT = "/rest/agile/1.0/board"
    JIRA_SPRINTS_ENDPOINT = "/sprint"
    
    def __init__(self, jira_url, jira_username, jira_api_token, jira_project_key, jira_board_name, jira_max_issues, jira_max_sprints):
        self.jira_url = jira_url
        self.jira_username = jira_username
        self.jira_api_token = jira_api_token
        self.jira_project_key = jira_project_key
        self.jira_board_name = jira_board_name
        self.jira_max_issues = jira_max_issues
        self.jira_max_sprints = jira_max_sprints
        self.jira_auth = (self.jira_username, self.jira_api_token)


    def send_get_request(self, url, params, auth):  
        self.log(f"sending GET request to {url}")
        
        try:
            response = requests.get(url, params, auth=auth)
        except requests.exceptions.InvalidSchema:
            raise requests.HTTPError(404)
        
        self.log(f"{url} responded with code: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if content_type.startswith('image'):
                return response.content
            else:
                return response.json()
        else:
            raise requests.HTTPError(response.status_code)

    def log(self, message):
        print(f"\n[fetcher] {message}")

    def get_issues_urls(self):
        self.log("fetching issues urls...")
        
        issues = self.send_get_request(
            url=f"{self.jira_url}{self.JIRA_ISSUES_ENDPOINT}",
            params={
                "jql": f"project={self.jira_project_key} AND issuetype='story'",
                "maxResults": self.jira_max_issues,
            },
            auth=self.jira_auth
            )   

        issues_urls = [(issue["self"]) for issue in issues["issues"]]

        self.log("fetching issues urls done")
        
        return issues_urls
    
    def get_single_issue_data(self, issue_url):
        issue = self.send_get_request(url=issue_url, params=None, auth=self.jira_auth)
        
        self.log(f"fetching {issue['key']}...")
        self.log(f"fetching {issue['key']} status...")
        
        issue_status_url = issue["fields"]["status"]["self"]
        issue_status_response = self.send_get_request(url=issue_status_url, params=None, auth=self.jira_auth)
        issue_status = issue_status_response["name"]
        
        issue_simple = {
            "done": True if issue_status == "Done" else False,
            "storyPoints": self.get_story_points(issue),
            "statusChangeDate": self.convert_date(issue["fields"]["statuscategorychangedate"])
        }
        
        self.log(f"fetching {issue['key']} done")

        return issue_simple

    def get_issues_data_threaded(self, max_threads=20):        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            issues_urls = self.get_issues_urls()
            
            self.log("fetching issues data")
            
            futures = [executor.submit(self.get_single_issue_data, url) for url in issues_urls]
            issues_simple = []
            
            for future in as_completed(futures):
                issues_simple.append(future.result())
            
            self.log("fetching issues data done")
            
            return issues_simple

    def get_sprints_data(self):
        self.log("fetching boards data")
        
        boards = self.send_get_request(
            url=f"{self.jira_url}{self.JIRA_BOARDS_ENDPOINT}",
            params={
                "jql": f"project={self.jira_project_key}",
                "maxResults": self.jira_max_issues
            },
            auth=self.jira_auth
        )
        
        self.log("fetching boards data done")
        
        try:
            board_url = list(filter(lambda b: b["name"] == self.jira_board_name, boards["values"]))[0]['self']
        except IndexError:
            raise requests.HTTPError(404)
        
        self.log("fetching sprints data")
        
        sprints = self.send_get_request(url=f"{board_url}{self.JIRA_SPRINTS_ENDPOINT}", params=None, auth=self.jira_auth)
        sprints_simple = list(map(lambda sprint:
                                  {"name": sprint["name"],
                                   "startDate": self.convert_date(sprint["startDate"]),
                                   "endDate": self.convert_date(sprint["endDate"])}, sprints["values"]
                                  ))
        
        self.log("fetching sprints data done")    
    
        return sprints_simple

    def generate_burndown_data(self, issues_simple, sprints_simple):
        self.log("calculating burndown data")
        
        total_story_points = sum(map(lambda i: i["storyPoints"], issues_simple))
        burndown_data = []
        current_date = sprints_simple[0]["startDate"]
        
        while current_date <= sprints_simple[-1]["endDate"]:
            story_points_done = sum(issue["storyPoints"] for issue in issues_simple if
                                     issue["done"] and issue["statusChangeDate"] <= current_date)
            burndown_data.append((current_date, total_story_points - story_points_done))
            current_date += timedelta(days=1)
            
        self.log("calculating burndown data done")    
            
        return burndown_data

    def get_complete_data(self):
        sprints_simple = self.get_sprints_data()
        issues_simple = self.get_issues_data_threaded()
        burndown_data = self.generate_burndown_data(issues_simple, sprints_simple)
        
        return burndown_data, sprints_simple
    
    def get_error_image(self, error_code):
        self.log("fetching error img...")
        
        img = self.send_get_request(f"https://http.cat/{error_code}", params=None, auth=None)
        
        self.log("fetching error img done")
        
        return img

    @staticmethod
    def get_total_story_points(issues_simple):
        return sum(map(lambda i: i["storyPoints"], issues_simple))
    
    @staticmethod
    def get_story_points(issue):
        if "customfield_10031" in issue["fields"]:
            return issue["fields"]["customfield_10031"]
        return 0
    
    @staticmethod
    def convert_date(d):
        return datetime.strptime(d[:10], "%Y-%m-%d")
