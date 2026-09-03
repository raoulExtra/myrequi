# Graph GPU info

A practical way to use the phone GPU for graph work is to
reserve the GPU for bulk edge operations and keep control
logic on the CPU.

Good GPU fits:
- A* and other path scoring steps
- edge relaxation in shortest-path work
- batch weight updates
- parallel edge filtering
- neighbor expansion
- similarity or scoring across many edges

## Detail

### Edge relaxation in shortest-path work
Edge relaxation updates the tentative distance for a
neighbor using the current best known distance plus the edge
cost. Many edges can be checked in parallel, which is why
GPUs can help when the graph is large.

### Batch weight updates
If many node or edge weights need to be adjusted together, a
GPU can apply the same operation to many items at once.

### Parallel edge filtering
A GPU can test many edges against the same rule set at the
same time, such as removing edges below a threshold or
keeping only edges that match a predicate.

### Neighbor expansion
When exploring a frontier node set, a GPU can expand many
neighbors in parallel and gather candidate next steps faster
than a purely serial loop.

### Similarity / scoring across many edges
If many edges need a score or similarity measure, the GPU
can compute those scores in parallel and return the best
candidates.

Suggested division of labor:
- **CPU**: load the graph, manage SQLite, choose start/goal,
  coordinate work
- **GPU**: process many edges or nodes in parallel
- **CPU**: collect results and write them back to the DB

Practical workflow:
1. load graph from SQLite
2. export graph slices to GPU-friendly arrays
3. run a kernel on edges or nodes
4. store results back in the database

For this project, SQLite stays the source of truth and the
GPU is an accelerator for repeated graph computations.
