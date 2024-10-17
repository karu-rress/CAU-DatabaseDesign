import bisect
import unittest
from tqdm import tqdm
import pandas as pd
import sys


class Node:
    def __init__(self, leaf: bool = False) -> None:
        self.keys: list[list[int]] = []  # list of keys
        self.parent: (Node | None) = None  # parent node
        self.children: list[Node] = []  # list of children
        self.leaf: bool = leaf  # is leaf node


# B-Tree Class
class BTree:
    def __init__(self, t: int) -> None:
        self.root: Node = Node(True)
        self.t: int = t
            
    def search_key(self, x: Node, key: int, n: int=1) -> (tuple[Node, int] | None):
        i = bisect.bisect_left([k[0] for k in x.keys], key)
        
        if i < len(x.keys) and key == x.keys[i][0]:
            return x, i

        if x.leaf:  # failure: the key is not found
            return None

        return self.search_key(x.children[i], key, n+1)
    
    def traverse_key(self, x: Node, level: int = 0, level_counts: dict[int, int] = None) -> dict[int, int]:
        if level_counts is None:
            level_counts = {}
        if x:
            if level in level_counts:
                level_counts[level] += len(x.keys)
            else:
                level_counts[level] = len(x.keys)
            for child in x.children:
                self.traverse_key(child, level + 1, level_counts)
        return level_counts
    
    
    def delete_leaf_node(self, x: Node, i: int) -> None:
        """
        # delete the key in a leaf node
        # Case 1: The key is originally in a leaf node
        """

        # Case 1-1: x.n >= t, just delete the key
        # x: [ A B C D E ] -> [ A B D E ]
        if len(x.keys) >= self.t:
            x.keys.pop(i)

        # Case 1-2: x.n == t-1. We can't just delete the key from x!
        elif len(x.keys) <= self.t - 1:
            x.keys.pop(i)
            self.borrow_merge(x)


    @staticmethod
    def merge_sibling(x: Node, i: int) -> None:
        """
        # Merge the i-th child of x with its (i+1)-th sibling
        # x: Parent node
        # i: Index of the child node in parent node
        """

        left = i - 1 if i > 0 else i
        right = i if i > 0 else i + 1

        # Deleted key is in the i-th child of x
        # y: [ 25 ], z: [ ∅ ]
        y = x.children[left]
        z = x.children[right]

        # Move the key from x down to the left child
        # y: [ 25 ] -> [ 25 28 ]
        y.keys.append(x.keys[left])

        # Append all keys and children of the right child to the left child
        # y: [ 25 28 ] -> [ 25 28 ∅ ]
        y.keys.extend(z.keys)
        if not z.leaf:
            y.children.extend(z.children)

        # Remove the key and the right child from x
        # x: [.28 33.] -> [.33.]
        x.keys.pop(left)
        x.children.pop(right)

    def borrow_merge(self, x: Node) -> None:
        """
        # Case 1-2a: Borrow key from sibling or merge with sibling
        # Case 1-2b: borrow from parent and merge with sibling
        """
        parent = x.parent
        parent_idx = parent.children.index(x)

        # 1: borrow from left sibling
        if parent_idx > 0 and len(parent.children[parent_idx - 1].keys) >= self.t:
            self.borrow_sibling(x, parent_idx, parent_idx - 1)

        # 2: Borrow from the right sibling
        elif parent_idx < len(parent.children) - 1 and len(parent.children[parent_idx + 1].keys) >= self.t:
            self.borrow_sibling(x, parent_idx, parent_idx + 1)

        # Case 1-2b: Merge with sibling
        else:
            self.merge_sibling(parent, parent_idx)

            # After deleting the key, parent node's key count is reduced
            # So, we need to check the parent node again
            if len(parent.keys) < self.t - 1 and parent != self.root:
                self.borrow_merge(parent)

            # However, if the parent is the root and has no child node,
            # (1) set the merged node as the new root
            # (2) decrease the height of the B-tree
            if parent == self.root and len(parent.keys) == 0:
                self.root = parent.children[0]

    @staticmethod
    def borrow_sibling(x: Node, i: int, j: int) -> None:
        """
        # Borrow key from the sibling at sibling index j
        # i: the index of the node x in the parent node
        # j: the index of the sibling node in the parent node
        """

        # sibling: [ 25 28 ], parent: [.30｡33.]
        sibling = x.parent.children[j]
        parent = x.parent

        # Borrow from left sibling
        if j < i:
            # x: [ ∅ ] -> [ 30 ]
            x.keys.insert(0, parent.keys[i - 1])

            # sibling: [ 25 28 ] -> [ 25 ]
            # parent: [.30｡33.] -> [.28｡33.]
            parent.keys[i - 1] = sibling.keys.pop()
            if not sibling.leaf:
                x.children.insert(0, sibling.children.pop())
        # Borrow from right sibling
        else:
            x.keys.append(parent.keys[i])
            parent.keys[i] = sibling.keys.pop(0)
            if not sibling.leaf:
                x.children.append(sibling.children.pop(0))

    def delete_internal_node(self, x: Node, i: int) -> None:
        """
        # delete the key in an internal node
        # Case 2: The key is originally in an internal node
        # Trick: Transform this case into Case 1
        """

        # 1. find the predecessor of the node
        # x: [.30.33.], pred_node: [ 31 32 ], pred_idx: 1
        pred_node, pred_idx = self.find_successor(x, i)
        try:
            pred_key = pred_node.keys[pred_idx]
        except:
            print(f"Error: pred_node: {pred_node.keys}, pred_idx: {pred_idx}")
            print(f"Error: x: {x.keys}, i: {i}")
            raise

        # 2. replace the key with the predecessor
        # x: [.30.32.], pred_key: 33
        x.keys[i], pred_node.keys[pred_idx] = pred_key, x.keys[i]

        # 3. delete the predecessor and check Case 1
        self.delete_leaf_node(pred_node, pred_idx)

    @staticmethod
    def find_successor(x: Node, i: int) -> tuple[Node, int]:
        """
        # Find the successor of the key at index i in node x
        # Find the leftmost key in the right!
        """
        node = x.children[i + 1]
        while not node.leaf:
            node = node.children[0]        # go to leftmost
        return node, 0

def print_tree(B):
    level_counts = B.traverse_key(B.root)
    for level, counts in level_counts.items():
        if level == 0:
            print(f'Level {level} (root): Key Count = {counts}')
        else:
            print(f'Level {level}: Key Count = {counts}')

    total_keys = sum(counts for counts in level_counts.values())

    print(f'\nRoot keys: {B.root.keys}\n')

    print(f'Level 1: {B.root.children[0].keys} | {B.root.children[1].keys}\n')

    print(f'Children of first: {B.root.children[0].children[0].keys} | {B.root.children[0].children[1].keys}')
    print(f'Children of second: {B.root.children[1].children[0].keys} | {B.root.children[1].children[1].keys}')


node1 = Node(True); node1.keys = [[5, 5]]; node2 = Node(True); node2.keys = [[15, 15]]
node3 = Node(True); node3.keys = [[30, 30]]; node4 = Node(True); node4.keys = [[70, 70]]
node5 = Node(False); node5.keys = [[10, 10]]; node5.children = [node1, node2]; node1.parent = node2.parent = node5
node6 = Node(False); node6.keys = [[35, 35]]; node6.children = [node3, node4]; node3.parent = node4.parent = node6
node7 = Node(False); node7.keys = [[20, 20]]; node7.children = [node5, node6]; node5.parent = node6.parent = node7

B = BTree(2)
B.root = node7

print_tree(B)

print('='*50, end='\n\n')

x, i = B.search_key(B.root, 10)
B.delete_internal_node(x, i)

level_counts = B.traverse_key(B.root)
for level, counts in level_counts.items():
    if level == 0:
        print(f'Level {level} (root): Key Count = {counts}')
    else:
        print(f'Level {level}: Key Count = {counts}')

total_keys = sum(counts for counts in level_counts.values())

print(f'\nRoot keys: {B.root.keys}\n')
print(f'Level 1: {B.root.children[0].keys} | {B.root.children[1].keys} | {B.root.children[2].keys}\n')
