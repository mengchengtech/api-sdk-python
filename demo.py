import time
import json
import logging
import sys
import threading
import httpx

from kestrel_authentication import GatewayAuthentication

_log_format = '%(asctime)s | %(levelname)s | %(threadName)s | %(module)s | %(message)s'
logging.basicConfig(filename='api-test.log', level='INFO', format=_log_format)
_console = logging.StreamHandler(sys.stdout)
_console.setLevel('INFO')
_console.setFormatter(logging.Formatter(_log_format))
logging.getLogger('').addHandler(_console) 
logger = logging.getLogger(__name__)

base_url = 'http://dev.mctech.vip/api/'
access_id = '3zE1wPSyJWZJe94vLhLo'
secret_key = 'MaEx+H5AceWDkj6yfkVS9Ys/jY4vfmo9RaoAnvSi'
project_api_url = '/org-api/projects?start=%d&limit=%d'
pcr_api_url = '/external/project-construction-record?startId=%d&startVersion=%d&limit=%d&orgId=%d'
max_thread_count = 10
running_thread_count = 0
total_records = 0

lock = threading.RLock()
client = httpx.Client(auth=GatewayAuthentication(access_id, secret_key))
client.base_url = base_url

pcr_file = open('project-construction-record.txt', 'w', encoding = 'utf-8')


def get_projects():
    start_id = 0
    page_size = 200
    projects = []
    while True:
        url = project_api_url % (start_id, page_size)
        response = client.get(url)
        if not response.is_success:
            print(response.text)
            exit(-1)
        arr = response.json()
        for proj in arr:
            project_id = proj['id']
            projects.append(project_id)
        if len(arr) < page_size: break
        start_id = arr[len(arr) - 1]['version']
    return projects


def get_pcr(org_id):
    global total_records
    start_id = 0
    start_version = 0
    page_size = 50
    project_record_count = 0
    while True:
        url = pcr_api_url % (start_id, start_version, page_size, org_id)
        for i in range(3):
            try:
                response = client.get(url)
                content = response.text
                arr = json.loads(content)
                break
            except Exception as e:
                logger.error('call api fail %d time: %s' % (i + 1, url))
                logger.error(e)
                if i == 2: raise e
                time.sleep(10)
        count = len(arr)
        project_record_count += count

        lock.acquire()
        total_records += count
        lock.release()

        write_pcr_file(content)
        logger.info('get %d records on project %d, total get %d' % (project_record_count, org_id, total_records))
        if count < page_size: break
        start_id = arr[len(arr) - 1]['id']
        start_version = arr[len(arr) - 1]['version']

def write_pcr_file(content):
    lock.acquire()
    try:
        pcr_file.write(content)
    except Exception as e:
        logger.error('write pcr file error: %s' % e)
    finally:
        lock.release()

def thread_action(org_id):
    global running_thread_count
    while True:
        lock.acquire()
        if running_thread_count < max_thread_count:
            running_thread_count += 1
            lock.release()
            break
        else:
            lock.release()
            time.sleep(1)
    try:
        get_pcr(org_id)
    except Exception as e:
        logger.error('get_pcr for org %d error:\n%s' % (org_id, e))
    finally:
        lock.acquire()
        running_thread_count -= 1
        lock.release()

def main():
    start = time.time()

    projects = get_projects()
    thread_list = []
    for org_id in projects:
        t = threading.Thread(target=thread_action, args=(org_id,),  name='thread-%d' % org_id)
        t.setDaemon(True)
        thread_list.append(t)
    for t in thread_list:
        t.start()
    # use join cant response ctrl+c
    # for t in thread_list:
    #     t.join()
    while True:
        alive = False
        for t in thread_list:
            alive = alive or t.isAlive()
        if not alive:
            break
        time.sleep(0.1)

    print('finish get %d reocrds in %.2f seconds' % (total_records, time.time() - start))


if __name__ == '__main__':
    main()