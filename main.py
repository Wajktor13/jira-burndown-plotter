from fetcher import Fetcher
import plotter


if __name__ == "__main__":
    JIRA_USERNAME = ""
    JIRA_API_TOKEN = ""
    JIRA_PROJECT_KEY = ""
    JIRA_URL = ""
    JIRA_BOARD_NAME = ""
    JIRA_MAX_ISSUES = 200
    JIRA_MAX_SPRINTS = 20
    
    fetcher = Fetcher(JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, JIRA_PROJECT_KEY, JIRA_BOARD_NAME, JIRA_MAX_ISSUES, JIRA_MAX_SPRINTS)
    
    burndown_data, sprints_data = fetcher.get_complete_data()
    
    fig = plotter.generate_burndown_plot(burndown_data, sprints_data)
    
    fig.show()
    