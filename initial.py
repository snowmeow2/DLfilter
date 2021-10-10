import os
import argparse
import sqlite3
import pandas as pd
from module.dlsite import DLsite_catalog, genre_catalog

parser = argparse.ArgumentParser(
    description="Initial and update work databases.")
parser.add_argument("--path", default='database', help="The path of database.")
parser.add_argument("--model", default='distiluse-base-multilingual-cased-v2',
                    help="The name of language model.")
parser.add_argument("-d", "--date", nargs="+",
                    help="The start date and end dates for crawling the website. Only crawl one day if one argument is provided.")
parser.add_argument("-s", "--show", action="store_true",
                    help="Print the existing dates in catalogue if no argument is provided.")
parser.add_argument("-g", "--genre", action="store_true",
                    help="Get and update genre data.")
parser.add_argument("--raw_only", action="store_true",
                    help="Avoid exporting SQLite database.")
args = parser.parse_args()

# Create a new catalogue if not found
if os.path.isfile(os.path.join(args.path, 'works_table.json')):
    DL = DLsite_catalog(path=args.path)
    print('Loaded catalogue in {}.'.format(args.path))
    if args.show:
        print('Dates recorded in the catalogue: ')
        DL.print_date()
        exit()
else:
    flag = input(
        'No existing catalogue in {}. Create a new one?  (y/n)'.format(args.path))
    if flag.lower() == 'y':
        DL = DLsite_catalog()
    else:
        exit()

if args.genre:
    # will override the genre catalogue every time executed
    GG = genre_catalog(target='maniax')
    GH = genre_catalog(target='home')
    GL = genre_catalog(target='girls-pro')

    # concat and save
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)
    GG.concat_genre([GH, GL])
    GG.compute_embeddings(model=model, path=args.path)
    GG.save_genre(path=args.path)
    print('Save genre catalogue in {}.'.format(args.path))

if args.date:
    if len(args.date) == 1:
        # usage: get_data_one_day('2021-08-01')
        DL.get_data_one_day(args.date[0])
    elif len(args.date) == 2:
        # usage: get_data_duration('2021-08-01','2021-08-31')
        DL.get_data_duration(args.date[0], args.date[1])

    DL.save_tables(args.path)
    print('Save work catalogue in {}.'.format(args.path))

if not args.raw_only:
    df = DL.to_dataframe()
    genre_set = set(GG.get_genre_list())

    df['labels'] = [[j for j in i if j in genre_set] for i in df['labels']]
    df = df[(df['labels'].astype(bool))]

    df['sells'] = df['sells'].astype(int)
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    df['rating'] = df['rating'].astype(float)
    df['for_age'] = df['for_age'].astype(int)
    df['for_sex'] = df['for_sex'].astype(int)
    df['img_url'] = df['img_url'].str.contains(r'RJ\d\d\d\d\d\d_')
    df['labels'] = "#" + df['labels'].str.join('#') + "#"
    df.index = pd.to_numeric(df.index.str.replace('RJ', ''))

    db = sqlite3.connect(os.path.join(args.path, 'works.sqlite'))
    df.to_sql("maniax", db, if_exists="append")
    db.close()