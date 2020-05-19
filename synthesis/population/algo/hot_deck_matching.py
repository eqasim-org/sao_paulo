import pandas as pd
import numpy as np
from tqdm import tqdm
import functools, itertools
import multiprocessing as mp
import numpy.ma as ma

class HotDeckMatcher:
    def __init__(self, df_source, source_id, source_weight, mandatory_fields, preference_fields, default_id, minimum_source_samples):
        self.mandatory_fields = mandatory_fields
        self.preference_fields = preference_fields
        self.all_fields = self.mandatory_fields + self.preference_fields
        self.default_id = default_id
        self.minimum_source_samples = minimum_source_samples

        self.values = {
            field : list(np.unique(df_source[field]))
            for field in self.all_fields
        }

        self.field_sizes = [len(self.values[field]) for field in self.all_fields]
        self.field_indices = np.cumsum(self.field_sizes)

        for field in self.all_fields:
            print("Found categories for %s:" % field, ", ".join([str(c) for c in self.values[field]]))

        self.source_matrix = self.make_matrix(df_source, source = True)
        self.source_weights = df_source[source_weight]
        self.source_ids = df_source[source_id]

        search_order = [
            [list(np.arange(size) == k) for k in range(size)] +
            ([] if field in self.mandatory_fields else [[False] * size])
            for field, size in zip(self.all_fields, self.field_sizes)
        ]

        self.field_masks = list(itertools.product(*search_order))

    def make_matrix(self, df, chunk_index = None, source = False):
        columns = sum(self.field_sizes)

        matrix = np.zeros((len(df), columns), dtype = np.bool)
        column_index = 0

        with tqdm(total = columns, desc = "Reading categories (%s) ..." % ("source" if source else "target"), position = chunk_index) as progress:
            for field_name in self.all_fields:
                for field_value in self.values[field_name]:
                    matrix[:, column_index] = df[field_name] == field_value
                    column_index += 1
                    progress.update()

        return matrix

    def __call__(self, df_target, chunk_index = 0):
        target_matrix = self.make_matrix(df_target, chunk_index = None)

        matched_mask = np.zeros((len(df_target),), dtype = np.bool)
        matched_indices = np.ones((len(df_target), ), dtype = np.int) * -1

        # Note: This speeds things up quite a bit. We generate a random number
        # for each person which is later on used for the sampling.
        random = np.array([
            np.random.random() for _ in tqdm(range(len(df_target)), desc = "Generating random numbers", position = chunk_index)
        ])

        with tqdm(total = len(self.field_masks), position = chunk_index, desc = "Hot Deck Matching") as progress:
            for field_mask in self.field_masks:
                field_mask = np.array(functools.reduce(lambda x, y: x + y, field_mask), dtype = np.bool)
                source_mask = np.all(self.source_matrix[:, field_mask], axis = 1)

                if np.any(source_mask) and np.count_nonzero(source_mask) >= self.minimum_source_samples:
                    target_mask = np.all(target_matrix[:,field_mask], axis = 1)

                    if np.any(target_mask):
                        source_indices = np.where(source_mask)[0]
                        random_indices = np.floor(random[target_mask] * len(source_indices)).astype(np.int)
                        matched_indices[np.where(~matched_mask)[0][target_mask]] = source_indices[random_indices]

                        # We continuously shrink these matrix to make the matching
                        # easier and easier as the HDM proceeds
                        random = random[~target_mask]
                        target_matrix = target_matrix[~target_mask]
                        matched_mask[~matched_mask] |= target_mask

                progress.update()

        matched_ids = np.zeros((len(df_target),), dtype = self.source_ids.dtype)
        matched_ids[matched_mask] = self.source_ids.iloc[matched_indices[matched_mask]]
        matched_ids[~matched_mask] = self.default_id

        return matched_ids

def run(df_target, target_id, df_source, source_id, source_weight, mandatory_fields, preference_fields, default_id = int(-1), runners = -1, minimum_source_samples = 1):
    matcher = HotDeckMatcher(df_source, source_id, source_weight, mandatory_fields, preference_fields, default_id, minimum_source_samples)

    if runners == -1:
        runners = mp.cpu_count()

    if runners == 1:
        df_target.loc[:, "hdm_source_id"] = matcher(df_target, 0)
    else:
        with mp.Pool(processes = runners, initializer = initializer, initargs = (matcher,)) as pool:
            chunks = np.array_split(df_target, runners)
            df_target.loc[:, "hdm_source_id"] = np.hstack(pool.map(runner, enumerate(chunks)))

            for i in range(runners + 1): print(" ") # Formatting of output

matcher = None
def initializer(_matcher):
    global matcher
    matcher = _matcher

def runner(args):
    index, df_chunk = args
    return matcher(df_chunk, index)

















#
