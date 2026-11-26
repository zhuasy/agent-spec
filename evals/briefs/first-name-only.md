hey, can you spec out envcheck for me? it's a cli that validates a .env file against a json schema file before a
deploy. services keep crashing at startup because someone forgot a variable or typo'd a type.

what i want: report all the errors in one run, not just the first. never print the value of a secret. exit non-zero
when the file is bad. a --strict flag that rejects keys the schema doesn't know. json output for CI.

i'm the decider on this one.

- Sam
