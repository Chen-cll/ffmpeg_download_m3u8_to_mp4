import os
import time
import m3u8
import ffmpy
import tempfile
import requests
from glob import iglob
from urllib.parse import urljoin
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


@dataclass
class DownLoad_M3U8(object):
    m3u8_url: str
    file_name: str
    ts_max = 0

    def __post_init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36', }
        self.threadpool = ThreadPoolExecutor(max_workers=10)
        if not self.file_name:
            self.file_name = 'new.mp4'

    def get_ts_url(self):
        m3u8_obj = m3u8.load(self.m3u8_url)
        base_uri = m3u8_obj.base_uri
        for seg in m3u8_obj.segments:
            yield urljoin(base_uri, seg.uri)

    def download_single_ts(self, urlinfo):
        url, ts_name = urlinfo
        res = requests.get(url, headers=self.headers)
        with open(ts_name, 'wb') as fp:
            fp.write(res.content)

    def download_all_ts(self):
        ts_urls = self.get_ts_url()
        for index, ts_url in enumerate(ts_urls):
            self.ts_max += 1
            self.threadpool.submit(self.download_single_ts, [ts_url, f'{index}.ts'])
        self.threadpool.shutdown()

    def run(self):
        self.download_all_ts()
        temp_dir = tempfile.mktemp()
        os.mkdir(temp_dir)
        concat_file = os.path.join(temp_dir, 'concat_list.txt')

        with open(concat_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join([rf"file '{os.getcwd()}\{x}.ts'" for x in range(self.ts_max)]))

        ff = ffmpy.FFmpeg(
            executable=f'{os.getcwd()}//ffmpeg//bin//ffmpeg.exe',
            global_options=['-f', 'concat', '-safe', '0'],
            inputs={concat_file: None},
            outputs={self.file_name: ['-c', 'copy']}
        )
        ff.run()

        for ts in iglob('*.ts'):
            os.remove(ts)


def RUN(url: str, name: str):
    PATH = './videos'
    if not os.path.exists(PATH):
        os.mkdir(PATH)

    if 'hls' not in url:
        url = url.split('/index.m3u8')[0] + '/1000kb/hls/index.m3u8'

    m3u8_url = url
    file_name = PATH + '/' + name + '.mp4'
    start = time.time()
    M3U8 = DownLoad_M3U8(m3u8_url, file_name)
    M3U8.run()
    end = time.time()
    print(f'耗时:{end - start:.0f}秒')
    print(f'{name}下载成功！')


__all__ = ['RUN']

if __name__ == '__main__':
    url = input('输入m3u8链接：')
    name = input('输入视频文件名：')
    RUN(url, name)
