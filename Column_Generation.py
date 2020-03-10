# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 11:11:42 2020

@author: jaked
"""

from gurobipy import *
import numpy as np
import random
import math 

fname1 = 'City Name Number Mapping.txt'
fname2 = 'City Number Population Mapping.txt'
fname3 = 'Adjacency.txt'

def main():
    goodg = []
    # read data
    num2cit = readTwoCol(fname1) 
    num2pop = readTwoCol(fname2)
    adjcities = readAdjacency(fname3, len(num2cit.keys()))
    populations = list(num2pop.values())
    populations = [int(i) for i in populations]

    # # set district number, population parameters
    kdist = 6
    pop_centers = 51
    pbar = int(math.ceil(sum([int(i) for i in num2pop.values()])/float(kdist)))
    alpha = 0.05
    pmin = int(math.ceil((1-alpha)*pbar))
    pmax = int(math.ceil((1+alpha)*pbar))
    
    for i in range(0, pop_centers):
        refnode = i
        guess = findInitPlan(adjcities, kdist, num2pop, pmin, pmax, kdist, refnode)
        
        f = True
        for d in guess:
            if d[1] > pmax or d[1] < pmin:
            # if guess contains districts that don't satisfy population req.
            # do not use this guess 
                f = False
            d[0].sort()
        if f:
            goodg.append((refnode, guess))
    # form constraint matrix and cost vector for Master problem
    districts = []
    startnodes = []
    # Using all initial guesses, compile districts into an array
    for g in range(0, len(goodg)):
        startnodes.append(goodg[g][0])
        for d in goodg[g][1]:
            s = [i+1 for i in d[0]]
            districts.append(d[0])   
    
    
    # Creates Array each element is the number of edges in the shortest path from population center i 
    # to population center j
    S = shortestPathArray(adjcities)
    
    # Get costs of districts and create cost vector
    costs = []

    for d in districts:
        i = 0
        U = startnodes[i]
        costs.append(cost_district(d,S,U))
        i = i + 1
    
    # Column Generation 
    obj_value = -1
    while obj_value < 0:
        dual_sols = masterDual(districts,costs,pop_centers)
        print(dual_sols)
        [new_district, refnode, obj_value] = subProblem(dual_sols,districts,S,populations,pmin,pmax)
        districts.append(new_district)
        cost_column = cost_district(new_district,S)
        costs = costs.append(cost_column)
    
    
def master(districts,costs,pop_centers):      
    deltas = np.zeros((pop_centers, len(districts)), dtype = int)
    for d in range(0, len(districts)):
        for i in districts[d]:
            deltas[i-1][d] = 1

    m = Model()
    
    x = {}
    for k in range(0, len(districts)):
        x[k] = m.addVar(vtype=GRB.BINARY, name="x[%d]"%k)
    m.update()
    
    m.setObjective(LinExpr(costs, x.values()), GRB.MINIMIZE)
    for i in range(0,pop_centers):
        m.addConstr(LinExpr(deltas[i], x.values()), "=", 1)
    
    m.addConstr(quicksum(x.values()) == 1)
    
    m.update()
    m.optimize()
    return m.getVars()

def masterDual(districts,costs,pop_centers):      
    deltas = np.zeros((pop_centers, len(districts)), dtype = int)
    for d in range(0, len(districts)):
        for i in districts[d]:
            deltas[i-1][d] = 1
    
    np.append(deltas,[0]*len(districts))
    deltas_t = np.transpose(deltas)
    
    m = Model()

    y = {}
    for k in range(0, pop_centers):
        y[k] = m.addVar(vtype=GRB.BINARY, name="y[%d]"%k)
    m.update()
    
    obj_vector = [1]*pop_centers
    m.setObjective(LinExpr(obj_vector,y.values()), GRB.MAXIMIZE)
    
    for j in range(0, len(districts)):
        m.addConstr(LinExpr(deltas_t[j], y.values()), "=", costs[j])

    m.update()
    r = m.relax()
    r.optimize()
    sol_vector = []
    for v in r.getVars():
        sol_vector.append(v) 
    return r.status

def subProblem(dual_sols,districts,S,populations,pmin,pmax):
    obj_value = 1000000000000000
    sol_u = []
    for j in range(0,len(populations)):
        u = j
        m = Model()
        y = {}
        nodes = list(range(0,len(populations)))
        nodes.remove(u)
        
        for k in range(0,len(nodes)):
            y[k] = m.addVar(vtype=GRB.BINARY, name="y[%d]"%k)
            
        m.update()
        
        costs = []
        for i in nodes:
            costs.append(S[u][i] - dual_sols[i])
        
        pops_no_startnode = populations
        del pops_no_startnode[u]

        # Population requirements
        m.addConstr(LinExpr(pops_no_startnode,  y.values()),"<=",pmax - populations[u])
        m.addConstr(LinExpr(pops_no_startnode,  y.values()),">=",pmin - populations[u])
    
        m.setObjective(LinExpr(costs, y.values()), GRB.MAXIMIZE)
        m.update()
        m.optimize()
        
        new_obj_value =-1*dual_sols[u] - dual_sols[-1] + m.objval

        if new_obj_value < obj_value:
            obj_value = new_obj_value
            sol_vector = []
            for v in m.getVars():
                sol_vector.append(v.y)           
            min_u = j

    return [sol_vector, min_u, obj_value]
    
def readTwoCol(fname):
    # NOTE: For output dict, key is int but value is string 
    infodict = {}
    with open(fname) as f:
        data = [c.strip() for c in f.readlines()]
        for city in data:
            s = city.split("\t")
            infodict[int(s[0])] = s[1]
    return infodict


def readAdjacency(fname, numcities):
    adjmat = np.zeros((numcities, numcities), dtype = int)
    with open(fname) as f:
        data = [d.strip() for d in f.readlines()]
        for connects in data:
            c = [int(s) for s in connects.split("\t")]
            for k in range(2,2+c[1]):
                adjmat[c[0]-1][c[k]-1]= 1
                adjmat[c[k]-1][c[0]-1] = 1
    return adjmat

def dfs(graph, node, path = []):
    path += [node]

    for neighbor in graph[node]:
        if neighbor not in path:
            path = dfs(graph, neighbor, path)

    return path

def findInitPlan(adj, numdist, num2pop, pmin, pmax, kdist, refnode):
    districtlist = []
    L = list(range(0,51)) # all nodes not assigned to a district 
    # find furthest unused node from reference node 
    startnode = findFurthestNode(adj, refnode, num2pop, L)

    # print ("Starting at node", startnode)
    M = [startnode]
    L.remove(startnode)
    popM = int(num2pop[startnode+1])

    for i in range(0, kdist-1):
        # print "--------------------"
        # print "Creating District", i
        # print "THE OLD L", L
        [newM, newL, newpop] = createDistrict(adj, num2pop, L, M, popM, pmin, pmax, startnode)
        # print "THE NEW L", newL
        L = newL 
        districtlist.append((M, newpop))
        startnode = findFurthestNode(adj, refnode, num2pop, L)
        M = [startnode]
        popM = int(num2pop[startnode+1])
        L.remove(startnode)
        # print districtlist
    districtlist.append((L, sum([int(num2pop[i+1]) for i in L])))
    # for d in districtlist:
        # print d
    return districtlist 


def shortestPath(adj, source):
    # BFS implementation 
    flag = [False] * (len(adj))
    pred = [-1] * (len(adj))
    d = np.ones(len(adj)) * np.inf

    queue = []
    flag[source] = True
    queue.append(source)
    d[source] = 0

    while queue != []:
        v = queue.pop(0)
        neighbors = [i for i in range(0, len(adj)) if adj[v][i] == 1]
        for n in neighbors:
            if flag[n] == False:
                flag[n] = True
                pred[n] = v
                d[n] = d[v] + 1
                queue.append(n)
    dfinal = {}
    for i in range(0, len(d)):
        dfinal[i] = d[i]
    return dfinal 

def shortestPathArray(adj):
    # Shortest path Array initialized as a numpy array of infinities
    S = np.ones([len(adj),len(adj)])*float('inf')
    for i in range(0,len(adj)):
        paths = shortestPath(adj,i)
        S[i] = list(paths.values())
    return S

def findFurthestNode(adj, refnode, num2pop, L):
    # want to find node that's furthest from reference to start a new district 
    shorts = shortestPath(adj, refnode) # shortest paths from refnode 
    # print "the shortest options are", shorts.keys()
    # print("L is", L)
    
    # Creates copy of shorts.keys() to eliminate nodes in the current district from shorts
    hold = shorts.keys()
    for k in list(hold):
        if k not in L:
            shorts.pop(k)
    # print "Now shorts is", shorts
    furthest = max(shorts.values()) # find length of longest shortest path
    unts = [i for i in shorts.keys() if shorts[i] == furthest] # find pop units corresponding to furthest
    untswithpop = {i:num2pop[i+1] for i in unts}
    
    # select the start node 
    startnode = 999
    startpop = 0

    for popval in untswithpop.keys():
        if popval >= startpop:
            startnode = popval
    return startnode

def cost_district(district,S,U):
    cost = 0
    for i in district:
        cost = cost + S[U][i]
    return cost

def createDistrict(adj, num2pop, L, M, popM, pmin, pmax, startnode):
    # add nodes until terminate
    while popM < pmin:
        # print "popM ", popM
        # print "pmin", pmin
        # find closest nodes 
        nshorts = shortestPath(adj, startnode)
        
        # remove things already in the district 
        for i in range(0, 51):
            if i not in L:
                nshorts.pop(i)

        # find the closest node 
        closest = min(nshorts.values())
        nunts = [i for i in nshorts.keys() if nshorts[i] == closest]
        # print "NUNTS", nunts

        # get their corresponding populations 
        nuntswithpop = {i:int(num2pop[i+1]) for i in nunts}
        
        # find things that the closest nodes are adjacent to 
        nearkeys = {}
        # print "OLD N UNITS W POP IS", nuntswithpop
        for opts in nuntswithpop.keys():
            nearkeys[opts] = [i for i, val in enumerate(adj[opts]) if val == 1]
            # print nuntswithpop[opts] + popM
            if nuntswithpop[opts] + popM > pmax:
            # delete things that break the population req 
                nearkeys.pop(opts)
        # print "N UNITS W POP IS", nuntswithpop
        # print "NEAR KEYS IS THIS", nearkeys

        # count how many nodes in district, the nodes in nearkeys are closest to 
        nearcts = {}
        for node, neighs in nearkeys.items():
            nearcts[node] = 0
            for i in neighs:
                if i in M:
                    nearcts[node] = nearcts[node] + 1
        # print "Nearcts is this", nearcts

        # add the node that is adjacent to most nodes already in the district 
        # pick the first one if there are multiple
        if nearcts != {} and nearkeys != {}:
            maxval = max(nearcts.values())
            maxlist = []
            for i, j in nearcts.items():
                if j == maxval:
                    maxlist.append(i)
                    M.append(i)
                    # print "WE ADD " + str(i)
                    L.remove(i)
                    popM = popM + nuntswithpop[i]
                    # print "Population is now ", popM 
                    break
            # print "MAXLISt", maxlist
        else:
            break 
    return [M, L, popM] 


if __name__ == "__main__":
    main()
