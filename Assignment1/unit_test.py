import bisect

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

    def split_child(self, x: Node, i: int) -> None:
        y: Node = x.children[i]  # y is the i-th child of x
        z: Node = Node(leaf=y.leaf)  # create a new node z

        z.keys = y.keys[self.t:]  # move the right keys from y to z

        if not y.leaf:
            z.children = y.children[self.t:]
            y.children = y.children[:self.t]
            for child in z.children:
                child.parent = z
                
        x.children.insert(i + 1, z)  # insert z as a child of x
        z.parent = x
        x.keys.insert(i, y.keys[self.t - 1])  # insert the middle key of y to x
        y.keys = y.keys[:self.t - 1]  # keep the left keys in y

    def insert(self, k: list[int]) -> None:
        if len(self.root.keys) == (2 * self.t) - 1:
            new_root: Node = Node(leaf=False)            # Create new root
            new_root.children = [self.root]
            self.root.parent = new_root
            self.split_child(new_root, 0)              # Split the old root
            self.root = new_root

        self.insert_key(self.root, k)

    def insert_key(self, x: Node, k: list[int]) -> None:
        i = bisect.bisect_left(x.keys, k)
        if x.leaf:
            x.keys.insert(i, k)

        else:
            if len(x.children[i].keys) == (2 * self.t) - 1:
                self.split_child(x, i)
                if k > x.keys[i]:
                    i += 1

            self.insert_key(x.children[i], k)
            
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
    
B = BTree(3)

for i in range(1, 30):
    B.insert([i, i])

level_counts = B.traverse_key(B.root)
for level, counts in level_counts.items():
    if level == 0:
        print(f'Level {level} (root): Key Count = {counts}')
    else:
        print(f'Level {level}: Key Count = {counts}')

total_keys = sum(counts for counts in level_counts.values())
print(f'Total number of keys across all levels: {total_keys}')