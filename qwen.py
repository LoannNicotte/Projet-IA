import ollama
import json
import os
import time

# --- CONFIGURATION MATÉRIEL HAUT DE GAMME ---
# Avec 16Go VRAM, on utilise le 14 Milliards de paramètres
MODEL = "qwen2.5:14b" 

INPUT_FILE = "tous_les_arrets.jsonl"
OUTPUT_FILE = "dataset_resultats_ia.jsonl"

# Prompt un peu plus "intello" car le modèle peut comprendre des nuances
SYSTEM_PROMPT = """
Tu es un expert en Data Science juridique.
Analyse la décision de justice fournie.

OBJECTIF : Construire une base de données pour la justice prédictive (Quantum).
1. Repère s'il y a une condamnation pécuniaire (Dommages-intérêts, Rappel de salaire, Indemnités rupture).
2. Pour chaque condamnation, extrais :
   - Le motif juridique précis.
   - Le montant (converti en float).
   - Les facteurs clés qui ont influencé le juge (ex: "15 ans d'ancienneté", "Salarié protégé", "Faute grave écartée").
3. Ignore strictement les dépens et l'article 700.

FORMAT DE SORTIE (JSON UNIQUEMENT) :
{
  "statut_analyse": "succes",
  "juridiction_confirmee": boolean (est-ce que la cour confirme le jugement de 1ere instance ?),
  "prejudices": [
    {
      "type": "ex: Licenciement sans cause réelle et sérieuse",
      "montant": 15000.0,
      "elements_decisionnels": ["ancienneté 12 ans", "entreprise < 11 salariés"]
    }
  ]
}
"""

def main():
    print(f"🚀 Démarrage avec le modèle PUISSANT : {MODEL}")

    # Gestion de la reprise
    ids_faits = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "id_decision" in data: ids_faits.add(data["id_decision"])
                except: pass

    # Compteur pour la barre de progression
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)

    with open(INPUT_FILE, "r", encoding="utf-8") as f_in, \
         open(OUTPUT_FILE, "a", encoding="utf-8") as f_out:
        
        for i, line in enumerate(f_in):
            if i < 2911:
                continue  # Sauter les 800 premières lignes pour test rapide
            try:
                decision = json.loads(line)
                id_doc = decision.get("id")
                
                # Qwen 14B a une excellente mémoire, on envoie TOUT le texte
                # Plus besoin de tronquer à 15000 caractères
                texte = decision.get("text", "")

                if id_doc in ids_faits: continue

                print(f"⚡ [{i}/{total_lines}] Traitement ID {id_doc}...", end="\r")

                # Pas de limite de contexte artificielle, on laisse le modèle gérer
                response = ollama.chat(
                    model=MODEL,
                    messages=[
                        {'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': f"Décision ID {id_doc} :\n\n{texte}"}
                    ],
                    format='json', 
                    options={
                        'temperature': 0.1,
                        'num_ctx': 8192 # On force 8k contexte pour être sûr que tout rentre
                    } 
                )

                content_str = response['message']['content']
                resultat = json.loads(content_str)
                
                # Si le modèle a trouvé quelque chose d'intéressant
                if resultat.get("prejudices") and len(resultat["prejudices"]) > 0:
                    resultat["id_decision"] = id_doc
                    json.dump(resultat, f_out, ensure_ascii=False)
                    f_out.write("\n")
                    f_out.flush()
                    print(f"✅ {id_doc} : {len(resultat['prejudices'])} préjudice(s) extrait(s).      ")
                else:
                    # Optionnel : garder une trace des échecs/vides pour stats
                    # log_vide = {"id_decision": id_doc, "statut": "vide"}
                    # json.dump(log_vide, f_out) ; f_out.write("\n") ; f_out.flush()
                    pass

            except Exception as e:
                print(f"\n❌ Erreur sur {id_doc}: {e}")
                continue

if __name__ == "__main__":
    main()