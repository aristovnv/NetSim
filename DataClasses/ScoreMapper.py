import bisect
import numpy as np

class ScoreMapper:
    def __init__(self):
        self.sorted_scores = np.array([])
        self.id_by_score = np.array([])

    def build(self, entries, score_fn, min_val=0, max_val=1):
        """
        entries: list of entities with .id
        score_fn: function(entry) -> raw numeric value
        min_val / max_val: scale raw score into [0,1]
        """
        raw_scores = [score_fn(e) for e in entries]
        for e in entries:
            s = score_fn(e)
            if s is None:
                print(f"⚠️ Score None for: {e.id} as  min_val {min_val} and {max_val} and raw_Scores {s}")
        # scale into [0,1]
        scaled_scores = np.clip([(r - min_val) / (max_val - min_val) for r in raw_scores], 0, 1)
        ids = [e.id for e in entries]
        sort_idx = np.argsort(scaled_scores)
        self.sorted_scores = np.array(scaled_scores)[sort_idx]
        self.id_by_score = np.array(ids)[sort_idx]

    def decode(self, score, remove_if=False):
        idx = bisect.bisect_left(self.sorted_scores, score)
        if idx >= len(self.sorted_scores):
            idx = len(self.sorted_scores) - 1
        if idx < 0:
            return None
        chosen_id = self.id_by_score[idx]
        if remove_if:
            self.remove_by_index(idx)
        return chosen_id

    def remove_by_index(self, idx):
        self.sorted_scores = np.delete(self.sorted_scores, idx)
        self.id_by_score = np.delete(self.id_by_score, idx)

    def remove_by_score(self, score):
        idx = bisect.bisect_left(self.sorted_scores, score)
        if idx < len(self.sorted_scores):
            self.remove_by_index(idx)

    def remove_by_id(self, id):
        idx = np.where(self.id_by_score == id)[0]
        if len(idx) > 0:
            self.remove_by_index(idx[0])
