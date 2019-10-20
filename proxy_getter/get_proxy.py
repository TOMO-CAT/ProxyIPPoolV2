import requests
from bs4 import BeautifulSoup
import re
from proxy_getter.random_headers import RandomFakeHeaders
from db.redis import IPPool
from progress_bar.sign_progress_bar import DisplayProgressBySign # show progress bar in a circulation
import time

class GetProxy(object):

    def __init__(self):
        self.__URL_PREFIX = "https://www.xicidaili.com/nn/%d"
        self.__TEST_URL = "http://httpbin.org/get"

    @staticmethod
    def get_html(url, headers, proxies = False, retry_times = 3):
        response = None

        for cnt in range(retry_times):
            # noinspection PyBroadException
            try:
                if not proxies:
                    response = requests.get(url = url, headers = headers, timeout = 5)
                else:
                    response = requests.get(url = url, headers = headers, proxies = proxies, timeout = 5)
                break
            except Exception:
                continue

        if response is None:
            print("Warning: get response failed, please check the url: %s", url)

        # noinspection PyBroadException
        try:
            html = response.content.decode("utf-8")
            return html
        except:
            print("Warning: decode response failed")
            return None

    @staticmethod
    def parse_html2ip_list(html):

        ip_list = []
        soup = BeautifulSoup(html, "html.parser")
        tds = soup.find_all("td")

        for index, td in enumerate(tds):
            # use regex to match proxy_ip in tds
            if re.match(r"^\d+\.\d+\.\d+\.\d+$",
                        re.sub(r"\s+|\n+|\t+", "", td.text)):
                # the elements appear in sequence on the website, like "163.204.240.21, 9999, 广东, 高匿, HTTP"
                # each represents proxy_ip, port, province, type and protocol
                item = list()
                item.append(re.sub(r"\s+|\n+|\t+", "", td.text))
                item.append(re.sub(r"\s+|\n+|\t+", "", tds[index + 1].text))
                item.append(re.sub(r"\s+|\n+|\t+", "", tds[index + 2].text))
                item.append(re.sub(r"\s+|\n+|\t+", "", tds[index + 3].text))
                item.append(re.sub(r"\s+|\n+|\t+", "", tds[index + 4].text))
                ip_list.append(item)
        return ip_list

    #chenck  the validity of ip in ip_list
    def ip_validation(self, raw_ip):
        validation_flag = True

        # construct parameter
        ip_with_port = str(raw_ip[0]) + ":" + str(raw_ip[1])
        # print(ip_with_port)
        proxies = {"https" : "https://" + ip_with_port}
        # print(proxies)
        headers = RandomFakeHeaders().random_headers_for_validation()
        # print(headers)

        # check
        # noinspection PyBroadException
        try:
            response = requests.get(url = self.__TEST_URL,
                                    headers = headers,
                                    proxies = proxies,
                                    timeout = 5)
        except:
            print("Warning: request.get() failed")
            return False

        if response.status_code != 200:
            validation_flag = False

        return validation_flag

    def save_ip2redis(self, ip_list):
        ip_cnt = len(ip_list)
        cnt = 0 # calculate the ip number we put into redis
        print("Info: the progress bar of save ip into redis")
        for index, ip in enumerate(ip_list):
            progress_bar = DisplayProgressBySign()
            print(progress_bar(index+1 ,ip_cnt), end = "")

            # test validation
            if self.ip_validation(ip) and ip[3] == '高匿':
                IPPool().insert_ip(ip)
                cnt += 1
        print("\n")
        print("Info: get {} ip, the effective rate is {:.2f}%".format(
            cnt, cnt/ip_cnt * 100
        ))

    def gen_proxy_ip_pool(self, start_page=0, end_page=1):
        urls = [self.__URL_PREFIX % (index+1) for index in range(start_page, end_page)]
        url_cnt = len(urls)

        for index, url in enumerate(urls):
            print(u"Info: Now parse the {} url，the overall progress is {}/{}".format(index+1, index+1, url_cnt))

            headers = RandomFakeHeaders().random_headers_for_xici()
            ip = IPPool().get_random_key()
            proxies = {"http": "http://" + ip}

            response = self.get_html(url = url, headers = headers, proxies = proxies)
            ip_list = self.parse_html2ip_list(response)
            if len(ip_list) == 0:
                print("Warning: the ip_list is empty, please check the url:", url)
                return None
            self.save_ip2redis(ip_list)
            print("Info: we already crawl {} url, overall progress is {:.2f}%".format(
                index + 1, (index + 1)/url_cnt * 100
            ))
            print("Info: sleep for 30s...")
            time.sleep(30)

if __name__ == "__main__":
    print("Test: get the html of xici:")
    res = GetProxy().get_html("https://www.xicidaili.com/nn/7",
                                    headers = RandomFakeHeaders().random_headers_for_xici())
    # print(res)

    print("Test: parse the html to get ip list:")
    ips = GetProxy().parse_html2ip_list(res)
    ip = ips[5]
    print(ip)

    print("Test: test the ip validation test:")
    val_flag = GetProxy().ip_validation(ip)
    if val_flag:
        print("Info: ip is available")
    else:
        print("Error: please check other ip or modify the func defination")

    print("Test: test the save_ip2redis func:")
    GetProxy().save_ip2redis(ips)
    print("Test: All pass")

    print("Test: test the gen_proxy_ip_pool:")
