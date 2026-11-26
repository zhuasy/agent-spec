import sys

from .export import export_csv, read_csv
from .merge import merge_contacts


def main(argv):
    if len(argv) != 2:
        print("usage: python3 -m contacts IN.csv OUT.csv", file=sys.stderr)
        return 2
    records = merge_contacts(read_csv(argv[0]))
    export_csv(records, argv[1])
    print("wrote %d contacts" % len(records))
    return 0


sys.exit(main(sys.argv[1:]))
