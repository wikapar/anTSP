# anTSP presentation: speaker script

Audience: other students. Allowed length: 10 to 15 minutes.
Timings assume a calm 130 words per minute: 15:00 min in total. At a normal pace (about 145 words per minute) it is about 12.5 min, which leaves room for speaker changes. If you run long, shorten slide 11 or 14.
Speaker split (change freely): Jordy = intro + results 3-4, Wiktoria = ants + demo + parameters, Rita = exact methods + method + results 1-2 + conclusions.

The same text is in the speaker notes of every slide.

## Slide 1: Title
about 0:30 min

Hi everyone, we are Wiktoria, Jordy and Rita. Our project is about a very old puzzle, the Travelling Salesman Problem, and about a surprising way to attack it: by copying ants. We will show you why solving it exactly breaks down, how an ant colony algorithm works, and then we put both head to head on 90 random maps and tell you honestly who wins, and where.

## Slide 2: One salesman, n cities, one question
about 0:55 min

So, what is the TSP? You get a list of cities and the distances between them. You must visit every city exactly once and come back to where you started, and you want the shortest total route. That's it, a child understands the problem. And it is everywhere: delivery vans planning routes, machines drilling thousands of holes into circuit boards, even putting pieces of DNA in the right order. Look at the picture: these are the same 12 cities. On the left a random order: 3868 units long. On the right the best possible order: 1678. Same cities, and the order alone makes the route more than twice as long. So the question is: how do we find the picture on the right?

## Slide 3: Why not just try every tour?
about 1:05 min

The obvious idea: try every order and keep the shortest. With n cities there are (n minus 1) factorial over 2 different tours. For 10 cities that's 181 thousand: a computer does that in a blink. For 20 cities it's 6 times 10 to the 16. Even at one billion tours per second, that's about two years. For 50 cities, still a tiny delivery route, it's 3 times 10 to the 62: about 10 to the 46 years. The universe is only about 10 to the 10 years old. And it's not just us being lazy: the TSP is NP-hard. Nobody knows an algorithm that solves every instance in polynomial time. Find one, and you have also solved P versus NP, which comes with a million-dollar prize. Rita will now show how far we can push the exact approach anyway.

## Slide 4: Exact algorithms: smarter, but still exponential
about 1:20 min

We implemented two exact methods. Backtracking builds the tour city by city, like walking down this tree; every leaf is a complete tour. Plain backtracking visits every leaf: that's the explosion from the last slide. The trick is branch and bound. We keep the best tour so far, and at every node we compute a lower bound: the path so far plus the minimum spanning tree of the cities that are left. The rest of the route must connect those cities, so it can't be shorter than that tree. If the bound is already worse than our best tour, the whole branch is cut: the red nodes. We also search each tour in one direction only, and start with a quick greedy tour, so we have a good bound from the first step. The second method, Held-Karp from 1962, uses dynamic programming over subsets of cities: n squared times 2 to the n steps. Much better than n factorial, but still exponential. Both always return the optimal tour. The cost still explodes, just later.

## Slide 5: What ants know about shortest paths
about 1:00 min

So if being exact is too expensive, maybe we can be clever instead, and this is where the ants come in. In 1989 biologists gave an Argentine ant colony two bridges of different length leading to food. At first ants pick a branch randomly. But ants leave pheromone, a chemical trail, and they prefer to follow strong trails. Ants on the short branch come back sooner, so that branch is reinforced faster. More ants choose it, it gets even more pheromone, and after a while most of the colony uses the short path. At the same time pheromone evaporates, so the long path is slowly forgotten. No single ant knows the map. The short path emerges from very simple rules. In the early 1990s Marco Dorigo turned exactly this into an optimization algorithm.

## Slide 6: Ant Colony Optimization in four steps
about 1:10 min

Here is the algorithm. In every iteration each virtual ant builds a full tour. At each city it picks the next one randomly, but not uniformly: the probability depends on tau, the pheromone on that road, and on one over the distance, so close cities are attractive. Alpha and beta set how much we trust each. Then all trails evaporate by a factor rho, and every ant puts pheromone on its own tour: Q over L, so shorter tours leave more. Repeat 100 times, keep the best tour. Besides the classic Ant System we built two improved versions: Elitist, which rewards the best tour so far, and MAX-MIN, where only the best ant deposits and trails stay within limits, so the colony doesn't get stuck too early. Optionally each ant also untangles crossing roads in its tour, called 2-opt. Important: this is a heuristic, with no guarantee. That's exactly why we compare it with the exact methods.

## Slide 7: Emergence: one ant vs. a colony
about 0:55 min

Is the colony more than the sum of its ants? We tested that on 30-city maps. Every group builds 2000 tours with the same rules; the only difference is the shared trail. One ant alone draws a tour about 90 percent too long. Gray: 20 ants that ignore the pheromone, so 2000 independent tries. The best is still 35 percent too long. More ants alone don't help. Light orange: one ant following its own trail. It learns fast, then gets stuck on its own route: 6 percent. Dark orange, the colony: 20 ants sharing one trail. Half a percent. No ant knows the good route. It lives in the trail they build together. That is emergence.

## Slide 8: Same map, two strategies, live (animation)
about 1:00 min

This is our simulator. Both algorithms run on the same 10-city map, one step each at a time. On the left, the ants. The orange lines are the pheromone trails, and you can see them concentrating. The green line is the best tour so far. On the right, backtracking with the MST bound; the dashed blue line is the path it is exploring right now. At the bottom you see the best length found so far for both. Watch the orange line: the ants hit the optimal tour after only 77 steps. Backtracking keeps improving, finds the same tour at step 1660, and finishes at step 1704. Only at that moment do we actually know it is optimal. That difference, finding versus proving, is the main theme of our results.

## Slide 9: How we compared them fairly
about 1:00 min

One animation proves nothing, so we ran a real experiment: 90 random maps from 5 to 50 cities, and every ACO variant 3 times per map with different seeds. 1380 runs in total. How do you compare a step of an ant with a step of backtracking? You don't. We count edge evaluations, how often an algorithm reads the length of a road, which doesn't depend on the computer. We also report CPU time. Quality is the gap to the optimal length. Up to about 25 cities the exact algorithms gave us the optimum, and they always agreed with each other, a nice correctness check. Above that we compare with the best tour anyone found. Exact algorithms were stopped after 30 seconds, and everything is seeded, so anyone can rerun it.

## Slide 10: Result 1: Exact methods hit a wall, ACO keeps going
about 0:50 min

First result: runtime, on a log scale, so every grid line means ten times more. The red line is backtracking without pruning: 3 seconds at 10 cities, and at 11 cities none of the five maps finished within 30 seconds. That's the factorial explosion, live. Held-Karp, in gray, reaches 20 cities in 7 seconds, but its time and memory double with every city we add. Branch and bound, in blue, also reaches 20. The ant algorithms, orange and green, grow slowly: under 2 seconds even at 50 cities. Fair to say: for small maps the exact methods are actually faster. If you have 10 cities, just solve it exactly.

## Slide 11: Result 2: Better bounds move the wall, but don't remove it
about 0:45 min

This zooms in on the exact methods, because the improvements were dramatic. With a simple bound, cutting when the path is already too long, we reach 12 cities in 11 seconds. With the MST lower bound the same 12 cities take 0.14 seconds, about 80 times faster, and we get to 20 cities in under 2 seconds. But look at 25 cities: only 3 of the 5 maps finished in 30 seconds. A better bound moves the wall; it doesn't remove it. Jordy will now show what the ants do in the meantime.

## Slide 12: Result 3: Finding is cheap, proving is expensive
about 1:05 min

This is our favourite plot. All maps with 12 cities. The x-axis is work, edge evaluations on a log scale, and the y-axis is how far the best tour found so far is from the optimum. Solid lines are ACO, dashed lines are exact algorithms, and a square means that algorithm finished and proved optimality. The ant curves drop to zero after roughly ten thousand evaluations; in the median, Ant System reaches its final tour after about 11 thousand. Branch and bound with the MST bound needs about 51 thousand to finish its proof, and with the simple bound it's almost 5 million. So the ants are fast at finding a very good tour. What they can never do is tell you it is the best one. The exact methods spend most of their effort on that proof.

## Slide 13: Result 4: How good are the ants?
about 1:00 min

So how good are the ants? Up to 25 cities, where we know the optimum, plain Ant System found the optimal tour in 209 of 219 runs, about 95 percent, and when it missed, it was less than one percent too long. MAX-MIN with 2-opt found the optimum in every single run. Beyond 25 cities is the gray zone, where we compare with the best tour anyone found. At 50 cities Ant System is about 5 percent above it, MAX-MIN about 3 percent, and MAX-MIN with 2-opt 0.05 percent. One surprise: the Elitist variant was not better than plain Ant System on our maps. Our guess is that giving the best tour so much extra weight makes the colony settle too early, but we did not test that further.

## Slide 14: Result 5: Parameters matter
about 1:00 min

ACO has knobs, so we tested them on 40-city maps, 3 maps times 3 runs for each setting. The heatmap shows alpha, the weight of the pheromone, against beta, the weight of the distance. The left column is beta equal to zero: ants that only follow pheromone and ignore distance. They are more than 200 percent worse. So the distance information is essential; pheromone alone is not enough. The best combination was alpha 1 and beta 3, under 1 percent. On the right is evaporation. With almost no evaporation, 0.02, old bad trails never disappear: 5.5 percent. Around 0.2 to 0.6 is the sweet spot. And more ants help: 1 ant gives 13 percent, 40 ants about 1 percent, but every ant also costs time.

## Slide 15: Conclusions: What we learned
about 1:10 min

To sum up. Exact algorithms give a guarantee, and with good pruning they're fast for small problems: up to about 20 to 25 cities in our Python code. After that the cost explodes, no matter how clever the bound. Ant colony optimization gives no guarantee, but it found the optimum in about 95 percent of the small cases, stayed within a few percent at 50 cities, and its cost grows slowly. And the two combine nicely: the ants' tour can be the starting bound for branch and bound. The ants find, the exact method proves. Our tool supports that. To be honest about limitations: our maps are random points, not real roads; it's Python on one laptop, so trust the trends, not the absolute times. Professional solvers like Concorde solve tens of thousands of cities exactly. And above 25 cities our reference is the best known tour, not a proven optimum.

## Slide 16: Thank you / Questions
about 0:15 min

Thank you! The code is on GitHub. You can run python anTSP.py and watch the ants yourself, or rerun all our experiments with one command. We're happy to take your questions.
