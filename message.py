#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import json
from util import logger
from pynng import Surveyor0, Respondent0, Timeout
from handler import Handler

log = logger(__name__)

class Message():
    '''
    message was defined with following format:
    {
        'who': ['node id'],
        'do': 'cmd/discovery/redo, etc.',
        'detail': any,
    }
    '''
    def __init__(self, mode='respondent', fqdn=None, address=None, port=7788):
        '''
        mode - can be respondent or surveyor
        '''
        # should use internal vip instead of external vip
        self.me = fqdn if fqdn else os.environ.get('FQDN')
        if not self.me:
            raise ValueError('FQDN is required')
        self.url = 'tcp://{ip}:{port}'
        self.seq = 0
        self.handler = Handler()
        self.nodes = []

        self.survey = {
            'who': ['all'],
            'seq': 0,
            'do': 'discovery',
            'detail': 'who you are?',
        }
        self.reply = {
            'who': self.me,
            'do': 'done',
            'detail': '',
        }
        if mode == 'survey':
            self.ips = address if address else os.environ.get('MYIP', '0.0.0.0')
            log.info(f'Create message obj with {mode}, {fqdn}, {self.ips}, {port}')
            self.surveyor = Surveyor0(listen=self.url.format(ip=self.ips, port=port))
        else:
            addresses = address if address else os.environ.get('Surveyor', '0.0.0.0')
            self.ips = addresses.split(',')
            log.info(f'Create message obj with {mode}, {fqdn}, {self.ips}, {port}')
            self.responder = Respondent0()
            for ip in self.ips:
                self.responder.dial(self.url.format(ip=ip, port=port))

    async def getNodes(self):
        '''
        Discovery all nodes
        '''
        await asyncio.sleep(0.5)
        self.nodes = []
        nodes = await self.sendSurvey(['all'], do='discovery', survey='', timeout=500)
        for node in nodes:
            self.nodes.append(node['who'])
        return self.nodes

    async def sendSurvey(self, who: list, do, survey: any, resent=False, timeout=10000):
        '''
        If resend specified, survey will be ignored and previous survey will be used
        '''
        reply = []

        # fill the survey
        if not resent:
            if not who or type(who) is not list:
                raise ValueError('"who" should be list and cannot be empty if not resending')
            self.survey['who'] = who
            self.seq += 1
            self.survey['seq'] = self.seq
            self.survey['do'] = do
            self.survey['detail'] = survey

        log.info('Send a survey ({}) to {} and wait for reply ...'.format(self.survey, self.ips))
        # survey will be finished if all expect nodes replied
        # or timeout if some nodes not replied
        if self.survey['who'][0] == 'all' and self.nodes:
            expect_nodes = set(self.nodes)
        else:
            expect_nodes = set(self.survey['who'])

        # wait a little while for connecting
        self.surveyor.survey_time = timeout

        await self.surveyor.asend(json.dumps(self.survey).encode())
        while True:
            try:
                result = await self.surveyor.arecv()

                log.info('Got reply {} ...'.format(result))
                result = json.loads(result.decode())
                reply.append(result)
                expect_nodes.discard(result['who'])
                # got all responses
                if not expect_nodes:
                    log.info('All done, survey finished')
                    break
            except Timeout:
                log.info(f'Survey is over, no reply within time {timeout}')
                break
        return reply
    
    async def recvSurvey(self):
        log.info('Dialing to {} ...'.format(self.ips))
        who = self.reply.get('who')
        if not who:
            self.reply['who'] = self.me

        log.info('Prepare to get survey ...')
        while True:
            survey = await self.responder.arecv()

            log.info('Got a survey: {}'.format(survey))
            survey = json.loads(survey.decode())
            for_who = survey.get('who')
            if self.me in for_who or 'all' in for_who:
                # only handle survey for me
                reply = await self.handler.process_survey(survey)
                self.reply['detail'] = reply
                log.info(f'reply: {self.reply}')
            else:
                self.reply['do'] = 'ignore'
                self.reply['detail'] = 'Not for me'
                log.warning('Ignore this survey since it is not for me')
            await self.responder.asend(json.dumps(self.reply).encode())

async def main(mode):
    msg = Message(mode=mode)
    if mode.startswith('resp'):
        await msg.recvSurvey()
    else:
        who = input('who do your want to send?')
        do = input('what do your want to do?')
        survey = input('Please input your survey?')
        await msg.getNodes()
        await msg.sendSurvey(who=who.split(), do=do, resent=False, survey=survey)

if __name__ == '__main__':
    mode = ''
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    try:
        asyncio.run(main(mode))
    except KeyboardInterrupt:
        sys.exit()
