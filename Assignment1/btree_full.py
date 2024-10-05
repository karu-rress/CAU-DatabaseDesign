import bisect


class BTreeNode:
    def __init__(self, keys, children, is_leaf):
        self.keys = keys
        self.children = children
        self.is_leaf = is_leaf


class BTree:
    def __init__(self, t):
        self.root = BTreeNode([], [], True)
        self.t = t

    def search(self, key):
        return self._search_key(key, self.root)

    def _search_key(self, key, node):
        # get binary search lower bound index
        # if current node has key, return
        # if current node doesn't have key and is leaf node, return False
        # if current node isn't leaf node, call recursive for child[lower_bound]
        i = bisect.bisect_left(node.keys, key)
        if i < len(node.keys) and key == node.keys[i]:
            return (node, i)
        elif node.is_leaf:
            return None
        else:
            return self._search_key(key, node.children[i])

    def insert(self, key):
        # if root node is full, make root node as child
        # split new root as child -> new root would get value(median) from old root
        # call insert routine from root to leaf node recursively
        if len(self.root.keys) == 2 * self.t - 1:  # root is full
            self.root = BTreeNode([], [self.root], False)
            self._split_child(self.root, 0)
        self._insert_key(key, self.root)

    def _insert_key(self, key, node):
        # get lower bound idx -> keys[i] > key
        # if current node is leaf, then insert key at idx
        # else, check ith child is full. if is, do split ith child
        # after split ith child, ith child's median value added in cur node key
        # check value and change lower bound idx for key
        # call insert routine to ith child
        i = bisect.bisect_left(node.keys, key)
        if node.is_leaf:
            node.keys.insert(i, key)
        else:
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i = i + 1
            self._insert_key(key, node.children[i])

    def _split_child(self, node, i):
        # get ith child from node
        # split key and child half, except median value
        # get median value and insert in node
        # change ith child to left part(cause smaller then median)
        # insert left in i + 1 idx (case bigger than median)
        c = node.children[i]
        c_l = BTreeNode(c.keys[0:self.t - 1], c.children[0:self.t], c.is_leaf)
        c_r = BTreeNode(c.keys[self.t:2 * self.t - 1],
                        c.children[self.t:2 * self.t], c.is_leaf)
        median = c.keys[self.t - 1]
        node.keys.insert(i, median)
        node.children[i] = c_l
        node.children.insert(i + 1, c_r)

    def delete(self, key):
        # if root key cnt is 1 and all child's node key count also t - 1
        # B-Tree would shrink to h - 1
        # so, before delete operation, root needs to be preprocessed
        if len(self.root.keys) == 1:
            root = self.root
            t = self.t
            left, right = root.children[0], root.children[1]
            if len(left.keys) == t - 1 and len(right.keys) == t - 1:
                self.root = BTreeNode([], [], False)
                self.root.keys.extend(left.keys)
                self.root.keys.extend(root.keys)
                self.root.keys.extend(right.keys)
                self.root.children.extend(left.children)
                self.root.children.extend(right.children)
                if len(self.root.children) == 0:
                    self.root.is_leaf = True
        self._delete_key(key, self.root)

    def _delete_key(self, key, node):
        i = bisect.bisect_left(node.keys, key)
        # if key matched from currnet node
        if i < len(node.keys) and node.keys[i] == key:
            if node.is_leaf:
                node.keys.pop(i)
                return
            else:
                successor = self._find_successor(node.children[i + 1])
                node.keys[i], successor.keys[0] = successor.keys[0], node.keys[i]
                self._delete_key(key, node.children[i + 1])
        # if key didn't matched then check next node status
        else:
            if len(node.children[i].keys) == self.t - 1:
                self._delete_balancing(node.children[i], node, i)
            i = bisect.bisect_left(node.keys, key)
            self._delete_key(key, node.children[i])

    def _delete_balancing(self, node, parent, i):
        # if next destination index is last pos
        # next dst just has left siblings
        if i == len(parent.children) - 1:
            if len(parent.children[i - 1].keys) > self.t - 1:
                node.keys.insert(0, parent.keys.pop())
                parent.keys.append(parent.children[i - 1].keys.pop())
                if len(parent.children[i - 1].children) > 0:
                    node.children.insert(
                        0, parent.children[i - 1].children.pop())
            else:
                parent.children[i - 1].keys.append(parent.keys.pop())
                parent.children[i - 1].keys.extend(node.keys)
                parent.children.pop()
        # if next destination index is first pos
        # next dst just has right siblings
        elif i == 0:
            if len(parent.children[i + 1].keys) > self.t - 1:
                node.keys.append(parent.keys.pop(0))
                parent.keys.insert(0, parent.children[i + 1].keys.pop(0))
                if len(parent.children[i + 1].children) > 0:
                    node.children.append(
                        parent.children[i + 1].children.pop(0))
            else:
                parent.children[i + 1].keys.insert(0, parent.keys.pop(0))
                for k in node.keys:
                    parent.children[i + 1].keys.insert(0, k)
                parent.children.pop(0)
        else:
            if len(parent.children[i - 1].keys) > self.t - 1:
                node.keys.insert(0, parent.keys[i])
                parent.keys[i] = parent.children[i - 1].keys.pop()
                if len(parent.children[i - 1].children) > 0:
                    node.children.insert(
                        0, parent.children[i - 1].children.pop())
            elif len(parent.children[i + 1].keys) > self.t - 1:
                node.keys.append(parent.keys[i])
                parent.keys[i] = parent.children[i + 1].keys.pop(0)
                if len(parent.children[i + 1].children) > 0:
                    node.children.append(
                        parent.children[i + 1].children.pop(0))
            else:
                parent.children[i - 1].keys.append(parent.keys.pop(i - 1))
                parent.children[i - 1].keys.extend(node.keys)
                parent.children.pop(i)

    def _find_successor(self, node):
        if node.is_leaf:
            return node
        else:
            return self._find_successor(node.children[0])

    # Print the tree
    def print_tree(self, node, l=0):
        print("Level ", l, " ", end=":")
        for i in node.keys:
            print(i, end=" ")
        print()
        l += 1
        if len(node.children) > 0:
            for i in node.children:
                self.print_tree(i, l)


def main():
    B = BTree(2)

    for i in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
        B.insert(i)

    B.print_tree(B.root)

    if B.search(80) is not None:
        print("\n80 Found")
    else:
        print("\n80 Not found")

    for val in [50, 60]:
        print(f'delete val : {val}')
        B.delete(val)
        print(B.search(val))


if __name__ == '__main__':
    main()