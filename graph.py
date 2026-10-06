"""Concept dependency graph: root-cause and downstream impact."""
from src import config as C


def chain_upstream(topic, prereqs):
    """All prerequisites of topic, nearest first."""
    out, cur = [], topic
    while prereqs.get(cur):
        cur = prereqs[cur][0]
        out.append(cur)
    return out


def root_cause(topic, mastery, prereqs):
    """Earliest prerequisite that is itself below mastery; else the topic."""
    weak = [t for t in chain_upstream(topic, prereqs) if mastery.get(t, 1) < C.MASTERED]
    return weak[-1] if weak else topic


def downstream_impact(topic, mastery, prereqs):
    """Topics that depend on `topic` (transitively) and are not mastered."""
    out = []
    for t in prereqs:
        if topic in chain_upstream(t, prereqs) and mastery.get(t, 1) < C.MASTERED:
            out.append(t)
    return out
