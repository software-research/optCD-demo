import math
import re
from collections import Counter
from dateutil import parser
from bisect import bisect_right
import yaml

# How a responsible plugin is picked for an unused directory:
#   "time"       -- the original rule: the plugin whose "[INFO] --- ..." line
#                   is the last one before the directory appeared.
#   "tfidf_time" -- time still decides which plugins are candidates (those
#                   that had started when the directory appeared), but among
#                   them the directory path is matched against each plugin's
#                   name with TF-IDF. Candidates from the directory's own
#                   module are preferred. Falls back to "time" when no
#                   candidate's name matches the path.
DEFAULT_STRATEGY = "tfidf_time"

# Path words that say nothing about which plugin wrote a directory. "test"
# in particular would otherwise match surefire's "test" goal for any
# test-classes/ directory.
_STOPWORDS = {"target", "test", "tests", "default", "main", "java", "classes", "src",
              "generated", "sources", "home", "runner", "work", "meta", "inf"}
_RUNNER_PREFIX = re.compile(r"^/home/runner/work/[^/]+/[^/]+/")

# Directories the OptCD paper (ASE 2023, Sec. III-D) names as known outputs
# of a specific plugin. Their names do not contain the plugin's name, so
# the plugin's word is added to the query.
_KNOWN_DIRS = {"maven-status": "compiler", "surefire-reports": "surefire"}


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w and not w.isdigit()]


def _plugin_words(name: str) -> list[str]:
    """Words naming the plugin, goal and execution id (not the module).
    'maven-compiler-plugin:3.1:compile (default-compile) @ x' and
    'compiler:3.15.0:compile (default-compile) @ x' give the same words."""
    head = name.split(" @ ")[0]
    words = []
    for w in _words(head):
        if w in ("maven", "plugin") or re.fullmatch(r"\d+[a-z0-9]*", w):
            continue
        words.append(w)
    return [w for w in words if w not in _STOPWORDS]


def _module_of(name: str) -> str:
    return name.split(" @ ")[-1].strip().lower() if " @ " in name else ""


def _dir_module(rel: str) -> str | None:
    if "/target" not in "/" + rel:
        return None
    head = ("/" + rel).split("/target")[0].strip("/")
    return head.split("/")[-1].lower() if head else ""


def _same_module(dir_module: str | None, artifact_id: str) -> bool:
    if not dir_module or not artifact_id:
        return False
    return dir_module == artifact_id or dir_module in artifact_id or artifact_id in dir_module


def _tfidf_scores(query: list[str], docs: list[list[str]]) -> list[float]:
    """TF-IDF similarity between the query (directory path) and each doc
    (plugin name), with the candidate docs as the corpus. Normalised by the
    query only: full cosine would also divide by the doc's length and so
    favour plugins with short names ("bundle" over "javadoc:jar
    (attach-javadocs)" for javadoc-bundle-options/)."""
    n = len(docs)
    df = Counter(w for d in docs for w in set(d))
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}

    def vec(words):
        # Binary TF for docs: "bundle:bundle (default-bundle)" must not
        # outweigh a plugin whose name says "bundle" once.
        tf = Counter(w for w in set(words) if w in idf)
        return {w: c * idf[w] for w, c in tf.items()}

    q = vec(query)
    qn = math.sqrt(sum(v * v for v in q.values()))
    scores = []
    for d in docs:
        v = vec(d)
        dot = sum(q[w] * v.get(w, 0.0) for w in q)
        scores.append(dot / (qn * qn) if qn else 0.0)
    return scores


def pick_plugin(started_names: list[str], unused_dir: str, strategy: str = DEFAULT_STRATEGY) -> str:
    """Picks the responsible plugin among the executions that had started
    when `unused_dir` appeared (oldest first, so the last one is what the
    time rule picks)."""
    latest = started_names[-1]
    if strategy == "time":
        return latest

    rel = _RUNNER_PREFIX.sub("", unused_dir)
    module = _dir_module(rel)
    # De-duplicate keeping each name's latest position, oldest first.
    candidates = list(dict.fromkeys(reversed(started_names)))[::-1]
    exact = [c for c in candidates if module and _module_of(c) == module]
    same = exact or [c for c in candidates if _same_module(module, _module_of(c))]
    if same:
        candidates = same

    query = [w for w in _words(rel) if w not in _STOPWORDS]
    query += [plugin for dirname, plugin in _KNOWN_DIRS.items() if f"/{dirname}" in "/" + rel]
    scores = _tfidf_scores(query, [_plugin_words(c) for c in candidates])
    best = max(scores) if scores else 0.0
    if best <= 0.0:
        # No name evidence: newest candidate, from the directory's own module if any.
        return candidates[-1]
    # Ties go to the most recently started candidate.
    return candidates[max(range(len(candidates)), key=lambda k: (scores[k], k))]


def get_responsible_plugins(log: str, unused_dirs: list[str], timestamps: dict[str, str], input_yaml_filename: str, job_name: str) -> list[tuple[str, str, str, str]]:
    dummy_file_timestamps = []
    for file, timestamp in timestamps.items():
        if "optcd" in file:
            dummy_file_timestamps.append(parser.isoparse(timestamp))

    run_commands_in_steps = []
    uses_in_steps = []
    names_of_steps = []
    with open(input_yaml_filename, "r") as input_yaml:
        loaded_yaml = yaml.safe_load(input_yaml)
        job_id = job_name.split("(")[0].strip()
        for step in loaded_yaml["jobs"][job_id]["steps"]:
            run_commands_in_steps.append(step.get("run"))
            uses_in_steps.append(step.get("uses"))
            names_of_steps.append(step.get("name") or step.get("uses") or step.get("run"))

    in_maven = False
    tmp_plugin_timestamps = []
    tmp_plugin_names = []
    plugin_timestamps = []
    plugin_names = []
    responsible_plugins = []
    for line in log.splitlines():
        tokens = line.split(" ")
        if "##[group]" in line and in_maven:  # maven part ended
            in_maven = False
            timestamp = parser.isoparse(tokens[0])
            tmp_plugin_timestamps.append(timestamp)
            plugin_timestamps.append(tmp_plugin_timestamps)
            plugin_names.append(tmp_plugin_names)
            tmp_plugin_timestamps = []
            tmp_plugin_names = []
            continue
        if len(tokens) < 3:
            continue
        if tokens[1] != "[INFO]" or tokens[2] != "---":
            continue
        in_maven = True
        timestamp = parser.isoparse(tokens[0])
        name = ' '.join(tokens[3:-1])
        tmp_plugin_timestamps.append(timestamp)
        tmp_plugin_names.append(name)

    for unused_dir in unused_dirs:
        if unused_dir not in timestamps:
            continue
        timestamp = parser.isoparse(timestamps[unused_dir])
        j = bisect_right(dummy_file_timestamps, timestamp)
        for k in range(len(plugin_timestamps)):
            i = bisect_right(plugin_timestamps[k], timestamp)
            if 0 < i < len(plugin_timestamps[k]):
                responsible_plugins.append((unused_dir, pick_plugin(plugin_names[k][:i], unused_dir), run_commands_in_steps[j] or uses_in_steps[j], names_of_steps[j]))
                break
        else:
            responsible_plugins.append((unused_dir, "Not responsible by maven plugins", run_commands_in_steps[j] or uses_in_steps[j], names_of_steps[j]))

    return responsible_plugins
