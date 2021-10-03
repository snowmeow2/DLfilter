import os, sys
from module.dlsite import DLsite_catalog, genre_catalog

model_name = 'distiluse-base-multilingual-cased-v2'
path = r'E:\DLsite\DLfilter\database'
tags = False

# 若沒有既存目錄則新建之
if os.path.isfile(path+r'\works_table.json'):
    DL = DLsite_catalog(path=path)
    print('已經在 {} 載入目錄。'.format(path))
    if len(sys.argv) == 1:
        print('顯示目前已收錄的日期：')
        DL.print_date()
        exit()
else:
    DL = DLsite_catalog()
    print('沒有發現現存目錄。')
    if len(sys.argv) == 1:
        exit()

if tags:
    # 標籤目錄每次都會覆蓋更新
    GG = genre_catalog(target='maniax')
    GH = genre_catalog(target='home')
    GL = genre_catalog(target='girls-pro')

    # 合併計算後存檔
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    GG.concat_genre([GH, GL])
    GG.compute_embeddings(model=model, path=path)
    GG.save_genre(path=path)
    print('標籤目錄已經存檔在 {} 。'.format(path))

if len(sys.argv) == 2: # usage: get_data_one_day('2021-08-01')
    DL.get_data_one_day(sys.argv[1])
    DL.save_tables(path)
    print('作品目錄已經存檔在 {} 。'.format(path))
elif len(sys.argv) == 3: # usage: get_data_duration('2021-08-01','2021-08-31')
    DL.get_data_duration(sys.argv[1], sys.argv[2])
    DL.save_tables(path)
    print('作品目錄已經存檔在 {} 。'.format(path))
else:
    print('引數錯誤！')