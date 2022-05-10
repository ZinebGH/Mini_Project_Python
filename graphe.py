#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Implémentation d'un graphe non orienté et orienté représentant un réseau à l'aide d'un dictionnaire:
les clés sont les sommets, et les valeurs sont des tuples composés du sommet successeur et de la ligne
auquelle les deux sommets sont reliés. Les boucles sont autorisées et les aretes parallèles aussi.
"""


class Graphe(object):
    def __init__(self):
        """Initialise un graphe sans arêtes"""
        self.dictionnaire = dict()
        self.noms = dict() # Permet la correspondance entre identifiant et nom de station.

    def ajouter_arete(self, u, v, ligne):
        """Ajoute une arête entre les sommmets u et v, en créant les sommets
        manquants le cas échéant."""
        # vérification de l'existence de u et v, et création(s) sinon.
        if u not in self.dictionnaire:
            self.dictionnaire[u] = set()
        if v not in self.dictionnaire:
            self.dictionnaire[v] = set()

        # Si u et v étaient déjà reliés par la même ligne, on rajoute une arête parallèle.
        if (v, ligne) in self.dictionnaire[u] or (u, ligne) in self.dictionnaire[v]:
            # On choisit un nom de ligne arbitraire pour le différencier du précédent (un set n'accepte pas de doublons).
            i = 0
            ligne = "nouvelle_ligne_" + str(i)
            while (v, ligne) in self.dictionnaire[u] or (u, ligne) in self.dictionnaire[v]:
                i += 1
                ligne = "nouvelle_ligne_" + str(i)

        # ajout de u (resp. v) parmi les voisins de v (resp. u).
        self.dictionnaire[u].add((v, ligne))
        self.dictionnaire[v].add((u, ligne))

    def ajouter_aretes(self, iterable):
        """Ajoute toutes les arêtes de l'itérable donné au graphe. N'importe
        quel type d'itérable est acceptable, mais il faut qu'il ne contienne
        que des couples d'éléments (quel que soit le type du couple)."""
        for u, v, ligne in iterable:
            self.ajouter_arete(u, v, ligne)

    def ajouter_sommet(self, sommet, nom):
        """Ajoute un sommet (de n'importe quel type hashable) au graphe."""
    
        if not self.contient_sommet(sommet):        
            self.dictionnaire[sommet] = set()
            self.noms[sommet] = nom

    def ajouter_sommets(self, iterable):
        """Ajoute tous les sommets de l'itérable donné au graphe. N'importe
        quel type d'itérable est acceptable, mais il faut qu'il ne contienne
        que des éléments hashables."""
        for sommet, nom in iterable:
            self.ajouter_sommet(sommet, nom)

    def aretes(self):
        """Renvoie l'ensemble des arêtes du graphe. Une arête est représentée
        par un tuple (a, b) avec a <= b afin de permettre le renvoi de boucles.
        """
        return {
            tuple(sorted((u, v)) + [ligne]) for u in self.dictionnaire
            for v, ligne in self.dictionnaire[u]
        }

    def boucles(self):
        """Renvoie les boucles du graphe, c'est-à-dire les arêtes reliant un
        sommet à lui-même."""
        return {(u, u) for u in self.dictionnaire if self.contient_arete(u, u)}

    def contient_arete(self, u, v):
        """Renvoie True si l'arête {u, v} existe, False sinon."""
        if self.contient_sommet(u) and self.contient_sommet(v):
            for voisin, ligne in self.dictionnaire[u]:
                if voisin == v:
                    return True
        return False

    def contient_sommet(self, u):
        """Renvoie True si le sommet u existe, False sinon."""
        return u in self.dictionnaire

    def degre(self, sommet):
        """Renvoie le nombre de voisins du sommet; s'il n'existe pas, provoque
        une erreur."""
        return len(self.dictionnaire[sommet])

    def nombre_aretes(self):
        """Renvoie le nombre d'arêtes du graphe."""
        # attention à la division par 2 (chaque arête étant comptée deux fois)
        return sum(len(voisins) for voisins in self.dictionnaire.values()) // 2

    def nombre_boucles(self):
        """Renvoie le nombre d'arêtes de la forme {u, u}."""
        return len(self.boucles())

    def nombre_sommets(self):
        """Renvoie le nombre de sommets du graphe."""
        return len(self.dictionnaire)

    def retirer_arete(self, u, v):
        """Retire l'arête {u, v} si elle existe; provoque une erreur sinon."""
        if not self.contient_arete(u, v) or not self.contient_arete(v, u):
            raise ValueError("L'arête {" + str(u) + ", " + str(v) + "} n'existe pas.")

        lignes = []

        for voisin, ligne in self.dictionnaire[u]:
            if voisin == v:
                lignes.append(ligne)

        for ligne in lignes:
            self.dictionnaire[u].remove((v, ligne))

        lignes = []

        for voisin, ligne in self.dictionnaire[v]:
            if voisin == u:
                lignes.append(ligne)
        
        for ligne in lignes:
            self.dictionnaire[v].remove((u, ligne))

    def retirer_aretes(self, iterable):
        """Retire toutes les arêtes de l'itérable donné du graphe. N'importe
        quel type d'itérable est acceptable, mais il faut qu'il ne contienne
        que des couples d'éléments (quel que soit le type du couple)."""
        for u, v in iterable:
            self.retirer_arete(u, v)

    def retirer_sommet(self, sommet):
        """Efface le sommet du graphe, et retire toutes les arêtes qui lui
        sont incidentes."""
        del self.dictionnaire[sommet]
        # retirer le sommet des ensembles de voisins
        for u in self.dictionnaire:
            for v, ligne in self.dictionnaire[u]:
                if v == sommet:
                    self.dictionnaire[u].discard((v, ligne))

    def retirer_sommets(self, iterable):
        """Efface les sommets de l'itérable donné du graphe, et retire toutes
        les arêtes incidentes à ces sommets."""
        for sommet in iterable:
            self.retirer_sommet(sommet)

    def sommets(self):
        """Renvoie l'ensemble des sommets du graphe."""
        return set(self.dictionnaire.keys())

    def sous_graphe_induit(self, iterable):
        """Renvoie le sous-graphe induit par l'itérable de sommets donné."""
        G = DictionnaireAdjacence()
        G.ajouter_sommets(iterable)
        for u, v, ligne in self.aretes():
            if G.contient_sommet(u) and G.contient_sommet(v):
                G.ajouter_arete(u, v, ligne)
        return G

    def voisins(self, sommet):
        """Renvoie l'ensemble des voisins du sommet donné."""
        return self.dictionnaire[sommet]

    def nombre_liaisons(self, u, v):
        """ Renvoie le nombre d'arete reliant u et v en distinguant chaque ligne. """
        n = 0

        for voisin, ligne in self.dictionnaire[u]:
            if voisin == v:
                n += 1

        return n

    def nom_sommet(self, sommet):
        """Renvoie le nom correspondant à l'identifiant du sommet donné. """
        return self.noms[sommet]

    def ajouter_arc(self, u, v, ligne):
        """Ajoute un arc entre les sommmets u et v, en créant les sommets
        manquants le cas échéant."""

        if not self.contient_sommet(u):
            self.ajouter_sommet(u, None)
        if not self.contient_sommet(v):
            self.ajouter_sommet(v, None)

        self.dictionnaire[u].add((v, ligne))

    def ajouter_arcs(self, iterable):
        """Ajoute tous les arcs de l'itérable donné au graphe. N'importe
        quel type d'itérable est acceptable, mais il faut qu'il ne contienne
        que des couples d'éléments (quel que soit le type du couple)."""

        for u, v, ligne in iterable:
            self.ajouter_arc(u, v, ligne)

    def arcs(self):
        """Renvoie l'ensemble des arcs du graphe."""

        arcs = set()

        for u in self.sommets():
            for v, ligne in self.dictionnaire[u]:
                arcs.add((u, v, ligne))

        return arcs

    def contient_arc(self, u, v):
        """Renvoie True si l'arc (u, v) existe, False sinon."""

        if self.contient_sommet(u) and self.contient_sommet(v):
            for successeur, ligne in self.dictionnaire[u]:
                if successeur == v:
                    return True
        return False

    def degre_entrant(self, sommet):
        """Renvoie le nombre d'arcs de la forme (u, sommet) du graphe;
        Lève une exception si le sommet n'existe pas."""

        if not self.contient_sommet(sommet):
            raise ValueError("Le sommet " + str(sommet) + " n'existe pas.")

        return len(self.predecesseurs(sommet))

    def degre_sortant(self, sommet):
        """Renvoie le nombre d'arcs de la forme (sommet, v) du graphe;
        Lève une exception si le sommet n'existe pas."""

        if not self.contient_sommet(sommet):
            raise ValueError("Le sommet " + str(sommet) + " n'existe pas.")

        return len(self.successeurs(sommet))

    def nombre_arcs(self):
        """Renvoie le nombre d'arcs du graphe."""

        return len(self.arcs())

    def predecesseurs(self, sommet):
        """Renvoie l'ensemble des sommets u tels que l'arc
        (u, sommet) appartient au graphe.
        Lève une exception si le sommet n'existe pas."""

        if not self.contient_sommet(sommet):
            raise ValueError("Le sommet " + str(sommet) + " n'existe pas.")

        predecesseurs = set()

        for u in self.sommets():
            if self.contient_arc(u, sommet):
                predecesseurs.add(u)

        return predecesseurs

    def retirer_arc(self, u, v):
        """Retire l'arc (u, v) s'il existe; lève une exception sinon."""

        if not self.contient_arc(u, v):
            raise ValueError("L'arc (" + str(u) + ", " + str(v) + ") n'existe pas.")

        lignes = []

        for successeur, ligne in self.dictionnaire[u]:
            if successeur == v:
                lignes.append(ligne)

        for ligne in lignes:
            self.dictionnaire[u].remove((v, ligne))

    def retirer_arcs(self, iterable):
        """Retire tous les arcs de l'itérable donné du graphe. N'importe
        quel type d'itérable est acceptable, mais il faut qu'il ne contienne
        que des couples d'éléments (quel que soit le type du couple)."""

        for u, v in iterable:
            self.retirer_arc(u, v)

    def successeurs(self, sommet):
        """Renvoie l'ensemble des sommets u tels que l'arc
        (sommet, u) appartient au graphe.
        Lève une exception si le sommet n'existe pas."""

        if not self.contient_sommet(sommet):
            raise ValueError("Le sommet " + str(sommet) + " n'existe pas.")

        return {u for (u, ligne) in self.dictionnaire[sommet]}

def modifier_noms(graphe):
    """ Renvoie un graphe identique à celui donné en paramètre mais dont
    les noms des sommets sont des entiers allant de 0 à graphe.nombre_sommets(). """
    nouveau_graphe = Graphe()
    correspondance = dict()

    for sommet in sorted(graphe.sommets()):
        correspondance[sommet] = len(correspondance)
        nouveau_graphe.ajouter_sommet(correspondance[sommet], graphe.nom_sommet(sommet))

    for u in sorted(graphe.sommets()):
        for v, ligne in graphe.voisins(u):
            nouveau_graphe.ajouter_arc(correspondance[u], correspondance[v], ligne)

    return nouveau_graphe

def export_dot(graphe):
    """Renvoie une chaîne encodant le graphe au format dot."""
    
    dot = "graph " + "_".join(repr(graphe).split(" ")) + " {\n"

    for sommet in graphe.sommets():
        dot += "\t" + str(sommet) + ";\n"
    for arete in graphe.aretes():
        dot += "\t" + str(arete[0]) + " -- " + str(arete[1]) + ";\n"
    for boucle in graphe.boucles():
        dot += "\t" + str(boucle[0]) + " -- " + str(boucle[1]) + ";\n"
    dot += "}"

    return dot