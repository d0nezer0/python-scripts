from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from flask import jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from app.ocr.pipeline.medical import ocr_by_url
from app.ocr.pipeline.ocr_subtitle import OcrSubtitlePipline

app = Flask(__name__)


def scheduled_task():
    print("定时任务执行中...")


def job_function():
    print("每5分钟执行的任务...")


# 创建后台调度器
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_task, trigger="interval", seconds=1000)
scheduler.add_job(job_function, CronTrigger.from_crontab('*/50 * * * *'))
scheduler.start()

# 确保在应用退出时关闭调度器
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/data')
def get_data():
    data = {"key": "value"}
    return jsonify(data)


@app.route('/ocr/?url=<url>')
def get_img_ocr(url):
    preds = ocr_by_url(url)
    return preds




if __name__ == '__main__':
    app.run(debug=True)
    # 可以在这里控制需要跑哪些功能， 甚至加上定时功能；

