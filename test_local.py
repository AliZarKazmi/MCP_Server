from gmail_client import GmailClient

g = GmailClient()
print(g.list_unread(max_results=5))

