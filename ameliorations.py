#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphe import *
from argparse import *
from copy import deepcopy
from os import listdir
from os.path import isfile


def charger_donnees(graphe, fichier):
	""" Ajoute dans le graphe les sommets et les aretes contenues dans le fichier donné en paramètre.
	Lève une exception et n'ajoute pas les données si le fichier est syntaxiquement incorrect. """
	sommets = set()
	aretes = set()

	with open(fichier, 'r') as donnees:
		try:
			stations, connexions = donnees.read().split("# stations\n")[1].split("# connexions\n")

			for station in stations.split('\n')[:-1]:
				ident, nom = station.split(':')
				sommets.add((int(ident), nom))

			for connexion in connexions.split('\n')[:-1]:
				u, v, temps = connexion.split('/')
				aretes.add((int(u), int(v), fichier.rsplit(".txt")[0]))
		except ValueError:
			raise Exception("Le fichier de données '" + fichier + "' est syntaxiquement incorrect.")
		else:
			graphe.ajouter_sommets(sommets)
			graphe.ajouter_aretes(aretes)

def numerotation(reseau):
	""" Calcule et renvoie les listes correspondant aux dates de début d'exploration (basé sur un parcours en profondeur),
	aux dates de début d'un certain ancetre ainsi que le parent de chacun des sommets du réseau donné en paramètre. """
	graphe = modifier_noms(reseau) # On modifie les noms des sommets en entiers pour les utiliser comme indice de tableau.
	debut = [0 for _ in range(graphe.nombre_sommets())]
	parent = [None for _ in range(graphe.nombre_sommets())]
	ancetre = [-1 for _ in range(graphe.nombre_sommets())]
	instant = 0

	def numerotationRecursive(s):
		nonlocal instant, parent, ancetre, debut
		instant += 1
		debut[s] = ancetre[s] = instant

		for t, ligne in sorted(graphe.voisins(s), key=lambda voisin : voisin[0]):
			if debut[t] != 0:
				if parent[s] != t:
					ancetre[s] = min(ancetre[s], debut[t])
			else:
				parent[t] = s
				numerotationRecursive(t)
				ancetre[s] = min(ancetre[s], ancetre[t])

	for v in sorted(graphe.sommets()):
		if debut[v] == 0:
			numerotationRecursive(v)

	# On reconvertis les vrais noms de sommets.
	sommets = sorted(reseau.sommets())
	for i in range(reseau.nombre_sommets()):
		if parent[i] != None:
			parent[i] = sommets[parent[i]]

	return debut, parent, ancetre

def points_articulation(reseau):
	""" Renvoie l'ensemble des points d'articulations du réseau. """
	graphe = modifier_noms(reseau)
	debut, parent, ancetre = numerotation(graphe)
	articulations = []

	racines =  {v for v in graphe.sommets() if parent[v] == None}

	for depart in racines:
		if len([v for v in parent if v == depart]) >= 2: # Si le degré sortant de `depart` est >= 2.
			articulations.append(depart)

	racines.add(None)
	for v in graphe.sommets():
		if (parent[v] not in racines) and (ancetre[v] >= debut[parent[v]]):
			articulations.append(parent[v])

	sommets = sorted(reseau.sommets())
	for i in range(len(articulations)):
		articulations[i] = sommets[articulations[i]]

	return set(articulations)

def ponts(reseau):
	""" Renvoie l'ensemble des ponts du réseau. """
	graphe = modifier_noms(reseau)
	debut, parent, ancetre = numerotation(graphe)
	ponts = []

	for v in graphe.sommets():
		if parent[v] != None and ancetre[v] > debut[parent[v]] and graphe.nombre_liaisons(parent[v], v) == 1:
			ponts.append((parent[v], v))

	sommets = sorted(reseau.sommets())
	for i in range(len(ponts)):
		u, v = ponts[i]
		ponts[i] = (sommets[u], sommets[v])

	return set(ponts)

def arbre_composantes_sans_ponts(reseau):
	""" Renvoie un arbre dont chaque sommet correspond à une composante sans pont du réseau, et chaque arête correspond à un pont. """
	arbre = Graphe()
	lst_ponts = ponts(reseau)
	extremites_ponts = {u for pont in lst_ponts for u in pont}

	def parcours_recursif(s, pont, csp, traites):
		nonlocal extremites_ponts

		traites.add(s)
		csp.add(s)

		for voisin, ligne in reseau.voisins(s):
			if voisin not in traites and not ((s, voisin) in lst_ponts or (voisin, s) in lst_ponts):
				parcours_recursif(voisin, pont, csp, traites)

	for pont in lst_ponts:
		csp1 = set()
		traites = set()
		traites.add(pont[0])
		parcours_recursif(pont[1], pont, csp1, traites)
		csp1 = tuple(sorted(csp1))
		arbre.ajouter_sommet(csp1, None)

		csp2 = set()
		traites = set()
		traites.add(pont[1])
		parcours_recursif(pont[0], pont, csp2, traites)
		csp2 = tuple(sorted(csp2))
		arbre.ajouter_sommet(csp2, None)

		arbre.ajouter_arete(csp1, csp2, None)

	return arbre

def composantes_connexes(graphe):
	""" Renvoie un ensemble de tuples dont chaque tuple contient les sommets d'une composante connexe du graphe donné. """
	ccs = set()
	traites = set()

	def parcours_recursif(s, cc):
		""" Parcours la composante connexe incluant s et ajoute dans `cc` les sommets parcourus. """
		nonlocal traites

		traites.add(s)
		cc.add(s)
		for voisin, ligne in graphe.voisins(s):
			if voisin not in traites:
				parcours_recursif(voisin, cc)

	""" On lance l'algorithme de parcours sur chaque composante connexe du graphe, `racine` désigne en faite
	un sommet arbitraire d'une composante connexe non visitée. """
	for racine in graphe.sommets():
		if racine not in traites:
			cc = set()
			parcours_recursif(racine, cc)
			ccs.add(tuple(cc))


	return ccs

def est_dans_meme_cc(graphe, u, v):
	""" Renvoie True si `u` et `v` sont dans une même composante connexe de `graphe`, et False sinon. """
	for cc in composantes_connexes(graphe):
		if u in cc and v in cc:
			return True
	return False

def amelioration_ponts(reseau):
	""" Renvoie l'ensemble des arêtes à rajouter au réseau pour supprimer ses ponts. """
	aretes_a_rajouter = set()

	def supprimer_pont(reseau):
		nonlocal aretes_a_rajouter

		feuilles = []
		arbre_csp = arbre_composantes_sans_ponts(reseau)

		while len(feuilles) < 2: # On cherche deux feuilles à relier.
			for csp in sorted(arbre_csp.sommets()):
				if len(arbre_csp.voisins(csp)) <= 1: # Si c'est une feuille.
					if len(feuilles) > 0:
						if est_dans_meme_cc(reseau, feuilles[0][0], csp[0]): # On vérifie qu'on relie bien 2 sommets se situant dans la même composante connexe.
							feuilles.append(csp)
					else:
						feuilles.append(csp)

		# On rajoute une arete qui n'existait pas déjà. (Sauf si la composante connexe ne contient que deux sommets).
		for u in feuilles[0]:
			for v in feuilles[1]:
				if u != v and (not reseau.contient_arete(u, v) or (len(feuilles[0]) == len(feuilles[1]) == 1)):
					reseau.ajouter_arete(u, v, None)
					aretes_a_rajouter.add((u, v))
					return

	""" On rajoute dans une copie du réseau (pour ne pas modifier l'original) une arete supprimant un pont,
	puis on continue d'en rajouter une par une en vérifiant à chaque fois qu'il reste des ponts. """
	copie_reseau = deepcopy(reseau)
	while len(ponts(copie_reseau)) > 0:
		supprimer_pont(copie_reseau)

	return aretes_a_rajouter

"""
Dans la suite, l'expression 'sorted(graphe.sommets()).index(sommet)' fait référence à un alias du nom du sommet
qui correspond à un petit entier, qu'on utilise comme indice pour les tableaux.
"""

def trouver_racine(graphe, parent, sommet):
	""" Renvoie la racine de l'arbre menant au sommet donné, (son parent le plus lointain) dont `parent`
	est un tableau de pères (parent[i] est le père de i). """

	sommets_tries = sorted(graphe.sommets())

	while parent[sommets_tries.index(sommet)] != None:
		sommet = parent[sommets_tries.index(sommet)]

	return sommet

def ancetres(graphe, parent, sommet):
	""" Renvoie l'ensemble des ancetres de `sommet` dont `parent` est un tableau de pères. """

	sommets_tries = sorted(graphe.sommets())
	ancetres = set()

	while parent[sommets_tries.index(sommet)] != None:
		sommet = parent[sommets_tries.index(sommet)]
		ancetres.add(sommet)

	return ancetres

def amelioration_points_articulation(reseau):
	""" Renvoie l'ensemble des arêtes à rajouter au réseau pour supprimer ses points d'articulation. """
	aretes_a_rajouter = set()

	def supprimer_point_articulation(reseau, point):
		nonlocal aretes_a_rajouter, parent
		successeurs = [sommet for sommet in reseau.sommets() if parent[sorted(reseau.sommets()).index(sommet)] == point]

		def accessible_depuis_un_ancetre(u, v):
			""" Renvoie True si v est accessible à partir d'un ancetre de u sans passer par u, et False sinon. """
			voisins = {sommet for sommet, ligne in reseau.voisins(v)}
			return len(ancetres(reseau, parent, u).intersection(voisins)) != 0

		# Si le point d'articulation est une racine, on relie ses successeurs entre eux.
		if parent[sorted(copie_reseau.sommets()).index(point)] == None:
			for i in range(1, len(successeurs)):
				reseau.ajouter_arete(successeurs[i-1], successeurs[i], None)
				aretes_a_rajouter.add((successeurs[i-1], successeurs[i]))

		# Sinon on relie ses successeurs (qui ne sont pas accessible depuis un de ses ancetre) à sa racine.
		else:
			racine = trouver_racine(reseau, parent, point)
			for successeur in successeurs:
				if not accessible_depuis_un_ancetre(point, successeur):
					reseau.ajouter_arete(racine, successeur, None)
					aretes_a_rajouter.add((racine, successeur))

	copie_reseau = deepcopy(reseau)
	while len(points_articulation(copie_reseau)) > 0:
		debut, parent, ancetre = numerotation(copie_reseau)
		# Points d'articulation du réseau triés par ordre de date de début décroissante.
		points = sorted(points_articulation(copie_reseau),
						key=lambda point: debut[sorted(copie_reseau.sommets()).index(point)],
						reverse=True)
		supprimer_point_articulation(copie_reseau, points[0])

	return aretes_a_rajouter

def chercher_fichiers(prefixe, suffixe):
	""" Renvoie la liste de tous les fichiers commençant par `préfixe` et finissant par `suffixe` dans le répertoire courant. """
	fichiers = []

	for fichier in listdir('./'):
		if isfile(fichier) and fichier.startswith(prefixe) and fichier.endswith(suffixe):
			fichiers.append(fichier[len(prefixe):-len(suffixe)])

	return fichiers

def chargement_ok(reseau, fichier):
	""" Renvoie True s'il n'y a pas eu d'erreur lors de l'appel à charger_donnees().
	charger_donnees() aurait pu renvoyer un boolean mais elle n'est pas censée renvoyer de valeur (doctests). """
	try:
		charger_donnees(reseau, fichier)
	except:
		return False
	else:
		return True

def charger_lignes(reseau, lignes_metro, lignes_rer):
	""" Charge les lignes de métro et/ou de rer dans le réseau selon la valeur des paramètres.
	Indique pour chaque ligne s'il y a eu une erreur pendant le chargement, auquel cas elle n'est pas chargée. """
	if lignes_metro != None:
		if lignes_metro == []:
			lignes_metro = chercher_fichiers("METRO_", ".txt")
	else:
		lignes_metro = []

	if lignes_rer != None:
		if lignes_rer == []:
			lignes_rer = chercher_fichiers("RER_", ".txt")
	else:
		lignes_rer = []

	for ligne in lignes_metro + lignes_rer:
		prefixe = "METRO_" if ligne in lignes_metro else "RER_"
		if not isfile(prefixe + ligne + ".txt"):
			print("Erreur : ligne du", prefixe[:-1].lower(), "'" + ligne + "' introuvable.")
			continue
		
		print("Chargement de la ligne du", prefixe[:-1].lower(), ligne + "...", end=' ')

		if chargement_ok(reseau, prefixe + ligne + ".txt"):
			print("terminé.")
		else:
			print("échec.")

	print("Le réseau contient", reseau.nombre_sommets(), "sommets et", reseau.nombre_aretes(), "arêtes.")

def afficher_stations(reseau):
	""" Affiche la liste des stations constituant le réseau sous la forme 'nom (id)' dans l'ordre alphabétique. """
	print("\nLe réseau contient les", reseau.nombre_sommets(), "stations suivantes :")

	for station in sorted(reseau.sommets(), key=reseau.nom_sommet):
		print(reseau.nom_sommet(station), '(' + str(station) + ')')

def afficher_ponts(reseau):
	""" Affiche la liste des ponts du réseau dans l'ordre alphabétique de la première extrémitée du pont. """
	lst_ponts = ponts(reseau)

	print("\nLe réseau contient les", len(lst_ponts), "ponts suivants :")

	for u, v in sorted(lst_ponts, key=lambda pont: reseau.nom_sommet(pont[0])):
		u, v = sorted((reseau.nom_sommet(u), reseau.nom_sommet(v)))
		print('\t-', u, '--', v)

def afficher_points_articulations(reseau):
	""" Affiche la liste des points d'articulation du réseau dans l'ordre alphabétique. """
	lst_points = points_articulation(reseau)

	print("\nLe réseau contient les", len(lst_points), "points d'articulations suivants :")

	for i, point in enumerate(sorted(lst_points, key=reseau.nom_sommet)):
		print("\t" + str(i+1) + ":", reseau.nom_sommet(point))

def afficher_ameliorations_points_articulations(reseau):
	""" Affiche la liste des arêtes à rajouter au réseau pour supprimer ses points d'articulations dans l'ordre alphabétique de la première extrémitée. """
	lst_ameliorations = amelioration_points_articulation(reseau)

	print("\nOn peut éliminer tous les points d'articulations du réseau en rajoutant les", len(lst_ameliorations), "arêtes suivantes :")

	for u, v in sorted(lst_ameliorations, key=lambda arete: reseau.nom_sommet(arete[0])):
		u, v = sorted((reseau.nom_sommet(u), reseau.nom_sommet(v)))
		print('\t-', u, '--', v)

def afficher_ameliorations_ponts(reseau):
	""" Affiche la liste des arêtes à rajouter au réseau pour supprimer ses ponts dans l'ordre alphabétique de la première extrémitée. """
	lst_ameliorations = amelioration_ponts(reseau)

	print("\nOn peut éliminer tous les ponts du réseau en rajoutant les", len(lst_ameliorations), "arêtes suivantes :")

	for u, v in sorted(lst_ameliorations, key=lambda arete: reseau.nom_sommet(arete[0])):
		u, v = sorted((reseau.nom_sommet(u), reseau.nom_sommet(v)))
		print('\t-', u, '--', v)


def main():
	reseau = Graphe()
	parser = ArgumentParser(description="Ce programme charge des données depuis des fichiers et construit un réseau. Il est ensuite possible d'identifier les ponts et points d'articulation et d'afficher les connexions à rajouter pour les supprimer.", add_help=False)

	# Ajout des arguments un par un.
	parser.add_argument("-h", "--help", help="Indiquez les lignes à charger avec --metro et/ou --rer puis affichez des informations sur le réseau ainsi créé avec les options suivantes.", action="help")
	parser.add_argument("--metro", help="Précise les lignes de métro à charger. Si rien n'est spécifié, alors toutes les lignes de métro dans le répertoire courant sont chargées.", type=str, metavar="lignes", nargs='*', default=None)
	parser.add_argument("--rer", help="Précise les lignes de RER à charger. Si rien n'est spécifié, alors toutes les lignes de RER dans le répertoire courant sont chargées.", type=str, metavar="lignes", nargs='*', default=None)
	parser.add_argument("--liste-stations", help="Affiche la liste des stations du réseau avec leur identifiant triées par ordre alphabétique.", action="store_true")
	parser.add_argument("--articulations", help="Affiche les points d’articulation du réseau qui a été chargé.", action="store_true")
	parser.add_argument("--ponts", help="Affiche les ponts du réseau qui a été chargé.", action="store_true")
	parser.add_argument("--ameliorer-articulations", help="Affiche les points d’articulation du réseau qui a été chargé, ainsi que les arêtes à rajouter pour que ces stations ne soient plus des points d’articulation.", action="store_true")
	parser.add_argument("--ameliorer-ponts", help="Affiche les ponts du réseau qui a été chargé, ainsi que les arêtes à rajouter pour que ces arêtes ne soient plus des ponts.", action="store_true")

	args = parser.parse_args()

	charger_lignes(reseau, args.metro, args.rer)

	if args.liste_stations:
		afficher_stations(reseau)
	if args.ponts:
		afficher_ponts(reseau)
	if args.articulations:
		afficher_points_articulations(reseau)
	if args.ameliorer_articulations:
		afficher_ameliorations_points_articulations(reseau)
	if args.ameliorer_ponts:
		afficher_ameliorations_ponts(reseau)

if __name__ == '__main__':
	main()