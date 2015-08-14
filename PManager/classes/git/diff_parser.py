
from PManager.classes.git.file_diff import FileDiff
    _raw = None
    _raw_length = 0
        self.parse(raw)

    def raw(self, line):
        if self._raw_length <= line:
            return ''
        return self._raw[line]

    def parse(self, raw):
        self._raw = raw.split('\n')
        self._raw_length = len(self._raw)
        self.__load_message()
        self.__load_author()
        self.__load_date()
        self.__load_hash()
        self.__load_files()

    @staticmethod
    def __parse_binary(file_obj, m):
        mode = False
        (old_path, new_path) = m.groups()
        if old_path == '/dev/null':
            mode = "C"
            file_obj['path'] = new_path
        elif new_path == '/dev/null':
            mode = "D"
            file_obj['path'] = old_path
        else:
            file_obj['path'] = new_path
        file_obj['action'] = mode
        file_obj['diff'] = False
        file_obj['lines'] = []
        file_obj['summary'] = {
            "deleted": 1 if mode == "D" else 0,
            "created": 1 if mode == "C" else 0,
            "binary": True
        }
        return file_obj
    @property
    def files(self):
        return self._files

    def __load_hash(self):
        self._hash = self.raw(0).replace("commit ", "")

    def __load_author(self):
        data = self.raw(1).replace("Author: ", "")
        ts = data.split("<")
        self._author = {"name": ts[0].strip(" "), "email": ts[1].strip(" ><")}

    def __load_date(self):
        data = self.raw(2).replace("Date: ", "").strip(" ")
        self._date = data

            data += self.raw(i).strip(" \t") + "\n"
            if re.search('diff --git', self.raw(i)):
        self._files = self.__parse_files(self.message_end_offset)
    def __get_files_diff(self, start):
        files = []
        _file = []
        for i in range(start, self._raw_length):
            if self.raw(i).startswith('diff --git') and len(_file) > 0:
                files.append(_file)
                _file = [self.raw(i)]
                _file.append(self.raw(i))
        if len(_file) > 0:
            files.append(_file)
        return files

    def __parse_files(self, start):
        files = self.__get_files_diff(start)
        files_parsed = []
        for f in files:
            files_parsed.append(FileDiff(f))
        return files_parsed
