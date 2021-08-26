import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from collections import Counter


class Node:
    def __init__(self, feature_index=None, threshold=None, left=None, right=None, info_gain=None):
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.info_gain = info_gain

    def __str__(self):
        return f"feature_index: {self.feature_index}\nthreshold: {self.threshold}"


class Leaf(Node):
    def __init__(self, value, size=None):
        super().__init__()
        self.value = value
        self.size = size

    def __str__(self):
        return f"value: {self.value}, size: {self.size}"


class ClassificationTree:
    def __init__(self, dataset=None, min_sample_split=2, max_depth=100):
        """

        :param dataset: Pandas dataframe with numeric training and target data(must be the last column).
        :param min_sample_split: Minimal samples required to split dataset.
        :param max_depth: Maximal depth of the tree.
        """
        self.dataset = dataset
        self.root = None
        self.min_sample_split = min_sample_split
        self.max_depth = max_depth

    @property
    def features(self):
        """

        :return: Returns nothing.
        """
        return self.dataset.columns

    @property
    def numpy_data(self):
        """

        :return: Returns nothing.
        """
        return self.dataset.to_numpy()

    @staticmethod
    def generate_thresholds(column):
        """

        :param column: Numeric 1d np.array.
        :return: Yields threshold.
        """
        for i in range(len(column)):
            if i != len(column) - 1:
                yield (column[i] + column[i + 1]) / 2

    @staticmethod
    def get_leaf_value(dataset):
        """

        :param dataset: Dataset with merged train and target columns.
        :return: Most frequently occurring value in given dataset target column.
        """
        count = Counter(dataset[:, -1])
        return max(count, key=lambda x: count[x])

    @staticmethod
    def split(dataset, feature_index, threshold):
        """

        :param dataset: Dataset with merged train and target columns. often smaller size than original.
        :param feature_index: Column by which threshold dataset will be split.
        :param threshold: Numeric value by which dataset will be split.
        :return: dataset_left containing column with values smaller than threshold and
         dataset_right with column containing values bigger than threshold
        """
        dataset_left = np.array([row for row in dataset if row[feature_index] <= threshold])
        dataset_right = np.array([row for row in dataset if row[feature_index] > threshold])
        return dataset_left, dataset_right

    def get_optimal_split(self, dataset, feature_range):
        """

        :param dataset: Dataset with merged train and target columns. often smaller size than original.
        :param feature_range: Range of training features.
        :return: Dictionary with information about best split: feature_index, threshold,
         left_dataset, right_dataset, split_score, is_final(is it the last split that needs to be done).
        """
        best_score = float("inf")
        best_split = None
        for feature_index in range(feature_range):
            thresholds = self.generate_thresholds(np.unique(sorted(dataset[:, feature_index])))
            for threshold in thresholds:
                dataset_left, dataset_right = self.split(dataset, feature_index, threshold)
                score, is_final = self.gini_index(dataset_left, dataset_right)
                if score < best_score:
                    best_score = score
                    best_split = {"feature_index": feature_index,
                                  "threshold": threshold,
                                  "dataset_left": dataset_left,
                                  "dataset_right": dataset_right,
                                  "split_score": best_score,
                                  "is_final": is_final}
                if score == 0:
                    return best_split
        return best_split

    def fit(self, x=None, target=None):
        """

        :param x: Training dataset.
        :param target: Target dataset.
        :return: Returns nothing.
        """
        def build_tree(dataset, depth=0):
            """

            :param dataset: Dataset with merged train and target columns. often smaller size than original.
            :param depth: Current depth of this instance.
            :return: Node object if more splits will be required of Leaf object if no more split will be required.
            """
            sample_amount, feature_amount = dataset.shape
            if sample_amount >= self.min_sample_split and depth <= self.max_depth:
                optimal_split = self.get_optimal_split(dataset, feature_amount - 1)
                if optimal_split["split_score"] > 0 or (
                        optimal_split["split_score"] == 0 and not optimal_split["is_final"]):

                    left_subtree = build_tree(optimal_split["dataset_left"], depth=depth + 1)
                    right_subtree = build_tree(optimal_split["dataset_right"], depth=depth + 1)
                    return Node(optimal_split["feature_index"], optimal_split["threshold"],
                                left_subtree, right_subtree, optimal_split["split_score"])
            return Leaf(self.get_leaf_value(dataset), len(dataset))

        if not self.dataset:
            self.dataset = x
        self.dataset["target"] = target
        self.root = build_tree(self.dataset.to_numpy())

    @staticmethod
    def gini_index(dataset_left, dataset_right):
        """

        :param dataset_left: Dataset with column containing values smaller than some threshold.
        :param dataset_right: Dataset with column containing values greater than some threshold.
        :return: weighted gini index, information whether this split should be final.
        """
        scores = []
        counts = []
        for dataset in [dataset_left, dataset_right]:
            count = Counter(dataset[:, -1])
            counts.append(count)
            score = 0
            for value in count:
                score += (count[value] / len(dataset)) ** 2
            scores.append(1 - score)

        is_final = False
        is_single = True
        for count in counts:
            if len(count) != 1:
                is_single = False
        if is_single:
            if counts[0].keys() == counts[1].keys():
                is_final = True
        weighted_gini = (len(dataset_left) * scores[0] + len(dataset_right) * scores[1]) / (
                    len(dataset_left) + len(dataset_right))
        return weighted_gini, is_final

    def print_tree(self, indent="-", target_names=None):
        """

        :param indent: Symbol used to make indents.
        :param target_names: List with names of target classes.
        :return: String representation of the tree.
        """
        def _print_tree(node=None, multi=1):
            """

            :param node: Current worked on node.
            :param multi: Amount of indents required to represent this node.
            :return: Returns nothing.
            """
            if node is None:
                node = self.root
            if isinstance(node, Leaf):
                print(f"class: {target_names[int(node.value)]}, size: {node.size}")
            else:
                print(self.features[node.feature_index], "<=", node.threshold, "?", node.info_gain)
                print(f"{multi * indent}left: ", end="")
                _print_tree(node.left, multi=multi + 1, )
                print(f"{multi * indent}right: ", end="")
                _print_tree(node.right, multi=multi + 1)

        return _print_tree()


if __name__ == '__main__':
    iris = load_iris()
    train_df = pd.DataFrame(data=iris["data"], columns=iris["feature_names"])
    target_df = pd.DataFrame(data=iris["target"], columns=["target"])
    t1 = ClassificationTree()
    t1.fit(train_df, target_df)
    t1.print_tree(target_names=iris["target_names"])
