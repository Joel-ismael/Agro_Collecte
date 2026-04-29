import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Agri-Suivi Pro", page_icon="🚜", layout="wide")

# --- PARAMÈTRES ET LISTES ---
PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

CULTURES_PRO = sorted([
    "Maïs", "Manioc", "Cacao", "Café", "Tomate", "Riz", "Soja", "Palmier à huile", 
    "Hévéa", "Coton", "Banane-Plantein", "Ananas", "Avocat", "Mangue", "Oignon", 
    "Pomme de terre", "Haricot", "Arachide", "Sorgho", "Mil", "Poivre", "Igname", "AUTRE"
])

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('agri_pro_steve.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS recoltes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, date_saisie TEXT, 
                culture TEXT, quantite REAL, prix_unitaire REAL, parcelle TEXT,
                superficie REAL, type_sol TEXT, intrants_nom TEXT, cout_intrants REAL,
                main_d_oeuvre REAL, statut_stock TEXT, humidite REAL, notes TEXT)''')
    conn.commit()
    return conn, c

conn, c = init_db()
def hash_pwd(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

def main():
    if not st.session_state.auth:
        st.title("🚜 Agri-Suivi Pro : Gestion de Précision")
        t_log, t_sign = st.tabs(["Connexion", "Création de compte Professionnel"])

        with t_sign:
            with st.form("signup_pro"):
                c1, c2 = st.columns(2)
                with c1:
                    s_nom, s_pre = st.text_input("Nom"), st.text_input("Prénom")
                    s_em, s_sex = st.text_input("Email"), st.selectbox("Sexe", ["Masculin", "Féminin"])
                with c2:
                    s_pa = st.selectbox("Nationalité", list(PAYS_DATA.keys()))
                    s_ph = st.text_input(f"Téléphone ({PAYS_DATA[s_pa]['code']})")
                    s_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("S'enregistrer"):
                    if re.match(PAYS_DATA[s_pa]["regex"], s_ph):
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                     (s_em, s_nom, s_pre, f"{PAYS_DATA[s_pa]['code']} {s_ph}", hash_pwd(s_pw), s_sex, s_pa))
                            conn.commit()
                            st.success("Compte STEVE créé ! Connectez-vous.")
                        except: st.error("Email déjà utilisé.")
                    else: st.error("Numéro invalide.")

        with t_log:
            with st.form("login_pro"):
                l_nom, l_pre = st.text_input("Nom"), st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Accéder au Tableau de Bord"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_pre, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

    else:
        u_email = st.session_state.user[0]
        st.sidebar.title("🚀 STEVE")
        st.sidebar.caption("Système Expert de Gestion Agricole")
        
        choice = st.sidebar.selectbox("Menu Principal", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if choice == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif choice == "Mon Profil":
            st.header("👤 Paramètres du Compte")
            with st.form("p_edit"):
                n_nom = st.text_input("Nom", value=st.session_state.user[1])
                n_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Mettre à jour"):
                    c.execute('UPDATE users SET nom=?, phone=? WHERE email=?', (n_nom, n_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif choice == "Collecte de Données":
            t1, t2, t3 = st.tabs(["📥 Nouvelle Saisie", "📊 Analyse & Stats", "🛠️ Gestion des Stocks"])

            with t1:
                st.subheader("📝 Fiche de Suivi de Récolte")
                with st.form("form_expert"):
                    col_c1, col_c2 = st.columns(2)
                    c_sel = col_c1.selectbox("Culture", CULTURES_PRO)
                    c_custom = col_c2.text_input("Si AUTRE, nommez la culture ici")
                    final_cult = c_custom if c_sel == "AUTRE" else c_sel
                    
                    c1, c2, c3 = st.columns(3)
                    quant = c1.number_input("Quantité (kg)", min_value=0.0, step=0.1)
                    prix = c2.number_input("Prix unitaire (FCFA)", min_value=0.0)
                    parcelle = c3.text_input("Référence Parcelle")
                    
                    st.write("---")
                    st.info("Paramètres de Production Avancés")
                    c4, c5, c6 = st.columns(3)
                    surf = c4.number_input("Superficie exploitée (Hectares)", min_value=0.0)
                    sol = c5.selectbox("Type de sol", ["Sableux", "Argileux", "Humifère", "Latéritique"])
                    humid = c6.slider("Taux d'humidité (%)", 0, 100, 15)
                    
                    c7, c8, c9 = st.columns(3)
                    int_nom = c7.text_input("Engrais/Intrants utilisés")
                    int_cout = c8.number_input("Coût des intrants (FCFA)", min_value=0.0)
                    main = c9.number_input("Coût Main d'œuvre (FCFA)", min_value=0.0)
                    
                    statut = st.selectbox("Statut actuel", ["En séchage", "Stocké", "Vendu", "Transformé"])
                    notes = st.text_area("Observations techniques")
                    
                    if st.form_submit_button("💾 Enregistrer dans la base STEVE"):
                        c.execute('''INSERT INTO recoltes (user_email, date_saisie, culture, quantite, prix_unitaire, parcelle, superficie, type_sol, intrants_nom, cout_intrants, main_d_oeuvre, statut_stock, humidite, notes) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), final_cult, float(quant), float(prix), parcelle, float(surf), sol, int_nom, float(int_cout), float(main), statut, float(humid), notes))
                        conn.commit()
                        st.success("Donnée agricole sécurisée !")

            with t2:
                st.subheader("📈 Rapport d'Analyse Professionnel")
                df = pd.read_sql_query('SELECT * FROM recoltes WHERE user_email=?', conn, params=(u_email,))
                if not df.empty:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Production Totale", f"{df['quantite'].sum():,.1f} kg")
                    ca = (df['quantite'] * df['prix_unitaire']).sum()
                    k2.metric("Valeur Estimée", f"{ca:,.0f} FCFA")
                    k3.metric("Nombre de Parcelles", df['parcelle'].nunique())
                    
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        fig = px.pie(df, values='quantite', names='culture', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
                        st.plotly_chart(fig, use_container_width=True)
                    with col_g2:
                        st.dataframe(df[['date_saisie', 'culture', 'quantite', 'parcelle', 'statut_stock']], use_container_width=True)
                else:
                    st.warning("⚠️ Aucune donnée disponible.")

            with t3:
                st.subheader("🛠️ Gestion et Modification des données")
                # Sélection de la donnée
                c.execute('SELECT id, culture, parcelle, date_saisie FROM recoltes WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                
                if rows:
                    opt = {f"ID:{r[0]} | {r[1]} - {r[2]} ({r[3]})": r[0] for r in rows}
                    sel_id = st.selectbox("Choisir l'enregistrement à corriger", list(opt.keys()))
                    id_to_edit = opt[sel_id]

                    # Récupération des valeurs actuelles
                    c.execute('SELECT * FROM recoltes WHERE id=?', (id_to_edit,))
                    curr = c.fetchone()

                    # FORMULAIRE DE MODIFICATION
                    st.markdown("---")
                    st.info(f"📍 Mode édition pour : {sel_id}")
                    with st.form("edit_form_expert"):
                        e_c1, e_c2 = st.columns(2)
                        # On pré-sélectionne la culture actuelle si elle est dans la liste
                        idx_cult = CULTURES_PRO.index(curr[3]) if curr[3] in CULTURES_PRO else CULTURES_PRO.index("AUTRE")
                        new_cult_sel = e_c1.selectbox("Modifier Culture", CULTURES_PRO, index=idx_cult)
                        new_cult_cust = e_c2.text_input("Nouvelle culture (si AUTRE)", value=curr[3] if new_cult_sel == "AUTRE" else "")
                        
                        final_edit_cult = new_cult_cust if new_cult_sel == "AUTRE" else new_cult_sel

                        f1, f2, f3 = st.columns(3)
                        new_quant = f1.number_input("Quantité (kg)", value=float(curr[4]), min_value=0.0)
                        new_prix = f2.number_input("Prix unitaire (FCFA)", value=float(curr[5]), min_value=0.0)
                        new_parcelle = f3.text_input("Parcelle", value=curr[6])

                        f4, f5, f6 = st.columns(3)
                        new_surf = f4.number_input("Superficie (Ha)", value=float(curr[7]), min_value=0.0)
                        # Gestion de l'index pour le type de sol
                        sols = ["Sableux", "Argileux", "Humifère", "Latéritique"]
                        idx_sol = sols.index(curr[8]) if curr[8] in sols else 0
                        new_sol = f5.selectbox("Type de sol", sols, index=idx_sol)
                        new_humid = f6.slider("Humidité (%)", 0, 100, int(curr[13]))

                        f7, f8, f9 = st.columns(3)
                        new_int_n = f7.text_input("Intrants", value=curr[9])
                        new_int_c = f8.number_input("Coût Intrants", value=float(curr[10]), min_value=0.0)
                        new_main = f9.number_input("Coût Main d'œuvre", value=float(curr[11]), min_value=0.0)

                        statuts = ["En séchage", "Stocké", "Vendu", "Transformé"]
                        idx_stat = statuts.index(curr[12]) if curr[12] in statuts else 0
                        new_statut = st.selectbox("Statut", statuts, index=idx_stat)
                        new_notes = st.text_area("Notes", value=curr[14])

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("✅ Enregistrer les modifications"):
                            c.execute('''UPDATE recoltes SET 
                                culture=?, quantite=?, prix_unitaire=?, parcelle=?, superficie=?, 
                                type_sol=?, intrants_nom=?, cout_intrants=?, main_d_oeuvre=?, 
                                statut_stock=?, humidite=?, notes=? WHERE id=?''',
                                (final_edit_cult, float(new_quant), float(new_prix), new_parcelle, float(new_surf), 
                                 new_sol, new_int_n, float(new_int_c), float(new_main), new_statut, float(new_humid), new_notes, id_to_edit))
                            conn.commit()
                            st.success("Données mises à jour avec succès !")
                            st.rerun()

                    if st.button("🗑️ Supprimer définitivement cette récolte"):
                        c.execute('DELETE FROM recoltes WHERE id=?', (id_to_edit,))
                        conn.commit()
                        st.success("Enregistrement supprimé.")
                        st.rerun()
                else:
                    st.info("Aucune donnée à gérer.")

if __name__ == '__main__':
    main()