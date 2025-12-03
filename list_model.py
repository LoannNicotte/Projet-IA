import google.generativeai as genai

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyC0xKBtLdj17M6HjFY1P4t3nl7nikYIk94" # Collez votre clé ici

genai.configure(api_key=GOOGLE_API_KEY)

print("🔍 Recherche des modèles disponibles pour votre clé API...\n")

try:
    # On parcourt la liste des modèles
    for m in genai.list_models():
        
        # On filtre : on ne veut que ceux qui savent générer du texte/chat
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Modèle : {m.name}")
            print(f"   Nom complet : {m.display_name}")
            print(f"   Description : {m.description}...") # On coupe la description
            print(f"   Limite Entrée : {m.input_token_limit} tokens")
            print(f"   Limite Sortie : {m.output_token_limit} toke ns")
            print("-" * 40)

except Exception as e:
    print(f"❌ Erreur lors de la connexion : {e}")