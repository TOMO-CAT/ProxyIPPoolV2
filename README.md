## 工程目录
```
├── db  //提供IP池数据库增删查改功能  
├── progress_bar  //提供循环进度条展示功能  
├── README.md  //帮助文档  
├── proxy_getter  
│   ├── get_proxy.py  //从xici获取爬虫代理IP到数据库  
│   ├── random_headers.py  //获取随机请求头  
├── main  //主函数
```

## 主要思路

1. 通过`request.get`拿到`http response`

```python
response = requests.get(url = url, headers = headers, proxies = proxies, timeout = 5)
"""
<!DOCTYPE html>
<html>
<head>
  <title>国内高匿免费HTTP代理IP__第10页国内高匿</title>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <meta name="Description" content="国内高匿免费HTTP代理" />
  <meta name="Keywords" content="国内高匿,免费高匿代理,免费匿名代理,隐藏IP" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
  　　<meta name="applicable-device"content="pc,mobile">
  <link rel="stylesheet" media="screen" href="//fs.xicidaili.com/assets/application-9cf10a41b67e112fe8dd709caf886c0556b7939174952800b56a22c7591c7d40.css" />
  <meta name="csrf-param" content="authenticity_token" />
<meta name="csrf-token" content="IM54DJ4+2z15dlURDgc9LBxoLCyCUoiSVXDMCFXQIeP+ZCBHDmOL2/4IuwRzuVRkRfkS3+D2JBY/85slCEN3/g==" />
</head>
<body>
  <div id="wrapper">
    <div id="header">
      <h1>国内高匿代理IP</h1>
      <img alt="免费http代理" id="logo" src="//fs.xicidaili.com/images/logo.png" />
      <div id="myurl">
        XiciDaili.com
      </div>
...
...
    </script>
    
  </div>
</body>
</html>
```

2. 通过`BeautifulSoup`得到`<td>`中的数据

```python
soup = BeautifulSoup(html, "html.parser")
tds = soup.find_all("td")
```

3. 利用正则匹配拿到代理IP数据
```python
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
```      

4. IP有效性验证
```python
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
```

5. 将验证通过的IP存储到redis中
```python
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
```

6. 美化
多个代理IP写入redis中的循环耗时较长，又不想打印太多日志。利用`print`中的`\r`和`end`实现了进度条展示小工具。
```python
"""
sign_progress_bar.py
function: use number sign to display the overall progress in circulation
"""
import time

class DisplayProgressBySign(object):
    def __init__(self, length=50, decimal=2):
        self.decimal = decimal
        self.length = length # total length of the progress bar

    # __call__ enable use to use a Class like a Function
    def __call__(self, running_task_index, total_task_num):
        percentage = round(running_task_index/total_task_num, self.decimal)
        sign_cnt = int(self.length * percentage)
        progress_bar = self.gen_progress_bar(sign_cnt)
        overall_progress_percentage = str(int(percentage*100)) + "%"

        result = "\r%s %s" % (progress_bar, overall_progress_percentage)
        return result

    def gen_progress_bar(self, sign_cnt):
        """
        display progress bar: like [##########                                        ]
        """
        str_sign = "#" * sign_cnt
        str_space = " " * (self.length - sign_cnt)
        return '[%s%s]' % (str_sign, str_space)

if __name__ == "__main__":
    print("Test: show how to use sign_progress_bar")
    progress = DisplayProgressBySign()
    total_task_num = 1000
    for i in range(total_task_num):
        # use end = "" to avoid "\n" in the end of the line
        print(progress(i+1, total_task_num), end = '')
        time.sleep(0.01) # set refresh time of the progress bar
```

## 日志样例
```
Info: get 99 ip, the effective rate is 99.00%
Info: we already crawl 46 url, overall progress is 9.20%
Info: Now parse the 47 url，the overall progress is 47/500
Info: the progress bar of save ip into redis
[########################                          ] 49%Warning: request.get() failed
[##################################################] 100%

Info: get 99 ip, the effective rate is 99.00%
Info: we already crawl 47 url, overall progress is 9.40%
Info: Now parse the 48 url，the overall progress is 48/500
Info: the progress bar of save ip into redis
[######                                            ] 12%Warning: request.get() failed
[########                                          ] 17%Warning: request.get() failed
[################################################  ] 96%Warning: request.get() failed
[##################################################] 100%

Info: get 97 ip, the effective rate is 97.00%
Info: we already crawl 48 url, overall progress is 9.60%
Info: Now parse the 49 url，the overall progress is 49/500
Info: the progress bar of save ip into redis
[##################################################] 100%

Info: get 100 ip, the effective rate is 100.00%
Info: we already crawl 49 url, overall progress is 9.80%
Info: Now parse the 50 url，the overall progress is 50/500
Info: the progress bar of save ip into redis
[##############################################    ] 92%Warning: request.get() failed
[##################################################] 100%

Info: get 99 ip, the effective rate is 99.00%
Info: we already crawl 50 url, overall progress is 10.00%
Info: Now parse the 51 url，the overall progress is 51/500
Info: the progress bar of save ip into redis
[##################################################] 100%
```