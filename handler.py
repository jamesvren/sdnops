import command
from util import logger

log = logger(__name__)

class Handler():
    def __init__(self):
        self.reply = None
        self.seq = None

    async def process_survey(self, msg):
        log.info(f'handle survey - {msg}')
        reply = {}
        seq = msg.get('seq')
        if seq == self.seq:
            # it's for previous survey, just resturn previous result
            log.warning(f'redo ... reply with previous result')
            return self.reply

        self.seq = seq
        do = msg.get('do')
        if do == 'discovery':
            stdout, stderr = await command.run("ip -4 -br address show vhost0 | grep -oE '([0-9]{1,3}.){3}[0-9]{1,3}'")
            if not stderr:
                reply['ip'] = stdout.decode().strip('\n')
        if do == 'cmd':
            cmd = msg['detail']
            stdout, stderr = await command.run(cmd)
            reply['stdout'] = stdout.decode().strip('\n')
            reply['stderr'] = stderr.decode().strip('\n')
        # record reply in case of redo
        self.reply = reply

        return reply
