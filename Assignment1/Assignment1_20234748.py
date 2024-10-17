"""
#
# Database Design
#
# Assignment 1: B-Tree Implementation
#   20234748 나선우
#
# Comments:
#   [] stands for a node
#   [.A.B.C.] stands for a node with a key A, B and C
#   [.A｡B.] stands for a parent node, working between A and B
#   [.A｡∅｡B.] stands for a parent node,
#              working between A and B, with an empty key
#
"""

# importing libraries
import sys
import pandas as pd
from tqdm import tqdm
import bisect

# B-Tree Node Class
class Node:
    def __init__(self, leaf: bool = False) -> None:
        self.keys: list[list[int]] = []  # list of keys
        self.parent: (Node | None) = None  # parent node
        self.children: list[Node] = []  # list of children
        self.leaf: bool = leaf  # is leaf node


# B-Tree Class
class BTree:
    def __init__(self, t: int) -> None:
        """
        create an instance of the Class of a B-Tree
        t : the minimum degree t (min-child)
        (the max num of keys is 2*t -1, the min num of keys is t-1)
        """
        self.root: Node = Node(True)
        self.t: int = t


    # B-Tree-Split-Child
    def split_child(self, x: Node, i: int) -> None:
        """
        split the node x's i-th child that is full
        x: the current node
        i: the index of the node x's child to be split (starting from 0)
        """

        # z: [], y: [.P.Q.R.S.T.U.V.]
        y: Node = x.children[i]  # y is the i-th child of x
        z: Node = Node(leaf=y.leaf)  # create a new node z

        # z: [] -> [ T U V ]
        z.keys = y.keys[self.t:]  # move the right keys from y to z

        if not y.leaf:
            # z: [ T U V ] -> [.T.U.V.]
            z.children = y.children[self.t:]
            y.children = y.children[:self.t]
            for child in z.children:
                child.parent = z
                
        # x: [.N｡W.] -> [.N｡∅｡W.]
        x.children.insert(i + 1, z)  # insert z as a child of x
        z.parent = x

        # x: [.N｡∅｡W.] -> [.N｡S｡W.]
        x.keys.insert(i, y.keys[self.t - 1])  # insert the middle key of y to x

        # y: [.P.Q.R.S.T.U.V.] -> [.P.Q.R.]
        y.keys = y.keys[:self.t - 1]  # keep the left keys in y


    # B-Tree-Insert: insert the key k into the B-Tree
    def insert(self, k: list[int]) -> None:
        # If the root is full, split
        # r: [.A.B.C.D.E.] when t = 3
        if len(self.root.keys) == (2 * self.t) - 1:
            new_root: Node = Node(leaf=False)            # Create new root
            new_root.children = [self.root]
            self.root.parent = new_root
            self.split_child(new_root, 0)              # Split the old root
            self.root = new_root

        # After that (or the root is not full), insert the key
        self.insert_key(self.root, k)


    # B-Tree-Insert-Nonfull: "Only called when non-full"
    def insert_key(self, x: Node, k: list[int]) -> None:
        i = bisect.bisect_left(x.keys, k)
        # Case 1: if the node x is leaf (& non-full)
        if x.leaf:
            # x: [ A B D ] -> [ A B C D ]
            x.keys.insert(i, k)

        # Case 2: if the node x is an internal node
        else:
            if len(x.children[i].keys) == (2 * self.t) - 1:
                self.split_child(x, i)
                if k > x.keys[i]:
                    i += 1

            self.insert_key(x.children[i], k)

    # B-Tree-Search
    # Note that k is not list[int] but int
    def search_key(self, x: Node, key: int, n: int=1) -> (tuple[Node, int] | None):
        """
        # search for the key in node x
        # return: the node x that contains the key,
        #         the index of the key if the key is in the B-tree
        """

        # Binary search
        i = bisect.bisect_left([k[0] for k in x.keys], key)

        if i < len(x.keys) and key == x.keys[i][0]:
            return x, i

        if x.leaf:  # failure: the key is not found
            return None

        return self.search_key(x.children[i], key, n+1)

    # B-Tree-Delete
    # Note that k is not list[int] but int
    def delete(self, k: int):
        """
        # delete the key k from  the B-tree
        # return: None
        """
        x, i = 0, 0
        try:


            # Search for the key
            r = self.search_key(self.root, k)
            if r is None:
                return
            x, i = r

            # Case 1: The key is originally in a leaf node
            if x.leaf:
                self.delete_leaf_node(x, i)

            # Case 2: The key is originally in an internal node
            else:
                self.delete_internal_node(x, i)

            if len(self.root.keys) == 0:
                if self.root.leaf:
                    self.root = None
                else:
                    self.root = self.root.children[0]



        except IndexError: # 이거는 충분히 수정 가능할 것 같은데...
            # print(f"인덱스 오류! '{k}': x={x.keys}, i={i}")
            # exit(1)
            pass
        except ValueError:
            # print(f"찾는 값이 없음! '{k}': x={x.keys}, search={self.search_key(self.root, k)}")
            pass
        except Exception as e:
            print(f"Couldn't remove key '{k}': x={x.keys}, i={i}")
            print(f"Error: {e}")

    def delete_leaf_node(self, x: Node, i: int) -> None:
        """
        # delete the key in a leaf node
        # Case 1: The key is originally in a leaf node
        """

        # Case 1-1: x.n >= t, just delete the key
        # x: [ A B C D E ] -> [ A B D E ]
        x.keys.pop(i)

        # Case 1-2: x.n == t-1. We can't just delete the key from x!
        if len(x.keys) == self.t - 1:
            self.borrow_merge(x)

    def delete_internal_node(self, x: Node, i: int) -> None:
        """
        # delete the key in an internal node
        # Case 2: The key is originally in an internal node
        # Trick: Transform this case into Case 1
        """

        # 1. find the predecessor of the node
        # x: [.30.33.], pred_node: [ 31 32 ], pred_idx: 1
        pred_node, pred_idx = self.find_predecessor(x, i)
        try:
            pred_key = pred_node.keys[pred_idx]
        except:
            print(f"Error: pred_node: {pred_node.keys}, pred_idx: {pred_idx}")
            print(f"Error: x: {x.keys}, i: {i}")
            raise


        # 2. replace the key with the predecessor
        # x: [.30.32.], pred_key: 33
        x.keys[i], pred_key = pred_key, x.keys[i]

        # 3. delete the predecessor and check Case 1
        self.delete_leaf_node(pred_node, pred_idx)

    @staticmethod
    def find_predecessor(x: Node, i: int) -> tuple[Node, int]:
        """
        # Find the predecessor of the key at index i in node x
        # Find the rightmost key in the left!
        """
        node = x.children[i]
        while not node.leaf:
            node = node.children[-1]        # go to rightmost
        return node, len(node.keys) - 1

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
            if len(parent.keys) < self.t - 1:
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

    # for printing the statistic of the resulting B-tree
    def traverse_key(self, x: Node, level: int = 0, level_counts: dict[int, int] = None) -> dict[int, int]:
        """
        # run BFS on the B-tree to count the number of keys at every level
        # return: level_counts
        """
        if level_counts is None:
            level_counts = {}

        if x:
            # counting the number of keys at the current level
            if level in level_counts:
                level_counts[level] += len(x.keys)
            else:
                level_counts[level] = len(x.keys)

            # recursively call the traverse_key() for further traverse
            for child in x.children:
                self.traverse_key(child, level + 1, level_counts)

        return level_counts


# Btree Class done


def get_file() -> pd.DataFrame:
    """
    # read an input file (.csv) with its name
    """
    file_name = input(
        "Enter the file name you want to insert or delete ▷ (e.g., insert1 or delete1_50 or delete1_90 or ...) ")

    while True:
        try:
            file: pd.DataFrame = pd.read_csv('inputs/' + file_name + '.csv',
                                             delimiter='\t', names=['key', 'value'])
            return file
        except FileNotFoundError:
            print("File does not exist.")
            file_name = input("Enter the file name again. ▷ ")


def insertion_test(B: BTree, file: pd.DataFrame) -> BTree:
    """
    #   read all keys and values from the file and insert them into the B-tree
    #   B   : an empty B-tree
    #   file: a csv file that contains keys to be inserted
    #   return: the resulting B-tree
    """

    file_key: pd.Series[int] = file['key']
    file_value: pd.Series[int] = file['value']

    print('===============================')
    print('[ Insertion start ]')

    for i in tqdm(range(len(file_key))):  # tqdm shows the insertion progress and the elapsed time
        B.insert([file_key[i], file_value[i]])

    print('[ Insertion complete ]')
    print('===============================')
    print()

    return B


def deletion_test(B: BTree, delete_file: pd.DataFrame) -> BTree:
    """
    #   read all keys and values from the file and delete them from the B-tree
    #   B   : the current B-tree
    #   file: a csv file that contains keys to be deleted
    #   return: the resulting B-tree
    """

    delete_key: pd.Series[int] = delete_file['key']

    print('===============================')
    print('[ Deletion start ]')

    for i in tqdm(range(len(delete_key))):
        B.delete(delete_key[i])

    print('[ Deletion complete ]')
    print('===============================')
    print()

    return B


def print_statistic(B: BTree):
    """
    # print the information about the current B-tree
    # the number of keys at each level
    # the total number of keys in the B-tree
    """
    print('===============================')
    print('[ Print statistic of tree ]')

    level_counts = B.traverse_key(B.root)

    for level, counts in level_counts.items():
        if level == 0:
            print(f'Level {level} (root): Key Count = {counts}')
        else:
            print(f'Level {level}: Key Count = {counts}')
    print('-------------------------------')
    total_keys = sum(counts for counts in level_counts.values())
    print(f'Total number of keys across all levels: {total_keys}')
    print('[ Print complete ]')
    print('===============================')
    print()


def main():
    while True:
        try:
            num = int(input("1.insertion 2.deletion. 3.statistic 4.end ▶  "))

            # 1. Insertion
            if num == 1:
                t = 3
                B = BTree(t)  # make an empty b-tree with the minimum degree t

                insert_file: pd.DataFrame = get_file()
                B = insertion_test(B, insert_file)

            # 2. Deletion
            elif num == 2:
                delete_file: pd.DataFrame = get_file()
                B = deletion_test(B, delete_file)

            # 3. Statistic
            elif num == 3:
                print_statistic(B)

            # 4. End program
            elif num == 4:
                sys.exit(1)
                """
            ## FOR DEBUG
            elif num == 5:
                node1 = Node(True); node1.keys = [[5, 5]]
                node2 = Node(True); node2.keys = [[15, 15]]
                node3 = Node(False); node3.keys = [[10, 10]]
                node3.children = [node1, node2]
                node1.parent = node2.parent = node3

                node4 = Node(True); node4.keys = [[25, 25], [28, 28]]
                node5 = Node(True); node5.keys = [[31, 31], [32, 32]]
                node6 = Node(True); node6.keys = [[35, 35]]
                node7 = Node(False); node7.keys = [[30, 30], [33, 33]]
                node7.children = [node4, node5, node6]
                node4.parent = node5.parent = node6.parent = node7

                node8 = Node(True); node8.keys = [[45, 45]]
                node9 = Node(True); node9.keys = [[55, 55]]
                node10 = Node(True); node10.keys = [[65, 65]]
                node11 = Node(False); node11.keys = [[50, 50], [60, 60]]
                node11.children = [node8, node9, node10]
                node8.parent = node9.parent = node10.parent = node11

                node12 = Node(False); node12.keys = [[20, 20], [40, 40]]
                node12.children = [node3, node7, node11]
                node3.parent = node7.parent = node11.parent = node12

                B = BTree(2)
                B.root = node12
                """
            elif num == 6:
                B = BTree(3)

                for i in range(1, 11):
                    B.insert([i, i])
                    print_statistic(B)


            else:
                print("Invalid input. Please enter 1, 2, 3, or 4.")

        except ValueError:
            print("Invalid input. Please enter a number.")


if __name__ == '__main__':
    main()

