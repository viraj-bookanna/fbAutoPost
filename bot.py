import os,logging,asyncio,pytz,json
from telethon import TelegramClient, events
from fbAuto import fbAuto
from dotenv import load_dotenv
from datetime import datetime
from strings import direct_reply, strings
from database import DB

load_dotenv(override=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Colombo'))
bot = TelegramClient('bot', os.environ['API_ID'], os.environ['API_HASH']).start(bot_token=os.environ['BOT_TOKEN'])
fb_auto = fbAuto()
database = DB()
USER_LIST = [] if os.getenv('USER_LIST') is None else os.environ['USER_LIST'].split(',')

async def wait_until_next_minute():
    now = datetime.now(TIMEZONE)
    next_minute = now.replace(hour=now.hour, minute=now.minute+1 if now.minute!=59 else 0, second=0, microsecond=0)
    seconds_to_next_minute = (next_minute-now).total_seconds()
    await asyncio.sleep(seconds_to_next_minute)
async def cron():
    while True:
        await wait_until_next_minute()
        print('executing cron')
        for job in database.get_jobs_for_current_minute():
            print(job, datetime.now(TIMEZONE))
            await execute_job(job)
async def execute_job(job):
    if not fb_auto.logged_in:
        await fb_auto.login(os.environ['COOKIES_FILE'])
    for group in job['group_list']:
        await fb_auto.sharePost(job['post_link'], group, job['share_text'])

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
    if event.message.text in direct_reply:
        text = direct_reply[event.message.text]
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
    elif event.message.text.startswith('/del'):
        job_id = event.message.text.split(' ', 2)
        text = strings['delete_help']
        if len(job_id) == 3 and job_id[1].upper() == 'JOB':
            text = strings['job_invalid']
            if database.delete_job(job_id[2]):
                text = strings['job_deleted']
        elif len(job_id) == 3 and job_id[1].upper() == 'CRON':
            text = strings['cron_id_invalid']
            if database.delete_cron(job_id[2]):
                text = strings['cron_deleted']
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
            user['new']['group_list'] = json.dumps(group_list)
            text = strings['ask_share_text']
            user['next'] = 'share_text'
        except json.JSONDecodeError:
            text = strings['invalid_group_list']
    elif next == 'share_text':
        user['new']['share_text'] = event.message.text
        job_id = database.add_job(user['new'])
        del user['new']
        del user['next']
        text = f'Job added\nJob ID: `{job_id}`'
    else:
        text = strings['unknown_command']
    database.set_user(event.chat_id, user)
    await event.respond(text)
    
async def main():
    await fb_auto.login(os.environ['COOKIES_FILE'])

with bot:
    bot.loop.run_until_complete(main())
    bot.loop.create_task(cron())
    bot.run_until_disconnected()