# Purpose

- Deactivate inactive AWS access keys automatically after 60 days.
- Deactivate Engineers' keys 90 days after they were created.
- Send a notification to engineers before deactivating their key.

# Required manual setup

Add event source:

- Event source type: `CloudWatch Events - Schedule`
- Name: `daily-mon-fri`
