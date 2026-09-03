# Graph GPU thresholds

GPU use starts to make sense when the graph work is large or repeated.

Typical cases:
- tens or hundreds of thousands of edges for repeated work
- around one million or more nodes/edges for clearer benefit
- many graphs processed in a batch
- repeated relax/filter/scoring passes over the same data

Many passes are needed when the algorithm is iterative or search-heavy:
- A* on a large graph
- Dijkstra or Bellman-Ford
- beam search
- multi-source routing
- constraint filtering
- re-ranking or scoring after each expansion
- evolutionary search with repeated weight updates

Rule of thumb:
- small demo graphs should stay on CPU
- large repeated graph work can benefit from GPU acceleration
