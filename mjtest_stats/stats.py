import gzip
import os, datetime
import subprocess

from typing import Dict, List

from pprint import pprint

import functools

EXEC = "exec"
LEXER = "lexer"
SYNTAX = "syntax"
SEMANTIC = "semantic"

MODES = [LEXER, SYNTAX, SEMANTIC, EXEC]


class Creator:

    def __init__(self, name: str, group: int):
        self.name = name
        self.group = group

    @classmethod
    def from_name(cls, name: str) -> 'Creator':
        names = {
            "Johannes Bechberger": 3,
            "Benedikt Morbach": 4,
            "Lukas Böhm": 1,
            "Sebastian Graf": 3,
            "Florian Loch": 1,
            "Rolleander": 5,
            "Philipp Serrer": 2,
            "Simon Herter": 3,
            "Samuel Groß": 1,
            "Azegor": 4,
            "SrTobi": 2,
            "Markus Schlegel": 5
        }
        if name not in names:
            raise BaseException("Name {} unknown".format(name))
        return Creator(name, names[name])


class TestFile:

    def __init__(self, file_name: str, mode: str, creation_date: int, creator: Creator):
        self.file_name = file_name
        self.mode = mode
        self.creation_date = creation_date
        self.creator = creator

    @classmethod
    def from_file(cls, mode: str, file_name: str) -> 'TestFile':
        dirname = os.path.dirname(file_name)
        author, time = subprocess.check_output("cd {}; git log --date=unix --oneline --format='%an|%at' {} | tail -1".format(dirname, os.path.basename(file_name)), shell=True).decode().split("|")
        return TestFile(file_name, mode, time, Creator.from_name(author))

    def gzipped_size(self) -> int:
        with open(self.file_name) as f:
            return len(gzip.compress(f.read().encode('utf-8')))

class Files:

    def __init__(self, files_per_mode: Dict[str, List[TestFile]]):
        self.files_per_mode = files_per_mode

    @classmethod
    def create(cls, test_dir: str) -> 'Files':
        files_for_modes = {}
        for d in map(lambda x: os.path.join(test_dir, x), os.listdir(test_dir)):
            if not os.path.basename(test_dir).startswith(".") and os.path.isdir(d):
                files_for_modes[d.split("/")[-1]] = cls._process_mode(d, d.split("/")[-1])
        return Files(files_for_modes)

    @classmethod
    def _process_mode(cls, test_dir: str, mode: str) -> List[TestFile]:
        ret = []
        for d in map(lambda x: os.path.join(test_dir, x), os.listdir(test_dir)):
            if not os.path.basename(test_dir).startswith("."):
                if os.path.isdir(d):
                    ret.extend(cls._process_mode(d, mode))
                if d.endswith(".mj") or d.endswith(".java"):
                    ret.append(TestFile.from_file(mode, d))
        return ret

    def combined(self) -> List[TestFile]:
        arr = []
        for k in self.files_per_mode:
            arr.extend(self.files_per_mode[k])
        return arr

    def test_cases_per_group(self, weight_func = lambda t: 1) -> Dict[int, int]:
        d = {}
        for test_file in self.combined():
            group = test_file.creator.group
            if group not in d:
                d[group] = weight_func(test_file)
            else:
                d[group] += weight_func(test_file)
        return d

    def test_cases_per_group_latex(self, weight_func = lambda t: 1) -> str:
        tc = self.test_cases_per_group(weight_func)
        groups = sorted(list(tc.keys()))
        return """
\\documentclass[varwidth=true, border=2pt]{standalone}

\\usepackage{pgfplots}

\\begin{document}
    \\begin{tikzpicture}
        \\begin{axis}[
            symbolic x coords={%s},
            xtick=data
          ]
            \\addplot[ybar,fill=blue] coordinates {
                %s
            };
        \\end{axis}
    \\end{tikzpicture}
\\end{document}
        """ % (", ".join(map(str, groups)), "\n".join("({}, {})".format(g, tc[g]) for g in groups))

    def test_modes_per_week(self, mode, weight_func = lambda t: 1) -> str:
        map = {}  # type: Dict[int, int]
        week_to_date_str = {}  # type: Dict[int, str]
        for test_file in self.files_per_mode[mode]:
            date = datetime.datetime.fromtimestamp(float(test_file.creation_date))
            week = date.isocalendar()[1]
            week_to_date_str[week] = date.strftime("%y-%m-%d")
            test_file_weight = weight_func(test_file)
            if week not in map:
                map[week] = test_file_weight
            else:
                map[week] += test_file_weight
        return "\n".join("{}, {}".format(week_to_date_str[week], map[week]) for week in sorted(map.keys(), key=lambda x: week_to_date_str[x]))

    def test_modes_per_week_latex_filecontents(self, weight_func = lambda t: 1) -> str:
        ret = []
        for mode in self.files_per_mode.keys():
            ret.append("""
            \\begin{{filecontents*}}{{{}.csv}}
            d, c
            {}
            \\end{{filecontents*}}
            """.format(mode, self.test_modes_per_week(mode, weight_func)))
        return "\n".join(ret)

    def test_modes_time_series(self, weight_func=lambda t: 1) -> Dict[str, List[str]]:
        days = {}  # type: Dict[str, Dict[str, List[TestFile]]]
        date_str_to_unix = {}
        for mode in MODES:
            for test_file in self.files_per_mode[mode]:
                date = datetime.datetime.fromtimestamp(float(test_file.creation_date))
                date_str = date.strftime("%y-%m-%d")
                date_str_to_unix[date_str] = test_file.creation_date
                if date_str not in days:
                    days[date_str] = {}
                if mode not in days[date_str]:
                    days[date_str][mode] = []
                days[date_str][mode].append(test_file)
        sorted_date_strs = sorted(date_str_to_unix.keys())

        result = {}  # type: Dict[str, List[str]]
        mode_count = {}
        mode_count_combined = {}
        for mode in MODES:
            mode_count[mode] = 0
            mode_count_combined[mode] = 0

        for date_str in sorted_date_strs:
            data = days[date_str]
            for mode in MODES:
                combined_count = 0
                count = mode_count[mode]
                m_index = MODES.index(mode)
                if m_index > 0:
                    combined_count = mode_count_combined[MODES[m_index - 1]]
                if mode in data:
                    count += sum(map(lambda t: weight_func(t), data[mode]))
                mode_count[mode] = count
                combined_count += count
                if mode not in result:
                    result[mode] = []
                result[mode].append("{}, {}".format(date_str, combined_count))
                mode_count_combined[mode] = combined_count

        return result

    def test_modes_time_series_latex_filecontents(self, weight_func=lambda t: 1) -> str:
        ret = []
        data = self.test_modes_time_series(weight_func)
        for mode in self.files_per_mode.keys():
            ret.append("""
            \\begin{{filecontents*}}{{{}.csv}}
            d, c
            {}
            \\end{{filecontents*}}
            """.format(mode, "\n".join(data[mode])))
        return "\n".join(ret)

files = Files.create("../mjtest/tests")
pprint(files.test_cases_per_group())
print(files.test_cases_per_group_latex())
print("--------")
print(files.test_modes_time_series_latex_filecontents())
print("--------gzipped size summed----------")
print(files.test_cases_per_group_latex(lambda t: t.gzipped_size()))
print("--------")
print(files.test_modes_time_series_latex_filecontents(lambda t: t.gzipped_size()))