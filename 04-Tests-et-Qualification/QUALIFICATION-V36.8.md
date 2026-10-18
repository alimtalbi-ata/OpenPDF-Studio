# Qualification V36.8

Scénarios : découpage réussi, collision sans écrasement, injection d’échec à la deuxième publication avec rollback, lot invalide, source inchangée.

**Limite :** la publication de plusieurs fichiers n’est pas atomique vis-à-vis d’un lecteur concurrent ; un arrêt brutal du processus peut laisser des résultats partiels ou un verrou orphelin. Le rollback couvre les exceptions interceptées, pas la perte d’alimentation.
