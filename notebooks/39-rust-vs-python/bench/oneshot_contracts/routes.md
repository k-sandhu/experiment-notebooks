- Input: line 1 is `N M Q`. Then exactly M lines `u v w` with 0 <= u, v < N and 1 <= w <= 1000, then one line
  with Q source node numbers separated by single spaces. Roads are undirected. A road can join a node to
  itself, and several roads with different lengths can join the same two nodes.
- Output: exactly Q lines, one per source in input order, `s R TOTAL FAR NODE`, and nothing else.
- R counts the reachable nodes, including s itself at distance 0. A source with no roads prints `s 1 0 0 s`.
  Unreachable nodes are left out of R, TOTAL, FAR and NODE.
- TOTAL can exceed 2^31, so add it up in 64 bits. NODE is the smallest node number whose shortest distance
  equals FAR.
