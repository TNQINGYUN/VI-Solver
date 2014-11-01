import numpy as np

from Projection import *
from Utilities import *
from Solver import Solver

class DriftABE_Exact(Solver):

    def __init__(self,Domain,P=IdentityProjection(),Delta0=1e-2,GrowthLimit=2,MinStep=-1e10,MaxStep=1e10):
        
        self.F = Domain.F

        self.F_curl = Domain.F_curl

        self.Proj = P

        self.StorageSize = 3

        self.TempStorage = {}

        self.Delta0 = Delta0

        self.GrowthLimit = GrowthLimit

        self.MinStep = MinStep

        self.MaxStep = MaxStep

        self.Mod = 10 #(100)

        self.Agg = 10 #(10)

    def InitTempStorage(self,Start,Domain,Options):

        self.TempStorage['Data'] = self.StorageSize*[Start]
        self.TempStorage[self.F] = self.StorageSize*[self.F(Start)]
        self.TempStorage['Step'] = self.StorageSize*[Options.Init.Step]
        self.TempStorage['F Evaluations'] = self.StorageSize*[1]
        self.TempStorage['Projections'] = self.StorageSize*[0]
        self.TempStorage['F_2norm'] = self.StorageSize*[np.dot(self.TempStorage[self.F][-1],self.TempStorage[self.F][-1])]

        return self.TempStorage

    # BookKeeping(self,TempData) defined in super class 'Solver'

    def Update(self,Record):

        # Retrieve Necessary Data
        Data = Record.TempStorage['Data'][-1]
        Step = Record.TempStorage['Step'][-1]

        # Initialize Storage
        TempData = {}

        # Choose Agent for Curl Component
        agent_i = 0#np.random.randint(Data.shape[0])

        if (Record.thisPermIndex>=self.Mod) and (Record.thisPermIndex%self.Mod == 0):

            # Compute Curl Component for Agent i
            F = Record.TempStorage[self.F][-1]
            F[agent_i] = F[agent_i] - self.Agg*self.F_curl(Data)[agent_i]

            # Perform Euler Update
            NewData = self.Proj.P(Data,Step,F)

            # Record Projections
            TempData['Projections'] = 1 + self.TempStorage['Projections'][-1]

        else:

            # Perform Adams Bashforth Update
            Fs = Record.TempStorage[self.F]
            NewData = self.Proj.P(Data,Step,-0.5*Fs[-2]+1.5*Fs[-1])

            # Perform Euler Update
            _NewData = self.Proj.P(Data,Step,Fs[-1])

            # Adjust Stepsize
            Delta = max(abs(NewData-_NewData))
            if Delta == 0.: Step = 2.*Step
            else: Step = max(min(Step*min((self.Delta0/Delta)**0.5,self.GrowthLimit),self.MaxStep),self.MinStep)

            # Record Projections
            TempData['Projections'] = 2 + self.TempStorage['Projections'][-1]

        # Store Data
        TempData['Data'] = NewData
        TempData[self.F] = self.F(NewData)
        TempData['Step'] = Step
        TempData['F Evaluations'] = 1 + self.TempStorage['F Evaluations'][-1]
        TempData['F_2norm'] = np.dot(TempData[self.F],TempData[self.F])
        self.BookKeeping(TempData)
        
        return self.TempStorage




