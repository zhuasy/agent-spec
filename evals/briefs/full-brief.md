From: Dana Okafor (payments team)
Ticket: PAY-231

We lost 312 webhook deliveries on 14 March. The customer's endpoint was down for 20 minutes and we never retried.

I want retries for failed webhook deliveries. Retry when the endpoint returns a 5xx status or the connection times
out. Do not retry on a 4xx status. Make 5 attempts at most, with a wait that doubles each time, starting at 30
seconds. After the last failed attempt, mark the delivery as failed and show it in the delivery log. A successful
delivery today is sent once and must stay that way.

This covers the webhook sender service only, not the dashboard. I make the decisions for this change.
