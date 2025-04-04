import os,logging,asyncio,pytz,json,threading
from telethon import TelegramClient, events, Button
from fbAuto import fbAutoFirefox
from dotenv import load_dotenv
from datetime import datetime
from strings import direct_reply, strings
from database import DB

load_dotenv(override=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Colombo'))
bot = TelegramClient('bot', os.environ['API_ID'], os.environ['API_HASH']).start(bot_token=os.environ['BOT_TOKEN'])
database = DB()
USER_LIST = [] if os.getenv('USER_LIST') is None else os.environ['USER_LIST'].split(',')

async def wait_until_next_minute():
    now = datetime.now(TIMEZONE)
    next_minute = now.replace(
        hour=(now.hour + 1) % 24 if now.minute == 59 else now.hour,
        minute=(now.minute + 1) % 60,
        second=0,
        microsecond=0
    )
    seconds_to_next_minute = (next_minute-now).total_seconds()
    await asyncio.sleep(seconds_to_next_minute)
async def cron():
    while True:
        await wait_until_next_minute()
        curr_min = datetime.now(TIMEZONE).strftime('%H:%M')
        print('executing cron', curr_min)
        jobs = [job for job in database.get_jobs_for_current_minute()]
        if len(jobs) == 0:
            continue
        print(f"--------------- Jobs starting for {curr_min}")
        asyncio.create_task(execute_jobs(jobs, curr_min))
async def execute_jobs(jobs, curr_min):
    fb_auto = fbAutoFirefox()
    await asyncio.to_thread(fb_auto.shareToList, jobs, os.environ['COOKIES_FILE'])
    fb_auto.close()
    print(f"--------------- Jobs finished for {curr_min}")
def yesno(x,page,job_id):
    return [
        [Button.inline("Yes", '{{"page":"{}","press":"yes{}","id":{}}}'.format(page,x,job_id))],
        [Button.inline("No", '{{"page":"{}","press":"no{}","id":{}}}'.format(page,x,job_id))]
    ]

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def handler(event):
    if len(USER_LIST)>0 and str(event.sender_id) not in USER_LIST:
        return
    user = database.get_user(event.chat_id)
    if user is None:
        sender = await event.get_sender()
        user = {'first_name': sender.first_name, 'last_name': sender.last_name}
        database.set_user(event.chat_id, user)
    next = user.get('next')
    keyboard = []
    if event.message.text in direct_reply:
        text = direct_reply[event.message.text]
    elif event.message.text == '/time':
        text = datetime.now(TIMEZONE).strftime('Server Time: `%Y-%m-%d %H:%M:%S`')
    elif event.message.text == '/cancel':
        user = {'first_name': user['first_name'], 'last_name': user['last_name']}
        text = strings['cancelled']
    elif event.message.text == '/new':
        user['next'] = 'post_link'
        text = strings['ask_post_link']
    elif event.message.text.startswith('/cron'):
        cron = event.message.text.split(' ', 2)
        text = strings['cron_help']
        if len(cron) == 3:
            text = strings['cron_invalid']
            if database.add_cron(cron[1], cron[2]):
                text = strings['cron_added']
    elif event.message.text.startswith('/jobs'):
        text = strings['active_jobs']
        keyboard = [
            [Button.inline(f"Job: {job['id']}", json.dumps({'page': 'job', 'press': 'job', 'id': job['id']}))]
            for job in database.get_active_jobs()
        ]
        if keyboard == []:
            text = strings['no_jobs']
    elif next == 'post_link':
        user['new'] = {'post_link': event.message.text}
        user['next'] = 'group_list'
        text = strings['ask_group_list']
    elif next == 'group_list':
        group_list = event.message.text
        if event.message.file and event.message.file.size < 1024:
            file = await event.message.download_media()
            with open(file, 'r') as f:
                group_list = f.read()
            os.remove(file)
        try:
            group_list = json.loads(group_list)
            if 'edit' in user and user['edit']['target'] == 'group_list':
                text = strings['job_invalid']
                if database.edit_job(user['edit']['id'], 'group_list', json.dumps(group_list)):
                    text = strings['edit_success']
                    keyboard = [
                        [Button.inline(strings['back'], json.dumps({'page': 'job', 'press': 'job', 'id': user['edit']['id']}))]
                    ]
                    del user['edit']
                    del user['next']
            else:
                user['new']['group_list'] = json.dumps(group_list)
                text = strings['ask_share_text']
                user['next'] = 'share_text'
        except json.JSONDecodeError:
            text = strings['invalid_group_list']
    elif next == 'share_text':
        if 'edit' in user and user['edit']['target'] == 'share_text':
            text = strings['job_invalid']
            if database.edit_job(user['edit']['id'], 'share_text', event.message.text):
                text = strings['edit_success']
                keyboard = [
                    [Button.inline(strings['back'], json.dumps({'page': 'job', 'press': 'job', 'id': user['edit']['id']}))]
                ]
                del user['edit']
                del user['next']
        else:
            user['new']['share_text'] = event.message.text
            job_id = database.add_job(user['new'])
            del user['new']
            del user['next']
            text = f'Job added\nJob ID: `{job_id}`'
    else:
        text = strings['unknown_command']
    database.set_user(event.chat_id, user)
    await event.respond(text, buttons=None if keyboard==[] else keyboard, link_preview=False)

@bot.on(events.CallbackQuery())
async def handler(event):
    if len(USER_LIST)>0 and str(event.sender_id) not in USER_LIST:
        return
    try:
        data = json.loads(event.data.decode())
    except json.JSONDecodeError:
        return
    user = database.get_user(event.chat_id)
    if user is None:
        sender = await event.get_sender()
        user = {'first_name': sender.first_name, 'last_name': sender.last_name}
        database.set_user(event.chat_id, user)
    keyboard = []
    if data['page'] == 'job':
        job = database.get_job(data['id'])
        if job is None:
            await event.answer(strings['job_invalid'])
            return
        if data['press'] == 'job' or data['press'].startswith(('nodel_cron','nodel_job')):
            text = f"Job ID: {job['id']}\nPost Link: {job['post_link']}\nCron Expression: `{job['cron_expression']}`"
            keyboard = [
                [Button.inline(strings['group_list'], json.dumps({'page': data['page'], 'press': 'group_list', 'id': job['id']}))],
                [Button.inline(strings['share_text'], json.dumps({'page': data['page'], 'press': 'share_text', 'id': job['id']}))],
                [Button.inline(strings['delbtn_cron'], json.dumps({'page': data['page'], 'press': 'del_cron', 'id': job['id']}))],
                [Button.inline(strings['delbtn_job'], json.dumps({'page': data['page'], 'press': 'del_job', 'id': job['id']}))],
            ]
        elif data['press'] == 'group_list':
            text = f"Group List: ```{json.dumps(job['group_list'], indent=4, ensure_ascii=False)}```"
            keyboard = [
                [Button.inline(strings['edit'], json.dumps({'page': data['page'], 'press': 'edit_list', 'id': job['id']}))],
                [Button.inline(strings['back'], json.dumps({'page': data['page'], 'press': 'job', 'id': job['id']}))],
            ]
        elif data['press'] == 'share_text':
            text = job['share_text']
            keyboard = [
                [Button.inline(strings['edit'], json.dumps({'page': data['page'], 'press': 'edit_text', 'id': job['id']}))],
                [Button.inline(strings['back'], json.dumps({'page': data['page'], 'press': 'job', 'id': job['id']}))],
            ]
        elif data['press'] == 'del_cron':
            text = strings['confirm']
            keyboard = yesno(f"del_cron",'job', job['id'])
        elif data['press'] == 'del_job':
            text = strings['confirm']
            keyboard = yesno(f"del_job",'job', job['id'])
        elif data['press'] == 'edit_list':
            user['next'] = 'group_list'
            user['edit'] = {'target': 'group_list', 'id': job['id']}
            text = strings['ask_group_list']
        elif data['press'] == 'edit_text':
            user['next'] = 'share_text'
            user['edit'] = {'target': 'share_text', 'id': job['id']}
            text = strings['ask_share_text']
        elif data['press'].startswith(('yesdel_cron','yesdel_job')):
            delinfo = data['press'].split('_')
            if delinfo[1]=='cron' and database.delete_cron(job['id']):
                text = strings['del_cron']
            elif delinfo[1]=='job' and database.delete_job(job['id']):
                text = strings['del_job']
    database.set_user(event.chat_id, user)
    await event.edit(text, buttons=None if keyboard==[] else keyboard, link_preview=False)

with bot:
    bot.loop.create_task(cron())
    bot.run_until_disconnected()