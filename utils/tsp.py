"""Small TSP helpers shared by the algorithms. They work on node ids and a distance matrix
and return how many edge evaluations they used, so the work can be counted fairly."""


def tour_length(tour_ids: list[int], matrix) -> float:
    """Length of a closed tour given as [a, b, ..., a]."""
    return sum(matrix[tour_ids[i]][tour_ids[i + 1]] for i in range(len(tour_ids) - 1))


def nearest_neighbour_tour(start: int, matrix) -> tuple[list[int], int]:
    """Greedy tour: always go to the closest unvisited node. Returns (closed tour, evaluations)."""
    n = len(matrix)
    tour = [start]
    unvisited = set(range(n)) - {start}
    evaluations = 0
    while unvisited:
        current = tour[-1]
        evaluations += len(unvisited)
        nearest = min(unvisited, key=lambda node: (matrix[current][node], node))
        tour.append(nearest)
        unvisited.remove(nearest)
    tour.append(start)
    return tour, evaluations


def two_opt(tour_ids: list[int], matrix) -> tuple[list[int], int]:
    """2-opt local search: reverse a part of the tour while that makes it shorter.
    Takes and returns a closed tour [a, ..., a]. Returns (tour, evaluations)."""
    route = tour_ids[:-1]
    n = len(route)
    evaluations = 0
    if n < 4:
        return tour_ids[:], 0

    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            a, b = route[i], route[i + 1]
            row_a = matrix[a]
            d_ab = row_a[b]
            # j stops before the edge that touches (a, b)
            for j in range(i + 2, n if i > 0 else n - 1):
                c, d = route[j], route[(j + 1) % n]
                evaluations += 4
                delta = row_a[c] + matrix[b][d] - d_ab - matrix[c][d]
                if delta < -1e-9:
                    route[i + 1:j + 1] = reversed(route[i + 1:j + 1])
                    improved = True
                    b = route[i + 1]
                    d_ab = row_a[b]
    return route + [route[0]], evaluations


def mst_length(node_ids: list[int], matrix) -> tuple[float, int]:
    """Length of the minimum spanning tree over the given nodes (Prim, O(k^2)).
    Returns (length, evaluations)."""
    k = len(node_ids)
    if k <= 1:
        return 0.0, 0
    first = node_ids[0]
    rest = node_ids[1:]
    best = {node: matrix[first][node] for node in rest}
    total = 0.0
    evaluations = len(rest)
    while best:
        node = min(best, key=best.get)
        total += best.pop(node)
        row = matrix[node]
        evaluations += len(best)
        for other in best:
            if row[other] < best[other]:
                best[other] = row[other]
    return total, evaluations
