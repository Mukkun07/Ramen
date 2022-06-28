import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

# クラスメモ
# 電話番号 class="rstinfo-table__tel-num"
# 住所 class="rstinfo-table__address"
# 営業時間 class="rstinfo-table__subject"


class Tabelog:
    
    """
    食べログスクレイピングクラス
    test_mode=Trueで動作させると、最初のページの3店舗のデータのみを取得できる
    """

    def __init__(self, base_url, test_mode=False, begin_page=1, end_page=1):
        """
        コンストラクタ
        """
        # 変数宣言(メソッド名)
        self.store_id = ''
        self.store_id_num = 0
        self.store_name = ''
        self.store_tel = ''
        self.store_address = '';
        self.columns = ['store_name', 'store_tel', 'store_address']
        self.df = pd.DataFrame(columns=self.columns)
        self.__regexcomp = re.compile(r'\n|\s') # \nは改行、\sは空白

        page_num = begin_page # 店舗一覧ページ番号

        if test_mode:
            list_url = base_url + str(page_num) +  '/?Srt=D&SrtT=rt&sort_mode=1' #食べログの点数ランキングでソートする際に必要な処理
            self.scrape_list(list_url, mode=test_mode)
        else:
            while True:
                list_url = base_url + str(page_num) +  '/?Srt=D&SrtT=rt&sort_mode=1' #食べログの点数ランキングでソートする際に必要な処理
                if self.scrape_list(list_url, mode=test_mode) != True:
                    break

                # INパラメータまでのページ数データを取得する
                if page_num >= end_page:
                    break
                page_num += 1
        return

    def scrape_list(self, list_url, mode):
        """
        店舗一覧ページのパーシング
        """
        r = requests.get(list_url)
        if r.status_code != requests.codes.ok:
            return False

        soup = BeautifulSoup(r.content, 'html.parser')
        soup_a_list = soup.find_all('a', class_='list-rst__rst-name-target') # 店名一覧

        if len(soup_a_list) == 0:
            return False

        if mode:
            for soup_a in soup_a_list[:2]:
                item_url = soup_a.get('href') # 店の個別ページURLを取得
                self.store_id_num += 1
                self.scrape_item(item_url, mode)
        else:
            for soup_a in soup_a_list:
                item_url = soup_a.get('href') # 店の個別ページURLを取得
                self.store_id_num += 1
                self.scrape_item(item_url, mode)

        return True

    def scrape_item(self, item_url, mode):
        """
        個別店舗情報ページのパーシング
        """
        start = time.time()

        r = requests.get(item_url)
        if r.status_code != requests.codes.ok:
            print(f'error:not found{ item_url }')
            return

        soup = BeautifulSoup(r.content, 'html.parser')

        # 店舗名称取得
        # <h2 class="display-name">
        #     <span>
        #         麺匠　竹虎 新宿店
        #     </span>
        # </h2>
        store_name_tag = soup.find('h2', class_='display-name')
        store_name = store_name_tag.span.string
        print('{}→店名：{}'.format(self.store_id_num, store_name.strip()), end='')
        self.store_name = store_name.strip()

        # ラーメン屋、つけ麺屋以外の店舗は除外
        store_head = soup.find('div', class_='rdheader-subinfo') # 店舗情報のヘッダー枠データ取得
        store_head_list = store_head.find_all('dl')
        store_head_list = store_head_list[1].find_all('span')
        #print('ターゲット：', store_head_list[0].text)

        if store_head_list[0].text not in {'ラーメン', 'つけ麺'}:
            print('ラーメンorつけ麺のお店ではないので処理対象外')
            self.store_id_num -= 1
            return

        # 電話番号取得
        # <strong class="rstinfo-table__tel-num">050-5597-9651</strong>
        store_tel_tag = soup.find('strong', class_='rstinfo-table__tel-num')
        store_tel = store_tel_tag.string
        print('  電話番号：{}'.format(store_tel.strip()), end='')
        self.store_tel = store_tel.strip()

        # 住所取得
        # <p class="rstinfo-table__address">
        #   <span><a href="/osaka/" class="listlink">大阪府</a></span>
        #   <span>
        #           <a href="/osaka/C27123/rstLst/" class="listlink">大阪市淀川区</a>
        #           <a href="/osaka/C27123/C79777/rstLst/" class="listlink">塚本</a>2-23-15
        #   </span>
        #   <span></span>
        # </p>
        store_address = soup.find('p', class_='rstinfo-table__address')
        store_address = store_address.get_text()
        print('  住所：{}'.format(store_address), end='')
        self.store_address = store_address.strip()

        # 取得時間
        process_time = time.time() - start
        print('  取得時間：{}'.format(process_time))

        self.make_df()
        return

    def make_df(self):
        self.store_id = str(self.store_id_num).zfill(8) #0パディング
        se = pd.Series([self.store_name, self.store_tel, self.store_address], self.columns) # 行を作成
        self.df = self.df.append(se, self.columns) # データフレームに行を追加
        return

ramen_review = Tabelog(base_url="https://tabelog.com/osaka/rstLst/ramen/",test_mode=False)
#CSV保存
ramen_review.df.to_csv("ramen.csv")

