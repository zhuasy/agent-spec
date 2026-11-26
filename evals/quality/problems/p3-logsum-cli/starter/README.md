# ops-scripts

Small single-file scripts we copy onto the edge boxes. Rules of the house:

- one file per script at the top of the repo, Python standard library only
- each script has `main(argv)` returning the exit code, and ends with
  `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`
- results on stdout, complaints on stderr

Scripts:

- `linecount.py FILE...` - lines per file

Tests: `python3 -m unittest`
