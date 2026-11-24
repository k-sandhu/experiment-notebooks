# Routes

Find the shortest road distances from a few starting points in a large road network.

## Input

```
N M Q
u v w
...
s1 s2 ... sQ
```

The first line gives the number of nodes N, the number of roads M and the number of sources Q. Nodes are
numbered 0 to N-1. Each of the next M lines is an undirected road between nodes u and v with length w, an
integer from 1 to 1000. There can be several roads between the same two nodes, and roads from a node to
itself. The last line lists the Q source nodes, separated by single spaces. Some nodes cannot be reached from
some sources.

## Output

One line per source, in input order:

```
s R TOTAL FAR NODE
```

s is the source. R is the number of nodes reachable from s, counting s itself. TOTAL is the sum of the
shortest distances from s to all reachable nodes, and FAR is the largest of those distances. NODE is the
smallest node number whose shortest distance from s equals FAR. All values fit in a signed 64-bit integer.

## Benchmark size

N = 300,000 nodes, M = 900,000 roads and Q = 6 sources. The samples are smaller.
