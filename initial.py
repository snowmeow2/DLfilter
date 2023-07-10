import os
import argparse
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from module.dlsite import DLsite_catalog, genre_catalog

parser = argparse.ArgumentParser(
    description="Initial and update work databases.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-i", "--init", action="store_true",
                   help="Initialize the database. Equivalent to --show if the database has existed.")
group.add_argument("-s", "--show", action="store_true",
                   help="Print the existing dates in database.")
group.add_argument("-u", "--update", action="store_true",
                   help="Update the database to a day before current date.")
group.add_argument("-d", "--date", nargs="+",
                   help="Set the start date and end date for crawling the website into database. Only crawl one day if one argument is provided.")
parser.add_argument("--path", default='database', help="The path of database.")
parser.add_argument("--model", default='distiluse-base-multilingual-cased-v2',
                    help="The name of language model.")
parser.add_argument("--no_genre", action="store_true",
                    help="[Debug] Avoid updating genre data. Only available for --date and --update.")
parser.add_argument("--raw_only", action="store_true",
                    help="[Debug] Avoid exporting SQLite database. Only available for --date and --update.")
args = parser.parse_args()

if args.date:
    _ = datetime.strptime(args.date[0], '%Y-%m-%d')
    assert _ < datetime.today() and _ >= datetime(2000, 1, 1)
    if len(args.date) == 2:
        _2 = datetime.strptime(args.date[1], '%Y-%m-%d')
        assert _2 < datetime.today() and _2 >= datetime(2000, 1, 1) and _2 > _

# Find for the catalogue
if os.path.isfile(os.path.join(args.path, 'works_table.json')):
    DL = DLsite_catalog(path=args.path)
    print('Loaded catalogue in {}.'.format(args.path))
    print('Dates recorded in the catalogue: ')
    DL.print_date()
    # Do DATE or UPDATE if found
    if args.show or args.init:
        exit()
else:
    print('No existing catalogue in {}.'.format(args.path))
    # DO DATE or INIT if not found
    if args.show or args.update:
        exit()

    flag = input(
        'Create a new one?  (y/n)\n'.format(args.path))
    if flag.lower() == 'y':
        DL = DLsite_catalog()
    else:
        exit()

if args.init:
    print('Mode: init')
    while True:
        try:
            d1 = input(
                'Please input the start date you want: YYYY-MM-DD:\n')
            _ = datetime.strptime(d1, '%Y-%m-%d')
            assert _ < datetime.today() and _ >= datetime(2000, 1, 1)
            d2 = input(
                'Please input the end date you want (optional): YYYY-MM-DD:\n')
            if d2 != '':
                _2 = datetime.strptime(d2, '%Y-%m-%d')
                assert _2 < datetime.today() and _2 >= datetime(2000, 1, 1) and _2 > _
            break
        except Exception:
            print('Error: Date format incorrect, or out of available range.')
            pass

    if d2 == '':
        DL.get_data_one_day(d1)
    else:
        DL.get_data_duration(d1, d2)
    DL.save_tables(args.path)
    print('Save work catalogue in {}.'.format(args.path))

elif args.update:
    print('Mode: update')
    d1 = DL.print_date()
    d2 = datetime.today()-timedelta(1)
    if datetime.strptime(d1, '%Y-%m-%d') >= d2:
        print('Error: The database is up to date.')
        exit()
    d2 = d2.strftime('%Y-%m-%d')
    print('Update data from {} to {}'.format(d1, d2))
    DL.get_data_duration(d1, d2)
    DL.save_tables(args.path)
    print('Save work catalogue in {}.'.format(args.path))

elif args.date:
    print('Mode: date')
    if len(args.date) == 1:
        # usage: get_data_one_day('2021-08-01')
        DL.get_data_one_day(args.date[0])
    elif len(args.date) == 2:
        # usage: get_data_duration('2021-08-01','2021-08-31')
        DL.get_data_duration(args.date[0], args.date[1])

    DL.save_tables(args.path)
    print('Save work catalogue in {}.'.format(args.path))

if not args.no_genre or args.init:
    # will override the genre catalogue if not init
    GG = genre_catalog(target='maniax')
    GH = genre_catalog(target='home')
    GL = genre_catalog(target='girls-pro')
    print('Downloaded genre catalogues.')
    print('Loading language model... it may take time to download if this is the first time you run.')

    # concat and save
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)
    GG.concat_genre([GH, GL])
    GG.compute_embeddings(model=model, path=args.path)
    GG.save_genre(path=args.path)
    print('Save genre catalogue in {}.'.format(args.path))

if not args.raw_only or args.init:
    df = DL.to_dataframe()
    genre_set = set(GG.get_genre_list())

    df['labels'] = [[j for j in i if j in genre_set] for i in df['labels']]
    df = df[(df['labels'].astype(bool))]

    df['sells'] = df['sells'].astype(int)
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    df['rating'] = df['rating'].astype(float)
    df['for_age'] = df['for_age'].astype(int)
    df['for_sex'] = df['for_sex'].astype(int)
    df['img_url'] = df['img_url'].str.contains(r'RJ\d\d\d\d\d\d(\d\d)?_')
    df['labels'] = "#" + df['labels'].str.join('#') + "#"
    df.index = pd.to_numeric(df.index.str.replace('RJ', ''))

    db = sqlite3.connect(os.path.join(args.path, 'works.sqlite'))
    df.to_sql("maniax", db, if_exists="replace")
    db.close()
