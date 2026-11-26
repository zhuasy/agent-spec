Priya Raman here, from the data platform team. Ticket is DATA-77.

Our CSV export endpoint times out a lot for big accounts and customers complain all the time. We want exports to
run as a background job. When the job finishes, email the person who asked for the export a download link. Only
that person can use the link. An export for a small account works fine today and people like that it downloads
straight away, so keep that.

Download links have to expire, but I haven't decided after how long. I also don't know yet what counts as a big
account; ask Tom on the API team, he has the numbers.

I decide on this one.
