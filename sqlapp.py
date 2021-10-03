from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import norm
from module.dlsite import DLsite_catalog, genre_catalog
import numpy as np
import pandas as pd
import time
import sqlite3


def check_genres(genres, target):
    try:
        genre_list = genres.split('+')[:10]
        genre_list = [i for i in genre_list if i in genre_set]
        assert len(genre_list) >= 1
    except:
        msg = "Genres you requested are not accepted by the server. This can caused by incorrect request format or unknown genres."
        raise HTTPException(status_code=400, detail=target+msg)
    return genre_list


def date_function(x):
    return round(240 - 35.5*np.log2(x), 1)


def popular_function(x, sells):
    # const from fitting a Gaussian of whole dataset
    mean = 2.32
    std = 0.66
    sigma = -3/50*x+3
    sells = np.log10(sells+1)

    norm_raw = norm.pdf(sells, mean, std)
    norm_new = norm.pdf(sells, mean+sigma, std)
    return np.where(norm_raw > norm_new, norm_new/norm_raw, 1)


def works_vector(df, weights):  # 0.04s for 2700 items/
    return [sum([weights[j] for j in i])/len(i) for i in df['labels']]


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
lang_set = {'jp', 'en', 'zh-tw', 'zh-cn'}

GG = genre_catalog(target='', path='database/')
genre_set = set(GG.get_genre_list())
print("Catalog loaded.")


@app.get('/', response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/api/genres/{lang}')
def get_genres(lang: str):
    if lang in lang_set:
        return GG.get_class_dict()
    else:
        raise HTTPException(
            status_code=404, detail="The langauge is unavailable.")


@app.get('/api/works')
def get_works(rj_id: str = Query(..., regex=r"^RJ\d\d\d\d\d\d$")):
    db = sqlite3.connect("database/works.sqlite")
    content = pd.read_sql_query(
        "SELECT * FROM maniax WHERE [index] == "+rj_id[2:], db)
    if not len(content):
        raise HTTPException(status_code=404, detail="The work is unavailable.")

    result = content.iloc[0].to_dict()
    result['labels'] = [i for i in result['labels'].split('#') if i]
    result['sells'] = result['sells'].item()
    result['rating'] = result['rating'].item()

    db.close()
    return result


@app.get('/api/similarity')
def get_similar_works(
    genres: str,
    rj_id: Optional[str] = Query(None, regex=r"^RJ\d\d\d\d\d\d$"),
    weight_func: int = Query(1, ge=1, le=4),
    popular: int = Query(50, ge=0, le=100),
    date: int = Query(0, ge=0, le=100),
    all_age: bool = False,
    including_r15: bool = False,
    excluding_low_rate: bool = True,
    excluding_interest: bool = False,
    exclusive_category: bool = False,
    categories: Optional[int] = None,
    included_genres: Optional[str] = None,
    excluded_genres: Optional[str] = None,
):
    # check if id or labels are recorded in DB
    start = time.time()
    db = sqlite3.connect("database/works.sqlite")
    query = "SELECT [index], labels, sells FROM maniax WHERE for_age IN (#QUERY_AGE)"

    # check if is work
    if rj_id and rj_id != "RJ000000":
        data = pd.read_sql_query(
            "SELECT * FROM maniax WHERE [index] == "+rj_id[2:], db)
        query += " AND [index] != " + rj_id[2:]
        if exclusive_category:
            query += " AND category == '" + data['category'].item() + "'"
        else:
            pass

    genre_list = check_genres(genres, target='[on Search form] ')

    # check for df flags
    if all_age and not including_r15:
        query = query.replace("#QUERY_AGE", '1')
    elif all_age and including_r15:
        query = query.replace("#QUERY_AGE", '1, 2')
    elif not all_age and including_r15:
        query = query.replace("#QUERY_AGE", '2, 3')
    elif not all_age and not including_r15:
        query = query.replace("#QUERY_AGE", '3')

    if date and date > 0:
        month = date_function(date)
        query += " AND date > date('now', '-{} months')".format(month)

    # if categories and not exclusive_category:
    #     pass
    # if excluding_interest:
    #     pass

    if excluding_low_rate:
        query += " AND rating >= 4"

    # check if optional labels are recorded in DB
    if included_genres:
        included_genre_list = check_genres(
            included_genres, target='[on Include form] ')
        for i in included_genre_list:
            query += " AND labels LIKE '%#{}#%'".format(i)

    if excluded_genres:
        excluded_genre_list = check_genres(
            excluded_genres, target='[on Exclude form] ')
        for i in excluded_genre_list:
            query += " AND labels NOT LIKE '%#{}#%'".format(i)

    respond = pd.read_sql_query(query, db)
    if not len(respond):
        raise HTTPException(
            status_code=400, detail="DATABASE: I cannot find requested work.")
    respond['labels'] = respond['labels'].str[1:-1].str.split('#').to_list()

    end = time.time()
    print('Time spent in database: {}'.format(end - start))
    start = time.time()

    weights = GG.get_weighting(weight_func)
    query_embedding = sum([weights[i] for i in genre_list])/len(genre_list)
    works_embeddings = works_vector(respond, weights)

    distances = cosine_similarity(
        query_embedding.reshape(1, 512), np.stack(works_embeddings))
    if popular != 50:
        distances *= popular_function(popular, respond['sells'])

    keyworks = [(index, distances[0][index])
                for index in distances.argsort()[0]]
    keyworks.reverse()

    print(rj_id, len(respond))
    work_df = pd.DataFrame(keyworks[:50], columns=['iloc', 'similarity'])
    work_df['index'] = respond.iloc[work_df['iloc']]['index'].values
    work_query = ", ".join(work_df['index'].apply(str))

    result = pd.read_sql_query(
        "SELECT * FROM maniax WHERE [index] IN ({})".format(work_query), db)
    result['labels'] = result['labels'].str[1:-1].str.split('#').to_list()
    result = pd.merge(result, work_df[['index', 'similarity']], on=['index'])
    result = result.sort_values(['similarity'], ascending=False)
    result.index = result['index']
    result = result.to_dict('record')

    end = time.time()
    print('Time spent in computation: {}'.format(end - start))
    db.close()

    return result
