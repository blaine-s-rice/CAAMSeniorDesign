from gurobipy import *
import numpy as np
import random
import math


def main():
    # STEP 1: READ DATA
    f1 = DataReader('City Name Number Mapping.txt')
    num2cit = f1.by_cols()
    f2 = DataReader('City Number Population Mapping.txt')
    num2pop = f2.by_cols()
    f3 = DataReader('Adjacency.txt')
    unassigned_nodes = list(range(0,51))
    city_adj = GraphTraverse(f3.by_matrix(), num2pop, unassigned_nodes)

    # STEP 2: set district number, population parameters
    k_dist = 6  # number of districts to create
    p_bar = int(math.ceil(sum([int(i) for i in num2pop.values()]) / float(k_dist)))  # average population per district
    alpha = 0.05  # tuning parameter
    p_min = int(math.ceil((1 - alpha) * p_bar))  # min pop per district
    p_max = int(math.ceil((1 + alpha) * p_bar))  # max pop per district

    # STEP 3: make a districting plan
    district_list = []
    while len(district_list) < 6:
        # pick a start node furthest from reference node
        start_node = city_adj.furthest_nodes(14)
        # remove the start node from list of options
        unassigned_nodes.remove(start_node)
        city_adj.change_used_list(unassigned_nodes)
        # create a district from start node
        [district, unassigned, d_pop] = create_one_district(city_adj, unassigned_nodes, p_min, p_max, start_node)
        district_list.append((district, d_pop))
        city_adj.change_used_list(unassigned)
    for d in district_list:
        print(d)
    print(p_min, p_max)


class DataReader:
    # File reader class
    def __init__(self, filename):
        with open(filename, 'r') as input_file:
            self.content = input_file.readlines()
        self.nLines = max(51, len(self.content))

    def by_cols(self):
        new_form = {}
        for itm in self.content:
            s = itm.split("\t")
            new_form[int(s[0])-1] = s[1].strip()
        return new_form

    def by_matrix(self):
        adj = np.zeros((self.nLines, self.nLines), dtype=int)
        for connects in self.content:
            s = connects.strip()
            c = [int(i) for i in s.split("\t")]
            for k in range(2, 2 + c[1]):
                adj[c[0] - 1][c[k] - 1] = 1
                adj[c[k] - 1][c[0] - 1] = 1
        return adj


class GraphTraverse:
    # Move around a population graph - including shortest path, furthest node
    def __init__(self, adj_matrix, pop_info, used_list):
        self.adjacency = adj_matrix
        self.num_nodes = len(adj_matrix)
        self.population = pop_info
        self.unassigned = used_list

    def change_used_list(self, new_list):
        self.unassigned = new_list

    def shortest_path(self, source) -> dict:
        # trackers
        visited_flag = [False]*self.num_nodes  # tracks nodes we've visited and accounted for
        d = np.ones(self.num_nodes)*np.inf  # tracks distances from source to all other nodes

        # start up BFS
        queue = [source]  # nodes line up in queue for us to visit, starting with the source
        visited_flag[source] = True
        d[source] = 0  # distance from source to itself is 0

        # graph traversal
        while queue:  # while we still have nodes to visit
            v = queue.pop(0)  # visit the next node
            neighbors = [i for i in range(0, self.num_nodes) if self.adjacency[v][i] == 1]  # find all its neighbors
            for n in neighbors:  # for each neighbor
                if not visited_flag[n]:  # if we haven't visited it yet
                    visited_flag[n] = True  # mark it as visited
                    d[n] = d[v] + 1  # distance(source -> neighbor) = distance(source -> current node) + 1
                    queue.append(n)  # put the neighbor in our queue to visit later

        # convert results into a dictionary form
        final_dist = {}
        for i in range(0, len(d)):
            if i in self.unassigned:  # delete nodes unassigned
                final_dist[i] = d[i]
        return final_dist

    def furthest_nodes(self, source):
        neighbors = {}
        graph_distances = self.shortest_path(source)
        graph_temp = dict(graph_distances)
        for k in graph_temp.keys():
            # delete nodes already used
            if k not in self.unassigned:
                graph_distances.pop(k)
        furthest = max(graph_distances.values())  # find length of longest path
        # find node values (populations) of the furthest nodes
        far_values = {i: self.population[i] for i in graph_distances.keys() if graph_distances[i] == furthest}
        return max(far_values, key=far_values.get)  # return node with highest value (population)


def create_one_district(whole_county, free_nodes, min_pop, max_pop, start_node):
    curr_pop = int(whole_county.population[start_node])
    district_members = [start_node]
    while curr_pop < min_pop:
        # collect the possible nodes we can add
        neighbors = whole_county.shortest_path(start_node)
        closest = min(neighbors.values())
        close_pops = {i: whole_county.population[i] for i in neighbors.keys() if neighbors[i] == closest}
        close_neighbors = {}
        for opts in close_pops.keys():
            close_neighbors[opts] = [i for i, val in enumerate(whole_county.adjacency[opts]) if val == 1]
            if int(close_pops[opts]) + int(curr_pop) > max_pop:
                close_neighbors.pop(opts)

        # count the number of district nodes that the new nodes are neighbors to
        near_ct = {}
        for node, neighs in close_neighbors.items():
            near_ct[node] = 0
            for i in neighs:
                if i in district_members:
                    near_ct[node] = near_ct[node] + 1

        # find the node to add
        if near_ct != {} and close_neighbors != {}:
            max_val = max(near_ct.values())
            max_list = []
            for i, j in near_ct.items():
                if j == max_val:
                    max_list.append(i)
                    district_members.append(i)
                    free_nodes.remove(i)
                    whole_county.change_used_list(free_nodes)
                    curr_pop = curr_pop + int(close_pops[i])
                    break
        else:
            break
    return [district_members, free_nodes, curr_pop]


if __name__ == "__main__":
    main()
