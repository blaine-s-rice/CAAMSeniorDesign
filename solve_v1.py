from gurobipy import * 
import numpy as np
import random
import math 

def main():
	c = [15, 7, 8, 17, 9, 13]
	d0 = [3, 5, 6, 7, 10, 11, 17, 20, 29, 31, 42]
	d1 = [1, 4, 25, 27, 34, 41]
	d2 = [8, 12, 16, 23, 24, 48, 50]
	d3 = [15, 18, 19, 30, 32, 33, 35, 38, 39, 44]
	d4 = [13, 14, 26, 46, 47, 49, 51]
	d5 = [2, 9, 21, 22, 28, 36, 37, 40, 43, 45]
	districts = [d0, d1, d2, d3, d4, d5]
	deltas = np.zeros((51, 6), dtype = int)
	for d in range(0, 6):
		for i in districts[d]:
			deltas[i-1][d] = 1
	for d in deltas:
		print d

	m = Model("Test1")
	x = {}
	for k in range(0, 6):
		x[k] = m.addVar(vtype=GRB.BINARY, name="x[%d]"%k)
	m.update()

	m.setObjective(LinExpr(c, x.values()), GRB.MINIMIZE)

	for i in range(51):
		m.addConstr(LinExpr(deltas[i], x.values()), "=", 1)

	m.update()

	r = m.relax()
	r.optimize()

	for v in r.getVars():
		print v.varName
		print v.x



if __name__ == "__main__":
	main()
