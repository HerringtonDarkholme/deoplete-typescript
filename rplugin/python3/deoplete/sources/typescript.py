import deoplete.util
import re
import logging
from subprocess import Popen, PIPE
import json
from .base import Base

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.rank = 600
        self.name = 'typescript'
        self.mark = '[TS]'
        self.min_pattern_length = 0
        self.filetypes = ['typescript']
        self.command = ['tsserver']
        self.cached = {'row': -1, 'end': -1}
        self.process = None


    def startServer(self):
        self.process = Popen(self.command, stdout=PIPE, stdin=PIPE, shell=True)

    def stop_server(self):
        if self.process is None:
            return

        self.process.stdin.close()
        self.process.wait()
        self.process = None

    def completation(self, pos):
        current_row = pos['line']
        current_col = pos['ch']
        current_line = self.vim.current.line

        cached = current_row == int(self.cached["row"])
        cached = cached and current_col >= int(self.cached["end"])
        cached = cached and current_line[0:int(self.cached["end"])] == self.cached["word"]
        cached = cached and not re.match(".*\\W", current_line[int(self.cached["end"]):current_col])

        if cached and self.cached['data']:
            return self.cached['data']

        command = {
            "type": "completions",
            "types": True,
            "docs": True
        }

        # def run_command
        data = self.run_command(command, pos)
        #
        completions = []

        if data is not None:

            for rec in data["completions"]:
                completions.append({"word": rec["name"],
                                    "menu": self.completion_icon(rec.get("type")),
                                    "info": self.type_doc(rec)})

            start, end = (data["start"]["ch"], data["end"]["ch"])
            self.cached = {
                "row": current_row,
                "start": start,
                "end": end,
                "word": current_line[0:end],
                "data": completions
            }

        return completions

    # Good.
    def get_complete_position(self, context):
        m = re.search(r'\w*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        self._file_changed = 'TextChanged' in context['event'] or self._tern_last_length != len(self.vim.current.buffer)
        line = context['position'][1]
        col = context['complete_position']
        pos = {"line": line - 1, "ch": col}
        # self.debug(context)
        result = self.completation(pos) or []
        # self.debug('*' * 100)
        # self.debug(result)
        # self.debug('*' * 100)
        return result
