import requests
import json
import time
import os

# --- VOS IDENTIFIANTS ---
CLIENT_ID = "b3a5a14c-b984-41c0-b713-02fa93141335"
CLIENT_SECRET = "9ec43178-a51f-4741-9ca2-6f909f97a42e"

# --- CONFIGURATION ---
AUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
DECISION_URL = "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0/decision"

# Vos 3 fichiers
FILE_A_FAIRE = "export_arrets.txt"       # La source (va diminuer)
FILE_RESULTAT = "tous_les_arrets.jsonl"  # Le stockage (va grossir)
FILE_FAIT = "ids_termines.txt"           # Le journal (va grossir)

class JudilibreWorker:
    def __init__(self):
        self.token = None
        self.token_time = 0

    def get_token(self):
        # Renouvelle le token s'il a plus de 55 minutes
        if self.token and (time.time() - self.token_time < 3300):
            return self.token

        try:
            response = requests.post(AUTH_URL, data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": "openid"
            })
            response.raise_for_status()
            self.token = response.json()["access_token"]
            self.token_time = time.time()
            return self.token
        except Exception as e:
            print(f"⛔ Erreur Token : {e}")
            return None

    def download_one(self, id_decision):
        token = self.get_token()
        if not token: return None

        try:
            # On appelle l'endpoint /decision pour avoir le texte complet
            resp = requests.get(
                DECISION_URL,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                params={"id": id_decision}
            )
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return "not_found" # On considère comme traité même si vide
            elif resp.status_code == 429:
                print("⏳ Quota ! Pause 10s...")
                time.sleep(10)
                return self.download_one(id_decision) # On réessaye
            else:
                print(f"❌ Erreur {resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erreur Réseau : {e}")
            return None

def remove_id_from_todo(filename, id_to_remove):
    """Supprime la première ligne (l'ID qu'on vient de faire)"""
    try:
        with open(filename, 'r', encoding='utf-8') as fin:
            data = fin.read().splitlines(True)
        if data:
            with open(filename, 'w', encoding='utf-8') as fout:
                fout.writelines(data[1:])
    except Exception as e:
        print(f"Erreur fichier : {e}")

def main():
    worker = JudilibreWorker()
    
    if not os.path.exists(FILE_A_FAIRE):
        print(f"❌ Le fichier {FILE_A_FAIRE} n'existe pas !")
        return

    print(f"🚀 Démarrage du traitement sécurisé...")

    while True:
        # 1. On lit le PREMIER ID de la liste
        current_id = None
        with open(FILE_A_FAIRE, "r", encoding="utf-8") as f:
            line = f.readline()
            if not line:
                print("🎉 La liste est vide ! Tout est fini.")
                break
            current_id = line.strip()

        if not current_id: continue

        # 2. On télécharge
        print(f"Traitement ID {current_id}...", end="\r")
        data = worker.download_one(current_id)

        # 3. Si succès, on sauvegarde et on nettoie les fichiers
        if data:
            # A. Sauvegarde JSONL (Sauf si 404)
            if data != "not_found":
                with open(FILE_RESULTAT, "a", encoding="utf-8") as f_json:
                    json.dump(data, f_json, ensure_ascii=False)
                    f_json.write("\n")
            
            # B. Ajout dans la liste "FAIT"
            with open(FILE_FAIT, "a", encoding="utf-8") as f_done:
                f_done.write(current_id + "\n")
            
            # C. SUPPRESSION de la liste "À FAIRE"
            remove_id_from_todo(FILE_A_FAIRE, current_id)
            
            # Petit log
            print(f"✅ {current_id} traité et archivé.")
        
        else:
            # Si échec critique (réseau/api), on arrête tout pour ne pas perdre l'ID
            print(f"\n⛔ Arrêt sur erreur pour l'ID {current_id}. Relancez plus tard.")
            break

if __name__ == "__main__":
    main()