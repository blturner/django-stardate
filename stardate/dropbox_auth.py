# Modified from Michael Shepanski's django-dbbackup.
# Copyright (c) 2010, Michael Shepanski
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:

#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name django-dbbackup nor the names of its contributors
#       may be used to endorse or promote products derived from this software without
#       specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import pickle

from dropbox import client, session
from dropbox.rest import ErrorResponse

from stardate import settings


class DropboxAuth(object):
    APP_KEY = settings.DROPBOX_APP_KEY
    APP_SECRET = settings.DROPBOX_APP_SECRET
    ACCESS_TYPE = settings.DROPBOX_ACCESS_TYPE
    TOKENS_FILEPATH = settings.TOKENS_FILEPATH
    _request_token = None
    _access_token = None

    def __init__(self):
        self.dropbox_client = self.get_dropbox_client()

    def get_dropbox_client(self):
        self.read_token_file()
        sess = session.DropboxSession(self.APP_KEY, self.APP_SECRET, self.ACCESS_TYPE)
        access_token = self.get_access_token(sess)
        sess.set_token(access_token.key, access_token.secret)
        dropbox = client.DropboxClient(sess)
        return dropbox

    def create_access_token(self, sess):
        request_token = self.get_request_token(sess)
        try:
            self._access_token = sess.obtain_access_token(request_token)
        except ErrorResponse:
            request_token = self.create_request_token(sess)
            self.prompt_for_authorization(sess, request_token)
        self.save_token_file()
        return self._access_token

    def create_request_token(self, sess):
        self._request_token = sess.obtain_request_token()
        self.save_token_file()
        return self._request_token

    def get_access_token(self, sess):
        if not self._access_token:
            return self.create_access_token(sess)
        return self._access_token

    def get_request_token(self, sess):
        if not self._request_token:
            return self.create_request_token(sess)
        return self._request_token

    def prompt_for_authorization(self, sess, request_token):
        message = "Dropbox needs authorization:\n"
        message += sess.build_authorize_url(request_token)
        raise Exception(message)

    def save_token_file(self):
        tokendata = dict(request_token=self._request_token, access_token=self._access_token)
        with open(self.TOKENS_FILEPATH, 'wb') as tokenhandle:
            pickle.dump(tokendata, tokenhandle)

    def read_token_file(self):
        if os.path.exists(self.TOKENS_FILEPATH):
            with open(self.TOKENS_FILEPATH, 'rb') as tokenhandle:
                tokendata = pickle.load(tokenhandle)
            self._request_token = tokendata.get('request_token')
            self._access_token = tokendata.get('access_token')
