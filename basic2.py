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

	# # set district number, population parameters
	kdist = 6
	pbar = int(math.ceil(sum([int(i) for i in num2pop.values()])/float(kdist)))
	alpha = 0.05
	pmin = int(math.ceil((1-alpha)*pbar))
	pmax = int(math.ceil((1+alpha)*pbar))

	for i in range(0, 51):
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
	print len(goodg)

	# print the good guesses
	for g in range(0, len(goodg)):
		print "----------------GUESS ", str(g), "------------"
		print "Reference Node:", str(goodg[g][0])
		for d in goodg[g][1]:
			s = [i+1 for i in d[0]]
			print s, " ", d[1]
	print pmin 

	#####################################################
	# TESTING 
	# print "TOTAL P", sum([int(i) for i in num2pop.values()])
	# print "PBAR", pbar
	# print "PMIN", pmin
	# print "PMAX", pmax

	# a = [[0,1,0,1,0,1,0],[1,0,0,0,1,1,1],[0,0,0,0,0,0,0,1],[1,0,0,0,0,0,1],[0,1,0,0,0,0,0],[1,1,0,0,0,0,0],[0,1,1,1,0,0,0]]
	# d = shortestPath(a, 6)
	# print d

	# findFurthestNode(a, 1, {0: 12, 1: 1, 2: 43, 3: 45, 4:99, 5:111, 6:109}, [1, 4])


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


def findInitPlan(adj, numdist, num2pop, pmin, pmax, kdist, refnode):
	districtlist = []
	L = range(0,51) # all nodes not assigned to a district 

	# find furthest unused node from reference node 
	startnode = findFurthestNode(adj, refnode, num2pop, L)
	# print "Starting at node", startnode
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


def findFurthestNode(adj, refnode, num2pop, L):
	# want to find node that's furthest from reference to start a new district 
	shorts = shortestPath(adj, refnode) # shortest paths from refnode 
	# print "the shortst options are", shorts.keys()
	# print "L is", L
	for k in shorts.keys():
		if k not in L:
			shorts.pop(k)
	# print "Now shorts is", shorts
	furthest = max(shorts.values()) # find length of longest shortest path 
	unts = [i for i in shorts.keys() if shorts[i] == furthest] # find pop units corresponding to furthest
	untswithpop = {i:num2pop[i+1] for i in unts}

	# select the start node 
	startnode = 999
	startpop = 0
	for punit, popval in untswithpop.items():
		if popval > startpop:
			startnode = punit
	return startnode


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
