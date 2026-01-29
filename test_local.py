from gmail_client import GmailClient

g = GmailClient()
print(g.list_unread(max_results=5))

# After you see an email id above, paste it here:
# print(g.create_draft_reply(original_message_id="PASTE_ID", reply_body="Thanks—got it. I’ll get back to you shortly."))
