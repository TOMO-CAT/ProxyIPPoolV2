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