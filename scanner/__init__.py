# scanner/__init__.py
# Module de reconnaissance réseau - Projet de fin d'année Cybersécurité
# Lab pédagogique Red Team / Blue Team - Environnement isolé et contrôlé
#
# Ce module expose la fonction principale run_network_scan()
# utilisable directement depuis main.py ou tout autre orchestrateur.

from .network_scanner import run_network_scan

__all__ = ["run_network_scan"]
