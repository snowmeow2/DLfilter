# DLfilter
Filter whatever you like on DLsite.

使用DLsite作品標籤的詞向量嵌入來搜尋類似作品的系統。

展示用網頁：(WIP)

理論上，類似的作品會有類似的標籤。不同於one-hot編碼，使用詞向量可以輕易分辨類似語意（但字面完全不同，如`癒し`跟`オールハッピー`）的標籤，藉此大幅改善搜尋品質。

## 功能
* 按標籤相似度搜尋作品
* 按作品類型搜尋
* 可強制包含 / 排除標籤
* 可依照標籤人氣程度進行加權
* 可依作品人氣與販售時間進行加權
* (WIP) 日本語 / English

## 自己部署服務
### 需求
* numpy
* pandas
* beautifulsoup4
* fastapi
* sklearn
* scipy
* sqlite3
* ...

如果你希望自己計算標籤的詞向量：
* sentence_transformers

### 建構資料庫
```
$.../DLfilter python initial.py --help
$.../DLfilter python initial.py -g --date <START_DATE> <END_DATE> 
```
這會在`.../DLfilter/database/`建立從`<START_DATE>`到`<END_DATE>`發售的作品資料庫及並計算各標籤的向量嵌入。預設以`distiluse-base-multilingual-cased-v2`來計算。`--model <NAME>`以使用其他支援的語言模型。


你也可以直接從[這裡](#)下載預先建立好的資料庫。(WIP)

#### 更新某日的資料庫
```
$.../DLfilter python initial.py --date 2021-10-01
```
#### 更新某段日期的資料庫
```
$.../DLfilter python initial.py --date 2021-10-01 2021-10-31
```
#### 自動更新
WIP

### 啟動服務
```
uvicorn sqlapp:app
```
你應該可以在 http://127.0.0.1:XXXX/ 開啟搜尋網頁。
