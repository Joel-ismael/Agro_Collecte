import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Agri-Suivi Pro", page_icon="🌾", layout="wide")

# --- DONNÉES PAYS & VALIDATION ---
PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('agri_data_final.db', check_same_thread=False)
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    # Table Collecte Agricole
    c.execute('''CREATE TABLE IF NOT EXISTS recoltes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, date_saisie TEXT, 
                culture TEXT, quantite REAL, prix_vente REAL, parcelle TEXT,
                intrants TEXT, main_d_oeuvre REAL, statut TEXT,
                date_recolte TEXT, notes TEXT)''')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pwd(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- GESTION DE LA SESSION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

# --- CORPS DE L'APPLICATION ---
def main():
    if not st.session_state.auth:
        st.title("🌾 Bienvenue sur Agri-Suivi Pro")
        tab_login, tab_signup = st.tabs(["Se Connecter", "Créer un compte"])

        with tab_signup:
            with st.form("inscription"):
                col1, col2 = st.columns(2)
                with col1:
                    s_nom = st.text_input("Nom")
                    s_pre = st.text_input("Prénom")
                    s_em = st.text_input("Email")
                    s_sex = st.selectbox("Sexe", ["Masculin", "Féminin"])
                with col2:
                    s_pa = st.selectbox("Nationalité", list(PAYS_DATA.keys()))
                    st.info(f"Indicatif pays : {PAYS_DATA[s_pa]['code']}")
                    s_ph = st.text_input("Numéro (sans indicatif)")
                    s_pw = st.text_input("Mot de passe", type='password')
                
                if st.form_submit_button("S'inscrire"):
                    if re.match(PAYS_DATA[s_pa]["regex"], s_ph):
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                     (s_em, s_nom, s_pre, f"{PAYS_DATA[s_pa]['code']} {s_ph}", hash_pwd(s_pw), s_sex, s_pa))
                            conn.commit()
                            st.success("🎉 Compte créé avec succès ! Connectez-vous maintenant.")
                        except: st.error("Erreur : cet email est déjà utilisé.")
                    else: st.error(f"Le format du numéro est incorrect pour le {s_pa}.")

        with tab_login:
            with st.form("connexion"):
                l_nom = st.text_input("Nom")
                l_pre = st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Se connecter"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_pre, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

    else:
        # Interface après connexion
        u_email = st.session_state.user[0]
        st.sidebar.title("🚀 KERIANE")
        st.sidebar.caption("Agri-Suivi (Gestion Agricole)")
        
        menu = st.sidebar.selectbox("Navigation", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("👤 Modifier mes informations personnelles")
            with st.form("profil_form"):
                n_nom = st.text_input("Nom", value=st.session_state.user[1])
                n_pre = st.text_input("Prénom", value=st.session_state.user[2])
                n_em = st.text_input("Email", value=st.session_state.user[0])
                n_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Mettre à jour le profil"):
                    c.execute('UPDATE users SET nom=?, prenom=?, email=?, phone=? WHERE email=?', 
                             (n_nom, n_pre, n_em, n_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Collecte de Données":
            t_saisie, t_analyse, t_gestion = st.tabs(["📥 Saisie", "📊 Analyse", "🛠️ Gestion"])

            with t_saisie:
                with st.form("form_saisie"):
                    colA, colB = st.columns(2)
                    culture = colA.selectbox("Culture", ["Maïs", "Manioc", "Cacao", "Café", "Tomate", "AUTRE"])
                    parcelle = colB.text_input("Nom de la Parcelle")
                    
                    colC, colD = st.columns(2)
                    # Sécurité : Conversion float() forcée pour éviter l'erreur NumberBounds
                    quant = colC.number_input("Quantité récoltée (kg)", min_value=0.0, value=0.0, step=0.1)
                    prix = colD.number_input("Prix de vente (FCFA/kg)", min_value=0.0, value=0.0)
                    
                    st.write("---")
                    colE, colF = st.columns(2)
                    main_d = colE.number_input("Coût Main d'œuvre (FCFA)", min_value=0.0, value=0.0)
                    statut = colF.selectbox("Statut", ["En stock", "Vendu", "Réservé"])
                    
                    notes = st.text_area("Notes additionnelles")
                    
                    if st.form_submit_button("Enregistrer la donnée"):
                        c.execute('''INSERT INTO recoltes (user_email, date_saisie, culture, quantite, prix_vente, parcelle, main_d_oeuvre, statut, notes) 
                                     VALUES (?,?,?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), culture, float(quant), float(prix), parcelle, float(main_d), statut, notes))
                        conn.commit()
                        st.success("Donnée enregistrée avec succès !")

            with t_analyse:
                c.execute('SELECT culture, quantite FROM recoltes WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Culture", "Quantité"])
                    fig = px.pie(df, values='Quantité', names='Culture', title="Répartition des cultures (%)", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                else: st.info("Aucune donnée disponible.")

            with t_gestion:
                c.execute('SELECT id, culture, date_saisie FROM recoltes WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"{r[1]} du {r[2]} (ID:{r[0]})": r[0] for r in rows}
                    sel_id = opt[st.selectbox("Choisir une donnée", list(opt.keys()))]
                    
                    c.execute('SELECT * FROM recoltes WHERE id=?', (sel_id,))
                    curr = c.fetchone()
                    
                    with st.form("edit_data"):
                        st.subheader(f"Modifier : {curr[3]}")
                        # Chargement des valeurs actuelles avec conversion float sécurisée
                        e_q = st.number_input("Modifier Quantité", value=float(curr[4] if curr[4] else 0.0))
                        e_p = st.number_input("Modifier Prix", value=float(curr[5] if curr[5] else 0.0))
                        e_st = st.selectbox("Modifier Statut", ["En stock", "Vendu", "Réservé"])
                        
                        if st.form_submit_button("💾 Mettre à jour"):
                            c.execute('UPDATE recoltes SET quantite=?, prix_vente=?, statut=? WHERE id=?', 
                                     (float(e_q), float(e_p), e_st, sel_id))
                            conn.commit()
                            st.success("Donnée mise à jour !")
                            st.rerun()
                    
                    if st.button("🗑️ Supprimer définitivement"):
                        c.execute('DELETE FROM recoltes WHERE id=?', (sel_id,))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()