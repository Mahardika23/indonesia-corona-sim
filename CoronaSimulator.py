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

SimConfig = namedtuple('SimConfig', 'ro hosprob isoprob medcnt dstart dend hstart hend')
Config = {
        'Jakarta' : SimConfig(1, 50, 30, 1000, 5, 15, 14, 30), 
        'Bandung' : SimConfig(1, 50, 50, 1000, 5, 15, 14, 30)
        }
ClusterState = recordtype('ClusterState', 'total infect hosp isol danger died heal') 
# XXX: Total available Medical fascility for Hospitalization = SimConfig.medcnt - ClusterState.hosp

# Clusters Initial State
JakartaCluster = ClusterState(0, 0, 0, 0, 0, 0, 0)

# Patient data structure records: 
# - id of patient (City + number) 
# - day of infection
# - hospitalization probability
# - isolation act (yes, no)
# - traveling probability
# - infecting probablity
# - infecting status (1=yes, 2=no)
# - if probable of dying, die day 
# - if probable of healing, healing day 
Patient = recordtype('Patient', 'id doi hop iso trv inf infstat dday hday')
# Array of Patients
PatientArr = {} 

def randomSeedArray(pctFail):
    someArray = []
    choices = [1,2] #1 === good option  2 === bad bad bad
    cnt = 0

    for i in range(1,100):
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
  
    HealOrDieArray = randomSeedArray(8)

    fname = inspect.stack()[0][3] # get function name
    SimConfig = Config[fname]

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
        add_patient = int(JakartaCluster.infect * SimConfig.ro)

        for i in range (0, max(add_patient-1,1)):
            curIndex = int(JakartaCluster.total+1)
            # Shuffle our magic array

            NewPatient = Patient('Jakarta'+str(curIndex), env.now, 0, 0, 0.5, 90, 2, -1, 14)
            JakartaCluster.total += 1
            JakartaCluster.danger += 1
            
            
            Hospitalized(env, JakartaCluster, NewPatient, SimConfig)
            if NewPatient.hop != 1 :
                Isolate(env, JakartaCluster, NewPatient, SimConfig)

            if NewPatient.hop == 1 or NewPatient.iso == 1 : NewPatient.inf = 10
            else : NewPatient.inf = 90

            Infect(env, JakartaCluster, NewPatient, SimConfig)
            
            probHealOrDie = random.choice(HealOrDieArray)
            random.shuffle(HealOrDieArray)

            #print('PROB HEAL DIE %d' % probHealOrDie)
            if probHealOrDie == 1: #heal
                NewPatient.dday = -1
                NewPatient.hday = env.now + randint(SimConfig.hstart, SimConfig.hend)
            elif probHealOrDie == 2: #dead
                NewPatient.dday = env.now + randint(SimConfig.dstart, SimConfig.dend)
                NewPatient.hday = -1
            PatientArr['Jakarta'+str(curIndex)] = NewPatient

        #print(PatientArr)
        print('Jakarta Day#%d' % env.now, JakartaCluster)
        yield env.timeout(1)


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

def Die(env):
    global PatientArr
    global JakartaCluster

    while True:
        DelArr = []
        cnt = 0
        for x in PatientArr:
            if PatientArr[x].dday == env.now:
                #print('Jakarta HEAL 1 patient %s' % x)
                DelArr.append(x)
                cnt += 1
        for x in DelArr:
            Patient = PatientArr[x]
            isinfect = Patient.infstat 
            del PatientArr[x]
            if isinfect == 1 : JakartaCluster.infect -= 1
            JakartaCluster.died += 1

        print('DEAD: Jakarta Day#%d' % env.now, JakartaCluster)
        yield env.timeout(1)


def Heal(env):
    global PatientArr
    global JakartaCluster

    while True:
        DelArr = []
        cnt = 0
        for x in PatientArr:
            if PatientArr[x].hday == env.now:
                #print('Jakarta HEAL 1 patient %s' % x)
                DelArr.append(x)
                cnt += 1
        for x in DelArr:
            Patient = PatientArr[x]
            isinfect = Patient.infstat 
            del PatientArr[x]
            if isinfect == 1 : JakartaCluster.infect -= 1
            JakartaCluster.heal += 1

        print('HEAL: Jakarta Day#%d' % env.now, JakartaCluster)
        yield env.timeout(1)

env = simpy.Environment()
env.process(Jakarta(env, 2))
env.process(Heal(env))
env.process(Die(env))
env.run(until=48)

print('Jakarta Day#%d' % env.now, JakartaCluster)
#print(PatientArr)
