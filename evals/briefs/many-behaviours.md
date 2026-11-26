Spec request from Lee Jordan (accounts team), ticket ACC-140.

People cannot control which emails we send them. We need notification preferences in the API.

1. A user can read their preferences.
2. A user can switch each of these on or off: comment emails, mention emails, weekly digest, billing emails.
3. Billing emails cannot be switched off by a user who is the account owner.
4. A new user starts with everything on.
5. A request to change a preference that does not exist is rejected with a 400.
6. A user cannot read or change the preferences of another user. That gets a 404.
7. The email sender checks the preference before each send and skips the email when it is off.
8. Password reset emails ignore preferences and always send.
9. Each change is written to the audit log with the user, the preference and the new value.
10. An admin can read the preferences of any user in their account but cannot change them.
11. Users who exist today get everything on, the same as now.

API only. I decide.
