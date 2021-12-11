# DLfilter
Filter whatever you like on DLsite.

使用DLsite作品標籤的詞向量嵌入來搜尋類似作品的系統。

展示用網頁：https://www.dlfilter.moe/ (可能隨時下線)

理論上類似的作品會有類似的標籤。不同於one-hot編碼，使用詞向量可以輕易分辨類似語意（但字面完全不同，如`癒し`跟`オールハッピー`）的標籤，藉此大幅改善搜尋品質。
緩慢開發中，歡迎建議與PR。

## 功能
* 按標籤相似度搜尋作品
* 按作品類型搜尋
* 可強制包含 / 排除標籤
* 可依照標籤人氣程度進行加權
* 可依作品人氣與販售時間進行加權
* (WIP) 日本語 / English
* (WIP) 自動更新

## 部署您自己的服務
### 需求
- Python 3
- `uvicorn`
- `fastapi`
- `jinja2`
- `beautifulsoup4`
- `pandas`
- `sklearn`
- `sentence_transformers` （如果您希望自己計算標籤的詞向量）



## 執行 `initial.py` 來初始化並更新您的作品資料庫
### 初始化
您也可以直接從 **[這裡](https://drive.google.com/file/d/12hbh-XMiUXKKYsVh38k-8YI8AMm0S0GP/view?usp=sharing)** 下載預先建立好的資料庫（收錄日期：2000-01-01 ~ 2021-09-30）。
**請注意：若您已經下載了現有的資料庫，則不需進行初始化。** 

在此專案資料夾下執行該程式以初始化資料庫。
```
python initial.py -i
```
首次執行時，程式會在 `.../DLfilter/database` 資料夾下建立以下檔案：
- `works_table.json`: 作品的metadata
- `dates_table.json`: 收集各發售日作品的時間
- `genre.json`: 標籤的metadata
- `genre_vec.npy`: 標籤的向量嵌入
- `works.sqlite`: 作品資料庫

檔案的詳細結構請參閱 `.../DLfilter/database/readme.md` 。

程式會詢問您要收集的日期範圍。請依 `YYYY-MM-DD` 格式輸入您希望的一個或一段日期：

`2021-01-01` 或 `2021-01-01 2021-01-31`

程式會收集在這些日期發售的作品。首次執行時，需要下載語言模型以計算各標籤的向量嵌入（預設為`distiluse-base-multilingual-cased-v2`。使用`--model 'model_name'`以更換為[其他支援的語言模型](https://www.sbert.net/docs/pretrained_models.html)）。

### 更新資料庫
使用 `-u` 或 `--update` 引數更新資料庫至前一日的資料：
```
python initial.py -u
```
假設今日為 `2021-03-02` ，而更新前的資料庫只收錄至 `2021-01-31` ，則此指令會新增從 `2021-02-01` 到 `2021-03-01` 期間所發售的作品至資料庫。

### 進階選項
使用 `--help` 引數來檢查可用的選項：
```
python initial.py --help

usage: initial.py [-h] (-i | -s | -u | -d DATE [DATE ...]) 
       [--path PATH] [--model MODEL] [--no_genre] [--raw_only]
       ...
```
#### 更新某日的資料庫
```
python initial.py -d 2021-03-01
```
#### 更新某段日期的資料庫
```
python initial.py -d 2021-01-01 2021-03-01
```

## 啟動服務
```
uvicorn sqlapp:app
```
你應該可以在 http://127.0.0.1:XXXX/ 開啟搜尋網頁。
