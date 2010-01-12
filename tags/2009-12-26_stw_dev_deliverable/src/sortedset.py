# Written by Stephen Weber
# stephen.t.weber@gmail.com
import pdb

class SortedSet():
    """A list of objects, having unique network addresses but sorted
    using their own inequality methods (e.g. by timestamp)."""

    def __init__(self, sourcesequence=None):
        if sourcesequence:
            self.list = sourcesequence
        else:
            self.list = list()
        if len(self.list) > 1:
            self.remove_duplicates()

    def remove_duplicates(self):
        clist = [i.addrport for i in self.list if self.list.count(i) > 1]
        for each in set(clist):
            timestamps = []
            current = 0
            for i in range(self.list.count(each)):
                local_index = self.list[current:].index(each)
                abs_index = local_index + current
                timestamps.append((abs_index, self.list[abs_index]))
                current = abs_index + 1
            maxstamp = timestamps[0]
            for each in timestamps[1:]:
                if each[1] > maxstamp[1]:
                    maxstamp = each
            timestamps.remove(maxstamp)
            indices = range(len(timestamps))
            for each,index in zip(timestamps,indices):
                del self.list[each[0]-index]

    def oldest_entry(self):
        return min(self.list)

    def get_entry(self, addrport):
        if addrport in self.list:
            return self.list[self.list.index(addrport)]
        return None

    def add_entry(self, entry):
        if entry in self.list:
            myentry = self.get_entry(entry.addrport)
            if entry > myentry:
                myentry.update(entry.timestamp)
        else:
            self.list.append(entry)

    def remove_entry(self, addrport):
        self.list.remove(addrport)

    def __len__(self):
        return len(self.list)

    def __contains__(self, item):
        return (item in self.list)

    def __str__(self):
        return '_'.join([repr(i) for i in self.list])
