import time, os, re, json, requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/22.0'}

class DLsite_catalog:
    def __init__(self, path=None):
        if path is None:
            self.works_table = {}
            self.dates_table = {}
        else:
            with open(os.path.join(path, 'works_table.json'), 'r') as f:
                self.works_table = json.load(f)
            with open(os.path.join(path, 'dates_table.json'), 'r') as f:
                self.dates_table = json.load(f)

    def get_data_duration(self, date1, date2):
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        duration = (d2-d1).days
        assert duration > 0

        for i in range(duration + 1):
            date = (d1 + timedelta(i)).strftime("%Y-%m-%d")
            self.get_data_one_day(date)
            
    def get_data_one_day(self, date):
        while True:
            table = self._getOutline(date)
            if table is not None:
                break
            else:
                print('{} : 發生錯誤，正在重試'.format(date))
                # flag = input('是否繼續？按 N 跳過')
                # if flag == 'N':
                #     break
                # else:
                #     time.sleep(1)
                break

        if table is not None:
            today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            self.works_table.update(table)
            self.dates_table.update({date: today})
            print('成功取得 {} 的資料（共 {} 筆）'.format(date, len(table)))

    def print_date(self):
        dates = []
        for i in self.dates_table.keys():
            dates.append(datetime.strptime(i, '%Y-%m-%d'))
        dates.sort()
        if len(dates) < 2:
            print(dates)
            return datetime.strptime(i, '%Y-%m-%d')

        temp = dates[0]
        for i, j in zip(dates[:-1], dates[1:]):
            if (j-i).days > 1:
                if i != temp:
                    print('{} = {}'.format(temp.strftime("%Y-%m-%d"), i.strftime("%Y-%m-%d")))
                else: print(i.strftime("%Y-%m-%d"))
                temp = j

        if j != temp:
            print('{} = {}'.format(temp.strftime("%Y-%m-%d"), j.strftime("%Y-%m-%d")))
        else: print(j.strftime("%Y-%m-%d"))
        return j.strftime("%Y-%m-%d")

    def to_dataframe(self):
        df = pd.DataFrame.from_dict(self.works_table).T
        return df
    
    def save_tables(self, path):
        with open(os.path.join(path, 'works_table.json'), 'w') as f:
            json.dump(self.works_table, f)
        with open(os.path.join(path, 'dates_table.json'), 'w') as f:
            json.dump(self.dates_table, f)

    @staticmethod
    def _getOutline(date): #usage: DLsite_catalog._getOutline('2021-09-01')
        url = 'https://www.dlsite.com/maniax/new/=/date/{}'.format(date)
        req = Request(url=url, headers=headers)
        try:
            html = urlopen(req).read()
            soup = BeautifulSoup(html, "html.parser")
            works = soup.find_all(class_='n_worklist_item')

            day_table = {}
            for work in works:
                work_ID = re.search(r'RJ\d\d\d\d\d\d(\d\d)?', work.find('a')['href']).group(0)
                work_dict = {}

                work_dict['date'] = date
                work_dict['category'] = work.find(class_='work_category').text
                work_dict['title'] = work.find(class_='work_name').find('a')['title']
                work_dict['group'] = work.find(class_='maker_name').text.replace('\n', '')
                work_dict['description'] = work.find(class_='work_text').text.replace('\n', '')
                work_dict['for_age'] = work['data-age-category'] #1:all 2:15+ 3:18+
                work_dict['for_sex'] = work['data-sex-category'] #1:male 2:female (no female in 'maniax' scope)

                try:
                    work_dict['labels'] = [tag.text for tag in work.find(class_='search_tag').find_all('a')]
                except Exception:
                    work_dict['labels'] = []
                try:
                    work_dict['sells'] = int(work.find(class_='_dl_count_'+work_ID).text.replace(',', ''))
                except Exception:
                    work_dict['sells'] = 0
                try:
                    work_dict['rating'] = int(work.find(class_='star_rating').get('class')[1][-2:])/10
                except Exception:
                    work_dict['rating'] = -1.0
                try:
                    work_dict['img_url'] = work.find('img')['src'][2:]
                except Exception:
                    work_dict['img_url'] = work.find('img')['data-src'][2:]

                day_table[work_ID] = work_dict

        except Exception as e:
            print(e, work_dict)
            return None

        return day_table

class genre_catalog:
    def __init__(self, target, path=None):
        self.target = target
        self.class_names = {
            1: ['アクション', 'クイズ', 'アドベンチャー', 'ロールプレイング', 'テーブル', 'デジタルノベル', 'シミュレーション', 'タイピング', 'シューティング', 'パズル', 'その他ゲーム'],
            2: ['マンガ', '劇画'],
            3: ['CG・イラスト'],
            4: ['ノベル', '官能小説'],
            5: ['動画'],
            6: ['ボイス・ASMR'],
            7: ['音楽'],
            8: ['ツール/アクセサリ', '画像素材', '音素材'],
            9: ['その他', 'ボイスコミック'],
        }
        if path is None:
            self.table = {}
            self.genre_class_names = set()
            self.embeddings = {}

            self._update_counts()
        else:
            with open(os.path.join(path, 'genre.json'), 'r') as f:
                self.table = json.load(f)
            self.genre_class_names = set([i[1] for i in self.table.values()])
            self.load_embeddings(path)

    def _update_counts(self):
        url = 'https://www.dlsite.com/{}/genre/list'.format(self.target)

        while True:
            try:
                req = Request(url=url, headers=headers)
                html = urlopen(req).read()
                soup = BeautifulSoup(html, "html.parser")
                for genre_class in soup.find_all('h2', class_='versatility_linklist_title'):
                    genre_class_name = genre_class.text
                    genre_ul = genre_class.find_next_sibling('ul')
                    for genre in genre_ul.find_all('li'):
                        genre_a = genre.find('a')
                        # https://www.dlsite.com/home/works/genre/=/genre/{genre_id}
                        genre_id = genre_a['href'][48:]
                        genre_name_count = genre_a.text
                        m = re.search(r'(.+)\((.+)\)', genre_name_count)
                        genre_name = m.group(1)
                        genre_count = m.group(2).replace(',', '')
                        self.table[genre_id] = [genre_name, genre_class_name, int(genre_count)]
                break
            except Exception as e:
                print(e)
                time.sleep(1)

    def save_genre(self, path):
        with open(os.path.join(path, 'genre.json'), 'w') as f:
            json.dump(self.table, f)

    def concat_genre(self, tables):
        for i in tables:
            assert self.table != i.table
            for k, v in i.table.items():
                if k in self.table:
                    self.table[k][2] += v[2]
                else:
                    self.table[k] = v
    
    def get_genre_list(self):
        return [i[0] for i in self.table.values()]

    def get_genre_count_dict(self):
        return {i[0]:i[2] for i in self.table.values()}

    def get_class_dict(self):
        class_dict = {}
        for k, v in self.table.items():
            if v[1] not in class_dict:
                class_dict[v[1]] = [{v[0]:[k, v[2]]}]
            else:
                class_dict[v[1]].append({v[0]:[k, v[2]]})
        return class_dict
    
    def load_embeddings(self, path):
        self.embeddings = np.load(os.path.join(path, 'genre_vec.npy'), allow_pickle=True)

    def compute_embeddings(self, model, path):
        genre_list = self.get_genre_list()
        for i in genre_list:
            if '/' in i:
                temp_i = i.split('/')
                temp_i = sum(model.encode(temp_i))/len(temp_i)
                self.embeddings[i] = temp_i
            else:
                self.embeddings[i] = model.encode([i])[0]

        # self.embeddings = {k:v for k,v in zip(genre_list, model.encode(genre_list))}
        np.save(os.path.join(path, 'genre_vec.npy'), self.embeddings)

    def get_weighting(self, weight_func='r_logistic'):
        if self.target == '':
            count = self.get_genre_count_dict()
            return {k: self.embeddings.item()[k]*self.weight(v, weight_func) for k,v in count.items()}
        else:
            print('Error!')

    @staticmethod
    def weight(x, weight_func):
        x = np.log10(int(x))

        if weight_func == 'r_logistic' or weight_func == 1:
            y = -1/(1+np.exp((-x+4)*4)) + 1
        elif weight_func == 'logistic' or weight_func == 2:
            y = 1/(1+np.exp((-x+3.5)*4))
        elif weight_func == 'gaussian' or weight_func == 3:
            y = np.exp(-(x-3.75)**2/(2*0.7**2))
        elif weight_func == 'linear' or weight_func == 4:
            y = 1

        return y

