import gurobipy 
import numpy as np
import random
import math 

fname1 = 'City Name Number Mapping.txt'
fname2 = 'City Number Population Mapping.txt'
fname3 = 'Adjacency.txt'

def main():
	# read data
	num2cit = readTwoCol(fname1) 
	num2pop = readTwoCol(fname2)
	adjcities = readAdjacency(fname3, len(num2cit.keys()))

	# set district number, population parameters
	kdist = 6
	pbar = int(math.ceil(sum([int(i) for i in num2pop.values()])/float(kdist)))
	alpha = 0.05
	pmin = int(math.ceil((1-alpha)*pbar))
	pmax = int(math.ceil((1+alpha)*pbar))

	# create initial guess 
	degdict = findInitPlan(adjcities, kdist, num2pop, pmin, pmax)


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


def findInitPlan(adj, numdist, num2pop, pmin, pmax):
	districtlist = []
	refnode = 14 # random.randint(0,50) # reference node
	L = range(0,50) # all nodes not assigned to a district 

	# deg[i] = num nodes in L that are adjacent to node i 
	degdict = {}
	for i in range(0, len(adj)):
		degdict[i] = sum(adj[i])

	startnode = findFurthestNode(adj, refnode, num2pop)


	L.remove(startnode) # remove v from L
	M = [] # list of nodes in new district S
	M.append(startnode) 
	print M

	degM = {}
	for i in range(0, len(adj)):
		degM[i] = sum([adj[i][j] for j in M])
	print degM

	popM = sum([int(num2pop[ctnum+1]) for ctnum in M])
	print popM


	for i in range(0, 1):
		[M, newL] = createDistrict(adj, num2pop, L, M, popM, pmin, pmax, startnode)
		L = newL 
		districtlist.append(M)

	return districtlist


def createDistrict(adj, num2pop, L, M, popM, pmin, pmax, startnode):
	# add nodes until terminate
	while popM < pmin:
		# find closest nodes 
		nshorts = shortestPath(adj, startnode)
		print nshorts

		# remove things already in the district 
		for i in M:
			nshorts.pop(i)

		# find the closest node 
		closest = min(nshorts.values())
		nunts = [i for i in nshorts.keys() if nshorts[i] == closest]

		# get their corresponding populations 
		nuntswithpop = {i:int(num2pop[i+1]) for i in nunts}

		print "SHORT"
		print nshorts
		print "CLOSEST"
		print closest
		print "UNITS"
		print nunts

		for i in nunts: 
			# add the first one we find which doesn't exceed pmax 
			if popM + nuntswithpop[i] <= pmax:
				M.append(i)
				print "WE ADD " + str(i)
				print i 
				L.remove(i)
				popM = popM + nuntswithpop[i]
				break

		print "THIS IS M"
		print M
	return [M, L] 


def findFurthestNode(adj, refnode, num2pop):
	# want to find node that's furthest from reference to 
	# start a new district 
	shorts = shortestPath(adj, refnode) # shortest paths from refnode 
	furthest = max(shorts.values()) # find length of longest shortest path 
	unts = [i for i in range(0, len(shorts.values())) if shorts[i] == furthest] # find pop units corresponding to furthest
	untswithpop = {i:num2pop[i+1] for i in unts}

	# select the start node 
	startnode = 999
	startpop = 0
	for punit, popval in untswithpop.items():
		if popval > startpop:
			startnode = punit
	return startnode


def shortestPath(adj, source):
	# BFS implementation 
	flag = [False] * (len(adj))
	pred = [-1] * (len(adj))
	d = np.ones(len(adj)) * np.inf

	queue = []
	flag[source] = True
	queue.append(source)
	d[source] = 0
	print source

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



if __name__ == "__main__":
	main()
