
    ## Copyright (C) 2016  Luca Massarelli

    ## This program is free software: you can redistribute it and/or modify
    ## it under the terms of the GNU General Public License as published by
    ## the Free Software Foundation, either version 3 of the License, or
    ## any later version.

    ## This program is distributed in the hope that it will be useful,
    ## but WITHOUT ANY WARRANTY; without even the implied warranty of
    ## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    ## GNU General Public License for more details.

    ## You should have received a copy of the GNU General Public License
    ## along with this program.  If not, see <http://www.gnu.org/licenses/>.


    ## Questo programma crea il grafo delle linee degli autous di roma
    ## i percorsi delle linee sono i nodi, due percorsi sono uniti se hanno due fermate
    ## che si trovano a meno di una distanza DISTANCE parametrizzata
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
from geopy.distance import great_circle
from time import sleep
from pprint import pprint

nomeGrafo = "Grafo_Linee"                                                                           #nome con cui salvare il grafo

stop_file = open("/Users/lucamassarelli/Documents/CloudStation/SisCompl/google_transit/stops.txt")  #!!!apro il file delle fermata (da cambiare)
in_line = stop_file.readline()                                                                      #leggo la prima linea di commento e la butto

line_file = open("/Users/lucamassarelli/Documents/CloudStation/SisCompl/google_transit/routes.txt") #!!!apro il file delle linee (da cambiare)
in_line = line_file.readline()                                                                      #leggo la prima linea di commento e la butto

DEV_KEY = 'V0BTvQ1Tgl3BuOsNw1W4evggT4n24Mfi'                                                        #!!!la mia chiave sviluppare (da cambiare)
DISTANCE = 50                                                                                       #distanza geografica tra due fermate per considerale unite
numLinee = 10                                                                                       #numero di linee da analizzare, per prenderle tutte mettere >1000

#per prima cosa mi leggo il file delle fermate e mi salvo id, latitudine e longitudine  
 
latitudine = {}      #dictionary latitudine per accedere: latitudine[stop_id] = float
longitudine = {}     #dictionary longitudine per accedere: longitudine[stop_id] = float
list_stop_id = {}    #list stop_id progressivi per accedere: list_stop_id[i] = string

in_line = stop_file.readline() #leggo la prima linea di commento e la butto

stopCount = 0                                               #inizializzo contatore fermate
while 1:
    in_line = stop_file.readline()                          #leggo una linea del file
    if(in_line == ""):                                      #se ho finito il file esco
        break
    line = string.split(in_line,",")                      
    stop_id = line[0].strip(" \"\" ")                       #leggo il nome della fermata e tolgo gli apici
    latitudine[stop_id] = float(line[2].strip(" \"\" "))    #leggo la latitudine della fermata, tolgo gli apici, porto in float
    longitudine[stop_id] = float(line[3].strip(" \"\" "))   #leggo la longitudine della fermata e tolgo gli apici, porto in float
    list_stop_id[stopCount] = stop_id                       #mi salvo progressivamente gli stop id
    stopCount = stopCount + 1

    
numNode = 0;                #inizializzo contatore nodi
count = 0;                  #inizializzo contatore cicli
numPercorso = 0             #inizializzo contatore percorsi
percorso = {}               #list percorsi, mi salve tutte le fermate di una linea, per accedere: percorso[i] = list(string)
labels = snap.TIntStrH()    #hash table che mi salva i label per disegnare il grafo
Graph = snap.TUNGraph.New() #creo un nuovo grafo


s1 = Server('http://muovi.roma.it/ws/xml/autenticazione/1')  #uri delle richeste
s2 = Server('http://muovi.roma.it/ws/xml/paline/7')
s3 = Server('http://muovi.roma.it/ws/xml/percorso/2')

token = s1.autenticazione.Accedi(DEV_KEY, '')                #autenticazione al server
  
while count <  numLinee:
    count = count + 1
    in_line = line_file.readline()                                                 #leggo una linea
    if(in_line == ""):                                                           #se ho finito il file esco
        break
    line = string.split(in_line,",")                                             #splitto le parti della linea con la virgola
    id_linea = line[2].strip(" \"\" ")                                           #leggo il nome della linea e tolgo gli apici
    print(str(count) + ", linea numero: " + id_linea)                            #stampo il numero della linea che sto analizzando
    res = s2.paline.Percorsi(token, id_linea, 'it')                              #richiedo al server i percorsi della linea
    for i in range(0,len(res['risposta']['percorsi'])):                          #per ogni percorso delle linea mi salvo tutte le fermate
        idpercorso = res['risposta']['percorsi'][i]['id_percorso']               #prendo l'id del percorso in esame
        try:
            fermate = s2.paline.Percorso(token,idpercorso,'','2016-02-04','it')  #richiedo al server le fermate del percorso
            go = 1
        except:
            pprint("OOPS!! Questo e' imbarazzante, error on request")            #se trovo errore vado avanti con il prossimo percorso
            go = 0
        if(go == 1):
            orari  = fermate['risposta']['orari_partenza']                       #controllo che il percorso della linea sia attivo tra le 9 e le 10 del 4/2/2016
            active = 0 
            j = 0
            while(active == 0 and j < len(orari)):                               #ciclo sugli orari che ho ricevuto dal server per vedere se ci sono   
                ora  = int(orari[j]['ora'])                                      #partenze negli orari che mi interessano
                if(ora == 9) :
                    minuti = orari[j]['minuti']
                    if(minuti != []):
                        active = 1                                               #se trovo una partenza il percorso e' attivo!
                        break                                                    #in questo caso procedo con l'analisi delle fermate
                j = j+1  

            if(active == 1):
                print('    percorso: ' + idpercorso + ' active')                 #stampo a schermo se la linea e' attiva
            else:
                print('    percorso: ' + idpercorso + ' not active')             #stampo a schermo se il percorso non e' attivo

            if(active == 1):                                                                        #se il percorso e' attivo allora mi leggo tutte gli id delle fermate che fa
                id_fermata = range(1,len(fermate['risposta']['fermate'])+1)                         #inizializzo il dictionary in cui salvo gli id delle fermate
                for k in range(0,len(fermate['risposta']['fermate'])):                              #ciclo sulle fermate per salvarmi l'id 
                    id_fermata[k] = fermate['risposta']['fermate'][k]['id_palina']
                nodeId = Graph.AddNode(numPercorso)                                                 #aggiungo al grafo il nodo che corrisponde a questo percorso
                percorso[nodeId] = id_fermata                                                       #in percorso[node_id] mi salvo la lista delle fermate di questo percoso
                numPercorso = numPercorso + 1
                labels[nodeId] = id_linea + " -dir: " + res['risposta']['percorsi'][i]['capolinea'] #mi salvo il label da usare nel grafo per questo nodo
                
    pprint("------------------------------------")                              #quando ho finito di analizzare una linea bus, stampo a schermo una linea


for i in range(0,len(percorso)):                                                                          #ciclo su tutti i percorsi attivi
    pprint("percorso n. " + str(i) + " di " + str(len(percorso)))                                         #stampo il percorso che sto analizzando
    for j in range(0,len(percorso)):                                                                      #per ogni percorso lo confronto tutti gli altri
        for k in range(0,len(percorso[i])):                                                               #ciclo su ogni fermata del primo percorso
            for l in range(0,len(percorso[j])):                                                           #ciclo su ogni fermata del secondo percorso
                if(latitudine.has_key(percorso[i][k]) == 1 and latitudine.has_key(percorso[j][l]) == 1):  #verifico che l'id fermata sia presente (alcune non ci sono nel file)
                    if(DISTANCE == 0):                                                                    #se sto verficando che le due fermate coincidano
                       if(percorso[i][k] == percorso[j][l]):                                              #controllo solo che i due id siano gli stessi
                            Graph.AddEdge(i,j)                                                            #se sono gli stessi aggiungo un link    
                    else:                                                                                 #se sto considerando distanze maggiori di zero vado qui
                        stop1 = (latitudine[percorso[i][k]], longitudine[percorso[i][k]])                 #leggo lat e lon delle prima fermata
                        stop2 = (latitudine[percorso[j][l]], longitudine[percorso[j][l]])                 #leggo lat e lon della seconda fermata
                        if(great_circle(stop1, stop2).m < 50):                                            #se la distanza tra le due fermate e' minore di quella scelta
                            Graph.AddEdge(i,j)                                                            #aggiungo un link
    

snap.SaveEdgeList(Graph, nomeGrafo + '.txt')                                                    #salvo il grafo in formato .txt
pprint("---SAVED GRAPH .txt---")
snap.SaveGViz(Graph, nomeGrafo + ".dot", nomeGrafo, labels)                                     #salvo il grafo in formato .dot
pprint("---SAVED GRAPH .dot---")
snap.PlotSccDistr(Graph, nomeGrafo + "cluster", nomeGrafo + " - scc distribution")              #salvo la distribuzione dei cluster
pprint("---SAVED PLOT CLUSTER---")
snap.PlotInDegDistr(Graph, nomeGrafo + "inDegree", nomeGrafo + " - in-degree Distribution")     #salvo la distribuzione del grado in
pprint("---SAVED PLOT IN DEGREE---")
snap.PlotInDegDistr(Graph, nomeGrafo + "outDegree", nomeGrafo + " - out-degree Distribution")   #salvo la distribuzione del grado out
pprint("---SAVED OUT DEGREE---")

