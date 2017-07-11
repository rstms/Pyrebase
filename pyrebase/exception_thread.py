#!/bin/env python

import threading

class ExceptionThread(threading.Thread):

    def __init__(self, callback=None, tid=None, *args, **kwargs):
        """
        Redirect exceptions of thread to an exception handler.

        :param callback: function to handle occured exception
        :type callback: function(thread, exception)
        :param args: arguments for threading.Thread()
        :type args: tuple
        :param kwargs: keyword arguments for threading.Thread()
        :type kwargs: dict
        """
        self._callback = callback
        self.tid = tid
        super().__init__(*args, **kwargs)

    def run(self):
        retry=True
        try:
            while retry == True:
                try:
                    if self._target:
                        self._target(*self._args, **self._kwargs)
                    retry = False
                except BaseException as e:
                    if self._callback is None:
                        raise e
                    else:
                        retry = self._callback(self, e)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs, self._callback
