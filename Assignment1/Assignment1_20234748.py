# Thanks to SK lee who provided the skeleton code

"""
#
# Database Design
#
# Assignment 1: B-Tree
# 20234748 나선우
#
# Comments:
#   [ ] stands for a node
#   [.A.B.C.] stands for a node with a key A, B and C
#   [.A｡B.] stands for a parent node, working between A and B
#   [.A｡∅｡B.] stands for a parent node,
#              working between A and B, with an empty key
#
"""

# importing libraries
import math, sys
import pandas as pd
import numpy as np
from tqdm import tqdm

# B-Tree Node Class
class Node:
    def __init__(self, leaf=False):
        self.keys: list[int]        = []    # list of keys
        self.parent: list           = []
        self.children: list[Node]   = []    # list of children
        self.leaf: bool             = leaf  # is leaf node

# B-Tree Class
class BTree:
    def __init__(self, t: int):
        '''
        # create a instance of the Class of a B-Tree
        # t : the minimum degree t
        # (the max num of keys is 2*t -1, the min num of keys is t-1)
        '''
        self.root: Node  = Node(True)
        self.t: int      = t

    # B-Tree-Split-Child
    def split_child(self, x: Node, i: int):
        '''
        # split the node x's i-th child that is full
        # x: the current node
        # i: the index of the node x's child to be split
        # return: None
        '''

        z: Node = Node()            # create a new node z
        y: Node = x.children[i]     # y is the i-th child of x
        z.leaf = y.leaf             # y is a leaf => z if a leaf

        # z: [] -> [ T U V ]
        z.keys = y.keys[self.t:]    # move the right keys from y to z

        # z: [ T U V ] -> [.T.U.V.]
        z.children = [] if y.leaf else y.children[self.t:]

        # y: [.P.Q.R.S.T.U.V.] -> [.P.Q.R.]
        # middle: S
        middle = y.keys[self.t-1]   # the middle key of y
        y.keys = y.keys[:self.t-1]  # keep the left keys in y
        y.children = [] if y.leaf else y.children[:self.t]

        # x: [.N｡W.] -> [.N｡∅｡W.]
        x.children.insert(i+1, z)   # insert z as a child of x

        # x: [.N｡∅｡W.] -> [.N｡S｡W.]
        x.keys.insert(i, middle)    # insert the middle key of y to x


    # B-Tree-Insert
    def insert(self, k):
        '''
        # insert the key k into the B-Tree
        # return: None
        '''
        # (TODO)
        # Write your own code here
        # Case 1: if the root is full
        # Case 2: if the root is not full


    # B-Tree-Insert-Nonfull
    def insert_key(self, x, k):
        '''
        # insert the key k into node x
        # return: None
        '''
        # (TODO)
        # Write your own code here
        # Case 1: if the node x is leaf
        # Case 2: if the node x is an internal node


    # B-Tree-Search
    def search_key(self, x, key):
        '''
        # search for the key in node x
        # return: the node x that contains the key, the index of the key if the key is in the B-tree
        '''
        # (TODO)
        # Write your own code here



    def delete(self, k):
        '''
        # delete the key k from the B-tree
        # return: None
        '''
        # (TODO)
        # Write your own code here

    def delete_leaf_node(self, x, i):
        '''
        # delete the key in a leaf node
        '''
        # (TODO)
        # Write your own code here

    def delete_internal_node(self, x, i):
        '''
        # delete the key in an internal node
        '''
        # (TODO)
        # Write your own code here


    # implement whatever you need
    #  def borrow_merge(self, x, j):
        #  pass

    #  def check_smaller_than_t(self, x):
        #  pass

    #  def find_predecessor(self, x):
        #  pass

    #  def merge_sibling(self, x, i, j):
        #  pass

    #  def borrow_sibling(self, x, i, j):
        #  pass


    # for printing the statistic of the resulting B-tree
    def traverse_key(self, x, level=0, level_counts=None):
        '''
        # run BFS on the B-tree to count the number of keys at every level
        # return: level_counts
        '''
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


def get_file():
    '''
    # read an input file (.csv) with its name
    '''
    file_name = (input("Enter the file name you want to insert or delete ▷ (e.g., insert1 or delete1_50 or delete1_90 or ...) "))

    while True:
        try:
            file = pd.read_csv('inputs/'+file_name+'.csv',
                               delimiter='\t', names=['key', 'value'])
            return file
        except FileNotFoundError:
            print("File does not exist.")
            file_name = (input("Enter the file name again. ▷ "))


def insertion_test(B, file):
    '''
    #   read all keys and values from the file and insert them into the B-tree
    #   B   : an empty B-tree
    #   file: a csv file that contains keys to be inserted
    #   return: the resulting B-tree
    '''

    file_key = file['key']
    file_value = file['value']

    print('===============================')
    print('[ Insertion start ]')

    for i in tqdm(range(len(file_key))): # tqdm shows the insertion progress and the elapsed time
        B.insert([file_key[i], file_value[i]])

    print('[ Insertion complete ]')
    print('===============================')
    print()

    return B


def deletion_test(B, root, delete_file):
    '''
    #   read all keys and values from the file and delete them from the B-tree
    #   B   : the current B-tree
    #   file: a csv file that contains keys to be deleted
    #   return: the resulting B-tree
    '''

    delete_key = delete_file['key']

    print('===============================')
    print('[ Deletion start ]')

    for i in tqdm(range(len(delete_key))):
        B.delete(delete_key[i])

    print('[ Deletion complete ]')
    print('===============================')
    print()

    return B


def print_statistic(B):
    '''
    # print the information about the current B-tree
    # the number of keys at each level
    # the total number of keys in the B-tree
    '''
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
                t = 3 # minimum degree
                B = BTree(2*t-1, t) # make an empty b-tree with the minimum degree t

                insert_file = get_file()
                B = insertion_test(B, insert_file)

            # 2. Deletion
            elif num == 2:
                delete_file = get_file()
                B = deletion_test(B, delete_file)

            # 3. Statistic
            elif num == 3:
                print_statistic(B)

            # 4. End program
            elif num == 4:
                sys.exit(1)

            else:
                print("Invalid input. Please enter 1, 2, 3, or 4.")

        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == '__main__':
    main()

