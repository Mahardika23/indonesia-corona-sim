#
# Corona simulator for Indonesia 
#
# Copyright (C) 2020 - Arya Gamas Mahardika <aryagamas@gmail.com>
# This software is declared as Public Domain.
# 
# Disclaimer: Results is not guaranteed. Only for academic purposes.
# 

import simpy
import inspect
import math
import random
import os
from random import seed,randint
from collections import namedtuple
from recordtype import recordtype

# Configuration by Cluster
# ro = r0 factor
# hosprob = hospitalization probability
# isoprob = isolation probability
# medcnt = medical facilities count (bed-count)
# dstart = start range of dead (in days)
# dend = end range of dead (in days)
# hstart = start range of heal (in days)
# dend = end range of heal (in days)
Config = namedtuple('Config', 'ro hosprob isoprob medcnt dstart dend hstart hend')
Config = {
        'Jakarta' : Config(1, 50, 30, 1000, 5, 15, 14, 30), 
        'Bandung' : Config(1, 50, 50, 1000, 5, 15, 14, 30)
        }

# Recording data structure
# total = total patient count
# infect = total still has infecting probablity
# hosp = hospitalized patient count
# isol = isolated patient count
# danger = patient not hospitalized not isolated
# died = total death 
# heal = total healed
# XXX: Total available Medical fascility for Hospitalization = Config.medcnt - ClusterState.hosp
ClusterState = recordtype('ClusterState', 'total infect hosp isol danger died heal') 

# Clusters Initial State
JakartaCluster = ClusterState(0, 0, 0, 0, 0, 0, 0)

# Patient data structure records: 
# id = ID of patient (City + number) 
# doi = when (day) got infection
# hop = hospitalization probability
# iso = isolation act (yes, no)
# trv = traveling probability
# inf = infecting probablity
# infstat = infecting status (1=yes, 2=no)
# dday = if probable of dying, die day 
# hday = if probable of healing, healing day 
Patient = recordtype('Patient', 'id doi hop iso trv inf infstat dday hday')

# Dict of Patients
PatientArr = {} 

# Dict of Patients die or healed
HealOrDieList = {}

# RO probability
ROPROB = 90

# function to generate probability Array
def randomSeedArray(pctFail):
    someArray = []
    choices = [1,2] #1 === good option  2 === bad bad bad
    cnt = 0
    for i in range(100):
        c = random.choice(choices)
        if c == 2: 
            cnt+=1
        if cnt > pctFail:
            c = 1
        if i >= (100-pctFail) and cnt < pctFail :
            c = 2 
            cnt+=1
        someArray.append(c)
    #print(someArray)
    return someArray

def Jakarta(env, start_with):
    global Config
    global JakartaCluster
    global PatientArr
    global HealOrDieList

    HealOrDieArray = randomSeedArray(8)

    fname = inspect.stack()[0][3] # get function name
    Config = Config[fname]

    print('Jakarta started with %d patient at %d' % (start_with, env.now))

    JakartaCluster.total = start_with
    JakartaCluster.infect = start_with
    JakartaCluster.hosp = 0
    JakartaCluster.isol = 0
    JakartaCluster.danger = start_with
    JakartaCluster.died = 0
    JakartaCluster.heal = 0

    NewPatient = Patient('Jakarta1', env.now, 0, 0, 0.5, 100, 1, -1, 14)
    PatientArr['Jakarta1'] = NewPatient

    curIndex = 1
    while True:
        add_patient = CalcNewInfection(JakartaCluster, Config)

        for i in range (add_patient):
            curIndex = int(JakartaCluster.total+1)
            # Shuffle our magic array

            NewPatient = Patient('Jakarta'+str(curIndex), env.now, 0, 0, 0.5, 90, 2, -1, 14)
            JakartaCluster.total += 1
            JakartaCluster.danger += 1
            
            
            Hospitalized(env, JakartaCluster, NewPatient, Config)
            if NewPatient.hop != 1 :
                Isolate(env, JakartaCluster, NewPatient, Config)

            if NewPatient.hop == 1 or NewPatient.iso == 1 : NewPatient.inf = 10
            else : NewPatient.inf = 90

            Infect(env, JakartaCluster, NewPatient, Config)
            
            probHealOrDie = random.choice(HealOrDieArray)
            random.shuffle(HealOrDieArray)

            #print('PROB HEAL DIE %d' % probHealOrDie)
            if probHealOrDie == 1: #heal
                hday = env.now + randint(Config.hstart, Config.hend)
                NewPatient.dday = -1
                NewPatient.hday = hday
                if hday not in HealOrDieList: HealOrDieList[hday] = []
                HealOrDieList[hday].append(NewPatient.id)
            elif probHealOrDie == 2: #dead
                dday = env.now + randint(Config.dstart, Config.dend)
                NewPatient.dday = dday
                NewPatient.hday = -1
                if dday not in HealOrDieList: HealOrDieList[dday] = []
                HealOrDieList[dday].append(NewPatient.id)
            PatientArr['Jakarta'+str(curIndex)] = NewPatient

        #print(PatientArr)
        print('Jakarta Day#%d' % env.now, JakartaCluster)
        yield env.timeout(1)

def CalcNewInfection(Cluster, Config):
    global ROPROB
    ro = Config.ro
    infectcnt = Cluster.infect
    someArray = randomSeedArray(100-ROPROB)

    totnew = 0
    for i in range(infectcnt):
        random.shuffle(someArray)
        prob = random.choice(someArray)
        if prob == 1: #infectingggg!!!
            totnew += ro

    print('Jakarta Day#%d - New Patient: %d' % (env.now, totnew), JakartaCluster)
    return totnew

def Hospitalized(env, Cluster, Patient, Config):
    someArray = randomSeedArray(Config.hosprob)
    random.shuffle(someArray)
    prob = random.choice(someArray)
    if prob == 1: #hospitalized
        Patient.hop = 1
        Cluster.hosp += 1
        Cluster.danger -= 1

def Travel(env): 
    print('not yet')

def Isolate(env, Cluster, Patient, Config): 
    someArray = randomSeedArray(Config.isoprob)
    random.shuffle(someArray)
    prob = random.choice(someArray)
    if prob == 1: #isolated
        Patient.iso = 1
        Cluster.isol += 1
        Cluster.danger -= 1

def Infect(env, Cluster, Patient, Config):
    someArray = randomSeedArray(Patient.inf)
    random.shuffle(someArray)
    prob = random.choice(someArray)
    if prob == 2: #infecting
        Cluster.infect += 1
        Patient.infstat = 1

def HealOrDie(env):
    global PatientArr
    global JakartaCluster
    global HealOrDieList

    while True:
        curday = env.now
        hcnt = 0
        dcnt = 0
        if curday in HealOrDieList:
            for x in HealOrDieList[curday]:
                Patient = PatientArr[x]
                isinfect = Patient.infstat 
                ishealed = 0
                if Patient.dday == -1:
                    ishealed = 1
                del PatientArr[x]
                if isinfect == 1 : 
                    JakartaCluster.infect -= 1
                if ishealed : 
                    JakartaCluster.heal += 1
                    hcnt += 1
                else :
                    JakartaCluster.died += 1
                    dcnt += 1

        print('Jakarta Day#%d - HEALED: %d - DIED: %d' % (env.now, hcnt, dcnt), JakartaCluster)
        yield env.timeout(1)

env = simpy.Environment()
env.process(Jakarta(env, 2))
env.process(HealOrDie(env))
#env.process(Heal(env))
#env.process(Die(env))
env.run(until=10)

print('Jakarta Day#%d' % env.now, JakartaCluster)
#print(PatientArr)
