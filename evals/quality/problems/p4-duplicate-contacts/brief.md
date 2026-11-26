Ticket #4412, from Marisol (sales ops):

> The contact export has duplicates again. Jane Okafor is in there three times - jane.okafor@northwind.example, Jane.Okafor@Northwind.example, and one that looks identical to the first but I think has a space in front of it. The mail-merge tool then emails her three times and she has complained. Can you just dedupe on name? That would fix it.

Notes from Tom (dev) when he triaged it, pasted from the ticket comments:

- do NOT dedupe on name. We have at least two different John Smiths at different companies and they'd get glued together. The email is the key, it's just being compared too literally.
- addresses should be compared ignoring upper/lower case and any spaces around them. The export should write the cleaned-up lowercase address.
- careful: billing+jane@northwind.example style addresses are real separate inboxes for some customers. Don't get clever and strip those.
- rows with no email at all (import junk) stay as separate rows like today. Don't lose them, sales goes through them by hand.
- which row wins when rows merge doesn't change: first one in the file, later ones only fill in blanks.
- I haven't looked at whether the problem is in the merge or in the csv reading. Marisol runs it as `python3 -m contacts in.csv out.csv`.
