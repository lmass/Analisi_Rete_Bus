
    ## Copyright (C) 2016  Luca Massarelli

    ## This program is free software: you can redistribute it and/or modify
    ## it under the terms of the GNU General Public License as published by
    ## the Free Software Foundation, either version 3 of the License, or
    ## (at your option) any later version.

    ## This program is distributed in the hope that it will be useful,
    ## but WITHOUT ANY WARRANTY; without even the implied warranty of
    ## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    ## GNU General Public License for more details.

    ## You should have received a copy of the GNU General Public License
    ## along with this program.  If not, see <http://www.gnu.org/licenses/>.


    ## Questo programma crea il grafo delle paline degli autous di roma
    ## le paline sono i nodi, ogni palina e' unita ad un'altra se sono
    ## due fermate consecutive di uno stesso percorso
    ## prima di lanciarlo:

    ##  --- e' necessario avere i file google_transiti forniti da atac
    ## e scaricabili qui:
    ##  http://www.agenziamobilita.roma.it/it/progetti/open-data/dataset.html
    ## la destinazione del file stops.txt e routes.txt va indicata sotto.

    ##  --- e' necessario richiedere una chiave sviluppatore per l'api qui:
    ##  http://www.agenziamobilita.roma.it/it/progetti/open-data/api-real-time.html

    ##  --- e' necessario installare tutti i pacchetti indicati nel readMe 



from _snap import gvlDot
try:
    # Python 2 import
    from xmlrpclib import Server
except ImportError:
    # Python 3 import
    from xmlrpc.client import Server

import string
import snap
from time import sleep
from pprint import pprint

DEV_KEY = 'V0BTvQ1Tgl3BuOsNw1W4evggT4n24Mfi'    #mia chiave sviluppatore, da modificare
numLinee = 10                                   #numero di linee da analizzare >1000 per prenderle tutte
nomeGrafo ='GrafoPaline'

line_file = open("/Users/lucamassarelli/Documents/CloudStation/SisCompl/google_transit/routes.txt");  #file con tutte le designazioni delle linee, da modificare
in_line = line_file.readline()                                                                        #leggo una la prima linea di commento e la butto

s1 = Server('http://muovi.roma.it/ws/xml/autenticazione/1')    #uri dei server a cui fare le query
s2 = Server('http://muovi.roma.it/ws/xml/paline/7')
s3 = Server('http://muovi.roma.it/ws/xml/percorso/2')

stopGraph = snap.TNGraph.New()      #creo un nuovo grafo direzionato
nodeTable = {}                      #Dictionary con cui mi salvo il l'id dei nodi per accedere: nodeTable[stop_id] = node_id (int)
numNode = 0;                        #contatore numero di nodi
count = 0;                          #contatore cicli
labels = snap.TIntStrH()            #hash table per salvare i label dei nodi

token = s1.autenticazione.Accedi(DEV_KEY, '')  #autenticazione all'api di muoversi a roma

  
while count < numLinee:
    count = count + 1
    in_line = line_file.readline()                               #leggo una linea
    if(in_line == ""):                                           #se ho finito il file esco
        break
    line = string.split(in_line,",")                             #splitto la linea letta dal file con ,
    id_linea = line[2].strip(" \"\" ")                           #leggo il nome della linea del bus e tolgo gli apici
    print(str(count) + ", linea numero: " + id_linea)            #stampo il nome della linea che sto analizzando
    res = s2.paline.Percorsi(token, id_linea, 'it')              #percorsi della linea
    
    for i in range(0,len(res['risposta']['percorsi'])):                      #per ogni linea ciclo sui percorsi e mi leggo le fermate di ogni percorso
        idpercorso = res['risposta']['percorsi'][i]['id_percorso']           #leggo l'id del percorso

        try:
            fermate = s2.paline.Percorso(token,idpercorso,'','2016-02-04','it')  #richiedo al server le fermate del percorso
            go = 1
        except:
            pprint("OOPS!! Questo e' imbarazzante, error on request")            #se trovo errore vado avanti con il prossimo percorso
            go = 0

        if(go == 1):
            orari  = fermate['risposta']['orari_partenza']                       #leggo gli orari di partenza
            active = 0
            j = 0
            while(active == 0 and j < len(orari)):                               #ciclo sugli orari per vedere se il percorso e' attivo tra le 9 e le 10 del 4/2/2016
                ora  = int(orari[j]['ora'])
                if(ora == 9) :
                    minuti = orari[j]['minuti']
                    if(minuti != []):
                        active = 1
                        break                                                   #se e' attiva allora vado avanti
                j = j+1  

            if(active == 1):
                print('    percorso: ' + idpercorso + ' active')                #stampo a schermo se e' attiva o no
            else:
                print('    percorso: ' + idpercorso + ' not active')

            if(active == 1):                                                        #se e' attivo procedo ad aggiungere le fermate alla rete
                id_fermata = range(1,len(fermate['risposta']['fermate'])+1)         #alloco spazio per la lista delle fermate
                for k in range(0,len(fermate['risposta']['fermate'])):              #ciclo su tutte le fermate
                    id_fermata[k] = fermate['risposta']['fermate'][k]['id_palina']  #leggo id della fermata
                    if(nodeTable.has_key(id_fermata[k]) == 0):                      #se la fermata non e' ancora stata inserita la aggiungo come nodo al grafo
                        nodeId = stopGraph.AddNode(numNode)                          
                        nodeTable[id_fermata[k]] = nodeId;                          #mi salvo il nodeId nella nodeTable
                        labels[nodeId] = fermate['risposta']['fermate'][k]['nome']  #mi salvo il label nella hashTable dei label 
                        numNode = numNode + 1                                       #incremeto il numero dei nodi

                for k in range(1,len(id_fermata)):                                         #ciclo su tutte le fermate della linea
                    stopGraph.AddEdge(nodeTable[id_fermata[k-1]],nodeTable[id_fermata[k]]) #aggiungo link tra fermate consecutive
    
    pprint("------------------------------------")                              #quando ho finito di analizzare una linea, stampo a schermo una linea

                    
snap.SaveEdgeList(stopGraph, nomeGrafo + '.txt')                                                    #salvo il grafo in formato .txt
pprint("---SAVED GRAPH .txt---")
snap.SaveGViz(stopGraph, nomeGrafo + ".dot", nomeGrafo, labels)                                     #salvo il grafo in formato .dot
pprint("---SAVED GRAPH .dot---")
snap.PlotSccDistr(stopGraph, nomeGrafo + "cluster", nomeGrafo + " - scc distribution")              #salvo la distribuzione dei cluster
pprint("---SAVED PLOT CLUSTER---")
snap.PlotInDegDistr(stopGraph, nomeGrafo + "inDegree", nomeGrafo + " - in-degree Distribution")     #salvo la distribuzione del grado in
pprint("---SAVED PLOT IN DEGREE---")
snap.PlotInDegDistr(stopGraph, nomeGrafo + "outDegree", nomeGrafo + " - out-degree Distribution")   #salvo la distribuzione del grado out
pprint("---SAVED OUT DEGREE---")



