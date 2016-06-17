"""
    rotation
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
from collections import defaultdict

import numpy

from mceditlib.blocktypes import parseBlockstate, joinBlockstate, PCBlockTypeSet

log = logging.getLogger(__name__)


def blankRotationTable():
    table = numpy.indices((32768, 16))

    # Roll array so table[x, y] returns [x, y]
    table = numpy.rollaxis(numpy.rollaxis(table, 1), 2, 1)
    return table


class BlockRotations(object):
    mappings = {
        'y': {
            'north': 'east',
            'east': 'south',
            'south': 'west',
            'west': 'north',
        },
        'x': {
            'up': 'south',
            'south': 'down',
            'down': 'north',
            'north': 'up',
        },
        'z': {
            'east': 'up',
            'up': 'west',
            'west': 'down',
            'down': 'east',
        }
    }

    axisMappings = {
        'y': {
            'x': 'z',
            'z': 'x',
        },
        'x': {
            'y': 'z',
            'z': 'y',
        },
        'z': {
            'x': 'y',
            'y': 'x',
        },

    }

    railShapes = {
        'ascending_north': 'ascending_east',
        'ascending_east': 'ascending_south',
        'ascending_south': 'ascending_west',
        'ascending_west': 'ascending_north',
        'east_west': 'north_south',
        'north_east': 'south_east',
        'south_east': 'south_west',
        'south_west': 'north_west',
        'north_west': 'north_east',

    }

    def __init__(self, blocktypes):
        self.blocktypes = blocktypes

        self.blocksByInternalName = defaultdict(list)

        for block in self.blocktypes:
            self.blocksByInternalName[block.internalName].append(block)

        self.rotateY90 = self.buildTable(axis='y')
        self.rotateX90 = self.buildTable(axis='x')
        self.rotateZ90 = self.buildTable(axis='z')

    def buildTable(self, axis):
        mapping = self.mappings[axis]
        axisMapping = self.axisMappings[axis]

        table = blankRotationTable()

        for block in self.blocktypes:
            state = block.stateDict
            if not len(state):
                continue

            # First pass: facing=north and similar
            newState = {}
            for k, v in state.items():
                n = mapping.get(v)
                if n:
                    newState[k] = n
                else:
                    newState[k] = v

            state = newState
            newState = dict(state)

            # Second pass: north=true and similar
            for k, v in mapping.items():
                if k in state:
                    if state[k] == 'true':
                        newState[k] = 'false'
                        newState[v] = 'true'

            state = newState

            if axis == 'y':
                # For signs and banners: rotation=10 and similar

                if 'rotation' in state:
                    rotation = (int(state['rotation']) + 4) % 16
                    state['rotation'] = unicode(rotation)

                # For rails, powered rails, etc: shape=north_east

                if 'shape' in state:
                    shape = state['shape']

                    newShape = self.railShapes.get(shape)
                    if newShape:
                        state['shape'] = newShape

            # For logs and such: axis=x and similar

            if 'axis' in state:
                axis = state['axis']
                axis = axisMapping.get(axis, axis)
                state['axis'] = axis

            #print("Changed %s \nto %s" % (stateString, newStateString))

            newBlock = self.matchingState(block.internalName, state)
            if newBlock is block:
                pass
            # elif newBlock is None:
                # newStateString = joinBlockstate(state)
                # print("no mapping for %s%s" % (block.internalName, newStateString))
            elif newBlock is not None:
                # print("Changed %s \nto %s" % (block, newBlock))
                table[block.ID, block.meta] = [newBlock.ID, newBlock.meta]

        return table

    def matchingState(self, internalName, stateDict):
        """
        Find the first block with the given name whose state matches all of the keys
        and values in stateDict.

        Parameters
        ----------
        internalName : unicode
            block's internal name
        stateDict : dict
            the keys and values that the returned state must match

        Returns
        -------

        block: BlockType

        """
        for b in self.blocksByInternalName[internalName]:
            bsd = b.stateDict
            for k, v in stateDict.iteritems():
                if bsd.get(k) != v:
                    break
            else:
                return b

        return None


def xxxtest_yAxisTable():
    from . import PCBlockTypeSet
    blocktypes = PCBlockTypeSet()
    table = yAxisTable(blocktypes)

    assert (table != blankRotationTable()).any(), "Table is blank"

    changed = False
    changedNames = set()
    for i in range(32768):
        for j in range(16):
            e = table[i,j]
            if e[0] != i or e[1] != j:
                changed = True
                name = blocktypes[i, j].internalName
                if name not in changedNames:
                    # print("%s is changed" % name)
                    changedNames.add(name)

    assert changed, "Table is unchanged"

def main():
    from timeit import timeit
    blocktypes = PCBlockTypeSet()

    secs = timeit(lambda: BlockRotations(blocktypes), number=1)
    print("Time: %0.3f" % secs)

    assert secs < 0.1

if __name__ == '__main__':
    main()